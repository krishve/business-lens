"""Generate repeatable fictional records. Run only to replace bundled sample data."""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from schema import SCHEMAS, fields

ROOT = Path(__file__).resolve().parent


def generate(destination=None):
    destination = Path(destination or ROOT / 'data' / 'sample')
    destination.mkdir(parents=True, exist_ok=True)
    rng = random.Random(71)
    data = {name: [] for name in SCHEMAS}
    end = datetime(2025, 12, 31, 23, 59, 59)

    def add(name, **values):
        data[name].append(values)

    def log(when, staff, activity, minutes, case='', defect='', project=''):
        rate = {'Support': 55, 'Engineering': 115, 'Services': 85}[activity] * 1.04 ** (when.year - 2021)
        add('worklogs', worklog_id=f'W{len(data["worklogs"])+1:06}', work_date=when,
            staff_id=staff, activity=activity, case_id=case, defect_id=defect,
            project_id=project, minutes=minutes, hourly_cost_usd=round(rate, 2))

    names = ['Aster Labs', 'Birch Manufacturing', 'Cobalt Foods', 'Delta Devices',
             'Elm Logistics', 'Fable Pharma', 'Grove Packaging', 'Harbor Chemicals',
             'Indigo Health', 'Juniper Energy', 'Kite Robotics', 'Linden Foods']
    topics = [
        ('Reporting', 'Export reports', True, True),
        ('Workflow', 'Explain workflow status', True, True),
        ('Access', 'Understand permission roles', True, True),
        ('Integrations', 'API authentication setup', False, True),
        ('Inventory', 'Correct inventory balances', False, False),
        ('Reporting', 'Large report timeout', False, False),
        ('Workflow', 'Transition validation', False, False),
        ('Integrations', 'Duplicate import records', False, False),
        ('Inventory', 'Stock history questions', True, True),
        ('Access', 'Change access rights', True, False),
    ]
    for i, (area, functionality, approved, answer_only) in enumerate(topics):
        add('topics', topic_id=f'T{i+1:02}', product_area=area, functionality=functionality,
            approved_answer=approved, answer_only=answer_only,
            knowledge_article=f'KB-{i+1:03}' if approved else 'Not available')
    for i, name in enumerate(names):
        add('customers', customer_id=f'C{i+1:03}', customer_name=name,
            industry=['Life sciences', 'Manufacturing', 'Food', 'Medical devices'][i % 4],
            joined_date=datetime(2023 if i >= 10 else 2021, 1, 1))
    for i, name in enumerate(['Alex Rivera', 'Morgan Chen', 'Sam Patel', 'Jordan Blake',
                              'Casey Brooks', 'Taylor Kim', 'Riley Park', 'Jamie Lee']):
        add('staff', staff_id=f'S{i+1:02}', staff_name=name,
            role='Support' if i < 4 else 'Engineering' if i < 6 else 'Services')
    for year in range(2021, 2026):
        add('periods', year=year, complete=True)
        for q in range(1, 5):
            add('releases', release_id=f'{year-2019}.{q}', release_date=datetime(year, q*3-2, 1))
        active = [c for c in data['customers'] if c['joined_date'].year <= year]
        for i, c in enumerate(active):
            cid = c['customer_id']
            users = 60 + i * 22
            training = 2 if i == 4 else 8 if i == 6 else 15 + (year-2021)*5
            add('customer_years', customer_id=cid, year=year, licensed_users=users,
                active_users=round(users * (.28 if i == 4 else .42 if i == 6 else .65 + .045*(year-2021))),
                customizations=14 if i == 4 else 9 if i == 6 else 1+i % 4,
                training_hours=training)
            support_fee = [52000, 68000, 38000, 72000, 1800, 84000, 13000, 67000, 49000, 58000, 41000, 34000][i] * 1.04**(year-2021)
            license_fee = [135000, 185000, 80000, 175000, 3500, 240000, 14000, 155000, 110000, 145000, 100000, 80000][i] * (1+.08*(year-2021))
            # Renewal/expansion sales vary, rather than treating every license as ARR.
            license_fee *= 1 if year == c['joined_date'].year else [.45, .6, .8, .95][(year-2022) % 4]
            add('license_revenue', entry_id=f'L-{year}-{cid}', customer_id=cid,
                revenue_date=datetime(year, 2+i % 10, 15), amount_usd=round(license_fee, 2),
                delivery_cost_usd=round(license_fee*.09, 2))
            for month in range(1, 13):
                add('support_revenue', entry_id=f'SR-{year}-{cid}-{month:02}', customer_id=cid,
                    revenue_date=datetime(year, month, 1), amount_usd=round(support_fee/12, 2))
            project = f'P-{year}-{cid}'
            hours = 170 + i*18
            service_rate = 55 if i == 4 else 92 if i == 6 else 165 + i*3
            add('projects', project_id=project, customer_id=cid,
                project_name=['Implementation', 'Migration', 'Training', 'Customization'][i % 4],
                billing_model='Fixed price' if i % 2 == 0 else 'Time and materials', budget_hours=hours)
            for q in range(1, 5):
                add('services_revenue', entry_id=f'SV-{project}-{q}', project_id=project,
                    revenue_date=datetime(year, q*3, 20), amount_usd=round(hours*service_rate/4, 2))
                for week in range(4):
                    when = datetime(year, q*3-1, 1)+timedelta(days=week*6)
                    actual_hours = hours/16*(1.35 if i in [4, 6] else rng.uniform(.85, 1.1))
                    log(when, f'S{7+i%2:02}', 'Services', round(actual_hours*60), project=project)
        # More Q&A over time; a 2023 release generates a distinct defect spike.
        for n in range(310 + (year-2021)*45):
            c = rng.choices(active, weights=[3 if x['customer_id']=='C005' else 2 if x['customer_id']=='C007' else 1 for x in active])[0]
            cid = c['customer_id']
            ti = rng.choices(range(10), weights=[14+(year-2021)*3, 12, 8, 8, 6, 12 if year==2023 else 6, 8, 6, 8, 4])[0]
            topic = f'T{ti+1:02}'
            kind = 'Q&A' if ti in [0,1,2,8] else 'Code defect' if ti in [5,6,7] else 'Data issue' if ti==4 else 'Configuration help'
            if rng.random()<.04:
                kind='Enhancement request'
            created=datetime(year,1,1)+timedelta(days=rng.randrange(360),hours=10)
            severity=rng.choices(['Critical','High','Medium','Low'],[3,17,50,30])[0]
            sla={'Critical':1,'High':4,'Medium':8,'Low':24}[severity]
            response=created+timedelta(hours=sla*rng.uniform(.1,1.4 if cid=='C005' else 1.13))
            days=rng.randint(7,100) if kind=='Code defect' else rng.randint(1,8)
            resolved=created+timedelta(days=days)
            if response and resolved <= response:
                resolved=response+timedelta(hours=4)
            if resolved>end or rng.random()<.045:
                resolved=None
            if response>end or rng.random()<.025:
                response=None
                resolved=None
            did=''
            gap='Documentation gap' if kind=='Q&A' else 'Missing validation' if kind=='Data issue' else 'Confusing UI'
            cause={'Q&A':'Expected behavior','Code defect':'Code defect','Data issue':'Data quality','Configuration help':'Incorrect configuration','Enhancement request':'Product limitation'}[kind]
            resolution={'Q&A':'Knowledge article','Code defect':'Code fix','Data issue':'Data correction','Configuration help':'Configuration change','Enhancement request':'Product review'}[kind] if resolved else 'Unresolved'
            if kind=='Code defect':
                did=f'D{len(data["defects"])+1:05}'
                gap=rng.choice(['Missing regression test','Missing integration test','Missing validation'])
                add('defects',defect_id=did,topic_id=topic,severity=severity,origin='Customer',
                    detected_release=f'{year-2019}.{(created.month-1)//3+1}',created_at=created,
                    resolved_at=resolved,prevention_gap=gap)
                associated=[cid]
                if rng.random()<.4:
                    associated+=rng.sample([x['customer_id'] for x in active if x['customer_id']!=cid],2)
                for ac in associated:
                    add('defect_customers',defect_id=did,customer_id=ac,associated_at=created)
                for j in range(3):
                    when=created+((resolved or min(created+timedelta(days=60),end))-created)*((j+1)/4)
                    log(when,'S05' if j%2 else 'S06','Engineering',rng.randrange(90,481,30),defect=did)
            case=f'CSE{len(data["support_cases"])+1:05}'
            analyst=f'S{rng.randint(1,4):02}'
            survey=resolved+timedelta(hours=4) if resolved and rng.random()<.65 else None
            if survey and survey>end:
                survey=None
            add('support_cases',case_id=case,customer_id=cid,topic_id=topic,defect_id=did,
                analyst_id=analyst,case_type=kind,confirmed_cause=cause,prevention_gap=gap,
                resolution=resolution,severity=severity,created_at=created,first_response_at=response,
                resolved_at=resolved,response_sla_hours=sla,csat_score=rng.choice([3,4,4,5,5]) if survey else '',survey_at=survey)
            handle=rng.randint(10,35) if kind=='Q&A' else rng.randint(70,260)
            if cid in ['C005','C007']:
                handle*=1.8
            stop=resolved or min(created+timedelta(days=3),end)
            log(created+(stop-created)*.5,analyst,'Support',round(handle),case=case)
        for n in range(18):
            created=datetime(year,1,10)+timedelta(days=n*18)
            resolved=created+timedelta(days=20)
            did=f'D{len(data["defects"])+1:05}'
            add('defects',defect_id=did,topic_id='T07',severity='Medium',origin='Internal',
                detected_release=f'{year-2019}.{(created.month-1)//3+1}',created_at=created,resolved_at=resolved,prevention_gap='Missing regression test')
            log(created+timedelta(days=10),'S05','Engineering',600,defect=did)
        for month in range(1,13):
            for category, base in [('Sales and marketing',14000),('Product development',17000),('Administration',11000),('Hosting and tools',3500)]:
                add('operating_expenses',expense_id=f'O-{year}-{month}-{category[:3]}',
                    expense_date=datetime(year,month,1),category=category,amount_usd=round(base*1.05**(year-2021),2))
    for name, rows in data.items():
        with (destination/f'{name}.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=[col for col,_ in fields(name)])
            writer.writeheader()
            for row in rows:
                writer.writerow({key:value.isoformat(timespec='seconds') if isinstance(value,datetime) else '' if value is None else value for key,value in row.items()})
    return {name:len(rows) for name,rows in data.items()}


if __name__=='__main__':
    print(generate())
