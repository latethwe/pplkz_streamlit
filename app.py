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
    base = alt.Chart(df)
    if color_col:
        bar = base.mark_bar().encode(
            x=alt.X(f"{x_col}:N", title=x_col),
            y=alt.Y(f"{y_col}:Q", title="%", axis=alt.Axis(format=".1f")),
            color=alt.Color(f"{color_col}:N"),
            tooltip=[x_col, color_col, alt.Tooltip(f"{y_col}:Q", format=".1f")],
        )
    else:
        bar = base.mark_bar().encode(
            x=alt.X(f"{x_col}:N", title=x_col),
            y=alt.Y(f"{y_col}:Q", title="%", axis=alt.Axis(format=".1f")),
            tooltip=[x_col, alt.Tooltip(f"{y_col}:Q", format=".1f")],
        )

    text = base.mark_text(dy=-8, size=11).encode(
        x=alt.X(f"{x_col}:N"),
        y=alt.Y(f"{y_col}:Q"),
        text="label:N",
    )
    return (bar + text).properties(title=title)


def _bar_pct_horizontal(
    df: pd.DataFrame, x_col: str, y_col: str, title: str, color_col: str | None = None
) -> alt.Chart:
    base = alt.Chart(df)
    if color_col:
        bar = base.mark_bar().encode(
            x=alt.X(f"{x_col}:Q", title="%", axis=alt.Axis(format=".1f")),
            y=alt.Y(f"{y_col}:N", sort="-x", title=y_col),
            color=alt.Color(f"{color_col}:N"),
            tooltip=[y_col, color_col, alt.Tooltip(f"{x_col}:Q", format=".1f")],
        )
    else:
        bar = base.mark_bar().encode(
            x=alt.X(f"{x_col}:Q", title="%", axis=alt.Axis(format=".1f")),
            y=alt.Y(f"{y_col}:N", sort="-x", title=y_col),
            tooltip=[y_col, alt.Tooltip(f"{x_col}:Q", format=".1f")],
        )
    text = base.mark_text(align="left", dx=3, size=10).encode(
        x=alt.X(f"{x_col}:Q"),
        y=alt.Y(f"{y_col}:N", sort="-x"),
        text="label:N",
    )
    return (bar + text).properties(title=title)


def _grouped_pct_chart(df: pd.DataFrame, x: str, group: str, y: str, title: str) -> alt.Chart:
    base = alt.Chart(df)
    bar = base.mark_bar().encode(
        x=alt.X(f"{x}:N", title=x),
        xOffset=alt.XOffset(f"{group}:N", title=group),
        y=alt.Y(f"{y}:Q", title="%", axis=alt.Axis(format=".1f")),
        color=alt.Color(f"{group}:N"),
        tooltip=[x, group, alt.Tooltip(f"{y}:Q", format=".1f")],
    )
    text = base.mark_text(dy=-8, size=9).encode(
        x=alt.X(f"{x}:N"),
        xOffset=alt.XOffset(f"{group}:N"),
        y=alt.Y(f"{y}:Q"),
        text="label:N",
    )
    return (bar + text).properties(title=title)


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

    if len(filtered_resp) == 0:
        st.warning("По выбранным фильтрам нет респондентов.")
        st.stop()

    tab_overview, tab_factors, tab_rankings, tab_company, tab_compare = st.tabs(
        [
            "Audience Overview",
            "Факторы",
            "Top / Anti-Top + Изменения к 2025",
            "Детально по компании",
            "Сравнение компаний",
        ]
    )

    with tab_overview:
        c1, c2 = st.columns(2)
        with c1:
            age_df = _make_pct_table(filtered_resp, "Возраст", ages)
            st.altair_chart(
                _bar_pct_vertical(age_df, "Возраст", "pct", "Возраст (доля, %)"),
                use_container_width=True,
            )
        with c2:
            gender_df = _make_pct_table(filtered_resp, "Гендер")
            st.altair_chart(
                _bar_pct_vertical(gender_df, "Гендер", "pct", "Gender (доля, %)"),
                use_container_width=True,
            )

        c3, c4 = st.columns(2)
        with c3:
            exp_df = _make_pct_table(filtered_resp, "Опыт работы в ИТ / Digital")
            st.altair_chart(
                _bar_pct_vertical(exp_df, "Опыт работы в ИТ / Digital", "pct", "Experience (доля, %)"),
                use_container_width=True,
            )
        with c4:
            spec_df = _make_pct_table(filtered_resp, "К какой специализации Вы себя относите?")
            spec_df = spec_df.head(20).copy()
            st.altair_chart(
                _bar_pct_horizontal(spec_df, "pct", "К какой специализации Вы себя относите?", "Specialization (доля, %)"),
                use_container_width=True,
            )

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
                top, by_pos = _prepare_factor_distribution(fdf, top_n)

                st.altair_chart(
                    _bar_pct_horizontal(top, "pct", "factor", f"{FACTOR_GROUP_LABELS[group_key]}: общий топ, %"),
                    use_container_width=True,
                )

                st.altair_chart(
                    _grouped_pct_chart(by_pos, "factor", "rank_position", "pct", "Распределение по позициям 1/2/3, %"),
                    use_container_width=True,
                )

    with tab_rankings:
        st.subheader("Top / Anti-Top (по отфильтрованной аудитории 2026)")
        if segment_metrics.empty:
            st.warning("Нет данных по компаниям после фильтрации.")
        else:
            top_n = st.slider("Количество компаний в топе", 5, 20, 10, key="segment_topn")
            c1, c2 = st.columns(2)
            with c1:
                top_want = segment_metrics.sort_values("want_pct", ascending=False).head(top_n).copy()
                top_want["pct"] = (top_want["want_pct"] * 100).round(1)
                top_want["label"] = top_want["pct"].map(lambda x: f"{x:.1f}%")
                st.altair_chart(
                    _bar_pct_horizontal(top_want, "pct", "company", "Топ компаний по «Хотят работать, %»", "sector"),
                    use_container_width=True,
                )
            with c2:
                anti_top = segment_metrics.sort_values("dont_want_pct", ascending=False).head(top_n).copy()
                anti_top["pct"] = (anti_top["dont_want_pct"] * 100).round(1)
                anti_top["label"] = anti_top["pct"].map(lambda x: f"{x:.1f}%")
                st.altair_chart(
                    _bar_pct_horizontal(anti_top, "pct", "company", "Анти-топ по «Не хотят работать, %»", "sector"),
                    use_container_width=True,
                )

        st.subheader("Изменение относительно 2025")
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
            top_up = movers.sort_values("change_pp", ascending=False).head(15).copy()
            top_down = movers.sort_values("change_pp", ascending=True).head(15).copy()

            for df_ in [top_up, top_down]:
                df_["pct"] = (df_["change_pp"] * 100).round(1)
                df_["label"] = df_["pct"].map(lambda x: f"{x:.1f} п.п.")

            c1, c2 = st.columns(2)
            with c1:
                st.altair_chart(
                    _bar_pct_horizontal(top_up, "pct", "company", "Лидеры роста, п.п.", "sector"),
                    use_container_width=True,
                )
            with c2:
                st.altair_chart(
                    _bar_pct_horizontal(top_down, "pct", "company", "Лидеры падения, п.п.", "sector"),
                    use_container_width=True,
                )

        show = yoy[
            ["company", "sector", "pct_2025", "pct_2026", "change_pp", "rank_2025", "rank_2026", "change_rank"]
        ].copy()
        show["pct_2025"] = (show["pct_2025"] * 100).round(1)
        show["pct_2026"] = (show["pct_2026"] * 100).round(1)
        show["change_pp"] = (show["change_pp"] * 100).round(1)
        show = show.rename(
            columns={
                "company": "Компания",
                "sector": "Сектор",
                "pct_2025": "2025, %",
                "pct_2026": "2026, %",
                "change_pp": "Изм., п.п.",
                "rank_2025": "Место 2025",
                "rank_2026": "Место 2026",
                "change_rank": "Изм. места",
            }
        )
        st.dataframe(show.sort_values("2026, %", ascending=False), use_container_width=True, hide_index=True)

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
                    delta=f"Δ п.п.: {_pct(row['change_pp'])} | Δ места: {_fmt_int(row['change_rank'])}",
                    delta_color="off",
                )

            compare_vals = detail_rank[["metric_label", "pct_2025", "pct_2026"]].melt(
                id_vars="metric_label", var_name="year", value_name="value"
            )
            compare_vals["year"] = compare_vals["year"].map({"pct_2025": "2025", "pct_2026": "2026"})
            compare_vals["pct"] = (compare_vals["value"] * 100).round(1)
            compare_vals["label"] = compare_vals["pct"].map(lambda x: f"{x:.1f}%")
            st.altair_chart(
                _grouped_pct_chart(compare_vals, "metric_label", "year", "pct", f"Профиль метрик: {selected_company}"),
                use_container_width=True,
            )

            company_sent = company_raw_f[company_raw_f["company_key"] == selected_key].copy()
            c1, c2 = st.columns(2)
            with c1:
                if company_sent.empty:
                    st.info("Нет ответов по компании после фильтрации.")
                else:
                    raw_cnt = (
                        company_sent["response_raw"].value_counts().reindex(RAW_RESPONSE_ORDER, fill_value=0).reset_index()
                    )
                    raw_cnt.columns = ["Ответ", "count"]
                    raw_cnt["pct"] = (raw_cnt["count"] / max(1, len(company_sent)) * 100).round(1)
                    raw_cnt["label"] = raw_cnt["pct"].map(lambda x: f"{x:.1f}%")
                    st.altair_chart(
                        _bar_pct_vertical(raw_cnt, "Ответ", "pct", "Распределение сырых ответов, %"),
                        use_container_width=True,
                    )
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
                    mapped_cnt.columns = ["Ответ", "count"]
                    mapped_cnt["pct"] = (mapped_cnt["count"] / max(1, len(company_sent)) * 100).round(1)
                    mapped_cnt["label"] = mapped_cnt["pct"].map(lambda x: f"{x:.1f}%")
                    st.altair_chart(
                        _bar_pct_vertical(mapped_cnt, "Ответ", "pct", "Хочу / Не хочу / Не уверен / Не знаю, %", "Ответ"),
                        use_container_width=True,
                    )

            st.markdown("**Как разные сегменты аудитории относятся к компании**")
            d1, d2 = st.columns(2)
            with d1:
                gender_dist = _company_demographic_distribution(company_sent, filtered_resp, "Гендер")
                st.altair_chart(
                    _grouped_pct_chart(gender_dist, "Гендер", "response_mapped", "pct", "Отношение по gender, %"),
                    use_container_width=True,
                )
            with d2:
                age_dist = _company_demographic_distribution(company_sent, filtered_resp, "Возраст", AGE_ORDER)
                st.altair_chart(
                    _grouped_pct_chart(age_dist, "Возраст", "response_mapped", "pct", "Отношение по age, %"),
                    use_container_width=True,
                )
            d3, d4 = st.columns(2)
            with d3:
                exp_dist = _company_demographic_distribution(company_sent, filtered_resp, "Опыт работы в ИТ / Digital")
                st.altair_chart(
                    _grouped_pct_chart(
                        exp_dist, "Опыт работы в ИТ / Digital", "response_mapped", "pct", "Отношение по experience, %"
                    ),
                    use_container_width=True,
                )
            with d4:
                spec_dist = _company_demographic_distribution(
                    company_sent, filtered_resp, "К какой специализации Вы себя относите?"
                )
                spec_dist = spec_dist[spec_dist["К какой специализации Вы себя относите?"].isin(
                    spec_dist.groupby("К какой специализации Вы себя относите?")["count"].sum().sort_values(ascending=False).head(12).index
                )]
                st.altair_chart(
                    _grouped_pct_chart(
                        spec_dist,
                        "К какой специализации Вы себя относите?",
                        "response_mapped",
                        "pct",
                        "Отношение по specialization, %",
                    ),
                    use_container_width=True,
                )

            rank_table = detail_rank[
                ["metric_label", "pct_2025", "pct_2026", "change_pp", "rank_2025", "rank_2026", "change_rank"]
            ].copy()
            rank_table["pct_2025"] = (rank_table["pct_2025"] * 100).round(1)
            rank_table["pct_2026"] = (rank_table["pct_2026"] * 100).round(1)
            rank_table["change_pp"] = (rank_table["change_pp"] * 100).round(1)
            rank_table = rank_table.rename(
                columns={
                    "metric_label": "Метрика",
                    "pct_2025": "2025, %",
                    "pct_2026": "2026, %",
                    "change_pp": "Изм., п.п.",
                    "rank_2025": "Место 2025",
                    "rank_2026": "Место 2026",
                    "change_rank": "Изм. места",
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
            cmp_rank["pct_2026_100"] = (cmp_rank["pct_2026"] * 100).round(1)
            cmp_rank["change_pp_100"] = (cmp_rank["change_pp"] * 100).round(1)
            cmp_rank["label"] = cmp_rank["pct_2026_100"].map(lambda x: f"{x:.1f}%")
            cmp_rank["label_chg"] = cmp_rank["change_pp_100"].map(lambda x: f"{x:.1f} п.п." if pd.notna(x) else "")

            st.altair_chart(
                _grouped_pct_chart(cmp_rank, "metric_label", "company_display", "pct_2026_100", "Сравнение компаний: 2026, %"),
                use_container_width=True,
            )

            cmp_chg = cmp_rank.dropna(subset=["change_pp_100"]).copy()
            if not cmp_chg.empty:
                cmp_chg["label"] = cmp_chg["change_pp_100"].map(lambda x: f"{x:.1f} п.п.")
                st.altair_chart(
                    _grouped_pct_chart(cmp_chg, "metric_label", "company_display", "change_pp_100", "Сравнение изменений к 2025, п.п."),
                    use_container_width=True,
                )

            cmp_sent = company_raw_f[company_raw_f["company_key"].isin(selected_keys)].copy()
            if not cmp_sent.empty:
                cmp_sent["company_display"] = cmp_sent["company_key"].map(selected_map)
                sent_dist = (
                    cmp_sent.groupby(["company_display", "response_mapped"])
                    .size()
                    .reset_index(name="count")
                )
                sent_dist["pct"] = (sent_dist["count"] / sent_dist.groupby("company_display")["count"].transform("sum") * 100).round(1)
                sent_dist["label"] = sent_dist["pct"].map(lambda x: f"{x:.1f}%")
                st.altair_chart(
                    _grouped_pct_chart(sent_dist, "company_display", "response_mapped", "pct", "Распределение ответов, %"),
                    use_container_width=True,
                )

            cmp_table = cmp_rank[
                ["company_display", "metric_label", "pct_2025", "pct_2026", "change_pp", "rank_2025", "rank_2026", "change_rank"]
            ].copy()
            cmp_table["pct_2025"] = (cmp_table["pct_2025"] * 100).round(1)
            cmp_table["pct_2026"] = (cmp_table["pct_2026"] * 100).round(1)
            cmp_table["change_pp"] = (cmp_table["change_pp"] * 100).round(1)
            cmp_table = cmp_table.rename(
                columns={
                    "company_display": "Компания",
                    "metric_label": "Метрика",
                    "pct_2025": "2025, %",
                    "pct_2026": "2026, %",
                    "change_pp": "Изм., п.п.",
                    "rank_2025": "Место 2025",
                    "rank_2026": "Место 2026",
                    "change_rank": "Изм. места",
                }
            )
            st.dataframe(cmp_table.sort_values(["Метрика", "Компания"]), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
