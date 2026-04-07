import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from app.core.config import get_settings

settings = get_settings()
API = f'http://{settings.api_host}:{settings.api_port}/api'

st.set_page_config(page_title='Threads Viral Hunter', layout='wide')
st.markdown(
    """
    <style>
        .stApp { background-color: #0f1117; color: #f5f7ff; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title('Threads Viral Hunter')

with st.sidebar:
    st.header('Controls')
    topic = st.text_input('Add topic')
    kws = st.text_input('Keywords comma-separated', 'sales,marketing,leads')
    if st.button('Добавить тему') and topic:
        requests.post(f'{API}/topics', json={'name': topic, 'keywords': [k.strip() for k in kws.split(',')]}, timeout=20)

    handle = st.text_input('Add account handle')
    if st.button('Добавить аккаунт') and handle:
        requests.post(f'{API}/accounts', json={'handle': handle}, timeout=20)

    seed_urls = st.text_area('Seed post URLs', 'demo://sample')
    kw_track = st.text_input('Tracking keywords', 'sales,saas')
    if st.button('Запустить сбор'):
        requests.post(
            f'{API}/collect',
            json={'post_urls': [u.strip() for u in seed_urls.splitlines() if u.strip()], 'keywords': [k.strip() for k in kw_track.split(',')]},
            timeout=60,
        )

    if st.button('Пересчитать аналитику'):
        st.info('Аналитика пересчитывается при каждом ingest в MVP.')

col1, col2 = st.columns(2)

posts = requests.get(f'{API}/posts', timeout=30).json()
posts_df = pd.DataFrame(posts)

with col1:
    st.subheader('Dashboard')
    if not posts_df.empty:
        st.metric('Posts', len(posts_df))
        st.metric('Avg Viral Score', round(posts_df['viral_score'].fillna(0).mean(), 2))
        fig = px.histogram(posts_df, x='viral_score', nbins=20, title='Viral score distribution')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write('No data yet.')

with col2:
    st.subheader('Jobs / Logs')
    jobs = requests.get(f'{API}/jobs', timeout=20).json()
    st.dataframe(pd.DataFrame(jobs), use_container_width=True)

st.subheader('Posts')
if not posts_df.empty:
    min_score, max_score = st.slider('Viral score range', 0.0, float(posts_df['viral_score'].fillna(0).max() + 1), (0.0, float(posts_df['viral_score'].fillna(0).max() + 1)))
    filt = posts_df[(posts_df['viral_score'].fillna(0) >= min_score) & (posts_df['viral_score'].fillna(0) <= max_score)]
    st.dataframe(filt[['post_url', 'text', 'likes', 'replies', 'reposts', 'viral_score', 'format_type', 'hook', 'cta']], use_container_width=True)
else:
    st.info('Сначала запустите сбор данных.')

st.subheader('Idea Lab')
if not posts_df.empty:
    top_hooks = posts_df['hook'].dropna().head(5).tolist()
    st.json(
        {
            'topic': 'selected from filters',
            'conflict': 'growth without ad budget',
            'pain': 'low reach and low conversion',
            'promise': 'predictable inbound from Threads',
            'angles_10': [f'Angle #{i+1}' for i in range(10)],
            'hooks_5': top_hooks or [f'Hook #{i+1}' for i in range(5)],
            'formats_3': ['story', 'breakdown', 'provocation'],
        }
    )

st.subheader('Exports')
st.markdown(f'- [CSV]({API}/export/csv)')
st.markdown(f'- [XLSX]({API}/export/xlsx)')
st.markdown(f'- [JSON]({API}/export/json)')
