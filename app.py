from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.data_processing import (
    METRIC_KIND_LABEL,
    SurveyData,
    apply_respondent_filters,
    load_survey_data,
    normalize_company_name,
)


DATA_PATH = Path(__file__).parent / "data" / "Copy_2026.xlsx"

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


def _bar_h(df: pd.DataFrame, x: str, y: str, color: str | None = None, title: str = "") -> alt.Chart:
    enc = {
        "x": alt.X(f"{x}:Q"),
        "y": alt.Y(f"{y}:N", sort="-x"),
        "tooltip": [y, x],
    }
    if color:
        enc["color"] = alt.Color(f"{color}:N")
        enc["tooltip"] = [y, color, x]
    return alt.Chart(df).mark_bar().encode(**enc).properties(title=title)


def _company_name_map(companies: pd.DataFrame) -> dict[str, str]:
    return {normalize_company_name(row["company"]): row["company"] for _, row in companies.iterrows()}


def main() -> None:
    st.set_page_config(page_title="Employer Analytics 2026", page_icon="📊", layout="wide")

    st.title("Employer Analytics Dashboard")
    st.caption("Источник: data/Copy_2026.xlsx")

    if not DATA_PATH.exists():
        st.error(f"Файл не найден: {DATA_PATH}")
        st.stop()

    data = load_data(str(DATA_PATH))
    respondents = data.respondents.copy()
    respondents["respondent_id"] = respondents["Номер ответа"].astype("Int64")

    st.sidebar.header("Фильтры аудитории (2026)")
    genders = sorted([x for x in respondents["Гендер"].dropna().unique().tolist()])
    ages = [x for x in AGE_ORDER if x in respondents["Возраст"].dropna().unique().tolist()] + sorted(
        [x for x in respondents["Возраст"].dropna().unique().tolist() if x not in AGE_ORDER]
    )
    exps = sorted([x for x in respondents["Опыт работы в ИТ / Digital"].dropna().unique().tolist()])
    specs = sorted([x for x in respondents["К какой специализации Вы себя относите?"].dropna().unique().tolist()])

    selected_gender = st.sidebar.multiselect("Gender", genders, default=genders)
    selected_age = st.sidebar.multiselect("Age", ages, default=ages)
    selected_exp = st.sidebar.multiselect("Experience", exps, default=exps)
    selected_spec = st.sidebar.multiselect("Specialization", specs, default=specs)

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

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Респондентов (фильтр)", f"{len(filtered_resp):,}".replace(",", " "))
    kpi2.metric("Респондентов (всего)", f"{len(respondents):,}".replace(",", " "))
    kpi3.metric("Компаний в рейтинге", f"{data.rankings['company_key'].nunique()}")

    tab_overview, tab_factors, tab_rankings, tab_company, tab_compare = st.tabs(
        [
            "Audience Overview",
            "Factors",
            "Top / Anti-Top + YoY",
            "Company Deep Dive",
            "Company Comparison",
        ]
    )

    with tab_overview:
        c1, c2 = st.columns(2)
        with c1:
            age_counts = filtered_resp["Возраст"].value_counts().reindex(ages, fill_value=0).reset_index()
            age_counts.columns = ["Возраст", "Количество"]
            chart_age = (
                alt.Chart(age_counts)
                .mark_bar()
                .encode(
                    x=alt.X("Возраст:N", sort=ages),
                    y=alt.Y("Количество:Q"),
                    tooltip=["Возраст", "Количество"],
                )
                .properties(title="Возраст")
            )
            st.altair_chart(chart_age, use_container_width=True)

        with c2:
            g_counts = filtered_resp["Гендер"].value_counts().reset_index()
            g_counts.columns = ["Гендер", "Количество"]
            chart_gender = (
                alt.Chart(g_counts)
                .mark_arc()
                .encode(theta="Количество:Q", color="Гендер:N", tooltip=["Гендер", "Количество"])
                .properties(title="Gender")
            )
            st.altair_chart(chart_gender, use_container_width=True)

        spec_counts = (
            filtered_resp["К какой специализации Вы себя относите?"].value_counts().head(20).reset_index()
        )
        spec_counts.columns = ["Специализация", "Количество"]
        chart_spec = _bar_h(spec_counts, x="Количество", y="Специализация", title="Top Specializations")
        st.altair_chart(chart_spec, use_container_width=True)

    with tab_factors:
        if factors_f.empty:
            st.warning("Нет данных по факторам после фильтрации.")
        else:
            group_key = st.selectbox(
                "Группа факторов",
                options=list(FACTOR_GROUP_LABELS.keys()),
                format_func=lambda x: FACTOR_GROUP_LABELS[x],
            )
            fdf = factors_f[factors_f["factor_group"] == group_key].copy()
            if fdf.empty:
                st.info("По выбранной группе нет данных.")
            else:
                top_n = st.slider("Top N факторов", min_value=5, max_value=30, value=15)
                top_factors = fdf["factor"].value_counts().head(top_n).reset_index()
                top_factors.columns = ["factor", "cnt"]
                chart_total = _bar_h(
                    top_factors, x="cnt", y="factor", title=f"{FACTOR_GROUP_LABELS[group_key]}: общий топ"
                )
                st.altair_chart(chart_total, use_container_width=True)

                by_pos = (
                    fdf[fdf["factor"].isin(top_factors["factor"])]
                    .groupby(["factor", "rank_position"])
                    .size()
                    .reset_index(name="cnt")
                )
                chart_pos = (
                    alt.Chart(by_pos)
                    .mark_bar()
                    .encode(
                        x=alt.X("cnt:Q", title="Количество"),
                        y=alt.Y("factor:N", sort="-x", title="Фактор"),
                        color=alt.Color("rank_position:N", title="Позиция"),
                        tooltip=["factor", "rank_position", "cnt"],
                    )
                    .properties(title=f"{FACTOR_GROUP_LABELS[group_key]}: позиции 1/2/3")
                )
                st.altair_chart(chart_pos, use_container_width=True)

    with tab_rankings:
        st.subheader("Top / Anti-Top (по отфильтрованной аудитории 2026)")
        if segment_metrics.empty:
            st.warning("Нет данных по компаниям после фильтрации.")
        else:
            top_n = st.slider("Количество компаний в топе", 5, 20, 10, key="segment_topn")
            c1, c2 = st.columns(2)
            with c1:
                top_want = segment_metrics.sort_values("want_pct", ascending=False).head(top_n)
                chart_top_want = _bar_h(
                    top_want,
                    x="want_pct",
                    y="company",
                    color="sector",
                    title="Top Companies by Want %",
                ).encode(x=alt.X("want_pct:Q", axis=alt.Axis(format=".0%")))
                st.altair_chart(chart_top_want, use_container_width=True)
            with c2:
                anti_top = segment_metrics.sort_values("dont_want_pct", ascending=False).head(top_n)
                chart_antitop = _bar_h(
                    anti_top,
                    x="dont_want_pct",
                    y="company",
                    color="sector",
                    title="Anti-Top Companies by Don't want %",
                ).encode(x=alt.X("dont_want_pct:Q", axis=alt.Axis(format=".0%")))
                st.altair_chart(chart_antitop, use_container_width=True)

        st.subheader("Изменение относительно 2025 (общий рейтинг)")
        metric_choice = st.selectbox(
            "Метрика",
            options=list(METRIC_KIND_LABEL.keys()),
            format_func=lambda x: METRIC_KIND_LABEL[x],
        )
        yoy = data.rankings[data.rankings["metric_kind"] == metric_choice].copy()
        yoy = yoy.dropna(subset=["pct_2026"]).copy()

        movers = yoy.dropna(subset=["change_pp"]).copy()
        if movers.empty:
            st.info("Нет числовых данных изменения по выбранной метрике.")
        else:
            top_up = movers.sort_values("change_pp", ascending=False).head(15)
            top_down = movers.sort_values("change_pp", ascending=True).head(15)
            c1, c2 = st.columns(2)
            with c1:
                chart_up = _bar_h(
                    top_up, x="change_pp", y="company", color="sector", title="Лидеры роста"
                ).encode(x=alt.X("change_pp:Q", axis=alt.Axis(format=".0%")))
                st.altair_chart(chart_up, use_container_width=True)
            with c2:
                chart_down = _bar_h(
                    top_down, x="change_pp", y="company", color="sector", title="Лидеры падения"
                ).encode(x=alt.X("change_pp:Q", axis=alt.Axis(format=".0%")))
                st.altair_chart(chart_down, use_container_width=True)

        table_cols = [
            "company",
            "sector",
            "pct_2025",
            "pct_2026",
            "change_pp",
            "rank_2025",
            "rank_2026",
            "change_rank",
        ]
        show = yoy[table_cols].rename(
            columns={
                "company": "Company",
                "sector": "Sector",
                "pct_2025": "2025 %",
                "pct_2026": "2026 %",
                "change_pp": "Δ p.p.",
                "rank_2025": "Rank 2025",
                "rank_2026": "Rank 2026",
                "change_rank": "Rank change",
            }
        )
        st.dataframe(
            show.sort_values("2026 %", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    with tab_company:
        st.subheader("Детальный анализ компании")
        companies_sorted = data.companies["company"].dropna().unique().tolist()
        selected_company = st.selectbox("Компания", companies_sorted)
        selected_key = normalize_company_name(selected_company)

        detail_rank = data.rankings[data.rankings["company_key"] == selected_key].copy()
        if detail_rank.empty:
            st.warning("Для выбранной компании нет строк в рейтинге.")
        else:
            detail_rank = detail_rank.sort_values("metric_kind")
            by_metric = detail_rank.set_index("metric_kind")
            metrics_order = ["want", "dont_want", "brand_awareness", "uncertainty"]
            mcols = st.columns(4)
            for i, mk in enumerate(metrics_order):
                if mk not in by_metric.index:
                    continue
                row = by_metric.loc[mk]
                mcols[i].metric(
                    label=METRIC_KIND_LABEL[mk],
                    value=_pct(row["pct_2026"]),
                    delta=f"Δ p.p.: {_pct(row['change_pp'])} | Δ rank: {_fmt_int(row['change_rank'])}",
                    delta_color="off",
                )

            compare_vals = detail_rank[
                ["metric_label", "pct_2025", "pct_2026"]
            ].melt(id_vars="metric_label", var_name="year", value_name="value")
            compare_vals["year"] = compare_vals["year"].map({"pct_2025": "2025", "pct_2026": "2026"})
            chart_profile = (
                alt.Chart(compare_vals)
                .mark_bar()
                .encode(
                    x=alt.X("metric_label:N", title="Метрика"),
                    xOffset=alt.XOffset("year:N", title="Год"),
                    y=alt.Y("value:Q", title="Значение", axis=alt.Axis(format=".0%")),
                    color=alt.Color("year:N"),
                    tooltip=["metric_label", "year", alt.Tooltip("value:Q", format=".1%")],
                )
                .properties(title=f"Профиль метрик: {selected_company}")
            )
            st.altair_chart(chart_profile, use_container_width=True)

            company_sent = company_raw_f[company_raw_f["company_key"] == selected_key].copy()
            c1, c2 = st.columns(2)
            with c1:
                if company_sent.empty:
                    st.info("Нет ответов по компании после фильтрации.")
                else:
                    raw_cnt = (
                        company_sent["response_raw"].value_counts().reindex(RAW_RESPONSE_ORDER, fill_value=0).reset_index()
                    )
                    raw_cnt.columns = ["Ответ", "Количество"]
                    raw_cnt["Доля"] = raw_cnt["Количество"] / max(1, len(company_sent))
                    chart_raw = (
                        alt.Chart(raw_cnt)
                        .mark_bar()
                        .encode(
                            x=alt.X("Ответ:N"),
                            y=alt.Y("Доля:Q", axis=alt.Axis(format=".0%")),
                            tooltip=["Ответ", "Количество", alt.Tooltip("Доля:Q", format=".1%")],
                        )
                        .properties(title="Распределение сырых ответов")
                    )
                    st.altair_chart(chart_raw, use_container_width=True)
            with c2:
                if company_sent.empty:
                    st.info("Нет данных.")
                else:
                    mapped_cnt = (
                        company_sent["response_mapped"]
                        .value_counts()
                        .reindex(MAPPED_RESPONSE_ORDER, fill_value=0)
                        .reset_index()
                    )
                    mapped_cnt.columns = ["Ответ", "Количество"]
                    mapped_cnt["Доля"] = mapped_cnt["Количество"] / max(1, len(company_sent))
                    chart_mapped = (
                        alt.Chart(mapped_cnt)
                        .mark_bar()
                        .encode(
                            x=alt.X("Ответ:N"),
                            y=alt.Y("Доля:Q", axis=alt.Axis(format=".0%")),
                            color=alt.Color("Ответ:N"),
                            tooltip=["Ответ", "Количество", alt.Tooltip("Доля:Q", format=".1%")],
                        )
                        .properties(title="Хочу / Не хочу / Не уверен / Не знаю")
                    )
                    st.altair_chart(chart_mapped, use_container_width=True)

            st.markdown("**Детали изменения рейтинга по метрикам**")
            rank_table = detail_rank[
                ["metric_label", "pct_2025", "pct_2026", "change_pp", "rank_2025", "rank_2026", "change_rank"]
            ].rename(
                columns={
                    "metric_label": "Metric",
                    "pct_2025": "2025 %",
                    "pct_2026": "2026 %",
                    "change_pp": "Δ p.p.",
                    "rank_2025": "Rank 2025",
                    "rank_2026": "Rank 2026",
                    "change_rank": "Rank change",
                }
            )
            st.dataframe(rank_table, use_container_width=True, hide_index=True)

    with tab_compare:
        st.subheader("Сравнение компаний")
        options = data.companies["company"].dropna().unique().tolist()
        default = options[:2] if len(options) >= 2 else options
        selected = st.multiselect("Выберите 2 или больше компаний", options=options, default=default)

        if len(selected) < 2:
            st.info("Выберите минимум 2 компании.")
        else:
            selected_keys = [normalize_company_name(x) for x in selected]
            selected_map = _company_name_map(data.companies)

            cmp_rank = data.rankings[data.rankings["company_key"].isin(selected_keys)].copy()
            cmp_rank["company_display"] = cmp_rank["company_key"].map(selected_map)

            chart_cmp_pct = (
                alt.Chart(cmp_rank)
                .mark_bar()
                .encode(
                    x=alt.X("metric_label:N", title="Метрика"),
                    xOffset=alt.XOffset("company_display:N", title="Компания"),
                    y=alt.Y("pct_2026:Q", axis=alt.Axis(format=".0%"), title="2026 %"),
                    color=alt.Color("company_display:N"),
                    tooltip=[
                        "company_display",
                        "metric_label",
                        alt.Tooltip("pct_2026:Q", format=".1%"),
                        alt.Tooltip("pct_2025:Q", format=".1%"),
                        alt.Tooltip("change_pp:Q", format=".1%"),
                    ],
                )
                .properties(title="Сравнение компаний: 2026 %")
            )
            st.altair_chart(chart_cmp_pct, use_container_width=True)

            cmp_chg = cmp_rank.dropna(subset=["change_pp"]).copy()
            if not cmp_chg.empty:
                chart_cmp_chg = (
                    alt.Chart(cmp_chg)
                    .mark_bar()
                    .encode(
                        x=alt.X("metric_label:N", title="Метрика"),
                        xOffset=alt.XOffset("company_display:N", title="Компания"),
                        y=alt.Y("change_pp:Q", axis=alt.Axis(format=".0%"), title="Δ p.p."),
                        color=alt.Color("company_display:N"),
                        tooltip=[
                            "company_display",
                            "metric_label",
                            alt.Tooltip("change_pp:Q", format=".1%"),
                            "rank_2025",
                            "rank_2026",
                            "change_rank",
                        ],
                    )
                    .properties(title="Сравнение компаний: изменение к 2025")
                )
                st.altair_chart(chart_cmp_chg, use_container_width=True)

            cmp_sent = company_raw_f[company_raw_f["company_key"].isin(selected_keys)].copy()
            if not cmp_sent.empty:
                cmp_sent["company_display"] = cmp_sent["company_key"].map(selected_map)
                sent_dist = (
                    cmp_sent.groupby(["company_display", "response_mapped"])
                    .size()
                    .reset_index(name="cnt")
                )
                sent_dist["share"] = sent_dist["cnt"] / sent_dist.groupby("company_display")["cnt"].transform("sum")
                chart_sent = (
                    alt.Chart(sent_dist)
                    .mark_bar()
                    .encode(
                        x=alt.X("company_display:N", title="Компания"),
                        y=alt.Y("share:Q", axis=alt.Axis(format=".0%"), title="Доля"),
                        color=alt.Color("response_mapped:N", title="Ответ"),
                        order=alt.Order(
                            "response_mapped:N",
                            sort="ascending",
                        ),
                        tooltip=["company_display", "response_mapped", alt.Tooltip("share:Q", format=".1%")],
                    )
                    .properties(title="Распределение ответов в выбранном сегменте")
                )
                st.altair_chart(chart_sent, use_container_width=True)

            cmp_table = cmp_rank[
                [
                    "company_display",
                    "metric_label",
                    "pct_2025",
                    "pct_2026",
                    "change_pp",
                    "rank_2025",
                    "rank_2026",
                    "change_rank",
                ]
            ].rename(
                columns={
                    "company_display": "Company",
                    "metric_label": "Metric",
                    "pct_2025": "2025 %",
                    "pct_2026": "2026 %",
                    "change_pp": "Δ p.p.",
                    "rank_2025": "Rank 2025",
                    "rank_2026": "Rank 2026",
                    "change_rank": "Rank change",
                }
            )
            st.dataframe(cmp_table.sort_values(["Metric", "Company"]), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
