"""Business Lens: a local dashboard for software revenue and delivery effort."""
from pathlib import Path
import io
import zipfile
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data_loader import DataError, read_files
from schema import SCHEMAS, fields
from metrics import (revenue_rows, cost_rows, customer_results, annual_results,
                     case_view, backlog, automation_opportunities, focus_areas, ratio)

ROOT = Path(__file__).resolve().parent
COLORS = ['#635BDB', '#138A83', '#DB9841', '#B85264', '#617A9C']
st.set_page_config(page_title='Business Lens', page_icon='📊', layout='wide')
st.markdown('''<style>
div[data-testid="stMetric"] {border:1px solid #8899aa40;border-radius:10px;padding:16px}
div[data-testid="stMetricValue"] {font-size:1.7rem}
.block-container {padding-top:2rem;max-width:1450px}
</style>''', unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def prepare(files):
    data = read_files(files)
    revenue = revenue_rows(data)
    costs = cost_rows(data)
    return data, revenue, costs, annual_results(data, revenue, costs)


def money(value):
    return 'N/A' if pd.isna(value) else f'${value:,.0f}'


def percent(value):
    return 'N/A' if pd.isna(value) else f'{value:.1f}%'


def chart(fig):
    fig.update_layout(margin=dict(l=10, r=10, t=35, b=15), font=dict(size=13),
                      legend_title_text='', colorway=COLORS, height=350)
    st.plotly_chart(fig, width='stretch', config={'displaylogo': False})


def show_table(df, key, height='auto'):
    display = df.copy()
    for col in display.select_dtypes('number'):
        display[col] = display[col].round(2)
    st.dataframe(display, hide_index=True, width='stretch', height=height)
    st.download_button('Download this table', display.to_csv(index=False).encode('utf-8'),
                       file_name=f'{key}.csv', mime='text/csv', key=f'download_{key}')


def kpis(items):
    for col, (label, value, help_text) in zip(st.columns(len(items)), items):
        col.metric(label, value, help=help_text)


def pick_customer(d, key):
    options = {'All customers': None, **dict(zip(d['customers'].customer_name, d['customers'].customer_id))}
    selected = st.selectbox('Customer', list(options), key=key)
    return options[selected]


st.sidebar.title('Business Lens')
st.sidebar.caption('Revenue, customer value and support effort')
source = st.sidebar.radio('Input data', ['Sample data', 'Upload CSV files'])
page = st.sidebar.radio('View', ['Intro', 'Business overview', 'Customers', 'Services', 'Support insights',
                                  'Product quality', 'Support team', 'FAQ opportunities', 'Data & definitions'])
if source == 'Upload CSV files':
    st.sidebar.caption('Upload the complete set. Use name__2025.csv for annual exports of the same table. Files are kept in this session, not written to disk.')
    uploads = st.sidebar.file_uploader('CSV inputs', type='csv', accept_multiple_files=True)
if page == 'Intro':
    st.title('Welcome to Business Lens')
    st.caption('Understand what your customers earn for your business and what it costs to serve them.')
    st.write('Business Lens brings together software sales, support fees, consulting work and the time spent helping customers. It helps you see how your business is doing, which customers leave the most money after delivery costs, and where you could improve.')
    st.info('Start with Sample data to explore five years of fictional business records (2021–2025). No upload or setup is needed to try the dashboard.')

    st.subheader('What can you learn?')
    left, right = st.columns(2)
    with left:
        st.markdown('**Where does the money go?**')
        st.write('Compare revenue with delivery costs and operating expenses. See how results change from one year to the next.')
        st.markdown('**Which customers are worth more to the business?**')
        st.write('Rank customers by the money left after serving them. Compare support effort, product usage, training and custom changes to understand what to investigate.')
    with right:
        st.markdown('**Where is the team spending time?**')
        st.write('Explore consulting hours, customer questions and product defects. Find product areas with repeated problems or gaps in testing and guidance.')
        st.markdown('**Which questions might an FAQ agent help answer?**')
        st.write('Review repeated questions across three years and estimate time that might be saved. This is a planning tool; it does not run an FAQ agent.')

    st.subheader('How to get started')
    st.markdown("""1. Leave **Input data** set to **Sample data** for your first visit.
2. Choose **Business overview** under **View** in the sidebar to see revenue, costs and profit.
3. Select a **Year** to review that period. YoY means the change from the previous year.
4. Open **Customers** to compare the most and least profitable accounts, then explore support and product quality to look for reasons.
5. Use the filters where available and **Download this table** to save a table as a CSV file.""")

    st.subheader('Choose a view')
    st.table(pd.DataFrame([
        ('Business overview', 'How much did we earn, what did it cost, and how did profit change?'),
        ('Customers', 'Which customers leave the most or least money after delivery costs?'),
        ('Services', 'Which consulting projects earn money, and which use more hours than planned?'),
        ('Support insights', 'What do customers ask about, and which topics take the most effort?'),
        ('Product quality', 'Where do defects occur, who finds them, and what is still unresolved?'),
        ('Support team', 'How is work shared, how quickly do we respond, and what do customers think?'),
        ('FAQ opportunities', 'Which repeated questions could be worth a trial with an FAQ agent?'),
        ('Data & definitions', 'What data was loaded, how are figures calculated, and do costs add up?'),
    ], columns=['View', 'What it helps you answer']), hide_index=True)

    with st.expander('A few terms in plain language'):
        st.markdown('**Revenue:** income recorded from software licenses, annual support and consulting services.')
        st.markdown('**Delivery costs:** recorded costs of providing licenses, consulting, support and engineering fixes. Time costs use hours worked multiplied by the hourly cost.')
        st.markdown('**Customer contribution:** customer revenue minus the delivery costs assigned to that customer. Shared business expenses and engineering costs that cannot be assigned to customers are deducted at the business level.')
        st.markdown('**Operating profit:** total revenue minus all recorded delivery costs and operating expenses, before tax and financing.')
        st.markdown('**Margin:** the money left as a percentage of revenue. **Handling time** is time spent working on a case, rather than the full time a customer waits for a resolution.')

    with st.expander('Use your own CSV files'):
        st.write('Open Data & definitions with Sample data selected and download the CSV set to see the required files and columns. Replace the fictional records with your own data using the same structure.')
        st.write('Choose Upload CSV files and upload the complete set of 15 tables together, including headers for tables with no records. Use complete calendar years; the app checks the files and explains any errors before showing results. Select a dashboard view to review them.')
        st.caption('Keep real customer records out of a public GitHub repository. Use the fictional sample for a public demonstration.')

    st.caption('Results depend on the data provided. Comparisons suggest questions to investigate, not proven causes. FAQ savings are estimates, and team figures should be read alongside case difficulty and survey response rates.')
    st.stop()
if source == 'Sample data':
    files = tuple((p.name, p.read_bytes()) for p in sorted((ROOT/'data'/'sample').glob('*.csv')))
else:
    if not uploads:
        st.title('Load your business data')
        st.write('Select the CSV files together. Each table needs a file, even if it contains only its headers.')
        st.code('\n'.join(name+'.csv' for name in SCHEMAS))
        st.info('Use the sample CSV headers as templates. Full calendar years only. Do not include real customer data in a public repository.')
        st.stop()
    files = tuple((f.name, f.getvalue()) for f in uploads)
try:
    d, revenue, costs, annual = prepare(files)
except DataError as exc:
    st.title('Check the input files')
    for message in str(exc).splitlines():
        st.error(message)
    st.stop()

years = sorted(d['periods'].year.tolist(), reverse=True)
year = st.sidebar.selectbox('Year', years)
st.sidebar.caption(f'{len(d["customers"])} customers · {min(years)}–{max(years)}')
st.sidebar.caption('Fictional sample data' if source=='Sample data' else 'Uploaded data · validated')
st.title(page)
st.caption(f'{year} · USD · Complete calendar year · Revenue recognized in the period')
current = annual.loc[annual.Year.eq(year)].iloc[0]
customers = customer_results(d, year, revenue, costs)
cases = case_view(d, year)
cutoff = pd.Timestamp(year, 12, 31, 23, 59, 59)

if page == 'Business overview':
    kpis([('Total revenue', money(current.Revenue), 'License + support + services revenue.'),
          ('Revenue YoY', percent(current['Revenue YoY %']), 'Change against the immediately preceding complete calendar year. N/A when absent or zero.'),
          ('Operating profit', money(current['Operating profit']), 'Revenue minus captured delivery costs and operating expenses. Before tax and financing.'),
          ('Operating margin', percent(current['Operating margin %']), 'Operating profit divided by revenue.')])
    left, right = st.columns([1.25, 1])
    with left:
        st.subheader('Revenue over time')
        trend = annual.melt(id_vars='Year', value_vars=['License', 'Support', 'Services'], var_name='Revenue type', value_name='USD')
        chart(px.bar(trend, x='Year', y='USD', color='Revenue type', barmode='stack', color_discrete_sequence=COLORS))
    with right:
        st.subheader('From revenue to profit')
        fig = go.Figure(go.Waterfall(x=['Revenue', 'Delivery', 'Operating expenses', 'Profit'],
                                    y=[current.Revenue, -current['Delivery cost'], -current['Operating expenses'], 0],
                                    measure=['absolute', 'relative', 'relative', 'total'],
                                    increasing={'marker': {'color': COLORS[1]}}, decreasing={'marker': {'color': COLORS[3]}}, totals={'marker': {'color': COLORS[0]}}))
        fig.update_yaxes(title='USD')
        chart(fig)
    st.subheader('Where to look next')
    for note in focus_areas(d, year, customers, annual, cases):
        st.write('• '+note)
    st.caption('These observations use fixed rules and your data. They identify questions to investigate, not proven causes.')
    with st.expander('Annual figures and cost definitions'):
        show_table(annual, 'annual_business_results')
        st.write('Delivery costs include license delivery, consulting labor, support labor and engineering fixes. Operating expenses must exclude those same costs to avoid double counting.')

elif page == 'Customers':
    st.subheader('Most profitable to least profitable')
    st.caption('Ranked by contribution after attributed delivery costs. Operating expenses and the internal quality pool are not allocated to individual customers.')
    kpis([('Customer contribution', money(customers.Contribution.sum()), 'Sum of customer results before the unallocated product-quality pool.'),
          ('Customers with a loss', str(int(customers.Contribution.lt(0).sum())), 'Customers with negative contribution.'),
          ('Internal quality pool', money(current['Internal quality cost']), 'Engineering logs without an affected customer known on that date. Subtract once at business level.')])
    chart(px.bar(customers.sort_values('Contribution'), y='customer_name', x='Contribution', orientation='h',
                 color=customers.sort_values('Contribution').Contribution.ge(0).map({True:'Positive', False:'Negative'}),
                 color_discrete_map={'Positive':COLORS[0], 'Negative':COLORS[3]}, labels={'customer_name':'Customer', 'Contribution':'Contribution (USD)'}))
    show_table(customers[['customer_name','License','Support','Services','Revenue','Delivery cost','Contribution','Margin %','Cases','Support hours']], 'customer_profitability')
    st.subheader('What differs between customers?')
    st.caption('Compare account size, usage, training and customization. These relationships do not establish cause and effect. Missing customer snapshots remain blank.')
    if len(customers) >= 6:
        compare_fields = ['Margin %','customizations','training_hours','Usage %','Cases / 100 active users','Support cost / $1k support revenue']
        groups = []
        for label, group in [('Top 3 by contribution', customers.head(3)), ('Bottom 3 by contribution', customers.tail(3))]:
            groups.append({'Group':label, 'Customers':len(group), **group[compare_fields].mean().to_dict()})
        st.dataframe(pd.DataFrame(groups).round(1), hide_index=True, width='stretch')
        st.caption('Unweighted means across each group. Blanks are excluded from each mean. Larger accounts can rank higher in contribution even with a lower margin.')
    driver = st.selectbox('Compare with contribution margin', ['customizations','training_hours','Usage %','Cases / 100 active users','Support cost / $1k support revenue'])
    plot = customers.dropna(subset=[driver, 'Margin %'])
    if not plot.empty:
        chart(px.scatter(plot, x=driver, y='Margin %', color='industry', hover_name='customer_name', size=plot.Revenue.clip(lower=1), color_discrete_sequence=COLORS))
    show_table(customers[['customer_name','Margin %','licensed_users','active_users','Usage %','customizations','training_hours','Cases / 100 active users','Support cost / $1k support revenue']], 'customer_drivers')
    cid = pick_customer(d, 'customer_detail')
    if cid:
        history = []
        for y in sorted(years):
            row = customer_results(d, y, revenue, costs)
            row = row[row.customer_id.eq(cid)]
            if len(row):
                history.append({'Year':y, **row.iloc[0][['Revenue','Contribution','Support hours','Cases']].to_dict()})
        st.subheader('Selected customer history')
        if history:
            show_table(pd.DataFrame(history), 'selected_customer_history')
        else:
            st.info('No financial or customer snapshot records for this customer.')

elif page == 'Services':
    sr = d['services_revenue'][d['services_revenue'].revenue_date.dt.year.eq(year)]
    logs = d['worklogs'][d['worklogs'].activity.eq('Services') & d['worklogs'].work_date.dt.year.eq(year)].copy()
    logs['cost'] = logs.minutes/60*logs.hourly_cost_usd
    ids = set(sr.project_id) | set(logs.project_id)
    projects = d['projects'][d['projects'].project_id.isin(ids)].merge(d['customers'][['customer_id','customer_name']], on='customer_id').set_index('project_id')
    projects['Revenue'] = sr.groupby('project_id').amount_usd.sum().reindex(projects.index,fill_value=0)
    projects['Delivery cost'] = logs.groupby('project_id').cost.sum().reindex(projects.index,fill_value=0)
    projects['Hours in year'] = logs.groupby('project_id').minutes.sum().div(60).reindex(projects.index,fill_value=0)
    life = d['worklogs'][d['worklogs'].activity.eq('Services') & (d['worklogs'].work_date<=cutoff)]
    projects['Lifetime hours to year-end'] = life.groupby('project_id').minutes.sum().div(60).reindex(projects.index,fill_value=0)
    projects['Contribution'] = projects.Revenue-projects['Delivery cost']
    projects['Margin %'] = projects.Contribution.div(projects.Revenue.replace(0,np.nan))*100
    kpis([('Services revenue',money(projects.Revenue.sum()),'Revenue schedule, including fixed-price milestones.'),
          ('Services contribution',money(projects.Contribution.sum()),'Recognized revenue less delivery labor in the year.'),
          ('Projects over hours budget',str(int((projects['Lifetime hours to year-end']>projects.budget_hours).sum())),'Lifetime hours observed through year-end compared with the total project budget. Only projects active in this year are shown.')])
    show_table(projects.reset_index()[['project_id','customer_name','project_name','billing_model','Revenue','Delivery cost','Contribution','Margin %','Hours in year','Lifetime hours to year-end','budget_hours']], 'services_projects')
    st.caption('Fixed-price revenue comes from services_revenue.csv. It is not inferred from hours × rate. A one-year margin can differ from the eventual whole-project margin.')

elif page == 'Support insights':
    cid = pick_customer(d, 'support_customer')
    cohort = case_view(d, year, cid)
    area = st.selectbox('Product area', ['All areas']+sorted(d['topics'].product_area.unique()))
    if area != 'All areas':
        cohort = cohort[cohort.product_area.eq(area)]
    known = cohort.handling_minutes.dropna()
    kpis([('Cases opened',str(len(cohort)),'Cases created during selected year.'),
          ('Average handling',f'{known.mean():.1f} min' if len(known) else 'N/A','Analyst effort per case with logs, observed through year-end. Unresolved cases may be incomplete.'),
          ('Median handling',f'{known.median():.1f} min' if len(known) else 'N/A','Median over cases with logged effort.'),
          ('Missing effort records',str(int(cohort.handling_minutes.isna().sum())),'Missing time is not treated as zero.')])
    if cohort.empty:
        st.info('No cases match these filters.')
    else:
        matrix = pd.crosstab(cohort.product_area, cohort.case_type)
        chart(px.imshow(matrix, text_auto=True, aspect='auto', color_continuous_scale='Purples', labels={'x':'Case type','y':'Product area','color':'Cases'}))
        topic = cohort.groupby(['product_area','functionality','case_type'],as_index=False).agg(Cases=('case_id','size'),Average_minutes=('handling_minutes','mean'),Median_minutes=('handling_minutes','median'),Logged_minutes=('handling_minutes',lambda s:s.sum(min_count=1)))
        show_table(topic.sort_values('Logged_minutes',ascending=False), 'support_topics')
        st.subheader('Prevention gaps')
        gaps = cohort.groupby('prevention_gap').size().reset_index(name='Cases')
        chart(px.bar(gaps,x='Cases',y='prevention_gap',orientation='h',labels={'prevention_gap':'Prevention gap'},color_discrete_sequence=COLORS))
        st.caption('Case type, confirmed cause and prevention gap are separate fields. One code defect can also have a missing-test prevention gap.')
        with st.expander('Case details'):
            show_table(cohort[['case_id','customer_id','functionality','case_type','confirmed_cause','prevention_gap','resolution','handling_minutes','response_hours','resolution_days']], 'support_case_details')

elif page == 'Product quality':
    new = d['defects'][d['defects'].created_at.dt.year.eq(year)].merge(d['topics'],on='topic_id')
    opened = backlog(d,year)
    kpis([('New defects',str(len(new)),'Distinct product defects created in this year.'),
          ('Customer origin',str(int(new.origin.eq('Customer').sum())),'First discovered by customers.'),
          ('Internal origin',str(int(new.origin.eq('Internal').sum())),'First discovered internally.'),
          ('Year-end backlog',str(len(opened)),'All unresolved defects at December 31, including older carryover.')])
    if not new.empty:
        matrix = pd.crosstab(new.detected_release,new.severity).reindex(columns=['Critical','High','Medium','Low'],fill_value=0)
        chart(px.imshow(matrix,text_auto=True,aspect='auto',color_continuous_scale='Purples',labels={'x':'Severity','y':'Detected release','color':'Defects'}))
        show_table(new[['defect_id','functionality','severity','origin','detected_release','prevention_gap','created_at','resolved_at']], 'product_defects')
    else:
        st.info('No new product defects in this year.')

elif page == 'Support team':
    eligible = cases.sla_eligible.sum()
    rated = cases[cases.survey_at.notna() & (cases.survey_at<=cutoff)]
    resolved = cases.resolved_by_cutoff.sum()
    kpis([('Response SLA',percent(ratio(cases.sla_met.sum(),eligible)*100),'Responded cases and overdue unanswered cases. Not-yet-due unanswered cases excluded.'),
          ('CSAT',f'{rated.csat_score.mean():.2f} / 5' if len(rated) else 'N/A','Survey results for the selected created-year cohort, received by year-end.'),
          ('Survey response rate',percent(ratio(len(rated),resolved)*100),'Survey count divided by cohort cases resolved by year-end.'),
          ('Pending SLA',str(int((~cases.sla_eligible).sum())),'Unanswered cases that were not yet due at year-end.')])
    rows=[]
    year_logs=d['worklogs'][d['worklogs'].activity.eq('Support') & d['worklogs'].work_date.dt.year.eq(year)]
    team_ids = set(cases.analyst_id) | set(year_logs.staff_id)
    for person in d['staff'][d['staff'].role.eq('Support') | d['staff'].staff_id.isin(team_ids)].itertuples():
        owned=cases[cases.analyst_id.eq(person.staff_id)]
        surveys=rated[rated.analyst_id.eq(person.staff_id)]
        rows.append({'Analyst':person.staff_name,'Cases':len(owned),'High / critical cases':owned.severity.isin(['High','Critical']).sum(),
                     'Logged hours':year_logs.loc[year_logs.staff_id.eq(person.staff_id),'minutes'].sum()/60,
                     'SLA %':ratio(owned.sla_met.sum(),owned.sla_eligible.sum())*100,'CSAT':surveys.csat_score.mean(),'Survey n':len(surveys)})
    show_table(pd.DataFrame(rows),'support_analysts')
    st.caption('Hours use work date; case and SLA measures use creation year. Compare case severity and survey sample size alongside volume. This is not an employee ranking.')

elif page == 'FAQ opportunities':
    st.write('Which repeated questions are worth testing with an FAQ agent?')
    left,right=st.columns(2)
    success=left.slider('Assumed successful self-service rate (%)',0,100,60,5)/100
    maintenance=right.number_input('Annual review and maintenance hours per topic',min_value=0.0,value=4.0,step=1.0)
    opportunities=automation_opportunities(d,year,success,maintenance)
    candidates=opportunities[opportunities.Recommendation.eq('FAQ pilot candidate')]
    kpis([('Pilot candidates',str(len(candidates)),'Documented answer-only questions; at least 12 eligible cases in the selected year and three consecutive years of history.'),
          ('Eligible candidate cases',str(int(candidates['Eligible cases'].sum())),'Resolved Q&A cases answered with a knowledge article and known handling effort.'),
          ('Estimated net hours freed',f'{candidates["Estimated net hours freed"].sum():.1f}','Selected-year eligible handling hours × assumed success rate, less maintenance per candidate topic.')])
    st.caption('Capacity estimate, not observed savings or an automatic budget reduction. Topic readiness comes from the current catalog; historic eligibility is a retrospective estimate. Validate correctness, repeat contacts and escalations in a pilot.')
    show_table(opportunities.drop(columns='topic_id'),'faq_opportunities')
    with st.expander('How the recommendation works'):
        st.write('Human-led: the topic requires action or investigation. Prepare documentation: no approved answer exists. Collect evidence: fewer than three consecutive years. Low volume: fewer than 12 eligible cases. Limited time benefit: maintenance outweighs estimated time freed. Otherwise: FAQ pilot candidate.')
        st.write('No language model or external AI service is used. No claim is made that an agent actually handled these historical cases. The trend is the change in topic case count from the first to the last of the three years; it is not a forecast.')

else:
    st.subheader('Input files')
    st.write('Each CSV has one kind of record. Keep IDs stable across exports. All financial amounts are USD; timestamps are interpreted as UTC.')
    show_table(pd.DataFrame([{'File':name+'.csv','Rows':len(d[name]),'Key columns':', '.join(col for col,_ in fields(name))} for name in SCHEMAS]),'input_inventory')
    st.write('Annual files may be named support_cases__2025.csv. Upload all required tables together, using header-only files for tables with no records. Duplicate keys are rejected rather than summed.')
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,content in files:
            archive.writestr(name,content)
    st.download_button('Download current CSV set',buffer.getvalue(),'business_lens_inputs.zip','application/zip')
    st.subheader('What the numbers mean')
    st.write('Customer contribution = license + support + services revenue − license delivery − support effort − consulting effort − allocated fixes. Business contribution also deducts the internal quality pool. Operating profit then deducts operating expenses.')
    st.write('Engineering cost is split equally among customers associated with the defect on the work date. A later association does not rewrite an earlier allocation. Customer filters never change the denominator.')
    st.write('Case handling time is logged analyst effort; resolution time is elapsed calendar time. They answer different questions. Missing logs and missing surveys remain unknown.')
    st.write('The app does not track cash, receivables, tax, interest, renewals, or unlogged effort. Upload recognized revenue schedules; do not mix bookings or invoices with recognized revenue.')
    st.subheader('Checks')
    labor=(d['worklogs'].minutes/60*d['worklogs'].hourly_cost_usd).sum()
    expected=labor+d['license_revenue'].delivery_cost_usd.sum()
    st.success(f'Cost reconciliation: {money(costs.cost_usd.sum())} allocated and unallocated costs = {money(expected)} recorded delivery costs.')
    st.caption('Validation checks schema, keys, references, dates, numeric ranges and activity targets. It cannot verify whether uploaded records are complete or accounting classifications are correct.')
