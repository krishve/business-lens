from pathlib import Path
import re
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest
from data_loader import load_folder
from lenny import QUESTIONS, answer_question
from metrics import customer_results

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def data():
    return load_folder(ROOT / 'data' / 'sample')


def test_answers_change_with_loaded_revenue(data):
    before = answer_question(data, 2025, 'revenue').table['Revenue (USD)'].sum()
    index = data['license_revenue'].index[data['license_revenue'].revenue_date.dt.year.eq(2025)][0]
    data['license_revenue'].loc[index, 'amount_usd'] += 1000
    after = answer_question(data, 2025, 'revenue').table['Revenue (USD)'].sum()
    assert after - before == pytest.approx(1000)
    change = answer_question(data, 2025, 'profit').table.set_index('Measure')['Change (USD)']
    assert change['Operating profit'] == pytest.approx(change.Revenue - change['Delivery cost'] - change['Operating expenses'])


def test_customer_breakdown_matches_ranked_contribution(data):
    cid = data['customers'].iloc[0].customer_id
    detail = answer_question(data, 2025, 'customer', cid).table.set_index('Component').USD
    customer = customer_results(data, 2025).set_index('customer_id').loc[cid]
    assert detail.iloc[:3].sum() - detail.iloc[3:].sum() == pytest.approx(customer.Contribution)
    # Loss selection is exactly negative contribution, never low revenue alone.
    losses = answer_question(data, 2025, 'losses').table
    assert losses.Contribution.lt(0).all()
    assert (losses.Revenue - losses['Delivery cost']).tolist() == pytest.approx(losses.Contribution.tolist())
    assert answer_question(data, 2025, 'customer', 'unknown').table.empty


def test_backlog_answer_counts_defects_once(data):
    data['defects'] = data['defects'].iloc[:1].copy()
    data['defects']['created_at'] = pd.Timestamp('2023-01-01')
    data['defects']['resolved_at'] = pd.Timestamp('2025-01-01')
    assert answer_question(data, 2024, 'defects').table['Unresolved defects'].sum() == 1
    assert answer_question(data, 2025, 'defects').table.empty


def test_missing_history_and_effort_stay_unknown(data):
    assert 'cannot compare' in answer_question(data, 2021, 'profit').summary
    data['worklogs'] = data['worklogs'][data['worklogs'].activity.ne('Support')]
    answer = answer_question(data, 2025, 'support')
    assert answer.table['Recorded hours'].isna().all()
    assert answer.table['Cases missing effort'].sum() == answer.table.Cases.sum()
    assert 'no recorded' in answer.summary
    assert 'No topics qualify' in answer_question(data, 2021, 'faq').summary


def test_all_questions_handle_header_only_transactions(data):
    for name in ['license_revenue', 'support_revenue', 'services_revenue', 'projects', 'worklogs', 'defects', 'defect_customers', 'support_cases', 'operating_expenses']:
        data[name] = data[name].iloc[:0]
    for question in QUESTIONS:
        answer = answer_question(data, 2025, question, data['customers'].iloc[0].customer_id)
        assert answer.summary
        assert not re.search(r'nan', answer.summary, re.IGNORECASE)
    assert answer_question(data, 2025, 'losses').table.empty
    assert answer_question(data, 2025, 'projects').table.empty
    with pytest.raises(ValueError):
        answer_question(data, 2025, 'invent an answer')


def test_all_lenny_questions_render_and_follow_year():
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
    app.sidebar.radio[1].set_value('Ask Lenny').run()
    for question in QUESTIONS:
        app.selectbox(key='lenny_question').set_value(question).run()
        assert not app.exception, (question, [x.message for x in app.exception])
    app.selectbox(key='lenny_question').set_value('profit').run()
    app.sidebar.selectbox[0].select(2021).run()
    assert any('cannot compare' in item.value for item in app.text)
    assert not app.exception


def test_context_filters_and_faq_assumptions(data):
    from metrics import case_view, automation_opportunities
    cid = data['customers'].iloc[0].customer_id
    cases = case_view(data, 2025, cid)
    area = cases.iloc[0].product_area
    expected = cases[cases.product_area.eq(area)]
    answer = answer_question(data, 2025, 'support', cid, product_area=area)
    assert answer.table.Cases.sum() == len(expected)
    assert answer.table['Recorded hours'].sum() == pytest.approx(expected.handling_minutes.sum()/60)
    assert set(answer.table['Product area']) == {area}
    faq = answer_question(data, 2025, 'faq', success=.25, maintenance_hours=8)
    expected_faq = automation_opportunities(data, 2025, .25, 8).drop(columns='topic_id')
    pd.testing.assert_frame_equal(faq.table, expected_faq)
    assert '25%' in faq.method and '8 maintenance' in faq.method


def test_floating_lenny_navigation_filters_and_missing_upload():
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
    app.button(key='lenny_toggle').click().run()
    app.button(key='lenny_suggest_Top customers').click().run()
    assert any('highest' in item.value for item in app.text)
    app.sidebar.radio[1].set_value('Support insights').run()
    assert app.session_state['lenny_panel_open']
    app.selectbox(key='support_customer').set_value('Aster Labs').run()
    area_widget = next(w for w in app.selectbox if w.label == 'Product area')
    area_widget.set_value(area_widget.options[1]).run()
    app.button(key='lenny_suggest_Support effort').click().run()
    assert any('Aster Labs' in item.value for item in app.caption)
    assert not app.exception
    app.sidebar.selectbox[0].select(2021).run()
    assert app.session_state['lenny_last_prompt'] is None
    app.sidebar.radio[1].set_value('Customers').run()
    app.selectbox(key='customer_detail').set_value('Aster Labs').run()
    app.button(key='lenny_suggest_Customer breakdown').click().run()
    assert any('Aster Labs recorded' in item.value for item in app.text)
    app.sidebar.radio[0].set_value('Upload CSV files').run()
    assert any('Upload the complete CSV set' in item.value for item in app.info)
    assert not app.exception
    app.button(key='lenny_toggle').click().run()
    assert not app.session_state['lenny_panel_open']


def test_typed_question_matching_and_boundaries(data):
    from lenny_intents import match_question
    assert match_question('Which customers are losing money?', data, 2025).question == 'losses'
    request = match_question('How profitable is Aster in 2024?', data, 2025)
    assert (request.question, request.year, request.customer_id) == ('customer', 2024, 'C001')
    assert match_question('show support hours for Integrations', data, 2025).product_area == 'Integrations'
    assert match_question('predict revenue next year', data, 2025).question is None
    assert match_question('tell me a joke', data, 2025).message
    assert match_question('revenue last year', data, 2025).year == 2024
    assert match_question('How did operating profit change from last year?', data, 2025).year == 2025
    assert match_question('How profitable is this customer?', data, 2025, 'C001').question == 'customer'
    assert match_question('revenue in 2030', data, 2025).question is None
    assert match_question('profit in 2021 and 2025', data, 2025).message
    assert match_question('profit for Acme', data, 2025).question is None
    assert match_question('profit and support hours', data, 2025).question is None
    assert match_question('set FAQ success to 80%', data, 2025).question is None


def test_dark_mode_and_typed_reply():
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=30).run()
    app.toggle(key='dark_mode').set_value(True).run()
    app.button(key='lenny_toggle').click().run()
    app.text_input(key='lenny_typed').set_value('Which customers are losing money?')
    next(b for b in app.button if b.label == 'Ask Lenny →').click().run()
    assert any('negative contribution' in item.value for item in app.text)
    assert not app.exception
    app.sidebar.radio[1].set_value('Business overview').run()
    assert app.session_state['dark_mode']
    assert not app.exception
