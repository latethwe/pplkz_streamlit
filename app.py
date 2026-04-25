from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
import altair as alt

from src.data_processing import (
    METRIC_KIND_LABEL,
    SurveyData,
    apply_respondent_filters,
    load_survey_data,
    normalize_company_name,
)


# ============================================================================
# КРАСИВЫЙ ДИЗАЙН И СТИЛИЗАЦИЯ
# ============================================================================

def setup_page():
    """Настраивает красивый дизайн страницы"""
    st.set_page_config(
        page_title="Employer Analytics 2026",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Красивая CSS стилизация
    st.markdown("""
    <style>
    /* Основной фон - красивый градиент */
    .main {
        background: linear-gradient(to bottom, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        color: #e2e8f0;
    }
    
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(to bottom, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    }
    
    /* Боковая панель - тёмная и стильная */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 2px solid #3b82f6;
    }
    
    [data-testid="stSidebar"] label {
        color: #e0e7ff;
        font-weight: 600;
        font-size: 0.95rem;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #cbd5e1;
    }
    
    [data-testid="stSidebar"] h2 {
        color: #60a5fa !important;
        font-size: 1.3rem;
        margin-bottom: 1rem;
    }
    
    /* Заголовки - синие и яркие */
    h1 {
        color: #60a5fa;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 0 4px 12px rgba(96, 165, 250, 0.3);
    }
    
    h2 {
        color: #60a5fa;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 1.5rem 0 1rem 0;
    }
    
    h3 {
        color: #93c5fd;
        font-size: 1.2rem;
        font-weight: 600;
    }
    
    /* Метрики - красивые карточки */
    [data-testid="stMetricContainer"] {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 2px solid #3b82f6;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(59, 130, 246, 0.15);
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetricContainer"]:hover {
        border-color: #60a5fa;
        box-shadow: 0 12px 48px rgba(96, 165, 250, 0.25);
        transform: translateY(-2px);
    }
    
    [data-testid="stMetricContainer"] .metric-label {
        color: #94a3b8;
    }
    
    [data-testid="stMetricContainer"] .metric-value {
        color: #60a5fa;
        font-size: 2rem;
    }
    
    /* Таблицы - красивые */
    [data-testid="stDataFrame"] {
        background: #1e293b;
        border: 1px solid #3b82f6;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(59, 130, 246, 0.1);
    }
    
    [data-testid="stDataFrame"] thead {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        color: white;
    }
    
    [data-testid="stDataFrame"] tbody tr:hover {
        background-color: #0f172a;
    }
    
    /* Tabs - красивые вкладки */
    [data-testid="stTabs"] [role="tab"] {
        font-weight: 600;
        color: #cbd5e1;
        padding: 0.75rem 1.5rem;
        border-radius: 8px 8px 0 0;
        background: transparent;
        border: none;
        margin-right: 0.5rem;
    }
    
    [data-testid="stTabs"] [role="tab"]:hover {
        background: rgba(59, 130, 246, 0.1);
        color: #60a5fa;
    }
    
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border-bottom: 3px solid #60a5fa;
    }
    
    /* Кнопки - красивые */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.5);
        transform: translateY(-2px);
    }
    
    /* Теги мультиселекта - убрать красный */
    [data-baseweb="tag"] {
        background-color: #1e40af !important;
        border: 1px solid #3b82f6 !important;
    }
    
    [data-baseweb="tag"] span {
        color: #e2e8f0 !important;
    }
    
    /* Кнопка X в теге */
    [data-baseweb="tag"] button {
        color: #93c5fd !important;
    }
    
    [data-baseweb="tag"] button:hover {
        color: #ffffff !important;
        background-color: #2563eb !important;
    }
    
    /* Слайдер - убрать красный */
    [data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
        background-color: #3b82f6 !important;
        border-color: #3b82f6 !important;
    }
    
    [data-testid="stSlider"] [data-baseweb="slider"] div[data-testid="stThumbValue"] {
        color: #60a5fa !important;
    }
    
    /* Трек слайдера */
    [data-testid="stSlider"] [data-baseweb="slider"] div:nth-child(2) > div {
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%) !important;
    }
    
    /* Сообщения - красивые */
    .stSuccess {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(34, 197, 94, 0.05) 100%);
        border-left: 4px solid #22c55e;
        border-radius: 8px;
        color: #86efac;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(245, 158, 11, 0.05) 100%);
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        color: #fbbf24;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(148, 163, 184, 0.15) 0%, rgba(148, 163, 184, 0.05) 100%);
        border-left: 4px solid #94a3b8;
        border-radius: 8px;
        color: #e2e8f0;
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(59, 130, 246, 0.05) 100%);
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        color: #93c5fd;
    }
    
    /* Text - красивый текст */
    p, .stMarkdown {
        color: #cbd5e1;
        line-height: 1.6;
    }
    
    .stCaption {
        color: #94a3b8;
        font-size: 0.9rem;
    }
    
    /* Selectbox arrow и drop-down */
    [data-baseweb="select"] {
        background-color: #1e293b !important;
    }
    
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# КОНСТАНТЫ
# ============================================================================

DATA_PATH = Path("Copy_2026.xlsx")

AGE_ORDER = ["Младше 21", "22 - 26", "27 - 31", "32 - 36", "37 - 41", "42 - 46", "Старше 46"]
RAW_RESPONSE_ORDER = [
    "Однозначно хочу",
    "Скорее да",
    "Не уверен",
    "Скорее нет",
    "Категорически не хочу",
    "Я не знаю эту компанию",
]
MAPPED_RESPONSE_ORDER = ["Хочу", "Не уверен", "Не хочу", "Я не знаю эту компанию"]

FACTOR_GROUP_LABELS = {
    "top_factors": "Факторы выбора работодателя",
    "offer_reject_factors": "Причины отказа от оффера",
    "sources": "Источники информации о работодателе",
    "job_change_reasons": "Причины смены работы",
}

# Красивая палитра для графиков
CHART_COLORS = ["#3b82f6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def _pct(v: float | None) -> str:
    if v is None or pd.isna(v):
        return "n/a"
    return f"{v * 100:.1f}%"


def _fmt_int(v: float | int | None) -> str:
    if v is None or pd.isna(v):
        return "n/a"
    return f"{int(v)}"


@st.cache_data(show_spinner=True)
def load_data(path: str) -> SurveyData:
    return load_survey_data(path)


def compute_company_metrics_for_segment(company_raw_long: pd.DataFrame, respondent_count: int) -> pd.DataFrame:
    if respondent_count <= 0 or company_raw_long.empty:
        return pd.DataFrame()

    grouped = (
        company_raw_long.groupby(["company_key", "company", "sector", "response_mapped"], dropna=False)
        .size()
        .reset_index(name="cnt")
    )
    pivot = grouped.pivot_table(
        index=["company_key", "company", "sector"],
        columns="response_mapped",
        values="cnt",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    for col in ["Хочу", "Не хочу", "Не уверен", "Я не знаю эту компанию"]:
        if col not in pivot.columns:
            pivot[col] = 0

    pivot["want_pct"] = pivot["Хочу"] / respondent_count
    pivot["dont_want_pct"] = pivot["Не хочу"] / respondent_count
    pivot["uncertain_pct"] = pivot["Не уверен"] / respondent_count
    pivot["unknown_brand_pct"] = pivot["Я не знаю эту компанию"] / respondent_count
    return pivot


def _make_pct_table(df: pd.DataFrame, category_col: str, sort_categories: list[str] | None = None) -> pd.DataFrame:
    out = df[category_col].value_counts().reset_index()
    out.columns = [category_col, "count"]
    total = out["count"].sum()
    out["pct"] = (out["count"] / total * 100).round(1) if total else 0
    out["label"] = out["pct"].map(lambda x: f"{x:.1f}%")
    if sort_categories:
        out[category_col] = pd.Categorical(out[category_col], categories=sort_categories, ordered=True)
        out = out.sort_values(category_col)
    return out


def _bar_pct_vertical(df: pd.DataFrame, x_col: str, y_col: str, title: str, color_col: str | None = None) -> alt.Chart:
    if color_col:
        bar = alt.Chart(df).mark_bar(cornerRadius=4).encode(
            x=alt.X(f"{x_col}:N", title=x_col, axis=alt.Axis(labelAngle=0)),
            y=alt.Y(f"{y_col}:Q", title="%", axis=alt.Axis(format=".1f")),
            color=alt.Color(f"{color_col}:N", scale=alt.Scale(scheme="tableau10")),
            tooltip=[x_col, color_col, alt.Tooltip(f"{y_col}:Q", format=".1f")],
        )
    else:
        bar = alt.Chart(df).mark_bar(color="#3b82f6", cornerRadius=4).encode(
            x=alt.X(f"{x_col}:N", title=x_col, axis=alt.Axis(labelAngle=0)),
            y=alt.Y(f"{y_col}:Q", title="%", axis=alt.Axis(format=".1f")),
            tooltip=[x_col, alt.Tooltip(f"{y_col}:Q", format=".1f")],
        )

    text = alt.Chart(df).mark_text(dy=-10, fontSize=12, color="#60a5fa", fontWeight="bold").encode(
        x=alt.X(f"{x_col}:N"),
        y=alt.Y(f"{y_col}:Q"),
        text="label:N",
    )
    return (bar + text).properties(title=title, height=350).configure_title(fontSize=14, anchor="start", color="#60a5fa")


def _bar_pct_horizontal(
    df: pd.DataFrame, x_col: str, y_col: str, title: str, color_col: str | None = None
) -> alt.Chart:
    if color_col:
        bar = alt.Chart(df).mark_bar(cornerRadius=4).encode(
            x=alt.X(f"{x_col}:Q", title="%", axis=alt.Axis(format=".1f")),
            y=alt.Y(f"{y_col}:N", sort="-x", title=y_col),
            color=alt.Color(f"{color_col}:N", scale=alt.Scale(scheme="tableau10")),
            tooltip=[y_col, color_col, alt.Tooltip(f"{x_col}:Q", format=".1f")],
        )
    else:
        bar = alt.Chart(df).mark_bar(color="#3b82f6", cornerRadius=4).encode(
            x=alt.X(f"{x_col}:Q", title="%", axis=alt.Axis(format=".1f")),
            y=alt.Y(f"{y_col}:N", sort="-x", title=y_col),
            tooltip=[y_col, alt.Tooltip(f"{x_col}:Q", format=".1f")],
        )
    text = alt.Chart(df).mark_text(align="left", dx=5, fontSize=11, color="#60a5fa", fontWeight="bold").encode(
        x=alt.X(f"{x_col}:Q"),
        y=alt.Y(f"{y_col}:N", sort="-x"),
        text="label:N",
    )
    return (bar + text).properties(title=title, height=400).configure_title(fontSize=14, anchor="start", color="#60a5fa")


def _grouped_pct_chart(df: pd.DataFrame, x: str, group: str, y: str, title: str) -> alt.Chart:
    bar = alt.Chart(df).mark_bar(cornerRadius=3).encode(
        x=alt.X(f"{x}:N", title=x),
        xOffset=alt.XOffset(f"{group}:N", title=group),
        y=alt.Y(f"{y}:Q", title="%", axis=alt.Axis(format=".1f")),
        color=alt.Color(f"{group}:N", scale=alt.Scale(scheme="tableau10")),
        tooltip=[x, group, alt.Tooltip(f"{y}:Q", format=".1f")],
    )
    text = alt.Chart(df).mark_text(dy=-8, fontSize=10, color="#60a5fa").encode(
        x=alt.X(f"{x}:N"),
        xOffset=alt.XOffset(f"{group}:N"),
        y=alt.Y(f"{y}:Q"),
        text="label:N",
    )
    return (bar + text).properties(title=title, height=350).configure_title(fontSize=14, anchor="start", color="#60a5fa")


def _sector_comparison_chart(df: pd.DataFrame, metric_col: str, title: str) -> alt.Chart:
    """График сравнения компаний внутри сектора"""
    bar = alt.Chart(df).mark_bar(cornerRadius=4).encode(
        x=alt.X(f"{metric_col}:Q", title="%", axis=alt.Axis(format=".1f")),
        y=alt.Y("company:N", sort="-x", title=""),
        color=alt.Color("company:N", scale=alt.Scale(scheme="tableau20"), legend=None),
        tooltip=["company", "sector", alt.Tooltip(f"{metric_col}:Q", format=".1f")],
    )
    text = alt.Chart(df).mark_text(align="left", dx=5, fontSize=11, color="#60a5fa", fontWeight="bold").encode(
        x=alt.X(f"{metric_col}:Q"),
        y=alt.Y("company:N", sort="-x"),
        text=alt.Text(f"{metric_col}:Q", format=".1f"),
    )
    return (bar + text).properties(title=title, height=max(250, len(df) * 35)).configure_title(
        fontSize=14, anchor="start", color="#60a5fa"
    )


def _company_name_map(companies: pd.DataFrame) -> dict[str, str]:
    return {normalize_company_name(row["company"]): row["company"] for _, row in companies.iterrows()}


def _prepare_factor_distribution(fdf: pd.DataFrame, top_n: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    top = fdf["factor"].value_counts().head(top_n).reset_index()
    top.columns = ["factor", "count"]
    total = top["count"].sum()
    top["pct"] = (top["count"] / total * 100).round(1) if total else 0
    top["label"] = top["pct"].map(lambda x: f"{x:.1f}%")

    by_pos = (
        fdf[fdf["factor"].isin(top["factor"])]
        .groupby(["factor", "rank_position"])
        .size()
        .reset_index(name="count")
    )
    total_pos = by_pos["count"].sum()
    by_pos["pct"] = (by_pos["count"] / total_pos * 100).round(1) if total_pos else 0
    by_pos["label"] = by_pos["pct"].map(lambda x: f"{x:.1f}%")
    by_pos["rank_position"] = by_pos["rank_position"].astype(str)
    return top, by_pos


def _company_demographic_distribution(
    company_sent: pd.DataFrame,
    filtered_resp: pd.DataFrame,
    dim_col: str,
    order: list[str] | None = None,
) -> pd.DataFrame:
    demo = filtered_resp[["respondent_id", dim_col]].copy()
    merged = company_sent[["respondent_id", "response_mapped"]].merge(demo, on="respondent_id", how="left")
    merged = merged[merged[dim_col].notna()].copy()
    dist = merged.groupby([dim_col, "response_mapped"]).size().reset_index(name="count")
    dist["pct"] = (dist["count"] / dist.groupby(dim_col)["count"].transform("sum") * 100).round(1)
    dist["label"] = dist["pct"].map(lambda x: f"{x:.1f}%")
    if order:
        dist[dim_col] = pd.Categorical(dist[dim_col], categories=order, ordered=True)
        dist = dist.sort_values([dim_col, "response_mapped"])
    return dist


# ============================================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ============================================================================

def main() -> None:
    setup_page()

    # Красивый заголовок
    st.markdown("### 📊 Employer Analytics Dashboard 2026")
    st.caption("✨ Профессиональный анализ данных опроса работодателей")

    if not DATA_PATH.exists():
        st.error(f"❌ Файл не найден: {DATA_PATH}")
        st.stop()

    data = load_data(str(DATA_PATH))
    respondents = data.respondents.copy()
    respondents["respondent_id"] = respondents["Номер ответа"].astype("Int64")

    # Боковая панель
    with st.sidebar:
        st.markdown("### ⚙️ Фильтры")
        st.divider()
        
        genders = sorted([x for x in respondents["Гендер"].dropna().unique().tolist()])
        ages = [x for x in AGE_ORDER if x in respondents["Возраст"].dropna().unique().tolist()] + sorted(
            [x for x in respondents["Возраст"].dropna().unique().tolist() if x not in AGE_ORDER]
        )
        exps = sorted([x for x in respondents["Опыт работы в ИТ / Digital"].dropna().unique().tolist()])
        specs = sorted([x for x in respondents["К какой специализации Вы себя относите?"].dropna().unique().tolist()])

        selected_gender = st.multiselect("👥 Гендер", genders, default=genders)
        selected_age = st.multiselect("📅 Возраст", ages, default=ages)
        selected_exp = st.multiselect("💼 Опыт в IT", exps, default=exps)
        selected_spec = st.multiselect("🎯 Специализация", specs, default=specs)
        
        st.divider()
        st.caption("💡 Используйте фильтры для анализа сегментов")

    filtered_resp = apply_respondent_filters(
        respondents,
        selected_gender=selected_gender,
        selected_age=selected_age,
        selected_experience=selected_exp,
        selected_specialization=selected_spec,
    )
    filtered_ids = set(filtered_resp["respondent_id"].dropna().astype(int).tolist())
    company_raw_f = data.company_raw_long[data.company_raw_long["respondent_id"].isin(filtered_ids)].copy()
    factors_f = data.factors_long[data.factors_long["respondent_id"].isin(filtered_ids)].copy()
    segment_metrics = compute_company_metrics_for_segment(company_raw_f, len(filtered_resp))

    # KPI метрики
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👤 Респондентов (фильтр)", f"{len(filtered_resp):,}".replace(",", " "))
    with col2:
        st.metric("👥 Респондентов (всего)", f"{len(respondents):,}".replace(",", " "))
    with col3:
        st.metric("🏢 Компаний в рейтинге", f"{data.rankings['company_key'].nunique()}")

    if len(filtered_resp) == 0:
        st.error("❌ По выбранным фильтрам нет респондентов.")
        st.stop()

    # Вкладки
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Обзор",
        "📈 Факторы",
        "🏆 Рейтинги",
        "🔍 Компания",
        "⚖️ Сравнение",
        "🏭 По секторам",
    ])

    with tab1:
        st.markdown("### Демография аудитории")
        c1, c2 = st.columns(2)
        with c1:
            age_df = _make_pct_table(filtered_resp, "Возраст", ages)
            st.altair_chart(_bar_pct_vertical(age_df, "Возраст", "pct", "По возрасту"), use_container_width=True)
        with c2:
            gender_df = _make_pct_table(filtered_resp, "Гендер")
            st.altair_chart(_bar_pct_vertical(gender_df, "Гендер", "pct", "По гендеру"), use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            exp_df = _make_pct_table(filtered_resp, "Опыт работы в ИТ / Digital")
            st.altair_chart(_bar_pct_vertical(exp_df, "Опыт работы в ИТ / Digital", "pct", "По опыту в IT"), use_container_width=True)
        with c4:
            spec_df = _make_pct_table(filtered_resp, "К какой специализации Вы себя относите?")
            spec_df = spec_df.head(15).copy()
            st.altair_chart(_bar_pct_horizontal(spec_df, "pct", "К какой специализации Вы себя относите?", "По специализации"), use_container_width=True)

    with tab2:
        st.markdown("### Анализ факторов")
        if factors_f.empty:
            st.warning("Нет данных по факторам")
        else:
            group_key = st.selectbox("Выберите группу факторов", options=list(FACTOR_GROUP_LABELS.keys()), format_func=lambda x: FACTOR_GROUP_LABELS[x])
            fdf = factors_f[factors_f["factor_group"] == group_key].copy()
            if fdf.empty:
                st.info("По выбранной группе нет данных")
            else:
                top_n = st.slider("Количество факторов", 5, 30, 15)
                top, by_pos = _prepare_factor_distribution(fdf, top_n)
                st.altair_chart(_bar_pct_horizontal(top, "pct", "factor", f"{FACTOR_GROUP_LABELS[group_key]}"), use_container_width=True)
                st.altair_chart(_grouped_pct_chart(by_pos, "factor", "rank_position", "pct", "По позициям"), use_container_width=True)

    with tab3:
        st.markdown("### Рейтинг компаний")
        if segment_metrics.empty:
            st.warning("Нет данных по компаниям")
        else:
            top_n = st.slider("Компаний в топе", 5, 20, 10, key="segment_topn")
            c1, c2 = st.columns(2)
            with c1:
                top_want = segment_metrics.sort_values("want_pct", ascending=False).head(top_n).copy()
                top_want["pct"] = (top_want["want_pct"] * 100).round(1)
                top_want["label"] = top_want["pct"].map(lambda x: f"{x:.1f}%")
                st.altair_chart(_bar_pct_horizontal(top_want, "pct", "company", "✅ Хотят работать", "sector"), use_container_width=True)
            with c2:
                anti_top = segment_metrics.sort_values("dont_want_pct", ascending=False).head(top_n).copy()
                anti_top["pct"] = (anti_top["dont_want_pct"] * 100).round(1)
                anti_top["label"] = anti_top["pct"].map(lambda x: f"{x:.1f}%")
                st.altair_chart(_bar_pct_horizontal(anti_top, "pct", "company", "❌ Не хотят работать", "sector"), use_container_width=True)

        st.divider()
        st.markdown("### Изменение к 2025")
        metric_choice = st.selectbox("Метрика", options=list(METRIC_KIND_LABEL.keys()), format_func=lambda x: METRIC_KIND_LABEL[x])
        yoy = data.rankings[data.rankings["metric_kind"] == metric_choice].copy()
        yoy = yoy.dropna(subset=["pct_2026"]).copy()
        movers = yoy.dropna(subset=["change_pp"]).copy()
        
        if movers.empty:
            st.info("Нет данных об изменениях")
        else:
            top_up = movers.sort_values("change_pp", ascending=False).head(15).copy()
            top_down = movers.sort_values("change_pp", ascending=True).head(15).copy()
            for df_ in [top_up, top_down]:
                df_["pct"] = (df_["change_pp"] * 100).round(1)
                df_["label"] = df_["pct"].map(lambda x: f"{x:.1f} п.п.")
            
            c1, c2 = st.columns(2)
            with c1:
                st.altair_chart(_bar_pct_horizontal(top_up, "pct", "company", "📈 Лидеры роста", "sector"), use_container_width=True)
            with c2:
                st.altair_chart(_bar_pct_horizontal(top_down, "pct", "company", "📉 Лидеры падения", "sector"), use_container_width=True)

        show = yoy[["company", "sector", "pct_2025", "pct_2026", "change_pp", "rank_2025", "rank_2026", "change_rank"]].copy()
        show["pct_2025"] = (show["pct_2025"] * 100).round(1)
        show["pct_2026"] = (show["pct_2026"] * 100).round(1)
        show["change_pp"] = (show["change_pp"] * 100).round(1)
        show = show.rename(columns={
            "company": "Компания", "sector": "Сектор", "pct_2025": "2025, %",
            "pct_2026": "2026, %", "change_pp": "Изм., п.п.", "rank_2025": "Место 2025",
            "rank_2026": "Место 2026", "change_rank": "Изм. места",
        })
        st.dataframe(show.sort_values("2026, %", ascending=False), use_container_width=True, hide_index=True)

    with tab4:
        st.markdown("### Детальный анализ")
        companies_sorted = data.companies["company"].dropna().unique().tolist()
        selected_company = st.selectbox("Выберите компанию", companies_sorted)
        selected_key = normalize_company_name(selected_company)

        detail_rank = data.rankings[data.rankings["company_key"] == selected_key].copy()
        if detail_rank.empty:
            st.warning("Нет данных по компании")
        else:
            detail_rank = detail_rank.sort_values("metric_kind")
            by_metric = detail_rank.set_index("metric_kind")
            metrics_order = ["want", "dont_want", "brand_awareness", "uncertainty"]
            
            mcols = st.columns(4)
            for i, mk in enumerate(metrics_order):
                if mk not in by_metric.index:
                    continue
                row = by_metric.loc[mk]
                with mcols[i]:
                    st.metric(METRIC_KIND_LABEL[mk], _pct(row["pct_2026"]), f"Δ {_pct(row['change_pp'])}")

            compare_vals = detail_rank[["metric_label", "pct_2025", "pct_2026"]].melt(
                id_vars="metric_label", var_name="year", value_name="value"
            )
            compare_vals["year"] = compare_vals["year"].map({"pct_2025": "2025", "pct_2026": "2026"})
            compare_vals["pct"] = (compare_vals["value"] * 100).round(1)
            compare_vals["label"] = compare_vals["pct"].map(lambda x: f"{x:.1f}%")
            st.altair_chart(_grouped_pct_chart(compare_vals, "metric_label", "year", "pct", f"Тренд: {selected_company}"), use_container_width=True)

            company_sent = company_raw_f[company_raw_f["company_key"] == selected_key].copy()
            c1, c2 = st.columns(2)
            with c1:
                if not company_sent.empty:
                    raw_cnt = company_sent["response_raw"].value_counts().reindex(RAW_RESPONSE_ORDER, fill_value=0).reset_index()
                    raw_cnt.columns = ["Ответ", "count"]
                    raw_cnt["pct"] = (raw_cnt["count"] / max(1, len(company_sent)) * 100).round(1)
                    raw_cnt["label"] = raw_cnt["pct"].map(lambda x: f"{x:.1f}%")
                    st.altair_chart(_bar_pct_vertical(raw_cnt, "Ответ", "pct", "Сырые ответы"), use_container_width=True)
            with c2:
                if not company_sent.empty:
                    mapped_cnt = company_sent["response_mapped"].value_counts().reindex(MAPPED_RESPONSE_ORDER, fill_value=0).reset_index()
                    mapped_cnt.columns = ["Ответ", "count"]
                    mapped_cnt["pct"] = (mapped_cnt["count"] / max(1, len(company_sent)) * 100).round(1)
                    mapped_cnt["label"] = mapped_cnt["pct"].map(lambda x: f"{x:.1f}%")
                    st.altair_chart(_bar_pct_vertical(mapped_cnt, "Ответ", "pct", "Категории"), use_container_width=True)

    with tab5:
        st.markdown("### Сравнение компаний")
        options = data.companies["company"].dropna().unique().tolist()
        default = options[:2] if len(options) >= 2 else options
        selected = st.multiselect("Выберите компании", options=options, default=default)

        if len(selected) < 2:
            st.info("Выберите минимум 2 компании")
        else:
            selected_keys = [normalize_company_name(x) for x in selected]
            selected_map = _company_name_map(data.companies)

            cmp_rank = data.rankings[data.rankings["company_key"].isin(selected_keys)].copy()
            cmp_rank["company_display"] = cmp_rank["company_key"].map(selected_map)
            cmp_rank["pct_2026_100"] = (cmp_rank["pct_2026"] * 100).round(1)
            cmp_rank["change_pp_100"] = (cmp_rank["change_pp"] * 100).round(1)
            cmp_rank["label"] = cmp_rank["pct_2026_100"].map(lambda x: f"{x:.1f}%")

            st.altair_chart(_grouped_pct_chart(cmp_rank, "metric_label", "company_display", "pct_2026_100", "Сравнение 2026"), use_container_width=True)

            cmp_chg = cmp_rank.dropna(subset=["change_pp_100"]).copy()
            if not cmp_chg.empty:
                cmp_chg["label"] = cmp_chg["change_pp_100"].map(lambda x: f"{x:.1f} п.п.")
                st.altair_chart(_grouped_pct_chart(cmp_chg, "metric_label", "company_display", "change_pp_100", "Изменения"), use_container_width=True)

            cmp_table = cmp_rank[["company_display", "metric_label", "pct_2025", "pct_2026", "change_pp", "rank_2025", "rank_2026", "change_rank"]].copy()
            cmp_table["pct_2025"] = (cmp_table["pct_2025"] * 100).round(1)
            cmp_table["pct_2026"] = (cmp_table["pct_2026"] * 100).round(1)
            cmp_table["change_pp"] = (cmp_table["change_pp"] * 100).round(1)
            cmp_table = cmp_table.rename(columns={
                "company_display": "Компания", "metric_label": "Метрика", "pct_2025": "2025, %",
                "pct_2026": "2026, %", "change_pp": "Изм., п.п.", "rank_2025": "Место 2025",
                "rank_2026": "Место 2026", "change_rank": "Изм. места",
            })
            st.dataframe(cmp_table.sort_values(["Метрика", "Компания"]), use_container_width=True, hide_index=True)


    with tab6:
        st.markdown("### 🏭 Сравнение компаний по секторам")
        st.caption("Выберите сектор чтобы увидеть все компании внутри него и сравнить их по метрикам")

        available_sectors = sorted(data.companies["sector"].dropna().unique().tolist())
        if not available_sectors:
            st.warning("Нет данных по секторам")
        else:
            selected_sector = st.selectbox(
                "Выберите сектор / тип компаний",
                options=available_sectors,
                key="sector_selectbox"
            )

            sector_companies = data.companies[data.companies["sector"] == selected_sector]["company_key"].tolist()
            sector_rankings = data.rankings[data.rankings["company_key"].isin(sector_companies)].copy()

            if sector_rankings.empty:
                st.info(f"Нет данных рейтингов для сектора «{selected_sector}»")
            else:
                companies_in_sector = sector_rankings["company"].unique()
                st.markdown(f"**Компаний в секторе «{selected_sector}»:** {len(companies_in_sector)}")

                metric_choice_s = st.selectbox(
                    "Метрика для сравнения",
                    options=list(METRIC_KIND_LABEL.keys()),
                    format_func=lambda x: METRIC_KIND_LABEL[x],
                    key="sector_metric"
                )

                sector_df = sector_rankings[sector_rankings["metric_kind"] == metric_choice_s].copy()
                sector_df = sector_df.dropna(subset=["pct_2026"]).copy()
                sector_df["pct_2026_pct"] = (sector_df["pct_2026"] * 100).round(1)

                if sector_df.empty:
                    st.info("Нет данных по выбранной метрике")
                else:
                    st.altair_chart(
                        _sector_comparison_chart(
                            sector_df,
                            "pct_2026_pct",
                            f"{METRIC_KIND_LABEL[metric_choice_s]} — {selected_sector} (2026)"
                        ),
                        use_container_width=True,
                    )

                st.divider()
                st.markdown("#### Все метрики по компаниям сектора")

                # Сводная таблица всех метрик для сектора
                pivot_sector = sector_rankings.pivot_table(
                    index="company",
                    columns="metric_kind",
                    values="pct_2026",
                    aggfunc="first"
                ).reset_index()

                rename_map = {k: v for k, v in METRIC_KIND_LABEL.items()}
                rename_map["company"] = "Компания"
                for col in pivot_sector.columns:
                    if col in METRIC_KIND_LABEL:
                        pivot_sector[col] = (pivot_sector[col] * 100).round(1)
                pivot_sector = pivot_sector.rename(columns=rename_map)
                
                st.dataframe(
                    pivot_sector.sort_values("Хотят работать" if "Хотят работать" in pivot_sector.columns else pivot_sector.columns[1], ascending=False),
                    use_container_width=True,
                    hide_index=True
                )

                st.divider()
                st.markdown("#### Изменения к 2025 внутри сектора")

                sector_change = sector_rankings[sector_rankings["metric_kind"] == metric_choice_s].copy()
                sector_change = sector_change.dropna(subset=["change_pp"]).copy()
                sector_change["change_pp_pct"] = (sector_change["change_pp"] * 100).round(1)

                if not sector_change.empty:
                    change_chart = alt.Chart(sector_change).mark_bar(cornerRadius=4).encode(
                        x=alt.X("change_pp_pct:Q", title="Изм., п.п.", axis=alt.Axis(format=".1f")),
                        y=alt.Y("company:N", sort="-x", title=""),
                        color=alt.condition(
                            alt.datum.change_pp_pct > 0,
                            alt.value("#10b981"),   # зелёный — рост
                            alt.value("#f59e0b"),   # жёлтый — падение
                        ),
                        tooltip=["company", alt.Tooltip("change_pp_pct:Q", title="Изм., п.п.", format=".1f")],
                    ).properties(
                        title=f"Изменение {METRIC_KIND_LABEL[metric_choice_s]} к 2025 — {selected_sector}",
                        height=max(250, len(sector_change) * 35)
                    ).configure_title(fontSize=14, anchor="start", color="#60a5fa")
                    
                    st.altair_chart(change_chart, use_container_width=True)


if __name__ == "__main__":
    main()
