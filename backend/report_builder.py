"""
report_builder.py
Centralised data loading and Markdown section builders for all report types.

Three public entry points:
  - build_executive_report(data)       → full 9-section executive report
  - build_deep_report(data)            → full 9-section deep analysis report
  - build_executive_report_brief(data) → 5-section summary (API default)

Data is loaded via:
  - load_report_data(start_date, end_date, include_faqs, top_n)
"""
from __future__ import annotations

import pandas as pd
from collections import defaultdict
from datetime import datetime

from .report_helpers import N, pct, md_table, trunc, dict_to_table, hourly_to_shifts, split_criteria_counts
from .engine import DataEngine
from .metrics import get_general_kpis
from .temporal import get_temporal_analysis
from .categorical import get_categorical_analysis
from .summary import get_survey_stats
from .reports import get_volume_report, get_survey_utility_analysis
from .dashboard_metrics import get_extended_funnel
from .gaps_analysis import analyze_gaps_and_referrals
from .faqs import get_faqs_by_category
from .reports_deep import get_kpis_detailed, get_categories_detailed, get_products_detailed, get_failures_detailed


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_report_data(
    start_date: str | None = None,
    end_date: str | None = None,
    include_faqs: bool = False,
    top_n: int = 5,
) -> dict:
    """
    Load all data and pre-compute analyses needed for report generation.
    Returns a dict with every computed artifact.
    """
    engine = DataEngine.get_instance()
    df = engine.get_messages(start_date, end_date)
    failures_df = engine.get_failures()
    referrals_df = engine.get_referrals()
    period = engine.get_data_period()

    # Apply date filter to failures_df and referrals_df
    if start_date or end_date:
        for name in ("failures_df", "referrals_df"):
            frame = failures_df if name == "failures_df" else referrals_df
            if frame is not None and not frame.empty and "fecha" in frame.columns:
                mask = pd.Series(True, index=frame.index)
                if start_date:
                    mask &= frame["fecha"].astype(str) >= start_date
                if end_date:
                    mask &= frame["fecha"].astype(str) <= end_date
                if name == "failures_df":
                    failures_df = frame[mask]
                else:
                    referrals_df = frame[mask]

    total_msgs = len(df)
    total_convs = df['thread_id'].nunique() if not df.empty else 0

    kpis = get_general_kpis(df)
    temporal = get_temporal_analysis(df)
    categorical = get_categorical_analysis(df)
    survey_stats = get_survey_stats(df)
    funnel = get_extended_funnel(df)
    funnel_kpis = funnel.get("kpis", {})
    survey_util = get_survey_utility_analysis(df)
    volume_rpt = get_volume_report(df)
    gaps_data = analyze_gaps_and_referrals(df)

    faqs = get_faqs_by_category(df, top_n=top_n) if include_faqs else {}

    # Detailed data for the expanded brief report
    kpis_detailed = get_kpis_detailed(df)
    categories_detailed = get_categories_detailed(df, referrals_df, failures_df)
    products_detailed = get_products_detailed(df, referrals_df, failures_df)
    failures_detailed = get_failures_detailed(df, failures_df)

    return {
        "df": df,
        "failures_df": failures_df,
        "referrals_df": referrals_df,
        "period": period,
        "total_msgs": total_msgs,
        "total_convs": total_convs,
        "kpis": kpis,
        "temporal": temporal,
        "categorical": categorical,
        "survey_stats": survey_stats,
        "funnel": funnel,
        "funnel_kpis": funnel_kpis,
        "survey_util": survey_util,
        "volume_rpt": volume_rpt,
        "gaps_data": gaps_data,
        "faqs": faqs,
        "kpis_detailed": kpis_detailed,
        "categories_detailed": categories_detailed,
        "products_detailed": products_detailed,
        "failures_detailed": failures_detailed,
        "generated_at": datetime.now(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# EXECUTIVE REPORT — Section builders
# ═══════════════════════════════════════════════════════════════════════════

def _exec_header(data: dict) -> str:
    period = data["period"]
    generated_at = data["generated_at"]
    return f"""# Informe Ejecutivo — Asistente Virtual

**Período de análisis:** {period.get("start", "N/A")} — {period.get("end", "N/A")}
**Generado:** {generated_at.strftime('%Y-%m-%d %H:%M:%S')}
**Fuente de datos:** `data/chat_data.db` · {N(data["total_msgs"])} mensajes · {N(data["total_convs"])} conversaciones

---"""


def _exec_summary(data: dict) -> str:
    kpis = data["kpis"]
    fk = data["funnel_kpis"]
    gaps_data = data["gaps_data"]

    total_convs = kpis.get("total_conversations", 0)
    abandonment = kpis.get("abandonment_rate", 0)
    self_service = fk.get("self_service_rate", 0)
    utility = fk.get("utility_index", 0)
    total_gaps = len(gaps_data.get("gaps", []))
    referral_rate = fk.get("referral_rate", 0)

    one_in = "3" if abandonment > 30 else "4"
    narrative = (
        f"Durante el período analizado, el asistente virtual atendió **{N(total_convs)} conversaciones**. "
        f"La tasa de abandono temprano fue del **{abandonment:.1f}%**, lo que indica que aproximadamente "
        f"1 de cada {one_in} usuarios no interactuó de forma significativa con el asistente. "
        f"El **{self_service:.1f}%** de las conversaciones se resolvió de forma autónoma sin derivar "
        f"al usuario a canales externos, mientras que el **{referral_rate:.1f}%** fue dirigido a "
        f"soporte humano o canales alternativos. "
        f"Entre quienes respondieron la encuesta de satisfacción, el índice de utilidad fue del "
        f"**{utility:.1f}%**. "
        f"Se identificaron **{N(total_gaps)} consultas sin respuesta adecuada** del bot, "
        f"representando oportunidades prioritarias de mejora en la base de conocimiento."
    )

    waste_count = fk.get("value_waste_count", 0)
    waste_pct = fk.get("value_waste_pct", 0)

    summary_rows = [
        ["Total conversaciones", N(total_convs)],
        ["Usuarios únicos", N(fk.get("unique_users", 0))],
        ["Tasa de abandono", f"{abandonment:.1f}%"],
        ["Auto-servicio", f"{self_service:.1f}%"],
        ["Índice de utilidad (enc.)", f"{utility:.1f}%"],
        ["Gasto de valor", f"{N(waste_count)} conv. ({waste_pct:.1f}%)"],
    ]

    return f"""## Resumen Ejecutivo

{narrative}

{md_table(summary_rows, ["Indicador", "Valor"])}"""


def _exec_kpis(data: dict) -> str:
    kpis = data["kpis"]
    survey_stats = data["survey_stats"]
    fk = data["funnel_kpis"]

    total_msgs = kpis.get("total_messages", 0)
    by_type = kpis.get("messages_by_type", {})
    total_convs = kpis.get("total_conversations", 0)
    abandonment = kpis.get("abandonment_rate", 0)
    active_rate = fk.get("active_rate", 0)
    total_users = kpis.get("total_users", 0)
    avg_msgs = kpis.get("avg_messages_per_thread", 0)
    median_msgs = kpis.get("median_messages_per_thread", 0)
    avg_human = kpis.get("avg_human_messages_per_thread", 0)
    inp_tok = kpis.get("total_input_tokens", 0)
    out_tok = kpis.get("total_output_tokens", 0)
    avg_inp = kpis.get("avg_input_tokens_per_ai_msg", 0)
    avg_out = kpis.get("avg_output_tokens_per_ai_msg", 0)

    abandon_count = int(total_convs * abandonment / 100) if total_convs else 0
    active_count = int(total_convs * active_rate / 100) if total_convs else 0

    stats = survey_stats.get("stats", {})
    total_surveys = stats.get("total", 0)
    useful_surveys = stats.get("useful", 0)
    notusef_surveys = stats.get("not_useful", 0)
    utility_index = fk.get("utility_index", 0)
    survey_part = fk.get("survey_participation", 0)

    vol_rows = [
        ["Total conversaciones", N(total_convs)],
        ["Total mensajes", N(total_msgs)],
        ["Mensajes humanos", f"{N(by_type.get('human', 0))} ({pct(by_type.get('human', 0), total_msgs)})"],
        ["Mensajes del bot (AI)", f"{N(by_type.get('ai', 0))} ({pct(by_type.get('ai', 0), total_msgs)})"],
        ["Mensajes de herramientas", f"{N(by_type.get('tool', 0))} ({pct(by_type.get('tool', 0), total_msgs)})"],
        ["Usuarios únicos", N(total_users)],
        ["Promedio mensajes / conversación", f"{avg_msgs:.2f}"],
        ["Mediana mensajes / conversación", f"{median_msgs:.2f}"],
        ["Promedio msgs. humanos / conv.", f"{avg_human:.2f}"],
    ]

    friction_rows = [
        ["Conversaciones abandonadas (≤1 msg humano)", N(abandon_count)],
        ["Tasa de abandono", f"{abandonment:.1f}%"],
        ["Conversaciones activas (≥3 msgs humanos)", N(active_count)],
        ["Tasa de actividad", f"{active_rate:.1f}%"],
    ]

    token_rows = [
        ["Total tokens de entrada", N(inp_tok)],
        ["Total tokens de salida", N(out_tok)],
        ["Tokens de entrada promedio / msg AI", f"{avg_inp:,.0f}"],
        ["Tokens de salida promedio / msg AI", f"{avg_out:,.0f}"],
    ]

    survey_rows = [
        ["Total encuestas respondidas", N(total_surveys)],
        ["Participación en encuestas", f"{survey_part:.1f}% de las conversaciones"],
        ["Respuestas 'Me fue útil'", f"{N(useful_surveys)} ({pct(useful_surveys, total_surveys)})"],
        ["Respuestas 'No me fue útil'", f"{N(notusef_surveys)} ({pct(notusef_surveys, total_surveys)})"],
        ["Índice de utilidad", f"**{utility_index:.1f}%**"],
    ]

    return f"""## 1. KPIs Operacionales

### 1.1 Volumen y Escala

{md_table(vol_rows, ["KPI", "Valor"])}

### 1.2 Fricción y Abandono

{md_table(friction_rows, ["KPI", "Valor"])}

### 1.3 Uso de Tokens (proxy de costo LLM)

{md_table(token_rows, ["Métrica", "Valor"])}

### 1.4 Encuestas de Satisfacción

{md_table(survey_rows, ["Métrica", "Valor"])}"""


def _exec_temporal(data: dict) -> str:
    temporal = data["temporal"]
    hourly = temporal.get("hourly_volume", {})
    dow = temporal.get("day_of_week_volume", {})
    daily = temporal.get("daily_volume", {})

    shifts = hourly_to_shifts(hourly)
    shift_total = sum(shifts.values())
    shift_rows = [[k, N(v), f"{v / shift_total * 100:.1f}%"] for k, v in shifts.items()] if shift_total else []

    top_hours = sorted(hourly.items(), key=lambda x: x[1], reverse=True)[:5]
    top_h_str = ", ".join(f"**{h:02d}:00** ({N(c)} msgs)" for h, c in top_hours)

    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow_es = {
        "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
        "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo",
    }
    dow_total = sum(dow.values())
    dow_rows = []
    for d in dow_order:
        cnt = dow.get(d, 0)
        dow_rows.append([dow_es.get(d, d), N(cnt), f"{cnt / dow_total * 100:.1f}%" if dow_total else "0.0%"])

    peak_day_en = max(dow, key=lambda k: dow.get(k, 0)) if dow else "—"
    peak_day_es = dow_es.get(peak_day_en, peak_day_en)
    wknd_msgs = dow.get("Saturday", 0) + dow.get("Sunday", 0)

    days_sorted = sorted(daily.items())
    if len(days_sorted) <= 10:
        sample = days_sorted
    else:
        sample = days_sorted[:5] + [("...", "...")] + days_sorted[-5:]
    daily_rows = [[d, N(c) if c != "..." else "..."] for d, c in sample]

    return f"""## 2. Análisis Temporal

### 2.1 Actividad por Franja Horaria

Top 5 horas de mayor carga: {top_h_str}

{md_table(shift_rows, ["Franja horaria", "Mensajes", "%"])}

### 2.2 Actividad por Día de la Semana

> El día de mayor actividad es **{peak_day_es}**.
> Los fines de semana representan el **{wknd_msgs / dow_total * 100:.1f}%** del volumen total.

{md_table(dow_rows, ["Día", "Mensajes", "%"])}

### 2.3 Tendencia Diaria (muestra)

{md_table(daily_rows, ["Fecha", "Mensajes"])}"""


def _exec_categorical(data: dict) -> str:
    categorical = data["categorical"]
    top_intents = categorical.get("top_intents", {})
    top_macros = categorical.get("top_macros", {})
    top_products = categorical.get("top_products", {})
    sentiment = categorical.get("sentiment_distribution", {})
    trends = categorical.get("trends", {})

    s_total = sum(sentiment.values())
    sent_rows = [[k, N(v), f"{v / s_total * 100:.1f}%"] for k, v in
                 sorted(sentiment.items(), key=lambda x: x[1], reverse=True)] if s_total else []

    winners = trends.get("winners", [])
    losers = trends.get("losers", [])

    def trend_rows(items):
        return [
            [t["name"], N(t["v1"]), N(t["v2"]), N(t["diff"]), f"{t['pct']:+.1f}%"]
            for t in items
        ]

    winners_table = md_table(trend_rows(winners), ["Categoría", "1ª mitad", "2ª mitad", "Δ", "% Cambio"])
    losers_table = md_table(trend_rows(losers), ["Categoría", "1ª mitad", "2ª mitad", "Δ", "% Cambio"])

    return f"""## 3. Distribución de Categorías

### 3.1 Top Macrocategorías

{dict_to_table(top_macros, "Macrocategoría", "Mensajes humanos")}

### 3.2 Top 15 Subcategorías

{dict_to_table(top_intents, "Subcategoría", "Mensajes humanos", top_n=15)}

### 3.3 Top Productos Mencionados

{dict_to_table(top_products, "Producto", "Mensajes", top_n=10)}

### 3.4 Distribución de Sentimiento

{md_table(sent_rows, ["Sentimiento", "Mensajes", "%"])}

### 3.5 Tendencias (primera vs. segunda mitad del período)

#### Categorías en crecimiento

{winners_table}

#### Categorías en descenso

{losers_table}"""


def _exec_quality(data: dict) -> str:
    failures_df = data["failures_df"]
    gaps_data = data["gaps_data"]
    fk = data["funnel_kpis"]

    # --- 4.1 Failures ---
    if failures_df is not None and not failures_df.empty:
        total_failures = len(failures_df)
        criteria_counts = split_criteria_counts(failures_df)
        crit_rows = [[k, N(v)] for k, v in
                     sorted(criteria_counts.items(), key=lambda x: x[1], reverse=True)]
        crit_table = md_table(crit_rows, ["Criterio de fallo", "Conversaciones"])

        top_fail = failures_df.sort_values('fecha', ascending=False).head(10)
        fail_detail_rows = [
            [r.get('intencion', '—'), r.get('product_type', '—'),
             str(r.get('fecha', '—'))[:10], r.get('criteria', '—')]
            for r in top_fail.to_dict('records')
        ]
        fail_detail_table = md_table(fail_detail_rows,
                                     ["Categoría", "Producto", "Fecha", "Criterio"])
    else:
        total_failures = 0
        crit_table = "_Sin datos de fallos._\n"
        fail_detail_table = "_Sin datos._\n"

    # --- 4.2 Knowledge gaps ---
    top_themes = gaps_data.get("top_themes", [])[:10]
    if top_themes:
        theme_rows = [
            [t.get("macro", "—"), t.get("category", "—"), N(t.get("count", 0)),
             t.get("examples", [""])[0][:80]]
            for t in top_themes
        ]
        themes_table = md_table(theme_rows,
                                ["Macro", "Subcategoría", "Ocurrencias", "Ejemplo de consulta"])
    else:
        themes_table = "_No se detectaron brechas significativas._\n"

    total_gaps = len(gaps_data.get("gaps", []))
    total_convs_for_ref = gaps_data.get("referrals", {}).get("total_conversations", 0)

    # --- 4.3 Referrals ---
    ref_data = gaps_data.get("referrals", {})
    ref_dist = ref_data.get("distribution", [])
    total_refs = ref_data.get("total_referrals", 0)
    total_convs_ref = ref_data.get("total_conversations", 0)
    ref_rows = [
        [r.get("channel", "—"), N(r.get("count", 0)),
         f"{r.get('percentage', 0):.1f}%"]
        for r in sorted(ref_dist, key=lambda x: x.get("count", 0), reverse=True)
    ]
    ref_table = md_table(ref_rows, ["Canal", "Conversaciones derivadas", "% del total"])

    # --- 4.4 Value waste ---
    waste_count = fk.get("value_waste_count", 0)
    waste_pct = fk.get("value_waste_pct", 0)

    return f"""## 4. Calidad y Fricción del Bot

### 4.1 Fallos Detectados

> **{N(total_failures)} conversaciones** presentaron indicios de fallo.

#### Distribución por criterio

{crit_table}

#### Top 10 conversaciones fallidas (recientes)

{fail_detail_table}

### 4.2 Brechas de Conocimiento

> El bot respondió con frases de desconocimiento en **{N(total_gaps)} instancias**.
> Los temas más frecuentes sin cobertura son:

{themes_table}

### 4.3 Derivaciones a Canales Externos

> **{N(total_refs)} conversaciones** ({pct(total_refs, total_convs_ref)}) fueron derivadas a canales externos.

{ref_table}

### 4.4 Gasto de Valor

> Conversaciones "no útiles" que **además** fueron derivadas = esfuerzo doble sin resolución.

| Métrica | Valor |
|---|---|
| Conversaciones con gasto de valor | {N(waste_count)} |
| % del total de conversaciones | {waste_pct:.1f}% |
"""


def _exec_survey_utility(data: dict) -> str:
    survey_util = data["survey_util"]
    if not survey_util:
        return "## 5. Utilidad por Categoría (Encuestas)\n\n_No hay datos de encuestas disponibles._\n"

    rows = []
    low_perf = []
    high_perf = []

    for r in survey_util[:15]:
        util_rate = r.get("utility_rate", 0)
        total = r.get("total", 0)
        useful = r.get("useful", 0)
        not_u = r.get("not_useful", 0)
        macro = r.get("macro", "—")
        cat = r.get("categoria", "—")
        prod = r.get("producto", "—")

        rows.append([macro, cat, prod, N(useful), N(not_u), N(total), f"{util_rate:.1f}%"])

        if util_rate < 40 and total >= 5:
            low_perf.append((cat, total, util_rate, not_u))
        if util_rate > 75 and total >= 5:
            high_perf.append((cat, total, util_rate, useful))

    table = md_table(rows, ["Macro", "Categoría", "Producto", "Útil", "No útil", "Total", "% Utilidad"])

    low_section = ""
    if low_perf:
        low_section = "\n#### Áreas de bajo rendimiento (<40% utilidad)\n\n"
        for cat, total, util_rate, not_u in sorted(low_perf, key=lambda x: x[2])[:3]:
            low_section += f"- **{cat}**: {not_u} respuestas negativas ({util_rate:.1f}% utilidad de {total} encuestas)\n"

    high_section = ""
    if high_perf:
        high_section = "\n#### Casos de éxito (>75% utilidad)\n\n"
        for cat, total, util_rate, useful in sorted(high_perf, key=lambda x: x[2], reverse=True)[:3]:
            high_section += f"- **{cat}**: {useful} respuestas positivas ({util_rate:.1f}% utilidad de {total} encuestas)\n"

    return f"""## 5. Utilidad por Categoría (Encuestas)

{table}
{low_section}{high_section}"""


def _exec_volume(data: dict) -> str:
    volume_rpt = data["volume_rpt"]
    if not volume_rpt:
        return "## 6. Reporte de Volumen Detallado\n\n_Sin datos._\n"

    top = volume_rpt[:30]
    rows = [
        [r.get("macro_yaml", "—"), r.get("categoria_yaml", "—"),
         r.get("product_yaml", "—"), N(r.get("count", 0)),
         f"{r.get('percentage', 0):.2f}%"]
        for r in top
    ]
    note = ""
    if len(volume_rpt) > 30:
        note = f"\n> _Mostrando las 30 filas de mayor volumen de {N(len(volume_rpt))} combinaciones totales._\n"

    return f"""## 6. Reporte de Volumen Detallado

> Solo se cuentan mensajes humanos. Ordenado de mayor a menor volumen.
{note}
{md_table(rows, ["Macro", "Categoría", "Producto", "Mensajes", "%"])}"""


def _exec_appendix(data: dict) -> str:
    kpis = data["kpis"]
    df = data["df"]

    total_human = kpis.get("messages_by_type", {}).get("human", 0)

    requires_rev = 0
    uncategorized_convs = 0
    if df is not None and not df.empty:
        hdf = df[df['type'] == 'human']
        if 'requires_review' in df.columns:
            requires_rev = int(hdf['requires_review'].sum())
        if 'macro_yaml' in df.columns:
            uncategorized_convs = int(
                df[df['macro_yaml'].isin(['Sin Clasificar', None])]['thread_id'].nunique()
            )

    categorized_human = total_human - requires_rev
    cov_pct = f"{categorized_human / total_human * 100:.1f}%" if total_human else "—"

    cov_rows = [
        ["Total mensajes humanos", N(total_human)],
        ["Mensajes categorizados (YAML)", f"{N(categorized_human)} ({cov_pct})"],
        ["Mensajes pendientes de revisión", N(requires_rev)],
        ["Conversaciones 'Sin Clasificar'", N(uncategorized_convs)],
    ]

    glosario = """
| Término | Definición |
|---|---|
| Conversación | Hilo único identificado por `thread_id` |
| Tasa de abandono | % de conversaciones con ≤1 mensaje humano |
| Derivación | El bot sugiere llamar o acudir a canal externo |
| Brecha de conocimiento | El bot responde con frase de desconocimiento |
| Gasto de valor | Conversación "no útil" que además fue derivada |
| Índice de utilidad | % encuestas marcadas como "Me fue útil" |
"""

    return f"""## Apéndice

### A. Cobertura de Categorización

{md_table(cov_rows, ["Métrica", "Valor"])}

### B. Glosario
{glosario}"""


def _exec_footer(data: dict) -> str:
    generated_at = data["generated_at"]
    return (f"\n---\n"
            f"*Generado automáticamente por `generate_report.py` · "
            f"{generated_at.strftime('%Y-%m-%d %H:%M:%S')}*\n")


# ═══════════════════════════════════════════════════════════════════════════
# DEEP REPORT — Section builders
# ═══════════════════════════════════════════════════════════════════════════

def _deep_header(data: dict) -> str:
    period = data["period"]
    generated_at = data["generated_at"]
    return f"""# Informe de Análisis Profundo — Plan de Acción

**Período:** {period.get("start", "N/A")} — {period.get("end", "N/A")}
**Generado:** {generated_at.strftime('%Y-%m-%d %H:%M:%S')}
**Base:** {N(data["total_msgs"])} mensajes · {N(data["total_convs"])} conversaciones

> Este informe está orientado a **decisión y acción**: entiende qué pasa en cada categoría,
> dónde falla el bot, qué no sabe responder y qué temas deben priorizarse para mejora.

---"""


def _deep_kpis_explained(data: dict) -> str:
    kpis = data["kpis"]
    funnel = data["funnel"]
    survey_stats = data["survey_stats"]

    fk = funnel.get("kpis", {})
    funnel_steps = funnel.get("funnel", [])
    waste_by_cat = funnel.get("waste_by_category", [])

    total_convs = kpis.get("total_conversations", 0)
    abandonment = kpis.get("abandonment_rate", 0)
    avg_msgs = kpis.get("avg_messages_per_thread", 0)
    avg_human = kpis.get("avg_human_messages_per_thread", 0)

    self_service = fk.get("self_service_rate", 0)
    referral_rate = fk.get("referral_rate", 0)
    active_rate = fk.get("active_rate", 0)
    survey_part = fk.get("survey_participation", 0)
    utility = fk.get("utility_index", 0)
    waste_count = fk.get("value_waste_count", 0)
    waste_pct = fk.get("value_waste_pct", 0)

    stats = survey_stats.get("stats", {})
    total_surveys = stats.get("total", 0)
    useful_s = stats.get("useful", 0)
    notusef_s = stats.get("not_useful", 0)

    abandon_count = int(total_convs * abandonment / 100) if total_convs else 0
    active_count = int(total_convs * active_rate / 100) if total_convs else 0
    self_srv_n = int(total_convs * self_service / 100) if total_convs else 0
    ref_n = int(total_convs * referral_rate / 100) if total_convs else 0

    funnel_rows = [[s["step"], N(s["count"]), f"{s['pct']:.1f}%"] for s in funnel_steps]

    waste_rows = [
        [r["category"], N(r["count"]), f"{r['pct_of_waste']:.1f}%"]
        for r in waste_by_cat[:10]
    ]

    return f"""## 1. KPIs Clave — Cómo se Calculan y Qué Significan

### 1.1 Tasa de Abandono

> **Definición:** % de conversaciones con **≤ 1 mensaje humano** (el usuario abrió el chat pero no interactuó de forma real).

| | Valor |
|---|---|
| Conversaciones totales | {N(total_convs)} |
| Conversaciones abandonadas (≤1 msg humano) | **{N(abandon_count)} ({abandonment:.1f}%)** |
| Conversaciones activas (≥3 msgs humanos) | {N(active_count)} ({active_rate:.1f}%) |
| Promedio mensajes / conversación | {avg_msgs:.2f} |
| Promedio mensajes humanos / conversación | {avg_human:.2f} |

**Interpretación:** Un abandono del {abandonment:.1f}% puede indicar que el saludo inicial del bot no genera confianza, el tiempo de respuesta es percibido como lento, o el usuario llegó por error al canal.

---

### 1.2 Auto-servicio vs. Derivación

> **Auto-servicio:** conversaciones donde el bot **nunca** mencionó palabras de derivación (servilínea, oficina, app, etc.).
> **Derivación:** conversaciones donde el bot redirigió al usuario a otro canal en al menos un mensaje.

| | Conversaciones | % |
|---|---:|---:|
| Auto-servicio (resolución autónoma) | {N(self_srv_n)} | **{self_service:.1f}%** |
| Derivadas a canales externos | {N(ref_n)} | **{referral_rate:.1f}%** |
| Total | {N(total_convs)} | 100% |

**Interpretación:** Un {referral_rate:.1f}% de derivación indica que el bot no pudo resolver esos casos. Reducirlo es un objetivo directo de mejora del conocimiento o los flujos.

---

### 1.3 Índice de Utilidad (Encuestas)

> **Definición:** % de encuestas respondidas marcadas como **"Me fue útil"** del total de encuestas con respuesta clasificable.

| | Valor |
|---|---|
| Conversaciones con encuesta respondida | {N(total_surveys)} ({survey_part:.1f}% del total) |
| "Me fue útil" | {N(useful_s)} ({pct(useful_s, total_surveys)}) |
| "No me fue útil" | {N(notusef_s)} ({pct(notusef_s, total_surveys)}) |
| **Índice de utilidad** | **{utility:.1f}%** |

**Interpretación:** El {utility:.1f}% de utilidad mide satisfacción declarada. El sesgo de participación ({survey_part:.1f}% responde) puede subestimar insatisfacción real — quienes tuvieron mala experiencia a veces no responden.

---

### 1.4 Gasto de Valor (Value Waste)

> **Definición:** Conversaciones que recibieron una calificación **"No me fue útil"** Y además fueron **derivadas** a un canal externo.
> Son el caso más grave: el bot no resolvió nada y encima redirigió al usuario.

| | Valor |
|---|---|
| Conversaciones con gasto de valor | **{N(waste_count)} ({waste_pct:.1f}%)** |

#### Categorías con mayor gasto de valor

{md_table(waste_rows, ["Categoría", "Conversaciones", "% del gasto"])}

---

### 1.5 Embudo Completo de Conversaciones

{md_table(funnel_rows, ["Etapa", "Conversaciones", "%"])}

> **Nota de lectura:** El % de "Útiles" está calculado sobre encuestadas, no sobre el total de conversaciones.

---"""


def _deep_friction(data: dict) -> str:
    kpis = data["kpis"]
    failures_df = data["failures_df"]

    total_convs = kpis.get("total_conversations", 0)
    abandonment = kpis.get("abandonment_rate", 0)
    abandon_count = int(total_convs * abandonment / 100) if total_convs else 0

    if failures_df is not None and not failures_df.empty:
        n_failures = len(failures_df)
        criteria_counts = split_criteria_counts(failures_df)
        crit_rows = [
            [k, N(v), pct(v, n_failures)]
            for k, v in sorted(criteria_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        top_fail = failures_df.sort_values('fecha', ascending=False).head(20)
        fail_rows = [
            [
                str(r.get('fecha', '—'))[:10],
                trunc(r.get('intencion', '—'), 30),
                trunc(r.get('last_user_message', '—'), 80),
                str(r.get('thread_id', '—')),
                r.get('criteria', '—'),
            ]
            for r in top_fail.to_dict('records')
        ]
        fail_table = md_table(fail_rows, ["Fecha", "Categoría", "Última pregunta del usuario", "thread_id", "Criterio"])
    else:
        n_failures = 0
        crit_rows = []
        fail_table = "_Sin datos de fallos._\n"

    crit_table = md_table(crit_rows, ["Criterio", "Conversaciones", "%"]) if crit_rows else "_Sin datos._\n"

    return f"""## 2. Fricción y Abandono

### 2.1 Conversaciones con Fallos Detectados

> El sistema detecta fallos usando tres criterios (pueden combinarse en una misma conversación):
> - **Incapacidad del bot:** el bot usó frases como "no puedo", "no tengo información", "error", etc.
> - **Repetición del usuario:** el usuario envió el mismo mensaje más de una vez (señal de frustración).
> - **Sentimiento negativo predominante:** >50% de los mensajes del hilo tienen sentimiento negativo.

Total de conversaciones con algún criterio de fallo: **{N(n_failures)} ({pct(n_failures, total_convs)})**

#### Distribución por criterio

{crit_table}

#### Top 20 conversaciones fallidas más recientes

{fail_table}

### 2.2 Abandono Temprano

> **{N(abandon_count)}** conversaciones ({abandonment:.1f}%) terminaron con ≤1 mensaje humano.
> Estas conversaciones **no se clasifican** en ninguna categoría de intención porque no hubo interacción real.

**Posibles causas a investigar:**
- El mensaje de bienvenida del bot no es lo suficientemente invitador o claro.
- El usuario llegó al canal por accidente.
- El tiempo de carga o respuesta inicial fue percibido como lento.
- El usuario encontró la respuesta antes de escribir (FAQ visible en interfaz).

---"""


def _deep_surveys(data: dict) -> str:
    survey_stats = data["survey_stats"]
    survey_util = data["survey_util"]
    funnel = data["funnel"]

    fk = funnel.get("kpis", {})
    utility = fk.get("utility_index", 0)
    survey_part = fk.get("survey_participation", 0)
    stats = survey_stats.get("stats", {})
    total = stats.get("total", 0)
    useful = stats.get("useful", 0)
    not_useful = stats.get("not_useful", 0)

    if survey_util:
        bottom = sorted(
            [r for r in survey_util if r.get("total", 0) >= 5],
            key=lambda x: x.get("utility_rate", 100)
        )[:10]
        top_perf = sorted(
            [r for r in survey_util if r.get("total", 0) >= 5],
            key=lambda x: x.get("utility_rate", 0),
            reverse=True
        )[:10]

        bottom_rows = [
            [r.get("macro", "—"), r.get("categoria", "—"), r.get("producto", "—"),
             N(r.get("useful", 0)), N(r.get("not_useful", 0)), N(r.get("total", 0)),
             f"**{r.get('utility_rate', 0):.1f}%**"]
            for r in bottom
        ]
        top_rows = [
            [r.get("macro", "—"), r.get("categoria", "—"), r.get("producto", "—"),
             N(r.get("useful", 0)), N(r.get("not_useful", 0)), N(r.get("total", 0)),
             f"**{r.get('utility_rate', 0):.1f}%**"]
            for r in top_perf
        ]
    else:
        bottom_rows = []
        top_rows = []

    headers_util = ["Macro", "Categoría", "Producto", "Útil", "No útil", "Total", "% Utilidad"]

    return f"""## 3. Encuestas de Satisfacción

| Métrica | Valor |
|---|---|
| Conversaciones con encuesta | {N(total)} ({survey_part:.1f}% del total) |
| "Me fue útil" | {N(useful)} ({pct(useful, total)}) |
| "No me fue útil" | {N(not_useful)} ({pct(not_useful, total)}) |
| Índice de utilidad | **{utility:.1f}%** |

> **Limitación:** Solo el {survey_part:.1f}% de las conversaciones tienen respuesta de encuesta.
> El restante {100 - survey_part:.1f}% no respondió — la satisfacción real puede diferir.

### 3.1 Categorías con Peor Calificación (acción prioritaria)

> Ordenadas de menor a mayor índice de utilidad. Solo se muestran categorías con ≥5 encuestas.

{md_table(bottom_rows, headers_util)}

### 3.2 Categorías con Mejor Calificación (casos de éxito a replicar)

{md_table(top_rows, headers_util)}

---"""


def _deep_categories(data: dict) -> str:
    df = data["df"]
    faqs = data["faqs"]

    if df is None or df.empty:
        return "## 4. Distribución de Categorías\n\n_Sin datos._\n"

    hdf = df[df['type'] == 'human'].copy()
    hdf = hdf[hdf['macro_yaml'].notna() & ~hdf['macro_yaml'].isin(['Sin Clasificar'])]

    if hdf.empty:
        return "## 4. Distribución de Categorías\n\n_Sin datos._\n"

    cat_convs = (
        hdf.groupby(['macro_yaml', 'categoria_yaml'])['thread_id']
        .nunique()
        .reset_index(name='conversaciones')
        .sort_values(['macro_yaml', 'conversaciones'], ascending=[True, False])
    )

    total_h_convs = hdf['thread_id'].nunique()

    cat_prod = (
        hdf.groupby(['macro_yaml', 'categoria_yaml', 'product_yaml'])['thread_id']
        .nunique()
        .reset_index(name='conversaciones')
        .sort_values(['macro_yaml', 'categoria_yaml', 'conversaciones'], ascending=[True, True, False])
    )

    sections = []
    macros_sorted = cat_convs.groupby('macro_yaml')['conversaciones'].sum().sort_values(ascending=False).index

    SKIP_MACROS = {'Encuestas', 'Sin Clasificar'}
    BRIEF_MACROS = {'Experiencia', 'Otros'}

    for macro in macros_sorted:
        if macro in SKIP_MACROS:
            continue

        macro_sub = cat_convs[cat_convs['macro_yaml'] == macro]
        macro_total = int(macro_sub['conversaciones'].sum())
        macro_pct = pct(macro_total, total_h_convs)

        sub_rows = [
            [r['categoria_yaml'], N(r['conversaciones']), pct(r['conversaciones'], macro_total)]
            for _, r in macro_sub.iterrows()
        ]
        sub_table = md_table(sub_rows, ["Subcategoría", "Conversaciones", "% dentro del macro"])

        if macro in BRIEF_MACROS:
            sections.append(f"### {macro} — {N(macro_total)} conversaciones ({macro_pct})\n\n{sub_table}")
            continue

        prod_sub = cat_prod[cat_prod['macro_yaml'] == macro]
        prod_rows = [
            [r['categoria_yaml'], r['product_yaml'], N(r['conversaciones'])]
            for _, r in prod_sub.iterrows()
        ]
        prod_table = md_table(prod_rows, ["Subcategoría", "Producto", "Conversaciones"])

        faq_block = ""
        macro_faqs = faqs.get(macro, {})
        for sub_name, phrases in macro_faqs.items():
            if not phrases:
                continue
            faq_block += f"\n**{sub_name}** — preguntas más frecuentes:\n\n"
            for p in phrases[:5]:
                faq_block += f"> *\"{trunc(p['phrase'], 120)}\"* ({p['count']}x)\n\n"

        sections.append(
            f"### {macro} — {N(macro_total)} conversaciones ({macro_pct})\n\n"
            f"#### Subcategorías\n\n{sub_table}\n"
            f"#### Por subcategoría y producto\n\n{prod_table}\n"
            f"#### Ejemplos de preguntas de usuarios\n{faq_block}"
        )

    content = "\n---\n\n".join(sections)

    return f"""## 4. Distribución de Categorías — Qué Sucede en Cada Una

> Para cada macro-categoría se detalla: volumen, desglose por subcategoría y producto,
> y ejemplos reales de lo que escriben los usuarios.
> Categorías como Encuestas, Saludos y Retroalimentación se mencionan al final sin detallar.

{content}

---"""


def _deep_failures(data: dict) -> str:
    failures_df = data["failures_df"]
    df = data["df"]

    if failures_df is None or failures_df.empty:
        return "## 5. Conversaciones Fallidas — Qué Preguntó el Usuario\n\n_Sin datos de fallos._\n"

    total_failures = len(failures_df)

    by_cat = (
        failures_df.groupby(['intencion', 'criteria'])
        .agg(
            conversaciones=('thread_id', 'count'),
            preguntas=('last_user_message', lambda x: list(x.dropna().unique()[:3]))
        )
        .reset_index()
        .sort_values('conversaciones', ascending=False)
    )

    sections_html = []
    for _, row in by_cat.head(25).iterrows():
        cat = row['intencion'] or 'Sin categoría'
        crit = row['criteria']
        n = row['conversaciones']
        pregs = row['preguntas']
        examples = "\n".join(f"> *\"{trunc(p, 120)}\"*" for p in pregs if p and p != "N/A")
        sections_html.append(
            f"**{cat}** ({N(n)} conversaciones) — *{crit}*\n\n{examples}\n"
        )

    content = "\n".join(sections_html)

    if df is not None and not df.empty:
        failed_ids = set(failures_df['thread_id'].tolist())
        failed_human = df[
            (df['thread_id'].isin(failed_ids)) & (df['type'] == 'human')
        ]
        if not failed_human.empty:
            top_msgs = (
                failed_human['text']
                .value_counts()
                .head(20)
                .reset_index()
            )
            top_msgs.columns = ['Pregunta del usuario', 'Frecuencia']
            top_msg_rows = [
                [trunc(r['Pregunta del usuario'], 120), N(r['Frecuencia'])]
                for _, r in top_msgs.iterrows()
                if str(r['Pregunta del usuario']).strip()
            ]
            top_msg_table = md_table(top_msg_rows, ["Pregunta del usuario (en conversaciones fallidas)", "Frecuencia"])
        else:
            top_msg_table = "_Sin datos._\n"
    else:
        top_msg_table = "_Sin datos._\n"

    return f"""## 5. Conversaciones Fallidas — Qué Preguntó el Usuario y Por Qué Falló el Bot

> Total de conversaciones con algún criterio de fallo: **{N(total_failures)}**
> A continuación se desglosa por categoría: qué preguntó el usuario y cuál fue el criterio de fallo.

### 5.1 Fallos por Categoría con Ejemplos de Preguntas

{content}

### 5.2 Top 20 Preguntas Más Frecuentes en Conversaciones Fallidas

> Estas son las frases exactas que escribieron los usuarios en conversaciones donde el bot falló.
> Son una guía directa de qué mejorar en el conocimiento del bot.

{top_msg_table}

---"""


def _deep_gaps(data: dict) -> str:
    gaps_data = data["gaps_data"]
    gaps = gaps_data.get("gaps", [])
    top_themes = gaps_data.get("top_themes", [])

    total_gaps = len(gaps)
    total_occurrences = sum(g.get("count", 0) for g in gaps)

    theme_rows = [
        [t.get("macro", "—"), t.get("category", "—"), N(t.get("count", 0)),
         "; ".join(trunc(e, 60) for e in t.get("examples", [])[:2])]
        for t in top_themes
    ]
    themes_table = md_table(theme_rows, ["Macro", "Categoría", "Ocurrencias", "Ejemplos"])

    top_gaps = sorted(gaps, key=lambda x: x.get("count", 0), reverse=True)[:30]
    gap_rows = [
        [
            g.get("macro", "—"),
            g.get("category", "—"),
            trunc(g.get("user_request", "—"), 100),
            N(g.get("count", 0)),
            str(g.get("thread_ids", [""])[0]) if g.get("thread_ids") else "—",
        ]
        for g in top_gaps
    ]
    gaps_table = md_table(gap_rows, ["Macro", "Categoría", "Consulta del usuario", "Ocurrencias", "thread_id ejemplo"])

    return f"""## 6. Mapa de Brechas de Conocimiento — Quick Wins

> **Brecha de conocimiento:** el bot respondió con una frase de desconocimiento
> ("no tengo información", "no puedo ayudarte con eso", etc.) ante una pregunta real del usuario.
>
> Estas son las **oportunidades de mejora más rápidas**: si el equipo entrena al bot en estas consultas,
> el impacto es inmediato y medible.

**Total de instancias detectadas:** {N(total_occurrences)} ocurrencias en {N(total_gaps)} patrones únicos de consulta.

### 6.1 Temas con Mayor Cantidad de Brechas (Top 10)

{themes_table}

### 6.2 Consultas Sin Respuesta — Top 30 por Frecuencia

> Cada fila es una consulta específica del usuario que el bot no supo responder.
> El `thread_id` permite revisar la conversación completa en el Explorador de Mensajes.
> **Acción sugerida:** ordenar por "Ocurrencias" y atacar de arriba hacia abajo.

{gaps_table}

---"""


def _deep_referrals(data: dict) -> str:
    referrals_df = data["referrals_df"]
    gaps_data = data["gaps_data"]

    ref_dist = gaps_data.get("referrals", {})
    distribution = ref_dist.get("distribution", [])
    total_refs = ref_dist.get("total_referrals", 0)
    total_convs = ref_dist.get("total_conversations", 0)

    dist_rows = [
        [r.get("channel", "—"), N(r.get("count", 0)), f"{r.get('percentage', 0):.1f}%"]
        for r in sorted(distribution, key=lambda x: x.get("count", 0), reverse=True)
    ]
    dist_table = md_table(dist_rows, ["Canal", "Conversaciones derivadas", "% del total"])

    channel_sections = ""
    if referrals_df is not None and not referrals_df.empty and 'channel' in referrals_df.columns:
        channel_map = {
            "serviline": "Telefónico (Servilínea)",
            "digital": "Digital (App/Web)",
            "office": "Físico (Oficinas)",
            "other": "Otros",
        }
        for ch_key, ch_label in channel_map.items():
            ch_df = referrals_df[referrals_df['channel'] == ch_key]
            if ch_df.empty:
                continue
            top_intents = ch_df['intencion'].value_counts().head(10)
            if top_intents.empty:
                continue
            rows = [[cat, N(cnt)] for cat, cnt in top_intents.items()]
            t = md_table(rows, ["Categoría / Intención", "Derivaciones"])
            channel_sections += f"\n#### {ch_label} ({N(len(ch_df))} derivaciones)\n\n{t}\n"

        top_responses = referrals_df['referral_response'].value_counts().head(10)
        resp_rows = [[trunc(txt, 120), N(cnt)] for txt, cnt in top_responses.items()]
        resp_table = md_table(resp_rows, ["Mensaje del bot al derivar", "Frecuencia"])
    else:
        channel_sections = "_No se pudo desglosar por canal desde los datos pre-computados._\n"
        resp_table = "_Sin datos._\n"

    return f"""## 7. Derivaciones a Canales Externos — Panorama por Canal y Tema

> Una derivación ocurre cuando el mensaje del bot menciona palabras clave que redirigen al usuario
> a otro canal: servilínea (telefónico), app/portal (digital) u oficina (físico).

**Total de conversaciones derivadas:** {N(total_refs)} ({pct(total_refs, total_convs)} del total)

### 7.1 Distribución por Canal

{dist_table}

### 7.2 Temas que Más se Derivan por Canal

> ¿Qué intenciones o categorías generan más derivaciones en cada canal?
> Esto permite identificar flujos que deben mejorar para reducir fricción.

{channel_sections}

### 7.3 Mensajes Más Comunes del Bot al Derivar

{resp_table}

---"""


def _deep_faqs_action(data: dict) -> str:
    faqs = data["faqs"]
    SKIP_MACROS = {'Sin Clasificar', 'Encuestas', 'Experiencia'}

    sections = []
    for macro, subcats in sorted(faqs.items()):
        if macro in SKIP_MACROS:
            continue
        macro_block = f"### {macro}\n\n"
        for sub, phrases in subcats.items():
            if not phrases:
                continue
            phrase_rows = [
                [trunc(p['phrase'], 120), N(p['count'])]
                for p in phrases
            ]
            macro_block += f"**{sub}**\n\n"
            macro_block += md_table(phrase_rows, ["Pregunta del usuario", "Frecuencia"])
            macro_block += "\n"
        sections.append(macro_block)

    content = "\n---\n\n".join(sections) if sections else "_Sin datos de FAQs._\n"

    return f"""## 8. Preguntas Más Frecuentes por Categoría — Base para Plan de Acción

> Estas son las frases **exactas** que más repiten los usuarios en cada subcategoría.
> Sirven como insumo directo para:
> - Mejorar las respuestas del bot en esos temas.
> - Identificar intenciones frecuentes que podrían merecer flujos dedicados.
> - Detectar variaciones de escritura que el bot debe reconocer.

{content}

---"""


def _deep_brief_cats(data: dict) -> str:
    df = data["df"]

    if df is None or df.empty:
        return ""

    hdf = df[df['type'] == 'human']
    brief = {}
    for macro in ['Encuestas', 'Sin Clasificar', 'Experiencia']:
        sub = hdf[hdf['macro_yaml'] == macro]
        if sub.empty:
            continue
        brief[macro] = {
            "conversaciones": int(sub['thread_id'].nunique()),
            "mensajes": len(sub),
        }

    if not brief:
        return ""

    rows = [[macro, N(v["conversaciones"]), N(v["mensajes"])] for macro, v in brief.items()]
    table = md_table(rows, ["Macro", "Conversaciones", "Mensajes"])

    return f"""## 9. Categorías sin Análisis Detallado

Las siguientes macrocategorías existen en los datos pero tienen menor valor de análisis accionable:

{table}

- **Encuestas:** mensajes con tag `[survey]`. Son retroalimentación del usuario, ya analizada en la sección 3.
- **Sin Clasificar:** conversaciones donde el NLP no encontró categoría. Se trabajan en el panel de revisión HITL.
- **Experiencia:** evaluaciones generales, usabilidad, recomendaciones. Útil para producto pero sin acción inmediata de bot.

---"""


def _deep_footer(data: dict) -> str:
    generated_at = data["generated_at"]
    return (
        f"\n---\n"
        f"*Generado automáticamente por `generate_deep_report.py` · "
        f"{generated_at.strftime('%Y-%m-%d %H:%M:%S')}*\n"
    )


# ═══════════════════════════════════════════════════════════════════════════
# Public assembly functions
# ═══════════════════════════════════════════════════════════════════════════

def build_executive_report(data: dict) -> str:
    """Full 9-section executive report."""
    sections = [
        _exec_header(data),
        _exec_summary(data),
        _exec_kpis(data),
        _exec_temporal(data),
        _exec_categorical(data),
        _exec_quality(data),
        _exec_survey_utility(data),
        _exec_volume(data),
        _exec_appendix(data),
        _exec_footer(data),
    ]
    return "\n\n".join(sections)


def build_deep_report(data: dict) -> str:
    """Full 9-section deep analysis report."""
    sections = [
        _deep_header(data),
        _deep_kpis_explained(data),
        _deep_friction(data),
        _deep_surveys(data),
        _deep_categories(data),
        _deep_failures(data),
        _deep_gaps(data),
        _deep_referrals(data),
        _deep_faqs_action(data),
        _deep_brief_cats(data),
        _deep_footer(data),
    ]
    return "\n\n".join(sections)


def build_executive_report_brief(data: dict) -> str:
    """10-section report (API default) with detailed categories, products, and failures."""
    kpis = data["kpis"]
    fk = data["funnel_kpis"]
    categorical = data["categorical"]
    temporal = data["temporal"]
    survey_stats = data["survey_stats"]
    survey_util = data["survey_util"]
    volume_rpt = data["volume_rpt"]
    failures_df = data["failures_df"]
    period = data["period"]
    generated_at = data["generated_at"]
    kpis_detailed = data["kpis_detailed"]
    categories_detailed = data["categories_detailed"]
    products_detailed = data["products_detailed"]
    failures_detailed = data["failures_detailed"]

    by_type = kpis.get("messages_by_type", {})
    total_convs = kpis.get("total_conversations", 0)
    total_msgs = kpis.get("total_messages", 0)
    abandon_rate = kpis.get("abandonment_rate", 0)
    abandon_n = int(total_convs * abandon_rate / 100) if total_convs else 0
    s_stats = survey_stats.get("stats", {})
    total_surveys = s_stats.get("total", 0)
    useful_s = s_stats.get("useful", 0)
    not_useful_s = s_stats.get("not_useful", 0)
    waste_count = fk.get("value_waste_count", 0)
    waste_pct = fk.get("value_waste_pct", 0)
    self_svc = fk.get("self_service_rate", 0)
    ref_rate = fk.get("referral_rate", 0)
    utility = fk.get("utility_index", 0)
    fail_n = failures_detailed.get("total", 0)

    # Top macros
    top_macros = categorical.get("top_macros", {})
    macro_rows = sorted(top_macros.items(), key=lambda x: x[1], reverse=True)[:10]
    m_total = sum(top_macros.values())
    macro_table = md_table(
        [[k, N(v), f"{v / m_total * 100:.1f}%"] for k, v in macro_rows],
        ["Macrocategoría", "Mensajes", "%"],
    ) if m_total else "_Sin datos._\n"

    # Top intents
    top_intents = categorical.get("top_intents", {})
    intent_rows = sorted(top_intents.items(), key=lambda x: x[1], reverse=True)[:15]
    i_total = sum(top_intents.values())
    intent_table = md_table(
        [[k, N(v), f"{v / i_total * 100:.1f}%"] for k, v in intent_rows],
        ["Subcategoría", "Mensajes", "%"],
    ) if i_total else "_Sin datos._\n"

    # Top products
    top_products = categorical.get("top_products", {})
    prod_rows_simple = sorted(top_products.items(), key=lambda x: x[1], reverse=True)[:15]
    p_total = sum(top_products.values()) or 1
    products_summary_table = md_table(
        [[k, N(v), f"{v / p_total * 100:.1f}%"] for k, v in prod_rows_simple],
        ["Producto", "Mensajes", "%"],
    )

    # Temporal: top hours & days
    hourly = temporal.get("hourly_volume", {})
    top_hours = sorted(hourly.items(), key=lambda x: x[1], reverse=True)[:5]
    hours_table = md_table(
        [[f"{int(h):02d}:00–{int(h):02d}:59", N(v)] for h, v in top_hours],
        ["Franja horaria", "Mensajes"],
    )

    dow = temporal.get("day_of_week_volume", {})
    dow_order = {
        "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
        "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado",
        "Sunday": "Domingo",
    }
    dow_rows_sorted = sorted(dow.items(), key=lambda x: x[1], reverse=True)
    dow_table = md_table(
        [[dow_order.get(d, d), N(v)] for d, v in dow_rows_sorted],
        ["Día", "Mensajes"],
    )

    # Sentiment
    sentiments = categorical.get("sentiment_distribution", {})
    sent_total = sum(sentiments.values()) or 1
    sent_table = md_table(
        [[s.capitalize(), N(v), f"{v / sent_total * 100:.1f}%"]
         for s, v in sorted(sentiments.items(), key=lambda x: x[1], reverse=True)],
        ["Sentimiento", "Mensajes", "%"],
    )

    # Trends
    trends = categorical.get("trends", {})
    winners = trends.get("winners", [])[:5]
    losers = trends.get("losers", [])[:5]
    trends_section = ""
    if winners or losers:
        trends_section = "\n### Tendencias de Categorías\n\n"
        if winners:
            trends_section += "**Categorías en crecimiento:**\n\n"
            trends_section += md_table(
                [[w["name"], f"+{w['diff']:,}", f"+{w['pct']:.1f}%"] for w in winners],
                ["Categoría", "Δ Mensajes", "Δ %"],
            )
        if losers:
            trends_section += "\n**Categorías en descenso:**\n\n"
            trends_section += md_table(
                [[l["name"], f"{l['diff']:,}", f"{l['pct']:.1f}%"] for l in losers],
                ["Categoría", "Δ Mensajes", "Δ %"],
            )

    # Categories detailed
    cat_detail_md = ""
    for macro_data in categories_detailed[:15]:
        macro_name = macro_data.get("macro", "—")
        macro_convs = macro_data.get("total_conversations", 0)
        macro_pct_val = macro_data.get("pct", 0)
        cat_detail_md += f"\n#### {macro_name} — {N(macro_convs)} conv. ({macro_pct_val:.1f}%)\n\n"

        subs = macro_data.get("subcategories", [])
        sub_rows = []
        for s in subs[:10]:
            name = s.get("name", "—")
            convs = s.get("conversations", 0)
            spct = s.get("pct_within_macro", 0)
            util_d = s.get("utility", {})
            util_pct_val = util_d.get("useful_pct", 0)
            redir = s.get("redirections", {})
            redir_pct_val = redir.get("pct", 0)
            fail_d = s.get("bot_failures", {})
            fail_pct_val = fail_d.get("pct", 0)
            prods = ", ".join(p["name"] for p in s.get("products", [])[:3]) or "—"
            sub_rows.append([
                name, N(convs), f"{spct:.1f}%",
                f"{util_pct_val:.0f}%", f"{redir_pct_val:.0f}%", f"{fail_pct_val:.0f}%",
                prods,
            ])
        cat_detail_md += md_table(
            sub_rows,
            ["Subcategoría", "Conv.", "% Macro", "Utilidad", "Redirig.", "Fallos", "Productos"],
        )

    # Products detailed
    prod_detail_md = ""
    for pmacro in products_detailed[:12]:
        pm_name = pmacro.get("macro", "—")
        pm_convs = pmacro.get("total_conversations", 0)
        pm_pct = pmacro.get("pct", 0)
        prod_detail_md += f"\n#### {pm_name} — {N(pm_convs)} conv. ({pm_pct:.1f}%)\n\n"

        prods_list = pmacro.get("products", [])
        prod_detail_rows = []
        for p in prods_list[:8]:
            pname = p.get("name", "—")
            pconvs = p.get("conversations", 0)
            ppct = p.get("pct_within_macro", 0)
            util_d = p.get("utility", {})
            util_pct_val = util_d.get("useful_pct", 0)
            redir = p.get("redirections", {})
            redir_pct_val = redir.get("pct", 0)
            fail_d = p.get("bot_failures", {})
            fail_pct_val = fail_d.get("pct", 0)
            top_cats = ", ".join(c["name"] for c in p.get("top_categories", [])[:3]) or "—"
            prod_detail_rows.append([
                pname, N(pconvs), f"{ppct:.1f}%",
                f"{util_pct_val:.0f}%", f"{redir_pct_val:.0f}%", f"{fail_pct_val:.0f}%",
                top_cats,
            ])
        prod_detail_md += md_table(
            prod_detail_rows,
            ["Producto", "Conv.", "% Macro", "Utilidad", "Redirig.", "Fallos", "Top Categorías"],
        )

    # Failures detailed
    criteria_global = failures_detailed.get("criteria_global", {})
    criteria_table = md_table(
        [[c, N(v), f"{v / fail_n * 100:.1f}%"] for c, v in
         sorted(criteria_global.items(), key=lambda x: x[1], reverse=True)],
        ["Criterio de fallo", "Casos", "% del total fallos"],
    ) if fail_n else "_Sin datos._\n"

    fail_by_cat = failures_detailed.get("by_category", [])
    fail_cat_rows = []
    for fc in fail_by_cat[:15]:
        cat = fc.get("category", "—")
        cnt = fc.get("count", 0)
        fpct = fc.get("pct", 0)
        top_crit = ", ".join(
            f"{c}({v})" for c, v in
            sorted(fc.get("criteria_breakdown", {}).items(), key=lambda x: x[1], reverse=True)[:2]
        ) or "—"
        top_prods = ", ".join(p["name"] for p in fc.get("top_products", [])[:2]) or "—"
        redir_pct_val = fc.get("redirected_pct", 0)
        fail_cat_rows.append([cat, N(cnt), f"{fpct:.1f}%", top_crit, top_prods, f"{redir_pct_val:.0f}%"])
    fail_cat_table = md_table(
        fail_cat_rows,
        ["Categoría", "Fallos", "% Total", "Criterios principales", "Productos", "% Redirigido"],
    )

    # Survey utility top 15
    util_rows = [
        [r.get("macro", "—"), r.get("categoria", "—"), r.get("producto", "—"),
         N(r.get("useful", 0)), N(r.get("not_useful", 0)),
         N(r.get("total", 0)), f"{r.get('utility_rate', 0):.1f}%"]
        for r in survey_util[:15]
    ]
    util_table = md_table(
        util_rows,
        ["Macro", "Categoría", "Producto", "Útil", "No útil", "Total", "% Utilidad"],
    )

    # Volume top 20
    vol_rows = [
        [r.get("macro_yaml", "—"), r.get("categoria_yaml", "—"),
         r.get("product_yaml", "—"), N(r.get("count", 0)),
         f"{r.get('percentage', 0):.2f}%"]
        for r in volume_rpt[:20]
    ]
    vol_table = md_table(vol_rows, ["Macro", "Categoría", "Producto", "Mensajes", "%"])

    # Methodology
    methodology = kpis_detailed.get("methodology", {})
    method_md = ""
    for key, m in methodology.items():
        method_md += f"- **{key.replace('_', ' ').title()}**: {m.get('description', '')} "
        method_md += f"Fórmula: `{m.get('formula', '')}` = {m.get('result', 0)}{m.get('unit', '')}\n"

    return f"""# Informe Ejecutivo — Asistente Virtual

**Período:** {period.get('start', 'N/A')} — {period.get('end', 'N/A')}
**Generado:** {generated_at.strftime('%Y-%m-%d %H:%M:%S')}
**Fuente:** data/chat_data.db · {N(total_msgs)} mensajes · {N(total_convs)} conversaciones

---

## Resumen Ejecutivo

| Indicador | Valor |
|---|---|
| Total conversaciones | {N(total_convs)} |
| Usuarios únicos | {N(fk.get('unique_users', 0))} |
| Tasa de abandono | {abandon_rate:.1f}% ({N(abandon_n)} conv.) |
| Auto-servicio | {self_svc:.1f}% |
| Tasa de derivación | {ref_rate:.1f}% |
| Índice de utilidad | {utility:.1f}% |
| Encuestas respondidas | {N(total_surveys)} (útil: {N(useful_s)}, no útil: {N(not_useful_s)}) |
| Gasto de valor | {N(waste_count)} conv. ({waste_pct:.1f}%) |
| Conversaciones con fallo | {N(fail_n)} ({pct(fail_n, total_convs)}) |

---

## 1. KPIs Operacionales

| KPI | Valor |
|---|---|
| Total mensajes | {N(total_msgs)} |
| Mensajes humanos | {N(by_type.get('human', 0))} ({pct(by_type.get('human', 0), total_msgs)}) |
| Mensajes bot (AI) | {N(by_type.get('ai', 0))} ({pct(by_type.get('ai', 0), total_msgs)}) |
| Mensajes tool | {N(by_type.get('tool', 0))} ({pct(by_type.get('tool', 0), total_msgs)}) |
| Promedio msgs/conv | {kpis.get('avg_messages_per_thread', 0):.2f} |
| Abandono (≤1 msg humano) | {N(abandon_n)} ({abandon_rate:.1f}%) |
| Auto-servicio | {self_svc:.1f}% |
| Tasa de derivación | {ref_rate:.1f}% |
| Encuestas respondidas | {N(total_surveys)} |
| Índice de utilidad | {utility:.1f}% |
| Tokens entrada (total) | {N(kpis.get('total_input_tokens', 0))} |
| Tokens salida (total) | {N(kpis.get('total_output_tokens', 0))} |

---

## 2. Patrones Temporales

### Horas de mayor volumen

{hours_table}

### Volumen por día de la semana

{dow_table}

---

## 3. Distribución de Sentimiento

{sent_table}

---

## 4. Distribución de Categorías

### Macrocategorías (Top 10)

{macro_table}

### Top 15 Subcategorías

{intent_table}
{trends_section}

---

## 5. Análisis Detallado por Categoría

Desglose macro → subcategoría con métricas de resultado (utilidad, redirecciones, fallos) y productos asociados.

{cat_detail_md}

---

## 6. Distribución de Productos

### Productos más consultados (Top 15)

{products_summary_table}

---

## 7. Análisis Detallado por Producto

Desglose por macro de producto → producto con métricas de resultado y categorías principales.

{prod_detail_md}

---

## 8. Calidad y Fricción

| Métrica | Valor |
|---|---|
| Conversaciones con fallo | {N(fail_n)} ({pct(fail_n, total_convs)}) |
| Conversaciones derivadas | {N(int(total_convs * ref_rate / 100) if total_convs else 0)} ({ref_rate:.1f}%) |
| Gasto de valor | {N(waste_count)} ({waste_pct:.1f}%) |

### Criterios de fallo globales

{criteria_table}

### Fallos por categoría (Top 15)

{fail_cat_table}

---

## 9. Utilidad por Categoría y Producto (Encuestas)

{util_table}

---

## 10. Reporte de Volumen Detallado

{vol_table}

---

## Metodología

{method_md}

---
*Generado automáticamente por el endpoint /api/reports/export/markdown — {generated_at.strftime('%Y-%m-%d %H:%M')}*
"""


# ═══════════════════════════════════════════════════════════════════════════
# Dimension Report (per-product or per-macro-category)
# ═══════════════════════════════════════════════════════════════════════════

def build_dimension_report_md(report: dict, period: dict | None = None) -> str:
    """
    Build a standalone Markdown report from the output of get_dimension_report().
    """
    dim_label = "Producto" if report["dimension"] == "product" else "Categoría"
    value = report.get("value", "—")
    parent = report.get("parent", "")
    n = report.get("total_conversations", 0)
    total_msgs = report.get("total_messages", 0)
    kpis = report.get("kpis", {})
    sentiments = report.get("sentiments", {})
    top_items = report.get("top_items", [])
    user_phrases = report.get("user_phrases", [])
    user_questions = report.get("user_questions", [])
    subcategories = report.get("subcategories", [])
    unanswered_questions = report.get("unanswered_questions", [])
    failures = report.get("failures_detail", {})
    redirections = report.get("redirections", {})
    utility = report.get("utility", {})
    sample_threads = report.get("sample_threads", [])
    underlying = report.get("underlying_intents", [])
    advisor = report.get("advisor_escalation", {})

    period_str = ""
    if period:
        period_str = f"**Período:** {period.get('start', 'N/A')} — {period.get('end', 'N/A')}"

    parent_line = f"\n**Macro:** {parent}" if parent else ""

    # --- Section 1: KPIs ---
    kpi_rows = [
        ["Total conversaciones", N(n)],
        ["Total mensajes", N(total_msgs)],
        ["Encuestados", f"{N(kpis.get('surveyed', 0))} ({kpis.get('surveyed_pct', 0):.1f}%)"],
        ["Con errores IA", f"{N(kpis.get('failures', 0))} ({kpis.get('failure_pct', 0):.1f}%)"],
        ["Redirigidos", f"{N(kpis.get('redirected', 0))} ({kpis.get('redirected_pct', 0):.1f}%)"],
        ["Auto-servicio", f"{N(kpis.get('self_service', 0))} ({kpis.get('self_service_pct', 0):.1f}%)"],
    ]
    kpi_table = md_table(kpi_rows, ["Indicador", "Valor"])

    # --- Section 2: What users ask ---
    item_label = "Categorías" if report["dimension"] == "product" else "Productos"
    item_rows = [
        [it["name"], N(it["conversations"]), f"{it['pct']:.1f}%"]
        for it in top_items
    ]
    items_table = md_table(item_rows, [item_label, "Conversaciones", "%"])

    phrases_list = "\n".join(
        f"- \"{p['phrase']}\" ({N(p['count'])} veces)"
        for p in user_phrases
    ) if user_phrases else "_Sin frases frecuentes._"

    # --- Subcategories section ---
    subcategories_section = ""
    if subcategories:
        sc_rows = [[sc["name"], N(sc["conversations"]), f"{sc['pct']:.1f}%"] for sc in subcategories]
        subcategories_section = f"""
### 2.2 Subcategorías

{md_table(sc_rows, ['Subcategoría', 'Conversaciones', '%'])}
"""

    questions_block = ""
    if user_questions:
        q_rows = [[f"\"{q['phrase']}\"", N(q["count"])] for q in user_questions]
        q_table = md_table(q_rows, ["Pregunta del usuario", "Veces"])
        questions_block = f"""
### 2.4 Preguntas reales de los usuarios

> Estas son las frases **exactas** que escriben los usuarios. Permiten identificar los puntos de dolor,
> errores de acceso, y necesidades no resueltas.

{q_table}
"""

    underlying_section = ""
    if underlying:
        u_rows = [[u["category"], N(u["threads"]), f"{u['pct']:.1f}%"] for u in underlying]
        underlying_section = f"\n### 2.5 Intenciones subyacentes\n\n{md_table(u_rows, ['Intención', 'Hilos', '%'])}"

    # --- Section 3: Failures ---
    fail_total = failures.get("total", 0)
    fail_pct = failures.get("pct", 0)
    by_criteria = failures.get("by_criteria", {})
    criteria_table = dict_to_table(by_criteria, "Criterio", "Casos") if by_criteria else "_Sin fallos detectados._\n"

    fail_examples = failures.get("examples", [])
    examples_rows = [
        [ex["thread_id"], ex.get("fecha", ""), trunc(ex.get("last_user_message", ""), 80),
         trunc(ex.get("last_ai_message", ""), 80)]
        for ex in fail_examples[:10]
    ]
    examples_table = md_table(examples_rows, ["Thread ID", "Fecha", "Último msg usuario", "Respuesta IA"]) if examples_rows else ""

    # --- Unanswered questions section ---
    unanswered_section = ""
    if unanswered_questions:
        uq_rows = [[f"\"{q['phrase']}\"", N(q["count"])] for q in unanswered_questions]
        uq_table = md_table(uq_rows, ["Pregunta del usuario", "Veces"])
        unanswered_section = f"""
### 3.1 Preguntas que el bot no supo responder

> Frases reales de usuarios en conversaciones donde el asistente falló.
> Excluye mensajes de encuesta y retroalimentación.

{uq_table}
"""

    # --- Section 4: Redirections ---
    redir_total = redirections.get("total", 0)
    redir_pct = redirections.get("pct", 0)
    by_channel = redirections.get("by_channel", {})
    channel_table = dict_to_table(by_channel, "Canal", "Conversaciones") if by_channel else "_Sin redirecciones._\n"

    # --- Section 5: Utility ---
    u_useful = utility.get("useful", 0)
    u_not = utility.get("not_useful", 0)
    u_no_survey = utility.get("no_survey", 0)
    u_pct = utility.get("useful_pct", 0)

    sent_total = sum(sentiments.values()) or 1
    sent_rows = [
        [s, N(c), f"{c / sent_total * 100:.1f}%"]
        for s, c in sentiments.items()
    ]
    sent_table = md_table(sent_rows, ["Sentimiento", "Mensajes", "%"])

    advisor_line = ""
    if advisor.get("total", 0) > 0:
        advisor_line = f"\n**Escalamiento a asesor:** {N(advisor['total'])} conversaciones ({advisor['pct']:.1f}%)\n"

    # --- Section 6: Sample threads ---
    thread_rows = [
        [t["thread_id"], t.get("fecha", ""), trunc(t.get("first_message", ""), 80), t.get("sentiment", "")]
        for t in sample_threads[:50]
    ]
    threads_table = md_table(thread_rows, ["Thread ID", "Fecha", "Primer mensaje", "Sentimiento"]) if thread_rows else "_Sin hilos._\n"

    return f"""# Reporte: {dim_label} — {value}
{parent_line}
{period_str}
**Total:** {N(n)} conversaciones · {N(total_msgs)} mensajes

---

## 1. Indicadores Generales

{kpi_table}

## 2. ¿Qué Preguntan los Usuarios?

### 2.1 {item_label} principales

{items_table}
{subcategories_section}
### 2.3 Frases más frecuentes

{phrases_list}
{questions_block}{underlying_section}

## 3. ¿Qué No Puede Responder el Asistente?

**Total fallos:** {N(fail_total)} ({fail_pct:.1f}% de las conversaciones)

{criteria_table}

{examples_table}
{unanswered_section}

## 4. Redirecciones

**Total redirigidas:** {N(redir_total)} ({redir_pct:.1f}%)

{channel_table}

## 5. Percepción de Utilidad

| Indicador | Valor |
|---|---|
| Me fue útil | {N(u_useful)} |
| No me fue útil | {N(u_not)} |
| Sin encuesta | {N(u_no_survey)} |
| Índice de utilidad | {u_pct:.1f}% |

{advisor_line}

### Sentimiento

{sent_table}

## 6. Hilos de Referencia

> Estos IDs permiten buscar las conversaciones completas en el Excel o en el Explorador de Mensajes.

{threads_table}

---
*Reporte generado automáticamente.*
"""


def build_dimension_csv(threads: list[dict]) -> bytes:
    """Convert thread dicts (from get_category_threads) to CSV bytes for Excel."""
    import io
    import csv

    if not threads:
        return b""

    fieldnames = [
        "thread_id", "fecha", "first_human_message", "product",
        "sentiment", "message_count", "was_redirected", "redirect_channel",
        "survey_result", "bot_failed", "failure_criteria", "intent_position",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(threads)
    return buf.getvalue().encode("utf-8-sig")
