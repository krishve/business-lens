"""Persistent, page-aware Lenny panel built with native Streamlit widgets."""
import streamlit as st
from ui_theme import style_chart, display_frame
from lenny import QUESTIONS, answer_question
from lenny_ui import ASSET


PAGE_HELP = {
    'Intro': 'Business Lens compares revenue with the cost of serving customers. Start with Business overview for the whole business, then Customers for individual accounts. The sample records are fictional.',
    'Business overview': 'This page combines license, support and consulting revenue. Operating profit deducts all recorded delivery costs and operating expenses. The year selector changes the totals; the revenue chart shows the loaded years.',
    'Customers': 'Customers are ranked by contribution: their revenue minus assigned delivery costs. Operating expenses and unallocated engineering costs are deducted at business level. The customer selector affects the history section, not the ranking. Usage, training and customization comparisons suggest things to investigate, not proven causes.',
    'Services': 'This page compares recognized consulting revenue with labor cost during the selected year. The hours budget comparison uses lifetime hours through year-end for projects active in that year. A one-year margin can differ from the final project margin.',
    'Support insights': 'This page shows cases opened in the selected year, with effort recorded through year-end. Customer and product-area filters apply together. Handling time is work time, not elapsed waiting time. Missing effort is unknown, not zero.',
    'Product quality': 'New defects are grouped by the release where they were detected and by severity. Customer/internal origin describes who first found the defect. The year-end backlog also includes unresolved defects from older years.',
    'Support team': 'Response SLA measures whether eligible cases received a first response on time. CSAT is the average survey score out of five. Read scores alongside survey counts and case difficulty. Logged hours use work date; case counts use creation year. This is not an employee ranking.',
    'FAQ opportunities': 'This page looks for repeated, documented, answer-only questions across three consecutive years. It estimates eligible hours multiplied by the assumed success rate, less maintenance. These are planning estimates, not measured savings or a running FAQ agent.',
    'Data & definitions': 'This page lists the loaded tables, offers a CSV download and explains the calculations. The cost check ensures allocated and unallocated delivery costs add up to recorded costs. It cannot tell whether source records are complete.',
    'Ask Lenny': 'This full-page guide offers all supported questions and larger supporting charts. The floating Lenny panel stays available when you move to another page.',
}

PAGE_QUESTIONS = {
    'Business overview': ['focus', 'profit', 'revenue'],
    'Customers': ['customer', 'top', 'bottom', 'losses'],
    'Services': ['projects'],
    'Support insights': ['support'],
    'Product quality': ['defects'],
    'FAQ opportunities': ['faq'],
    'Ask Lenny': list(QUESTIONS),
}


def toggle_lenny():
    st.session_state.lenny_panel_open = not st.session_state.get('lenny_panel_open', False)


def choose_prompt(prompt):
    st.session_state['lenny_last_prompt'] = prompt


SUGGESTIONS = {
    'Intro': [('Top customers', 'top'), ('Profit change', 'profit'), ('FAQ ideas', 'faq')],
    'Business overview': [('Profit change', 'profit'), ('Revenue sources', 'revenue'), ('Where to focus', 'focus')],
    'Customers': [('Customer breakdown', 'customer'), ('Top customers', 'top'), ('Loss-making customers', 'losses')],
    'Services': [('Over-budget projects', 'projects')],
    'Support insights': [('Support effort', 'support')],
    'Product quality': [('Unresolved defects', 'defects')],
    'FAQ opportunities': [('FAQ ideas', 'faq')],
}


def render_floating_lenny(page, data=None, year=None, customers=None, source='Sample data',
                          customer_id=None, product_area=None, success=.6, maintenance_hours=4,
                          unavailable=None):
    """A compact conversation with explicit matching and live page context."""
    from lenny_intents import match_question
    st.markdown("""<style>
    .st-key-lenny_launcher {position:fixed; bottom:18px; right:22px; width:205px; z-index:1000;
        background:var(--bl-surface,white); border-radius:24px; box-shadow:0 6px 24px #37285f26;}
    .st-key-lenny_panel {position:fixed; bottom:112px; right:22px; width:min(440px,calc(100vw - 24px));
        max-height:calc(100dvh - 175px); overflow-y:auto; z-index:1001; box-sizing:border-box;
        padding:20px !important; background:var(--bl-surface,white); color:var(--bl-text,#202b45);
        border:1px solid var(--bl-border,#dbe1ee); border-radius:22px; box-shadow:0 16px 56px #17213c33;}
    .st-key-lenny_panel h3 {font-size:23px; margin:0;}
    .st-key-lenny_panel [data-testid="stVerticalBlock"] {gap:.75rem;}
    .st-key-lenny_panel [data-testid="stText"] {font-size:14px; line-height:1.65;}
    .st-key-lenny_panel [data-testid="stChatMessage"] {padding:14px; border-radius:16px; background:var(--bl-bg,#f7f8fc);}
    .st-key-lenny_panel [data-testid="stChatMessage"] [data-testid="stText"] {color:var(--bl-text,#202b45);}
    .st-key-lenny_panel [data-testid="stForm"] {padding:12px; border-color:var(--bl-border,#dbe1ee); border-radius:14px;}
    .st-key-lenny_panel [data-testid="stFormSubmitButton"] button {background:#635bdb !important; color:white !important; border:0;}
    .st-key-lenny_panel [data-testid="stFormSubmitButton"] button p {color:white !important;}
    .st-key-lenny_launcher [data-testid="stHorizontalBlock"], .st-key-lenny_panel [data-testid="stHorizontalBlock"] {flex-wrap:nowrap; align-items:center;}
    .st-key-lenny_launcher [data-testid="stColumn"], .st-key-lenny_panel [data-testid="stColumn"] {min-width:0;}
    .st-key-lenny_panel button {font-size:13px;}
    .block-container {padding-bottom:125px;}
    @media(max-width:600px){.st-key-lenny_launcher{right:12px;bottom:12px;}
      .st-key-lenny_panel{right:12px;bottom:104px;max-height:calc(100dvh - 165px);}}
    </style>""", unsafe_allow_html=True)
    is_open = st.session_state.get('lenny_panel_open', False)
    with st.container(key='lenny_launcher', border=True):
        face, action = st.columns([1, 2], vertical_alignment='center')
        with face:
            st.image(str(ASSET), width=48)
        with action:
            st.button('Close Lenny' if is_open else 'Ask Lenny', key='lenny_toggle',
                      on_click=toggle_lenny, width='stretch')
    if not is_open:
        return
    # Context changes clear the last question; answers never masquerade as old-page results.
    context = (page, year, source, customer_id, product_area, success, maintenance_hours)
    if st.session_state.get('lenny_chat_context') != context:
        st.session_state['lenny_last_prompt'] = None
        st.session_state['lenny_chat_context'] = context
    with st.container(key='lenny_panel', border=False):
        heading, close = st.columns([5, 1], vertical_alignment='center')
        with heading:
            st.subheader('Lenny')
            st.caption('Your guide to the numbers')
        with close:
            st.button('✕', key='lenny_close', help='Close Lenny', on_click=toggle_lenny)
        st.caption(f'{page}' + (f' · {year}' if year is not None else '') + (' · Sample data' if source == 'Sample data' else ' · Uploaded data'))
        st.write('What would you like to explore?')
        suggestions = SUGGESTIONS.get(page, [('Where to focus', 'focus'), ('Top customers', 'top')])
        items = [(label, QUESTIONS[key]) for label, key in suggestions] if data is not None else []
        items.append(('Explain this page', 'Explain this page'))
        for start in range(0, len(items), 2):
            cols = st.columns(2)
            for col, (label, prompt) in zip(cols, items[start:start+2]):
                with col:
                    st.button(label, key='lenny_suggest_' + label, on_click=choose_prompt, args=(prompt,), width='stretch')
        with st.form('lenny_composer', clear_on_submit=True, border=True):
            typed = st.text_input('Your question', placeholder='e.g. Which customers are losing money?', max_chars=300,
                                  key='lenny_typed', label_visibility='collapsed')
            submitted = st.form_submit_button('Ask Lenny →', width='stretch')
        if submitted:
            st.session_state['lenny_last_prompt'] = typed.strip()
        prompt = st.session_state.get('lenny_last_prompt')
        if prompt is None:
            if unavailable:
                st.info(unavailable)
            st.caption('Ask about customers, profit, revenue, support, defects or FAQ ideas. I match supported topics and show the evidence.')
            return
        request = match_question(prompt, data, year, customer_id, product_area)
        with st.chat_message('user'):
            st.text(prompt or '(Empty question)')
        with st.chat_message('assistant', avatar=str(ASSET)):
            if request.message:
                st.text(request.message)
                return
            if request.question == 'page':
                st.text(PAGE_HELP.get(page, 'Choose a page to explore the business data.'))
                return
            if data is None:
                st.text(unavailable or 'Open a data view with Sample data, or upload valid CSV files, so I can calculate an answer.')
                return
            selected_customer = request.customer_id
            if request.question == 'customer' and selected_customer is None:
                from metrics import customer_results
                names = customer_results(data, request.year).set_index('customer_id').customer_name.to_dict()
                if not names:
                    st.text('No customers have records in that year.')
                    return
                selected_customer = st.selectbox('Which customer?', list(names), format_func=names.get, key='lenny_float_customer')
            names = data['customers'].set_index('customer_id').customer_name.to_dict()
            scope = str(request.year)
            if request.question in ('customer', 'support'):
                scope += ' · ' + names.get(selected_customer, 'All customers')
            else:
                scope += ' · Whole business'
            if request.question == 'support':
                scope += ' · ' + (request.product_area or 'All areas')
            st.caption(scope)
            answer = answer_question(data, request.year, request.question, selected_customer,
                                     product_area=request.product_area, success=success, maintenance_hours=maintenance_hours)
            st.text(answer.summary)
            for note in answer.notes:
                st.text('• ' + note)
            with st.expander('How I worked this out'):
                st.write(answer.method)
            if not answer.table.empty:
                with st.expander('See the figures', expanded=True):
                    display_frame(answer.table.round(2), hide_index=True, width='stretch')
                    st.download_button('Download figures', answer.table.to_csv(index=False).encode('utf-8'),
                                       file_name=f'lenny_{request.question}_{request.year}.csv', mime='text/csv', key='lenny_float_download')
        st.caption('Rule-based answers from loaded data. No LLM. A new question replaces the previous reply.')
