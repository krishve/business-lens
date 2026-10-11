"""CSV contracts shared by the loader, sample generator and data dictionary."""

SCHEMAS = {
    'periods': 'year:int complete:bool',
    'customers': 'customer_id:str customer_name:str industry:str joined_date:date',
    'customer_years': 'customer_id:str year:int licensed_users:int active_users:int customizations:int training_hours:float',
    'staff': 'staff_id:str staff_name:str role:str',
    'releases': 'release_id:str release_date:date',
    'topics': 'topic_id:str product_area:str functionality:str approved_answer:bool answer_only:bool knowledge_article:str',
    'license_revenue': 'entry_id:str customer_id:str revenue_date:date amount_usd:float delivery_cost_usd:float',
    'support_revenue': 'entry_id:str customer_id:str revenue_date:date amount_usd:float',
    'projects': 'project_id:str customer_id:str project_name:str billing_model:str budget_hours:float',
    'services_revenue': 'entry_id:str project_id:str revenue_date:date amount_usd:float',
    'defects': 'defect_id:str topic_id:str severity:str origin:str detected_release:str created_at:date resolved_at:date? prevention_gap:str',
    'defect_customers': 'defect_id:str customer_id:str associated_at:date',
    'support_cases': 'case_id:str customer_id:str topic_id:str defect_id:str? analyst_id:str case_type:str confirmed_cause:str prevention_gap:str resolution:str severity:str created_at:date first_response_at:date? resolved_at:date? response_sla_hours:float csat_score:float? survey_at:date?',
    'worklogs': 'worklog_id:str work_date:date staff_id:str activity:str case_id:str? defect_id:str? project_id:str? minutes:float hourly_cost_usd:float',
    'operating_expenses': 'expense_id:str expense_date:date category:str amount_usd:float',
}
KEYS = {name: [spec.split()[0].split(':')[0]] for name, spec in SCHEMAS.items()}
KEYS.update(customer_years=['customer_id', 'year'], defect_customers=['defect_id', 'customer_id'])
CASE_TYPES = ['Q&A', 'Configuration help', 'Code defect', 'Data issue', 'Enhancement request']
SEVERITIES = ['Critical', 'High', 'Medium', 'Low']


def fields(name):
    return [(item.split(':')[0], item.split(':')[1]) for item in SCHEMAS[name].split()]
