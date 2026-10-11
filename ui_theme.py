"""Avenlo branding and session-local presentation settings."""
import pandas as pd
import streamlit as st


LOGO = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Avenlo Software logo">
<rect width="64" height="64" rx="18" fill="#7567ed"/>
<path d="M14 46 29 16h7l15 30H40l-8-18-8 18Z" fill="white"/>
<path d="M26 40h20l5 6H23Z" fill="#50d6c5"/>
<circle cx="47" cy="17" r="5" fill="#50d6c5"/></svg>'''


def dark_mode():
    return st.session_state.get('dark_mode', False)


def palette():
    if dark_mode():
        return dict(bg='#101523', surface='#1a2235', sidebar='#141b2c', text='#e9edf7', muted='#aebbd0', border='#34405a', accent='#ac9eff', selected='#302b50')
    return dict(bg='#f7f8fc', surface='#ffffff', sidebar='#edf0f9', text='#202b45', muted='#5b6b85', border='#dbe1ee', accent='#635bdb', selected='#e5e1ff')


def brand_sidebar():
    st.sidebar.markdown(f'''<div class="avenlo-brand"><div class="avenlo-logo">{LOGO}</div>
    <div><strong>AVENLO</strong><span>SOFTWARE</span></div></div>
    <div class="avenlo-product">Business Lens</div><div class="avenlo-description">A clearer view of your business.</div>''', unsafe_allow_html=True)
    st.sidebar.toggle('Dark mode', key='dark_mode', help='Switch this session between light and dark appearances.')
    apply_theme()


def apply_theme():
    p = palette()
    css = '''
    :root {--bl-bg: BG; --bl-surface: SURFACE; --bl-text: TEXT; --bl-muted: MUTED; --bl-border: BORDER; --bl-accent: ACCENT; --background-color: SURFACE;}
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {background: BG; color: TEXT;}
    [data-testid="stHeader"] {background: BG; color: TEXT;}
    [data-testid="stSidebar"] {background: SIDEBAR; color: TEXT; border-right: 1px solid BORDER;}
    [data-testid="stSidebarUserContent"] {padding-top: 1.25rem;}
    .avenlo-brand {display:flex; align-items:center; gap:12px; margin:0 0 22px;}
    .avenlo-logo {width:48px; height:48px; flex-shrink:0;}
    .avenlo-brand strong {display:block; font-size:21px; letter-spacing:3px; color:TEXT; line-height:1.2;}
    .avenlo-brand span {display:block; font-size:10px; letter-spacing:4px; color:MUTED; margin-top:5px;}
    .avenlo-product {font-size:25px; font-weight:750; color:TEXT; letter-spacing:-.6px;}
    .avenlo-description {font-size:13px; color:MUTED; margin:5px 0 22px;}
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label, [data-testid="stText"] {color:TEXT;}
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {color:MUTED !important;}
    [data-testid="stText"] span {color:TEXT !important;}
    .stApp h1 {letter-spacing:-1px;}
    .st-key-primary_navigation [role="radiogroup"] {gap:4px; width:100%;}
    .st-key-primary_navigation [role="radiogroup"] > div {width:100%;}
    .st-key-primary_navigation [data-testid="stRadioOption"] {width:100%; box-sizing:border-box;}
    .st-key-primary_navigation [role="radiogroup"] label {padding:9px 12px; border-radius:11px; margin:0; transition:background .15s; border:1px solid transparent;}
    .st-key-primary_navigation [role="radiogroup"] label:hover {background:SURFACE;}
    .st-key-primary_navigation [role="radiogroup"] label:has(input:checked) {background:SELECTED; border-color:BORDER; box-shadow:inset 3px 0 ACCENT;}
    .st-key-primary_navigation [role="radiogroup"] label:has(input:checked) p {color:ACCENT; font-weight:650;}
    .st-key-primary_navigation [data-testid="stRadioOption"] > div > div:first-child {display:none;}
    .st-key-primary_navigation [data-testid="stRadioOption"] > div::before {content:"◇"; color:ACCENT; font-size:18px; margin-right:12px; width:18px; display:inline-block;}
    .st-key-primary_navigation [role="radiogroup"] > div:nth-child(1) label > div::before {content:"⌂";}
    .st-key-primary_navigation [role="radiogroup"] > div:nth-child(2) label > div::before {content:"✦";}
    .st-key-primary_navigation [role="radiogroup"] > div:nth-child(3) label > div::before {content:"▦";}
    .st-key-primary_navigation [role="radiogroup"] > div:nth-child(4) label > div::before {content:"◎";}
    .st-key-primary_navigation [role="radiogroup"] > div:nth-child(5) label > div::before {content:"▤";}
    .st-key-primary_navigation [role="radiogroup"] > div:nth-child(6) label > div::before {content:"◷";}
    .st-key-primary_navigation [role="radiogroup"] > div:nth-child(10) label > div::before {content:"≡";}
    [data-testid="stMetric"] {background:SURFACE; border:1px solid BORDER !important; border-radius:14px !important; box-shadow:0 3px 12px #17213c06;}
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {color:TEXT;}
    [data-testid="stVerticalBlockBorderWrapper"] > div {border-color:BORDER;}
    [data-testid="stTextInputRootElement"], [data-testid="stTextInputField"], [data-testid="stNumberInputContainer"], [data-testid="stNumberInputField"], [data-testid="stSelectbox"] [role="combobox"] {background:SURFACE !important; color:TEXT !important; border-color:BORDER !important;}
    input::placeholder {color:MUTED !important; -webkit-text-fill-color:MUTED; opacity:1;}
    [data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"] {background:SURFACE !important; color:TEXT !important; border-color:BORDER !important;}
    [data-baseweb="select"] span, [data-baseweb="select"] input, input, textarea {color:TEXT !important; -webkit-text-fill-color:TEXT;}
    [data-baseweb="popover"] ul, [role="listbox"], [role="option"] {background:SURFACE !important; color:TEXT !important;}
    [role="option"]:hover, [role="option"][aria-selected="true"] {background:SELECTED !important;}
    .stApp button {color:TEXT;}
    .stApp button[kind="secondary"], .stApp [data-testid="stBaseButton-secondary"] {background:SURFACE; border-color:BORDER; border-radius:10px;}
    .stApp button[kind="secondary"]:hover {border-color:ACCENT; color:ACCENT;}
    [data-testid="stExpander"] details {background:SURFACE; border-color:BORDER; border-radius:12px;}
    [data-testid="stExpander"] summary {color:TEXT;}
    [data-testid="stAlert"] {background:SELECTED; color:TEXT; border:1px solid BORDER; border-radius:12px;}
    [data-testid="stFileUploaderDropzone"], [data-testid="stCode"] {background:SURFACE; color:TEXT; border-color:BORDER;}
    [data-testid="stTable"] th, [data-testid="stTable"] td {background:SURFACE; color:TEXT; border-color:BORDER;}
    .st-key-lenny_panel, .st-key-lenny_launcher {background:SURFACE !important; color:TEXT;}
    .st-key-lenny_panel {padding:16px !important;}
    '''
    for token, value in [('SELECTED', p['selected']), ('SIDEBAR', p['sidebar']), ('SURFACE', p['surface']), ('BORDER', p['border']), ('ACCENT', p['accent']), ('MUTED', p['muted']), ('TEXT', p['text']), ('BG', p['bg'])]:
        css = css.replace(token, value)
    st.markdown('<style>' + css + '</style>', unsafe_allow_html=True)


def style_chart(fig):
    p = palette()
    fig.update_layout(template='plotly_dark' if dark_mode() else 'plotly_white',
                      paper_bgcolor=p['bg'], plot_bgcolor=p['bg'], font_color=p['text'])
    return fig


def display_frame(data, **kwargs):
    # Canvas cells do not inherit CSS. Give them explicit per-session colors.
    if isinstance(data, pd.DataFrame) and dark_mode():
        p = palette()
        data = data.style.set_properties(**{'background-color': p['surface'], 'color': p['text']})
    return st.dataframe(data, **kwargs)
