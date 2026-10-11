"""Business calculations. No Streamlit calls and no generated recommendations."""
import numpy as np
import pandas as pd


def ratio(numerator, denominator):
    return numerator / denominator if denominator else np.nan


def revenue_rows(d):
    parts = []
    for name, stream in [('license_revenue', 'License'), ('support_revenue', 'Support'), ('services_revenue', 'Services')]:
        df = d[name].copy()
        if stream == 'Services':
            df = df.merge(d['projects'][['project_id', 'customer_id']], on='project_id', validate='many_to_one')
        df['stream'] = stream
        parts.append(df[['customer_id', 'revenue_date', 'amount_usd', 'stream']])
    return pd.concat(parts, ignore_index=True)


def cost_rows(d):
    """Allocate each engineering log using associations known on that work date."""
    logs = d['worklogs'].copy()
    logs['cost_usd'] = logs.minutes / 60 * logs.hourly_cost_usd
    parts = []
    for activity, source, key in [('Support', 'support_cases', 'case_id'), ('Services', 'projects', 'project_id')]:
        part = logs[logs.activity.eq(activity)].merge(d[source][[key, 'customer_id']], on=key, validate='many_to_one')
        part['category'] = activity
        parts.append(part[['customer_id', 'work_date', 'cost_usd', 'category']])
    engineering = logs[logs.activity.eq('Engineering')]
    joined = engineering.merge(d['defect_customers'], on='defect_id', how='left')
    eligible = joined[joined.associated_at.notna() & (joined.associated_at <= joined.work_date)].copy()
    eligible['cost_usd'] /= eligible.groupby('worklog_id').worklog_id.transform('size')
    eligible['category'] = 'Shared fix'
    parts.append(eligible[['customer_id', 'work_date', 'cost_usd', 'category']])
    unallocated = engineering[~engineering.worklog_id.isin(eligible.worklog_id)].copy()
    unallocated['customer_id'] = ''
    unallocated['category'] = 'Internal quality'
    parts.append(unallocated[['customer_id', 'work_date', 'cost_usd', 'category']])
    license_cost = d['license_revenue'].rename(columns={'revenue_date': 'work_date', 'delivery_cost_usd': 'cost_usd'}).copy()
    license_cost['category'] = 'License delivery'
    parts.append(license_cost[['customer_id', 'work_date', 'cost_usd', 'category']])
    return pd.concat(parts, ignore_index=True)


def customer_results(d, year, revenue=None, costs=None):
    revenue = revenue if revenue is not None else revenue_rows(d)
    costs = costs if costs is not None else cost_rows(d)
    rev = revenue[revenue.revenue_date.dt.year.eq(year)]
    cost = costs[costs.work_date.dt.year.eq(year) & costs.customer_id.ne('')]
    ids = set(d['customer_years'].loc[d['customer_years'].year.eq(year), 'customer_id']) | set(rev.customer_id) | set(cost.customer_id)
    out = d['customers'][d['customers'].customer_id.isin(ids)][['customer_id', 'customer_name', 'industry']].set_index('customer_id')
    for stream in ['License', 'Support', 'Services']:
        out[stream] = rev[rev.stream.eq(stream)].groupby('customer_id').amount_usd.sum()
    for category in ['License delivery', 'Support', 'Services', 'Shared fix']:
        out[category + ' cost'] = cost[cost.category.eq(category)].groupby('customer_id').cost_usd.sum()
    out = out.fillna(0)
    out['Revenue'] = out[['License', 'Support', 'Services']].sum(axis=1)
    out['Delivery cost'] = out[[c for c in out.columns if c.endswith(' cost')]].sum(axis=1)
    out['Contribution'] = out.Revenue - out['Delivery cost']
    out['Margin %'] = out.Contribution.div(out.Revenue.replace(0, np.nan)) * 100
    case_counts = d['support_cases'].loc[d['support_cases'].created_at.dt.year.eq(year)].groupby('customer_id').size()
    out['Cases'] = case_counts.reindex(out.index, fill_value=0)
    # Both numerators below use selected-year activity, not a mixture of lifetime logs and yearly cases.
    support_logs = d['worklogs'][d['worklogs'].activity.eq('Support') & d['worklogs'].work_date.dt.year.eq(year)].merge(d['support_cases'][['case_id', 'customer_id']], on='case_id')
    out['Support hours'] = support_logs.groupby('customer_id').minutes.sum().div(60).reindex(out.index, fill_value=0)
    out = out.reset_index().merge(d['customer_years'][d['customer_years'].year.eq(year)].drop(columns='year'), on='customer_id', how='left')
    out['Usage %'] = out.active_users.div(out.licensed_users.replace(0, np.nan)) * 100
    out['Cases / 100 active users'] = out.Cases.div(out.active_users.replace(0, np.nan)) * 100
    out['Support cost / $1k support revenue'] = out['Support cost'].add(out['Shared fix cost']).div(out.Support.replace(0, np.nan)) * 1000
    return out.sort_values('Contribution', ascending=False)


def annual_results(d, revenue=None, costs=None):
    revenue = revenue if revenue is not None else revenue_rows(d)
    costs = costs if costs is not None else cost_rows(d)
    rows = []
    for year in sorted(d['periods'].year):
        rev = revenue[revenue.revenue_date.dt.year.eq(year)]
        cost = costs[costs.work_date.dt.year.eq(year)]
        expenses = d['operating_expenses'].loc[d['operating_expenses'].expense_date.dt.year.eq(year), 'amount_usd'].sum()
        row = {'Year': year, 'Revenue': rev.amount_usd.sum(), 'Delivery cost': cost.cost_usd.sum(), 'Operating expenses': expenses}
        row.update({stream: rev.loc[rev.stream.eq(stream), 'amount_usd'].sum() for stream in ['License', 'Support', 'Services']})
        row['Contribution'] = row['Revenue'] - row['Delivery cost']
        row['Operating profit'] = row['Contribution'] - expenses
        row['Operating margin %'] = ratio(row['Operating profit'], row['Revenue']) * 100
        row['Internal quality cost'] = cost.loc[cost.category.eq('Internal quality'), 'cost_usd'].sum()
        rows.append(row)
    result = pd.DataFrame(rows)
    previous = result.set_index('Year').Revenue
    result['Revenue YoY %'] = [ratio(row.Revenue - previous.get(row.Year-1, np.nan), previous.get(row.Year-1, np.nan))*100 for row in result.itertuples()]
    return result


def case_view(d, year, customer=None):
    """Created-year cohort with effort observed only through that year's cutoff."""
    cutoff = pd.Timestamp(year, 12, 31, 23, 59, 59)
    cases = d['support_cases'][d['support_cases'].created_at.dt.year.eq(year)].copy()
    if customer:
        cases = cases[cases.customer_id.eq(customer)]
    cases = cases.merge(d['topics'], on='topic_id', validate='many_to_one')
    logs = d['worklogs'][d['worklogs'].activity.eq('Support') & (d['worklogs'].work_date <= cutoff)]
    effort = logs.groupby('case_id').minutes.sum()
    cases['handling_minutes'] = cases.case_id.map(effort)  # Missing logs are unknown, not zero effort.
    responded = cases.first_response_at.notna() & (cases.first_response_at <= cutoff)
    cases['response_hours'] = (cases.first_response_at - cases.created_at).dt.total_seconds()/3600
    age = (cutoff-cases.created_at).dt.total_seconds()/3600
    cases['sla_eligible'] = responded | (age >= cases.response_sla_hours)
    cases['sla_met'] = responded & (cases.response_hours <= cases.response_sla_hours)
    cases['resolved_by_cutoff'] = cases.resolved_at.notna() & (cases.resolved_at <= cutoff)
    cases['resolution_days'] = ((cases.resolved_at-cases.created_at).dt.total_seconds()/86400).where(cases.resolved_by_cutoff)
    # Explicit topic and outcome rules, not a claim that historical cases were actually deflected.
    cases['faq_eligible'] = cases.case_type.eq('Q&A') & cases.resolution.eq('Knowledge article') & cases.approved_answer & cases.answer_only & cases.resolved_by_cutoff & cases.handling_minutes.notna()
    return cases


def backlog(d, year, customer=None):
    cutoff = pd.Timestamp(year, 12, 31, 23, 59, 59)
    defects = d['defects']
    mask = (defects.created_at <= cutoff) & (defects.resolved_at.isna() | (defects.resolved_at > cutoff))
    if customer:
        ids = d['defect_customers'].loc[d['defect_customers'].customer_id.eq(customer) & (d['defect_customers'].associated_at <= cutoff), 'defect_id']
        mask &= defects.defect_id.isin(ids)
    return defects[mask]


def automation_opportunities(d, year, success=.6, maintenance_hours=4, customer=None):
    years = [y for y in range(year-2, year+1) if y in set(d['periods'].year)]
    cohorts = {y: case_view(d, y, customer) for y in years}
    rows = []
    for topic in d['topics'].itertuples():
        row = {'Topic': topic.functionality, 'Area': topic.product_area, 'topic_id': topic.topic_id}
        for y, cases in cohorts.items():
            row[str(y)] = int(cases.topic_id.eq(topic.topic_id).sum())
        latest = cohorts[year]
        latest = latest[latest.topic_id.eq(topic.topic_id)]
        eligible = latest[latest.faq_eligible]
        row['Eligible cases'] = len(eligible)
        row['Eligible hours'] = eligible.handling_minutes.sum()/60
        row['Estimated net hours freed'] = row['Eligible hours']*success-maintenance_hours
        row['Trend'] = 'Insufficient history' if len(years)<3 else 'Growing' if row[str(year)]>row[str(year-2)] else 'Declining' if row[str(year)]<row[str(year-2)] else 'Flat'
        if not topic.answer_only:
            decision, reason = 'Human-led', 'Resolution may require changes or investigation.'
        elif not topic.approved_answer:
            decision, reason = 'Prepare documentation', 'No approved answer in the topic catalog.'
        elif len(years)<3:
            decision, reason = 'Collect evidence', 'Fewer than three consecutive years are available.'
        elif len(eligible)<12:
            decision, reason = 'Low volume', 'Fewer than 12 eligible cases in the selected year.'
        elif row['Estimated net hours freed']<=0:
            decision, reason = 'Limited time benefit', 'Estimated maintenance exceeds time freed.'
        else:
            decision, reason = 'FAQ pilot candidate', 'Repeated, documented questions with answer-only resolutions.'
        row.update(Recommendation=decision, Reason=reason)
        rows.append(row)
    return pd.DataFrame(rows).sort_values('Estimated net hours freed', ascending=False)


def focus_areas(d, year, customers, annual, cases):
    """Evidence-based observations with a suggested next check, not causal claims."""
    notes = []
    current = annual[annual.Year.eq(year)].iloc[0]
    if pd.notna(current['Revenue YoY %']):
        notes.append(f'Revenue changed {current["Revenue YoY %"]:+.1f}% from {year-1}. Compare the three revenue streams before changing prices or spending.')
    if len(customers):
        worst = customers.sort_values('Contribution').iloc[0]
        notes.append(f'{worst.customer_name} has the lowest customer contribution (${worst.Contribution:,.0f}). Review its fees, support effort and services costs together.')
        top = customers.nlargest(3, 'Revenue').Revenue.sum()
        total = customers.Revenue.sum()
        if total:
            notes.append(f'The top three customers account for {100*top/total:.1f}% of revenue. Review renewal dates and account coverage.')
    if len(cases):
        hours = cases.groupby('product_area').handling_minutes.sum(min_count=1).dropna()
        if len(hours):
            area = hours.idxmax()
            notes.append(f'{area} used {hours[area]/60:,.1f} logged support hours for cases opened in {year}, observed through year-end. Inspect its recurring topics and prevention gaps.')
    return notes
