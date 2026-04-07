from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from app.core.config import get_settings

settings = get_settings()
API = f'http://{settings.api_host}:{settings.api_port}/api'

st.set_page_config(page_title='Threads Viral Hunter', layout='wide', page_icon='🧵')

st.markdown(
    """
    <style>
        .stApp { background: #0b1020; color: #e5e7eb; }
        .block-container { padding-top: 1.2rem; }
        h1, h2, h3 { color: #f8fafc !important; }
        .metric-card { padding: 12px; border-radius: 10px; background: #121a2f; border: 1px solid #273554; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=20)
def api_get(path: str):
    return requests.get(f'{API}{path}', timeout=30).json()


def api_post(path: str, payload: dict):
    return requests.post(f'{API}{path}', json=payload, timeout=60)


def safe_posts_df() -> pd.DataFrame:
    try:
        rows = api_get('/posts')
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()


st.title('🧵 Threads Viral Hunter — русская панель аналитики')
st.caption('Локальный режим: сбор публичных данных (без логина) + аналитика вирусности.')

if 'last_action' not in st.session_state:
    st.session_state.last_action = 'Готово к работе'

with st.sidebar:
    st.header('⚙️ Управление')
    st.write('Все ключевые действия доступны прямо из этого интерфейса.')

    with st.expander('Добавить аккаунт', expanded=True):
        handle = st.text_input('Ник аккаунта (без @)', key='acc_handle')
        if st.button('Сохранить аккаунт', use_container_width=True):
            if handle.strip():
                api_post('/accounts', {'handle': handle.strip()})
                st.session_state.last_action = f'Добавлен аккаунт: {handle.strip()}'
                st.cache_data.clear()

    with st.expander('Добавить тему'):
        topic = st.text_input('Название темы', key='topic_name')
        kw = st.text_input('Ключевые слова (через запятую)', key='topic_kw')
        if st.button('Сохранить тему', use_container_width=True):
            if topic.strip():
                api_post('/topics', {'name': topic.strip(), 'keywords': [k.strip() for k in kw.split(',') if k.strip()]})
                st.session_state.last_action = f'Добавлена тема: {topic.strip()}'
                st.cache_data.clear()

    with st.expander('Запустить сбор', expanded=True):
        urls = st.text_area('Ссылки на посты (каждая с новой строки)', 'demo://sample')
        track_kw = st.text_input('Трекинг-ключи', 'продажи,маркетинг,saas')
        if st.button('🚀 Запустить сбор данных', type='primary', use_container_width=True):
            payload = {
                'post_urls': [u.strip() for u in urls.splitlines() if u.strip()],
                'keywords': [k.strip() for k in track_kw.split(',') if k.strip()],
            }
            result = api_post('/collect', payload).json()
            st.session_state.last_action = f"Сбор завершен: найдено {result.get('collected', 0)}, добавлено {result.get('inserted', 0)}"
            st.cache_data.clear()

    st.success(st.session_state.last_action)

posts_df = safe_posts_df()

# top line metrics
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric('Постов в базе', int(len(posts_df)))
with m2:
    st.metric('Средний viral score', round(float(posts_df['viral_score'].fillna(0).mean()), 2) if not posts_df.empty else 0)
with m3:
    st.metric('С медиа', int(posts_df['has_media'].fillna(False).sum()) if not posts_df.empty else 0)
with m4:
    st.metric('Обновлено', datetime.now().strftime('%H:%M:%S'))


tab_dash, tab_collect, tab_posts, tab_patterns, tab_idea, tab_export, tab_jobs = st.tabs(
    ['📊 Дашборд', '🛰️ Сбор', '🧾 Посты', '🧠 Паттерны', '💡 Idea Lab', '📤 Экспорт', '🧰 Задачи/логи']
)

with tab_dash:
    if posts_df.empty:
        st.info('Пока нет данных. Запустите сбор в боковой панели.')
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.histogram(posts_df, x='viral_score', nbins=20, title='Распределение viral score'), use_container_width=True)
        with c2:
            if 'format_type' in posts_df.columns:
                fdf = posts_df['format_type'].fillna('unknown').value_counts().reset_index()
                fdf.columns = ['format', 'count']
                st.plotly_chart(px.pie(fdf, names='format', values='count', title='Форматы постов'), use_container_width=True)

with tab_collect:
    try:
        accounts = api_get('/accounts')
        topics = api_get('/topics')
    except Exception:
        accounts, topics = [], []
    c1, c2 = st.columns(2)
    with c1:
        st.subheader('Watchlist аккаунтов')
        st.dataframe(pd.DataFrame({'account': accounts}), use_container_width=True)
    with c2:
        st.subheader('Темы и ключи')
        st.dataframe(pd.DataFrame(topics), use_container_width=True)

with tab_posts:
    if posts_df.empty:
        st.info('Нет постов для отображения.')
    else:
        score_max = float(posts_df['viral_score'].fillna(0).max() + 1)
        min_score, max_score = st.slider('Фильтр по viral score', 0.0, score_max, (0.0, score_max))
        media_only = st.checkbox('Только с медиа')
        filt = posts_df[(posts_df['viral_score'].fillna(0) >= min_score) & (posts_df['viral_score'].fillna(0) <= max_score)]
        if media_only:
            filt = filt[filt['has_media'].fillna(False)]
        st.dataframe(
            filt[[
                'post_url', 'text', 'likes', 'replies', 'reposts', 'quotes',
                'viral_score', 'format_type', 'hook', 'cta', 'sentiment', 'tone'
            ]],
            use_container_width=True,
        )

with tab_patterns:
    if posts_df.empty:
        st.info('Паттерны появятся после сбора данных.')
    else:
        left, right = st.columns(2)
        with left:
            st.subheader('Частые хуки')
            st.dataframe(posts_df['hook'].dropna().value_counts().head(15).reset_index().rename(columns={'index': 'hook', 'hook': 'count'}))
        with right:
            st.subheader('CTA-паттерны')
            st.dataframe(posts_df['cta'].dropna().value_counts().head(15).reset_index().rename(columns={'index': 'cta', 'cta': 'count'}))

with tab_idea:
    st.subheader('Генератор идей на основе паттернов')
    topic_for_idea = st.text_input('Тема для идей', 'маркетинг B2B SaaS')
    if st.button('Сгенерировать набор идей'):
        hooks = posts_df['hook'].dropna().head(5).tolist() if not posts_df.empty else []
        st.json(
            {
                'тема': topic_for_idea,
                'конфликт': 'нужны лиды без роста рекламного бюджета',
                'боль': 'много контента, мало заявок',
                'обещание': 'система стабильного входящего потока из Threads',
                '10_углов': [f'Угол #{i + 1}' for i in range(10)],
                '5_хуков': hooks or [f'Хук #{i + 1}' for i in range(5)],
                'форматы': ['История', 'Разбор', 'Провокация'],
            }
        )

with tab_export:
    st.markdown(f'**CSV:** {API}/export/csv')
    st.markdown(f'**XLSX:** {API}/export/xlsx')
    st.markdown(f'**JSON:** {API}/export/json')
    st.info('Откройте ссылку в браузере, чтобы скачать файл.')

with tab_jobs:
    try:
        jobs = pd.DataFrame(api_get('/jobs'))
        st.dataframe(jobs, use_container_width=True)
    except Exception as exc:
        st.error(f'Не удалось получить логи задач: {exc}')
