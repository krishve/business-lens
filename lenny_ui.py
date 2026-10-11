"""Guided question interface for Lenny; no model or external service."""
from pathlib import Path
import plotly.express as px
import streamlit as st
from ui_theme import style_chart, display_frame
from lenny import QUESTIONS, answer_question


ASSET = Path(__file__).resolve().parent / 'assets' / 'lenny.png'


def render_lenny(data, year, customers, source):
    with st.container(border=True):
        portrait, greeting = st.columns([1, 4], vertical_alignment='center')
        with portrait:
            st.image(str(ASSET), width=170)
        with greeting:
            st.subheader('Hi, I’m Lenny.')
            st.write('Clear answers from your business data.')
            st.write('Pick a question below. I’ll work out the answer and show the figures behind it.')
            st.caption(f'{year} · {"Fictional sample data" if source == "Sample data" else "Your uploaded data"} · Guided questions · No LLM')

    question = st.selectbox('What would you like to know?', list(QUESTIONS), format_func=QUESTIONS.get, key='lenny_question')
    customer_id = None
    if question == 'customer':
        names = customers.set_index('customer_id').customer_name.to_dict()
        if not names:
            st.info('No customer records are available for this year.')
            return
        customer_id = st.selectbox('Choose a customer', list(names), format_func=names.get, key='lenny_customer')
    st.caption('Answers update when you change the question, year or input data. Customer selection applies only to the customer breakdown question.')
    answer = answer_question(data, year, question, customer_id)
    with st.container(border=True):
        st.subheader('Lenny’s answer')
        # Treat uploaded customer and topic names as text, never as markup.
        st.text(answer.summary)
        for note in answer.notes:
            st.text('• ' + note)
        if answer.chart and not answer.table.empty:
            category, value = answer.chart
            plot = answer.table.dropna(subset=[value])
            if not plot.empty:
                fig = px.bar(plot, x=value, y=category, orientation='h', color_discrete_sequence=['#635BDB'])
                fig.update_layout(height=max(280, min(500, 45*len(plot))), margin=dict(l=5, r=10, t=10, b=5), yaxis={'autorange': 'reversed'})
                st.plotly_chart(style_chart(fig), width='stretch', theme=None, config={'displaylogo': False})
        st.caption('Explore further: ' + answer.next_view + ' in the sidebar.')
    with st.expander('How I worked this out', expanded=True):
        st.write(answer.method)
        st.caption('All figures come from the currently loaded CSV files. Missing or unrecorded costs can change the conclusion. Amounts are USD.')
    if not answer.table.empty:
        with st.expander('Supporting figures', expanded=answer.chart is None):
            table = answer.table.copy()
            for col in table.select_dtypes('number'):
                if col != 'Year':
                    table[col] = table[col].round(2)
            display_frame(table, hide_index=True, width='stretch')
            st.download_button('Download Lenny’s figures', table.to_csv(index=False).encode('utf-8'), file_name=f'lenny_{question}_{year}.csv', mime='text/csv')
    st.caption('This full-page guide uses the question menu. To type a question, open floating Lenny. Answers use fixed calculations; no predictions or external AI service.')
