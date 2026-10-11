from pathlib import Path
import pandas as pd
import pytest
from data_loader import load_folder, read_files, DataError
from metrics import cost_rows, revenue_rows, annual_results, customer_results, case_view, backlog, automation_opportunities

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def data():
    return load_folder(ROOT/'data'/'sample')


def test_every_year_reconciles_without_duplicate_revenue(data):
    costs=cost_rows(data)
    annual=annual_results(data)
    for year in range(2021,2026):
        row=annual[annual.Year.eq(year)].iloc[0]
        labor=data['worklogs'][data['worklogs'].work_date.dt.year.eq(year)]
        license=data['license_revenue'][data['license_revenue'].revenue_date.dt.year.eq(year)]
        expected=(labor.minutes/60*labor.hourly_cost_usd).sum()+license.delivery_cost_usd.sum()
        assert row['Delivery cost']==pytest.approx(expected)
        expected_revenue=sum(data[n].loc[data[n].revenue_date.dt.year.eq(year),'amount_usd'].sum() for n in ['license_revenue','support_revenue','services_revenue'])
        assert row.Revenue==pytest.approx(expected_revenue)
        customers=customer_results(data,year)
        assert customers.Contribution.sum()-row['Internal quality cost']==pytest.approx(row.Contribution)


def test_shared_fix_uses_effective_dates_and_preserves_total(data):
    data['worklogs']=pd.DataFrame([dict(worklog_id='W1',work_date=pd.Timestamp('2025-02-01'),staff_id='S05',activity='Engineering',case_id='',defect_id='D1',project_id='',minutes=360,hourly_cost_usd=100)])
    data['defect_customers']=pd.DataFrame([
        dict(defect_id='D1',customer_id=cid,associated_at=pd.Timestamp(date))
        for cid,date in [('C001','2025-01-01'),('C002','2025-01-01'),('C003','2025-03-01')]])
    result=cost_rows(data)
    shared=result[result.category.eq('Shared fix')]
    assert shared.cost_usd.sum()==600
    assert shared.loc[shared.customer_id.eq('C001'),'cost_usd'].sum()==300
    assert 'C003' not in set(shared.customer_id)
    # A customer-only view must not reallocate the entire fix to that customer.
    assert shared[shared.customer_id.eq('C001')].cost_usd.sum()==300


def test_unassociated_fix_stays_in_internal_pool(data):
    data['defect_customers']=data['defect_customers'].iloc[:0]
    result=cost_rows(data)
    engineering=data['worklogs'][data['worklogs'].activity.eq('Engineering')]
    assert result.loc[result.category.eq('Internal quality'),'cost_usd'].sum()==pytest.approx((engineering.minutes/60*engineering.hourly_cost_usd).sum())


def test_year_end_backlog_and_future_effort(data):
    data['defects']=pd.DataFrame([dict(defect_id='D1',created_at=pd.Timestamp('2024-12-10'),resolved_at=pd.Timestamp('2025-02-01'))])
    assert len(backlog(data,2024))==1
    assert len(backlog(data,2025))==0
    case=data['support_cases'].iloc[[0]].copy()
    case['created_at']=pd.Timestamp('2024-12-20')
    case['resolved_at']=pd.Timestamp('2025-02-01')
    case['first_response_at']=pd.Timestamp('2024-12-20T01:00')
    data['support_cases']=case
    data['worklogs']=pd.DataFrame([dict(activity='Support',case_id=case.iloc[0].case_id,work_date=pd.Timestamp('2025-01-10'),minutes=120)])
    cohort=case_view(data,2024)
    assert pd.isna(cohort.iloc[0].handling_minutes)
    assert pd.isna(cohort.iloc[0].resolution_days)


def test_unanswered_cases_breach_only_when_due(data):
    cases=data['support_cases'].iloc[:2].copy()
    cases['created_at']=[pd.Timestamp('2025-12-01'),pd.Timestamp('2025-12-31T23:00')]
    cases['first_response_at']=pd.NaT
    cases['resolved_at']=pd.NaT
    cases['response_sla_hours']=8.0
    data['support_cases']=cases
    result=case_view(data,2025)
    assert result.sla_eligible.tolist()==[True,False]
    assert not result.sla_met.any()


def test_zero_revenue_margin_and_customer_without_cases(data):
    for name in ['license_revenue','support_revenue']:
        data[name].loc[data[name].customer_id.eq('C001'),'amount_usd']=0
    project_ids=data['projects'].loc[data['projects'].customer_id.eq('C001'),'project_id']
    data['services_revenue'].loc[data['services_revenue'].project_id.isin(project_ids),'amount_usd']=0
    row=customer_results(data,2025).set_index('customer_id').loc['C001']
    assert pd.isna(row['Margin %'])
    assert row.Contribution<0
    data['support_cases']=data['support_cases'].iloc[:0]
    data['worklogs']=data['worklogs'][data['worklogs'].activity.ne('Support')]
    assert customer_results(data,2025).Cases.sum()==0


def test_faq_assumptions_change_estimate_not_history(data):
    low=automation_opportunities(data,2025,.25,2).set_index('topic_id')
    high=automation_opportunities(data,2025,.75,2).set_index('topic_id')
    assert low['2025'].equals(high['2025'])
    pd.testing.assert_series_equal(high['Estimated net hours freed']-low['Estimated net hours freed'],low['Eligible hours']*.5,check_names=False)
    assert low.loc['T05','Recommendation']=='Human-led'
    assert low.loc['T04','Recommendation']=='Prepare documentation'
    early=automation_opportunities(data,2021)
    assert not early.Recommendation.eq('FAQ pilot candidate').any()


def sample_files():
    return [(p.name,p.read_bytes()) for p in sorted((ROOT/'data'/'sample').glob('*.csv'))]


def test_upload_full_set_and_year_suffix():
    files=sample_files()
    renamed=[(n.replace('.csv','__2025.csv') if n=='support_cases.csv' else n,b) for n,b in files]
    assert len(read_files(renamed)['support_cases'])==2000


def test_upload_missing_duplicate_and_invalid_number():
    files=sample_files()
    with pytest.raises(DataError,match='Missing input'):
        read_files(files[:-1])
    with pytest.raises(DataError,match='supplied twice'):
        read_files(files+[files[0]])
    changed=[]
    for name,content in files:
        if name=='license_revenue.csv':
            rows=content.decode().splitlines()
            parts=rows[1].split(',');parts[-1]='NaN';rows[1]=','.join(parts)
            content='\n'.join(rows).encode()
        changed.append((name,content))
    with pytest.raises(DataError,match='finite'):
        read_files(changed)


def test_duplicate_rows_dangling_ids_and_partial_years(data):
    from data_loader import validate
    original=data['customers'].copy()
    data['customers']=pd.concat([original,original.iloc[[0]]])
    with pytest.raises(DataError,match='duplicate key'):
        validate(data)
    data['customers']=original
    data['worklogs'].loc[0,'staff_id']='MISSING'
    with pytest.raises(DataError,match='unknown staff'):
        validate(data)
    data['worklogs'].loc[0,'staff_id']='S07'
    data['periods'].loc[0,'complete']=False
    with pytest.raises(DataError,match='complete calendar'):
        validate(data)
