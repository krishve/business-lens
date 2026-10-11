"""Lenny's supported questions and deterministic, data-backed answers."""
from dataclasses import dataclass
import pandas as pd
from metrics import (annual_results, customer_results, case_view, backlog,
                     automation_opportunities, focus_areas, revenue_rows, cost_rows)


QUESTIONS = {
    'focus': 'Where should I focus this year?',
    'top': 'Which customers contribute the most?',
    'bottom': 'Which customers contribute the least?',
    'losses': 'Which customers are making a loss?',
    'customer': 'What makes up this customer’s profit or loss?',
    'profit': 'How did operating profit change from last year?',
    'revenue': 'Where does our revenue come from?',
    'support': 'Which product areas take the most support time?',
    'defects': 'Which product areas have unresolved defects?',
    'projects': 'Which projects exceeded their hours budget?',
    'faq': 'Which questions could an FAQ agent help with?',
}


@dataclass
class Answer:
    summary: str
    table: pd.DataFrame
    method: str
    next_view: str
    notes: tuple = ()
    chart: tuple | None = None


def money(value):
    return f'${value:,.0f}'


def answer_question(d, year, question, customer_id=None, *, product_area=None, success=.6, maintenance_hours=4):
    """Recalculate for the active dataset and year; never infer missing values."""
    if question not in QUESTIONS:
        raise ValueError('Choose one of Lenny’s supported questions.')
    if year not in set(d['periods'].year):
        raise ValueError('Choose a year included in the loaded data.')
    revenue, costs = revenue_rows(d), cost_rows(d)
    annual = annual_results(d, revenue, costs)
    current = annual.loc[annual.Year.eq(year)].iloc[0]
    customers = customer_results(d, year, revenue, costs)
    contribution_note = 'Customer contribution is revenue minus assigned delivery costs. Shared business expenses and unallocated engineering costs are deducted only at business level.'

    if question in ('top', 'bottom', 'losses'):
        table = customers.sort_values(['Contribution', 'customer_id'], ascending=[question != 'top', True])
        if question == 'losses':
            table = table[table.Contribution.lt(0)]
            summary = f'{len(table)} customers have negative contribution in {year}.' if len(table) else f'No customers have negative contribution in the recorded {year} data.'
        else:
            table = table.head(5)
            summary = f'Here are up to five customers with the {"highest" if question == "top" else "lowest"} contribution in {year}. Tied amounts share the same financial standing.'
            if table.empty:
                summary = f'No customer financial or snapshot records are available for {year}.'
        table = table[['customer_name', 'Revenue', 'Delivery cost', 'Contribution', 'Margin %']].rename(columns={'customer_name': 'Customer'})
        return Answer(summary, table, contribution_note, 'Customers', chart=('Customer', 'Contribution'))

    if question == 'customer':
        match = customers[customers.customer_id.eq(customer_id)]
        if match.empty:
            return Answer('Choose a customer with records in this year.', pd.DataFrame(), contribution_note, 'Customers')
        row = match.iloc[0]
        summary = f'{row.customer_name} recorded {money(row.Revenue)} in revenue and {money(row["Delivery cost"])} in assigned delivery costs in {year}, leaving {money(row.Contribution)} in contribution.'
        table = pd.DataFrame({'Component': ['License revenue', 'Support revenue', 'Services revenue', 'License delivery cost', 'Support cost', 'Services cost', 'Shared fix cost'],
                              'USD': [row.License, row.Support, row.Services, row['License delivery cost'], row['Support cost'], row['Services cost'], row['Shared fix cost']]})
        categories = ['License delivery cost', 'Support cost', 'Services cost', 'Shared fix cost']
        biggest = max(categories, key=lambda c: row[c])
        note = f'The largest assigned cost category is {biggest.lower()} ({money(row[biggest])}). Review its records before deciding what to change.' if row[biggest] > 0 else 'No delivery costs were recorded. Check completeness before interpreting the margin.'
        return Answer(summary, table, contribution_note + ' Shared fix costs use customer associations known on each work date.', 'Customers', (note, 'This breakdown explains the calculation, not the cause of the customer’s behavior.'), ('Component', 'USD'))

    if question == 'profit':
        previous = annual[annual.Year.eq(year - 1)]
        method = 'Operating profit = revenue − recorded delivery costs − operating expenses, before tax and financing. Only the immediately preceding calendar year is compared.'
        if previous.empty:
            return Answer(f'I cannot compare {year} with {year-1}: the previous year is not loaded.', annual.loc[annual.Year.eq(year), ['Year', 'Revenue', 'Delivery cost', 'Operating expenses', 'Operating profit']], method, 'Business overview')
        old = previous.iloc[0]
        fields = ['Revenue', 'Delivery cost', 'Operating expenses', 'Operating profit']
        table = pd.DataFrame({'Measure': fields, str(year-1): [old[f] for f in fields], str(year): [current[f] for f in fields], 'Change (USD)': [current[f]-old[f] for f in fields]})
        change = current['Operating profit'] - old['Operating profit']
        summary = f'Operating profit {"increased" if change > 0 else "decreased" if change < 0 else "was unchanged"}{" by " + money(abs(change)) if change else ""} from {year-1} to {year}, reaching {money(current["Operating profit"])}.'
        return Answer(summary, table, method, 'Business overview', ('Higher revenue adds to profit; higher costs reduce it. Dollar changes remain meaningful when the previous profit was zero or negative.',))

    if question == 'revenue':
        table = pd.DataFrame({'Source': ['License', 'Support', 'Services'], 'Revenue (USD)': [current.License, current.Support, current.Services]})
        return Answer(f'Total recorded revenue is {money(current.Revenue)} in {year}.', table, 'Revenue uses the recognition date in the three revenue tables. Consulting revenue is linked to customers through projects.', 'Business overview', chart=('Source', 'Revenue (USD)'))

    if question == 'support':
        cases = case_view(d, year, customer_id)
        if product_area and product_area != 'All areas':
            cases = cases[cases.product_area.eq(product_area)]
        table = cases.groupby('product_area', as_index=False).agg(Cases=('case_id', 'size'), Known_minutes=('handling_minutes', lambda s: s.sum(min_count=1)), Missing_effort=('handling_minutes', lambda s: int(s.isna().sum())))
        table['Recorded hours'] = table.pop('Known_minutes') / 60
        table = table.rename(columns={'product_area': 'Product area', 'Missing_effort': 'Cases missing effort'}).sort_values('Recorded hours', ascending=False, na_position='last')
        known = table.dropna(subset=['Recorded hours'])
        summary = f'{known.iloc[0]["Product area"]} has the most recorded support effort: {known.iloc[0]["Recorded hours"]:,.1f} hours.' if len(known) else 'There is no recorded handling effort for cases opened in this year.'
        return Answer(summary, table, 'Cases opened in the selected year; logged handling effort observed through December 31. Blank effort is unknown, not zero. Unresolved cases may need more work.', 'Support insights', chart=('Product area', 'Recorded hours'))

    if question == 'defects':
        defects = backlog(d, year).merge(d['topics'][['topic_id', 'product_area']], on='topic_id', validate='many_to_one')
        table = defects.groupby('product_area').size().reset_index(name='Unresolved defects').rename(columns={'product_area': 'Product area'}).sort_values('Unresolved defects', ascending=False)
        return Answer(f'{len(defects)} distinct defects were unresolved at the end of {year}.', table, 'Includes carryover defects created on or before December 31 and not resolved by then. Each defect is counted once, regardless of how many customers reported it.', 'Product quality', chart=('Product area', 'Unresolved defects'))

    if question == 'projects':
        cutoff = pd.Timestamp(year, 12, 31, 23, 59, 59)
        logs = d['worklogs'][d['worklogs'].activity.eq('Services') & (d['worklogs'].work_date <= cutoff)]
        sr = d['services_revenue']
        active = set(logs.loc[logs.work_date.dt.year.eq(year), 'project_id']) | set(sr.loc[sr.revenue_date.dt.year.eq(year), 'project_id'])
        table = d['projects'][d['projects'].project_id.isin(active)].copy()
        table['Lifetime hours'] = table.project_id.map(logs.groupby('project_id').minutes.sum()/60).fillna(0)
        table['Hours over budget'] = table['Lifetime hours'] - table.budget_hours
        table = table[table['Hours over budget'].gt(0)].sort_values('Hours over budget', ascending=False)
        table = table[['project_id', 'project_name', 'budget_hours', 'Lifetime hours', 'Hours over budget']].rename(columns={'project_id': 'Project ID', 'project_name': 'Project', 'budget_hours': 'Budget hours'})
        return Answer(f'{len(table)} projects active in {year} exceeded their hours budget by year-end.', table, 'Active means recorded services revenue or services work in the year. Compares lifetime logged hours through year-end with the whole-project hours budget; this is not a profit calculation.', 'Services')

    if question == 'faq':
        table = automation_opportunities(d, year, success, maintenance_hours)
        candidates = table[table.Recommendation.eq('FAQ pilot candidate')]
        summary = f'{len(candidates)} topics qualify for a trial, with an estimated {candidates["Estimated net hours freed"].sum():.1f} net hours freed per year.' if len(candidates) else 'No topics qualify for an FAQ trial under the current rules. The table explains what each topic needs.'
        return Answer(summary, table.drop(columns='topic_id'), f'Requires three consecutive years, an approved answer-only topic, at least 12 eligible cases in the selected year, and positive estimated time benefit. Assumptions: {success:.0%} success and {maintenance_hours:g} maintenance hours per topic per year.', 'FAQ opportunities', ('These are estimates, not measured savings. Topic readiness uses the current catalog; no FAQ agent is running. Change assumptions on the FAQ opportunities page.',))

    cases = case_view(d, year)
    notes = tuple(focus_areas(d, year, customers, annual, cases))
    return Answer('Here are the checks suggested by the recorded data.' if notes else 'There is not enough recorded activity to suggest a focus area.', annual.loc[annual.Year.eq(year), ['Year', 'Revenue', 'Delivery cost', 'Operating expenses', 'Operating profit']], 'Fixed checks cover revenue change, lowest customer contribution, customer revenue concentration and support effort. Suggestions are not proof of cause.', 'Business overview', notes)
