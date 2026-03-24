from __future__ import annotations

import pandas as pd
from .metrics import get_general_kpis
from .dashboard_metrics import get_extended_funnel
from .summary import get_survey_stats
from .faqs import get_faqs_by_category
from .referrals import detect_referrals


# ---------------------------------------------------------------------------
# Helpers for category enrichment
# ---------------------------------------------------------------------------

GREETING_PREFIXES = sorted([
    "hola buenas tardes", "hola buenas noches", "hola buenos dias",
    "hola buen dia", "buenas tardes", "buenas noches", "buenos dias",
    "buen dia", "buenas", "hola", "saludos", "que tal", "como estas",
    "hey", "hi", "hello",
], key=len, reverse=True)

REFERRAL_CHANNEL_KEYWORDS = {
    "serviline": ["servilínea", "servilinea", "línea de atención",
                   "linea de atencion", "llamar al", "marcar al"],
    "digital": ["banca móvil", "banca movil", "banca virtual", "portal",
                "página web", "app bolívar", "descarga la app"],
    "office": ["oficina", "sucursal", "punto físico"],
}


def _strip_greeting_prefix(text: str) -> str:
    lower = text.lower().strip()
    for prefix in GREETING_PREFIXES:
        if lower.startswith(prefix):
            return lower[len(prefix):].lstrip(" ,.:;!?").strip()
    return lower


def _is_pure_greeting(text: str) -> bool:
    return len(_strip_greeting_prefix(text)) < 5


def _compute_survey_sets(df: pd.DataFrame):
    """Return sets of thread_ids classified as useful / not_useful."""
    survey_mask = df["text"].str.contains(r"\[survey\]", case=False, na=False)
    survey_df = df[survey_mask]
    if survey_df.empty:
        return set(), set()
    not_useful_mask = survey_df["text"].str.contains("no me fue útil", case=False, na=False)
    useful_mask = (
        survey_df["text"].str.contains("me fue útil", case=False, na=False)
        & ~not_useful_mask
    )
    return set(survey_df.loc[useful_mask, "thread_id"]), set(survey_df.loc[not_useful_mask, "thread_id"])


def _build_referral_channel_map(referrals_df: pd.DataFrame) -> dict:
    """Map thread_id -> channel from referral_response text."""
    if referrals_df is None or referrals_df.empty:
        return {}
    channel_map = {}
    for _, row in referrals_df.iterrows():
        txt = str(row.get("referral_response", "")).lower()
        ch = "other"
        for channel, kws in REFERRAL_CHANNEL_KEYWORDS.items():
            if any(kw in txt for kw in kws):
                ch = channel
                break
        channel_map[row["thread_id"]] = ch
    return channel_map


# Categories that represent "user wants a human advisor"
ADVISOR_CATEGORIES = {"Canales Físicos y Asistidos", "Canales Físicos / Asesor"}

# Subcategories that are attributes/noise — don't count as underlying intents
_ATTRIBUTE_CATEGORIES = {
    "Encuesta", "Saludos", "Sin Sentido", "Retroalimentación",
    "Evaluación General",
}


def _enrich_subcategory(sub_name, sub_threads, hdf_with_pos,
                        referral_threads, referral_channel_map,
                        failure_threads, failure_criteria_map,
                        survey_useful, survey_not_useful,
                        filter_col="categoria_yaml"):
    """Compute outcome metrics for one subcategory (or product when filter_col='product_yaml')."""
    n = len(sub_threads)
    if n == 0:
        empty = {"first_intent": 0, "post_consultation": 0, "first_intent_pct": 0.0}
        return {
            "intent_position": empty,
            "greeting_contamination": {"pure_greeting_count": 0, "with_real_intent": 0, "no_greeting": 0},
            "redirections": {"total": 0, "pct": 0.0, "by_channel": {}},
            "utility": {"useful": 0, "not_useful": 0, "no_survey": 0, "useful_pct": 0.0},
            "bot_failures": {"total": 0, "pct": 0.0, "by_criteria": {}},
            "advisor_escalation": {"total": 0, "pct": 0.0},
        }

    # 1. Intent position — first occurrence of THIS subcategory/product in each thread
    sub_pos = hdf_with_pos[
        (hdf_with_pos["thread_id"].isin(sub_threads))
        & (hdf_with_pos[filter_col] == sub_name)
    ]
    first_pos = sub_pos.groupby("thread_id")["msg_pos"].min()
    first_intent = int((first_pos <= 2).sum())
    post_consult = int((first_pos > 2).sum())

    # 2. Greeting contamination — check first human msg per thread
    first_texts = hdf_with_pos[
        (hdf_with_pos["thread_id"].isin(sub_threads))
        & (hdf_with_pos[filter_col] == sub_name)
    ].drop_duplicates("thread_id")["text"]
    pure = int(first_texts.apply(_is_pure_greeting).sum())

    # 3. Redirections
    redirected = sub_threads & referral_threads
    by_channel: dict = {}
    for tid in redirected:
        ch = referral_channel_map.get(tid, "other")
        by_channel[ch] = by_channel.get(ch, 0) + 1

    # 4. Utility
    useful = sub_threads & survey_useful
    not_useful = sub_threads & survey_not_useful
    u, nu = len(useful), len(not_useful)
    useful_pct = round(u / (u + nu) * 100, 1) if (u + nu) > 0 else 0.0

    # 5. Bot failures
    failed = sub_threads & failure_threads
    by_criteria: dict = {}
    for tid in failed:
        for crit in (failure_criteria_map.get(tid, "") or "").split(","):
            crit = crit.strip()
            if crit:
                by_criteria[crit] = by_criteria.get(crit, 0) + 1

    # 6. Advisor escalation — threads where user requested an advisor AFTER this category
    #    (only for non-advisor categories; for advisor categories themselves, skip)
    advisor_escalated = 0
    if sub_name not in ADVISOR_CATEGORIES:
        # Find threads where this sub's first msg comes BEFORE an advisor request
        advisor_msgs = hdf_with_pos[
            (hdf_with_pos["thread_id"].isin(sub_threads))
            & (hdf_with_pos["categoria_yaml"].isin(ADVISOR_CATEGORIES))
        ]
        if not advisor_msgs.empty:
            # For each thread: check if advisor msg_pos > this sub's first msg_pos
            advisor_first = advisor_msgs.groupby("thread_id")["msg_pos"].min()
            sub_first = first_pos  # already computed above
            for tid in advisor_first.index:
                if tid in sub_first.index and advisor_first[tid] > sub_first[tid]:
                    advisor_escalated += 1

    # 7. Underlying intents — what OTHER categories appear in the same threads?
    #    This answers "why" for symptom categories (e.g., Funcionalidades Bloqueadas:
    #    40% were trying to do PQR, 25% were trying to transfer, etc.)
    skip_for_intent = _ATTRIBUTE_CATEGORIES | {sub_name} | ADVISOR_CATEGORIES
    other_cats = hdf_with_pos[
        (hdf_with_pos["thread_id"].isin(sub_threads))
        & (~hdf_with_pos["categoria_yaml"].isin(skip_for_intent))
        & (hdf_with_pos["categoria_yaml"].notna())
    ]
    underlying_intents = []
    if not other_cats.empty:
        intent_counts = (
            other_cats.groupby("categoria_yaml")["thread_id"]
            .nunique()
            .sort_values(ascending=False)
            .head(5)
        )
        for cat_name, cat_count in intent_counts.items():
            underlying_intents.append({
                "category": cat_name,
                "threads": int(cat_count),
                "pct": round(cat_count / n * 100, 1),
            })

    return {
        "intent_position": {
            "first_intent": first_intent,
            "post_consultation": post_consult,
            "first_intent_pct": round(first_intent / n * 100, 1) if n else 0.0,
        },
        "greeting_contamination": {
            "pure_greeting_count": pure,
            "with_real_intent": n - pure,
            "no_greeting": n - pure,
        },
        "redirections": {
            "total": len(redirected),
            "pct": round(len(redirected) / n * 100, 1) if n else 0.0,
            "by_channel": by_channel,
        },
        "utility": {
            "useful": u,
            "not_useful": nu,
            "no_survey": n - u - nu,
            "useful_pct": useful_pct,
        },
        "bot_failures": {
            "total": len(failed),
            "pct": round(len(failed) / n * 100, 1) if n else 0.0,
            "by_criteria": by_criteria,
        },
        "advisor_escalation": {
            "total": advisor_escalated,
            "pct": round(advisor_escalated / n * 100, 1) if n else 0.0,
        },
        "underlying_intents": underlying_intents,
    }


def get_kpis_detailed(df: pd.DataFrame, start_date: str = None, end_date: str = None) -> dict:
    """
    Returns KPIs with methodology explanations and drill-down data.
    Extracts values from the metrics[] array produced by get_extended_funnel().
    """
    if df is None or df.empty:
        return {"kpis": {}, "funnel": {}, "surveys": {}, "methodology": {}}

    kpis = get_general_kpis(df)
    funnel_data = get_extended_funnel(df, start_date, end_date)
    surveys = get_survey_stats(df)

    # Build lookup from metrics array
    metrics_list = funnel_data.get("metrics", [])
    m = {item["id"]: item for item in metrics_list}

    def _get(metric_id: str) -> int:
        return m.get(metric_id, {}).get("count", 0)

    def _pct(n: int, base: int) -> float:
        return round(n / base * 100, 1) if base > 0 else 0.0

    total = _get("total")
    greeting = _get("greeting_only")
    active = _get("active")
    self_service = _get("self_service")
    referred = _get("referred")
    failures = _get("failures")
    referred_failed = _get("referred_failed")
    useful = _get("useful")
    answered = _get("answered")
    waste = _get("waste")

    methodology = {
        "greeting_rate": {
            "formula": "Conversaciones solo saludo ÷ Total × 100",
            "description": "Hilos donde todos los mensajes humanos tienen ≤5 palabras. No representan necesidades reales.",
            "numerator": greeting,
            "denominator": total,
            "result": _pct(greeting, total),
            "unit": "%"
        },
        "self_service": {
            "formula": "Activas sin redirección ÷ Activas × 100",
            "description": "De las conversaciones activas (>2 msgs humanos), cuántas el bot resolvió sin escalar a otro canal.",
            "numerator": self_service,
            "denominator": active,
            "result": _pct(self_service, active),
            "unit": "%"
        },
        "utility_index": {
            "formula": "Encuestas 'Me fue útil' ÷ Encuestas contestadas × 100",
            "description": "Satisfacción declarada — solo de quienes respondieron la encuesta.",
            "numerator": useful,
            "denominator": answered,
            "result": _pct(useful, answered),
            "unit": "%"
        },
        "failure_rate": {
            "formula": "Fallos IA ÷ Activas × 100",
            "description": "Conversaciones activas donde la IA no supo responder, el usuario repitió la pregunta, o el sentimiento fue negativo.",
            "numerator": failures,
            "denominator": active,
            "result": _pct(failures, active),
            "unit": "%"
        },
        "referral_failure": {
            "formula": "Redirigidas por fallo IA ÷ Redirigidas × 100",
            "description": "De las conversaciones redirigidas, cuántas lo fueron porque la IA falló (no por diseño del flujo).",
            "numerator": referred_failed,
            "denominator": referred,
            "result": _pct(referred_failed, referred),
            "unit": "%"
        },
        "value_waste": {
            "formula": "(No útil ∩ Redirigidas) ÷ Total × 100",
            "description": "Doble fallo: el bot no resolvió Y redirigió al usuario a otro canal.",
            "numerator": waste,
            "denominator": total,
            "result": _pct(waste, total),
            "unit": "%"
        },
    }

    return {
        "kpis": kpis,
        "funnel": funnel_data,
        "surveys": surveys,
        "methodology": methodology
    }


def get_categories_detailed(df: pd.DataFrame,
                            referrals_df: pd.DataFrame = None,
                            failures_df: pd.DataFrame = None) -> list:
    """
    Returns macro -> subcategory -> product breakdown with user phrase examples
    and outcome metrics (intent position, redirections, utility, bot failures,
    greeting contamination).
    """
    if df is None or df.empty:
        return []

    SKIP_MACROS = {"Sin Clasificar", "Encuestas"}
    # Subcategories that are conversation attributes, not real user intents.
    # They still exist in the data for metrics (surveys, sentiment) but don't
    # belong in the deep analysis panel.
    SKIP_SUBCATEGORIES = {"Encuesta", "Saludos", "Sin Sentido", "Retroalimentación"}

    hdf = df[df["type"] == "human"].copy()
    if hdf.empty or "macro_yaml" not in hdf.columns:
        return []

    # Pre-compute message positions (chronological within each thread)
    hdf = hdf.sort_index()
    hdf["msg_pos"] = hdf.groupby("thread_id").cumcount()

    # Pre-compute outcome sets
    referral_threads = set(referrals_df["thread_id"]) if referrals_df is not None and not referrals_df.empty else set()
    referral_channel_map = _build_referral_channel_map(referrals_df)
    failure_threads = set(failures_df["thread_id"]) if failures_df is not None and not failures_df.empty else set()
    failure_criteria_map = (
        failures_df.set_index("thread_id")["criteria"].to_dict()
        if failures_df is not None and not failures_df.empty and "criteria" in failures_df.columns
        else {}
    )
    survey_useful, survey_not_useful = _compute_survey_sets(df)

    # Get FAQs (user phrases per subcategory)
    faqs = get_faqs_by_category(df, top_n=5)

    total_h_convs = hdf["thread_id"].nunique()

    # Macro totals sorted descending (excluding noise subs)
    filtered_hdf = hdf[
        ~hdf["macro_yaml"].isin(SKIP_MACROS)
        & ~hdf["categoria_yaml"].isin(SKIP_SUBCATEGORIES)
    ]
    macro_totals = (
        filtered_hdf
        .groupby("macro_yaml")["thread_id"]
        .nunique()
        .sort_values(ascending=False)
    )

    result = []
    for macro, macro_total in macro_totals.items():
        macro_pct = round(macro_total / total_h_convs * 100, 1) if total_h_convs else 0

        # Subcategories for this macro (excluding attribute-like subs)
        macro_hdf = hdf[(hdf["macro_yaml"] == macro) & (~hdf["categoria_yaml"].isin(SKIP_SUBCATEGORIES))]
        sub_totals = (
            macro_hdf.groupby("categoria_yaml")["thread_id"]
            .nunique()
            .sort_values(ascending=False)
        )

        subcategories = []
        macro_faqs = faqs.get(macro, {})

        for sub_name, sub_convs in sub_totals.items():
            if sub_name in SKIP_SUBCATEGORIES:
                continue
            sub_pct = round(sub_convs / macro_total * 100, 1) if macro_total else 0
            sub_hdf = macro_hdf[macro_hdf["categoria_yaml"] == sub_name]
            sub_threads = set(sub_hdf["thread_id"].unique())

            # Products
            prod_col = "product_yaml" if "product_yaml" in sub_hdf.columns else "product_type"
            products_raw = (
                sub_hdf[sub_hdf[prod_col].notna() & (sub_hdf[prod_col] != "")]
                .groupby(prod_col)["thread_id"]
                .nunique()
                .sort_values(ascending=False)
                .head(8)
            )
            products = [{"name": p, "conversations": int(c)} for p, c in products_raw.items()]

            # Sentiments
            sent_counts = {"positivo": 0, "neutral": 0, "negativo": 0}
            if "sentiment" in sub_hdf.columns:
                for s, cnt in sub_hdf["sentiment"].value_counts().items():
                    if s in sent_counts:
                        sent_counts[s] = int(cnt)

            # User phrases from FAQs
            user_phrases = macro_faqs.get(sub_name, [])

            # Outcome metrics
            outcomes = _enrich_subcategory(
                sub_name, sub_threads, hdf,
                referral_threads, referral_channel_map,
                failure_threads, failure_criteria_map,
                survey_useful, survey_not_useful,
            )

            subcategories.append({
                "name": sub_name,
                "conversations": int(sub_convs),
                "pct_within_macro": sub_pct,
                "user_phrases": user_phrases,
                "products": products,
                "sentiments": sent_counts,
                **outcomes,
            })

        result.append({
            "macro": macro,
            "total_conversations": int(macro_total),
            "pct": macro_pct,
            "subcategories": subcategories
        })

    return result


def get_category_threads(df: pd.DataFrame,
                         referrals_df: pd.DataFrame = None,
                         failures_df: pd.DataFrame = None,
                         macro: str = "",
                         subcategory: str = None,
                         product: str = None,
                         cross_category: str = None,
                         page: int = 1,
                         limit: int = 20,
                         exclude_greetings: bool = False,
                         product_macro: str = None,
                         failures_only: bool = False) -> dict:
    """
    Returns paginated thread list for a macro/subcategory/product combination
    with per-thread outcome indicators.

    cross_category: if set, only returns threads where BOTH the subcategory
    AND this cross_category appear (underlying intent drill-down).
    product_macro: if set, filters by product_macro_yaml instead of macro_yaml.
    failures_only: if True, only returns threads that are in failures_df.
    """
    if df is None or df.empty:
        return {"data": [], "total": 0, "page": page, "limit": limit}

    hdf = df[df["type"] == "human"].copy()
    if hdf.empty:
        return {"data": [], "total": 0, "page": page, "limit": limit}

    # Filter by macro (category macro) or product_macro
    if product_macro:
        # Filter by product macro — for ProductsDeepPanel
        prod_col = "product_macro_yaml" if "product_macro_yaml" in hdf.columns else "product_type"
        filtered = hdf[hdf[prod_col] == product_macro]
    else:
        filtered = hdf[hdf["macro_yaml"] == macro]
    if subcategory:
        filtered = filtered[filtered["categoria_yaml"] == subcategory]
    if product:
        prod_col = "product_yaml" if "product_yaml" in filtered.columns else "product_type"
        filtered = filtered[filtered[prod_col] == product]

    # Cross-category filter: only threads that ALSO have the cross_category
    if cross_category:
        cross_threads = set(
            hdf[hdf["categoria_yaml"] == cross_category]["thread_id"].unique()
        )
        filtered = filtered[filtered["thread_id"].isin(cross_threads)]

    if filtered.empty:
        return {"data": [], "total": 0, "page": page, "limit": limit}

    # Optional greeting exclusion
    if exclude_greetings:
        filtered = filtered[~filtered["text"].apply(_is_pure_greeting)]

    # Pre-compute outcome lookups
    referral_threads = set(referrals_df["thread_id"]) if referrals_df is not None and not referrals_df.empty else set()
    referral_channel_map = _build_referral_channel_map(referrals_df)
    failure_threads = set(failures_df["thread_id"]) if failures_df is not None and not failures_df.empty else set()

    # Filter to failures only if requested
    if failures_only and failure_threads:
        filtered = filtered[filtered["thread_id"].isin(failure_threads)]
        if filtered.empty:
            return {"data": [], "total": 0, "page": page, "limit": limit}

    # Compute msg positions
    hdf_sorted = hdf.sort_index()
    hdf_sorted["msg_pos"] = hdf_sorted.groupby("thread_id").cumcount()
    failure_criteria_map = (
        failures_df.set_index("thread_id")["criteria"].to_dict()
        if failures_df is not None and not failures_df.empty and "criteria" in failures_df.columns
        else {}
    )
    failure_last_ai_map = (
        failures_df.set_index("thread_id")["last_ai_message"].to_dict()
        if failures_df is not None and not failures_df.empty and "last_ai_message" in failures_df.columns
        else {}
    )
    failure_last_user_map = (
        failures_df.set_index("thread_id")["last_user_message"].to_dict()
        if failures_df is not None and not failures_df.empty and "last_user_message" in failures_df.columns
        else {}
    )
    survey_useful, survey_not_useful = _compute_survey_sets(df)

    # Get unique threads and first human message per thread
    thread_ids = filtered["thread_id"].unique()
    first_msgs = filtered.sort_index().drop_duplicates("thread_id")

    # Thread-level aggregation
    thread_data = []
    for _, row in first_msgs.iterrows():
        tid = row["thread_id"]

        # Intent position for this thread
        thread_pos = hdf_sorted[hdf_sorted["thread_id"] == tid]
        cat_filter = subcategory if subcategory else macro
        col = "categoria_yaml" if subcategory else "macro_yaml"
        cat_msgs = thread_pos[thread_pos[col] == cat_filter]
        min_pos = int(cat_msgs["msg_pos"].min()) if not cat_msgs.empty else 0
        intent_pos = "first_intent" if min_pos <= 2 else "post_consultation"

        # Thread message count (all types)
        msg_count = int(df[df["thread_id"] == tid].shape[0])

        prod_col = "product_yaml" if "product_yaml" in row.index else "product_type"
        fecha = row.get("fecha", "")
        if pd.notna(fecha) and hasattr(fecha, "strftime"):
            fecha = fecha.strftime("%Y-%m-%d")
        else:
            fecha = str(fecha)[:10] if pd.notna(fecha) else ""

        thread_data.append({
            "thread_id": str(tid),
            "first_human_message": str(row.get("text", ""))[:300],
            "message_count": msg_count,
            "intent_position": intent_pos,
            "product": str(row.get(prod_col, "") or ""),
            "sentiment": str(row.get("sentiment", "neutral")),
            "fecha": fecha,
            "was_redirected": tid in referral_threads,
            "redirect_channel": referral_channel_map.get(tid, ""),
            "survey_result": (
                "useful" if tid in survey_useful
                else "not_useful" if tid in survey_not_useful
                else ""
            ),
            "bot_failed": tid in failure_threads,
            "failure_criteria": failure_criteria_map.get(tid, ""),
            "last_ai_message": str(failure_last_ai_map.get(tid, ""))[:250] if tid in failure_threads else "",
            "last_user_message": str(failure_last_user_map.get(tid, ""))[:250] if tid in failure_threads else "",
        })

    # Sort by date descending
    thread_data.sort(key=lambda x: x["fecha"], reverse=True)

    total = len(thread_data)
    start = (page - 1) * limit
    end = start + limit

    return {
        "data": thread_data[start:end],
        "total": total,
        "page": page,
        "limit": limit,
    }


def get_failures_detailed(df: pd.DataFrame, failures_df: pd.DataFrame) -> dict:
    """
    Returns failures grouped by category with examples, criteria breakdown,
    and product association (from main df).
    """
    if failures_df is None or failures_df.empty:
        return {"total": 0, "total_conversations": 0, "criteria_global": {}, "by_category": []}

    total_failures = len(failures_df)
    cat_counts = failures_df["intencion"].value_counts()
    total_convs = df["thread_id"].nunique() if df is not None and not df.empty else 0

    # Global criteria totals
    criteria_global: dict[str, int] = {}
    for criteria_str in failures_df["criteria"].fillna(""):
        for crit in str(criteria_str).split(","):
            crit = crit.strip()
            if crit:
                criteria_global[crit] = criteria_global.get(crit, 0) + 1

    # Build product lookup per thread from main df
    thread_product: dict[str, str] = {}
    if df is not None and not df.empty and "product_yaml" in df.columns:
        prod_df = df[df["product_yaml"].notna() & (df["product_yaml"] != "")]
        if not prod_df.empty:
            thread_product = (
                prod_df.groupby("thread_id")["product_yaml"]
                .agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "")
                .to_dict()
            )

    by_category = []
    for cat, count in cat_counts.items():
        cat_df = failures_df[failures_df["intencion"] == cat]
        pct = round(count / total_failures * 100, 1) if total_failures else 0

        # Criteria breakdown
        criteria_breakdown: dict[str, int] = {}
        for criteria_str in cat_df["criteria"].fillna(""):
            for crit in str(criteria_str).split(","):
                crit = crit.strip()
                if crit:
                    criteria_breakdown[crit] = criteria_breakdown.get(crit, 0) + 1

        # Products associated with failed threads
        cat_threads = set(cat_df["thread_id"].unique())
        product_counts: dict[str, int] = {}
        for tid in cat_threads:
            prod = thread_product.get(tid)
            if prod:
                product_counts[prod] = product_counts.get(prod, 0) + 1
        top_products = sorted(product_counts.items(), key=lambda x: -x[1])[:5]

        # Top AI responses — what the bot says when it fails in this category
        top_ai_responses = []
        if "last_ai_message" in cat_df.columns:
            ai_texts = cat_df["last_ai_message"].dropna()
            ai_texts = ai_texts[ai_texts.str.strip() != ""]
            if not ai_texts.empty:
                # Truncate to first 150 chars for grouping (similar responses)
                truncated = ai_texts.str[:150]
                top_ai = truncated.value_counts().head(5)
                top_ai_responses = [
                    {"text": str(t), "count": int(c)}
                    for t, c in top_ai.items()
                ]

        # Correlations: redirected + survey
        n_cat = len(cat_df)
        redirected_count = 0
        if "was_redirected" in cat_df.columns:
            redirected_count = int(cat_df["was_redirected"].sum())

        # Examples (ALL, most recent first)
        examples_df = cat_df.sort_values("fecha", ascending=False)
        examples = []
        for _, row in examples_df.iterrows():
            fecha = row.get("fecha", "")
            if pd.notna(fecha) and hasattr(fecha, "strftime"):
                fecha = fecha.strftime("%Y-%m-%d")
            else:
                fecha = str(fecha)[:10] if pd.notna(fecha) else ""
            tid = str(row.get("thread_id", ""))
            examples.append({
                "thread_id": tid,
                "fecha": fecha,
                "last_user_message": str(row.get("last_user_message", "N/A"))[:200],
                "last_ai_message": str(row.get("last_ai_message", ""))[:200],
                "criteria": str(row.get("criteria", "")),
                "sentiment": str(row.get("sentiment", "neutral")),
                "product": thread_product.get(tid, "")
            })

        by_category.append({
            "category": str(cat),
            "count": int(count),
            "pct": pct,
            "criteria_breakdown": criteria_breakdown,
            "top_products": [{"name": p, "count": c} for p, c in top_products],
            "top_ai_responses": top_ai_responses,
            "redirected_count": redirected_count,
            "redirected_pct": round(redirected_count / n_cat * 100, 1) if n_cat else 0,
            "examples": examples
        })

    return {
        "total": total_failures,
        "total_conversations": total_convs,
        "criteria_global": criteria_global,
        "by_category": by_category
    }


# ---------------------------------------------------------------------------
# Products Detailed
# ---------------------------------------------------------------------------

SKIP_PRODUCTS = {"Ninguno", "General", "", None}


def get_products_detailed(df: pd.DataFrame,
                          referrals_df: pd.DataFrame = None,
                          failures_df: pd.DataFrame = None) -> list:
    """
    Returns product_macro -> product -> category breakdown with outcome metrics.
    Mirror of get_categories_detailed but with products as primary axis.
    """
    if df is None or df.empty:
        return []

    if "product_yaml" not in df.columns or "product_macro_yaml" not in df.columns:
        return []

    hdf = df[df["type"] == "human"].copy()
    if hdf.empty:
        return []

    # Filter out noise products
    hdf_prod = hdf[
        hdf["product_yaml"].notna()
        & (~hdf["product_yaml"].isin(SKIP_PRODUCTS))
    ]
    if hdf_prod.empty:
        return []

    # Pre-compute message positions
    hdf = hdf.sort_index()
    hdf["msg_pos"] = hdf.groupby("thread_id").cumcount()

    # Pre-compute outcome sets (same as get_categories_detailed)
    referral_threads = set(referrals_df["thread_id"]) if referrals_df is not None and not referrals_df.empty else set()
    referral_channel_map = _build_referral_channel_map(referrals_df)
    failure_threads = set(failures_df["thread_id"]) if failures_df is not None and not failures_df.empty else set()
    failure_criteria_map = (
        failures_df.set_index("thread_id")["criteria"].to_dict()
        if failures_df is not None and not failures_df.empty and "criteria" in failures_df.columns
        else {}
    )
    survey_useful, survey_not_useful = _compute_survey_sets(df)

    total_h_convs = hdf_prod["thread_id"].nunique()

    # Product macro totals
    macro_totals = (
        hdf_prod
        .groupby("product_macro_yaml")["thread_id"]
        .nunique()
        .sort_values(ascending=False)
    )

    result = []
    for macro, macro_total in macro_totals.items():
        if macro in SKIP_PRODUCTS:
            continue
        macro_pct = round(macro_total / total_h_convs * 100, 1) if total_h_convs else 0

        # Products within this macro
        macro_hdf = hdf_prod[hdf_prod["product_macro_yaml"] == macro]
        prod_totals = (
            macro_hdf.groupby("product_yaml")["thread_id"]
            .nunique()
            .sort_values(ascending=False)
        )

        products = []
        for prod_name, prod_convs in prod_totals.items():
            if prod_name in SKIP_PRODUCTS:
                continue
            prod_pct = round(prod_convs / macro_total * 100, 1) if macro_total else 0
            prod_hdf = macro_hdf[macro_hdf["product_yaml"] == prod_name]
            prod_threads = set(prod_hdf["thread_id"].unique())

            # Top categories for this product
            cat_col = "categoria_yaml" if "categoria_yaml" in prod_hdf.columns else "intencion"
            skip_cats = {"Encuesta", "Saludos", "Sin Sentido", "Retroalimentación", "Sin Clasificar"}
            cat_counts = (
                prod_hdf[prod_hdf[cat_col].notna() & (~prod_hdf[cat_col].isin(skip_cats))]
                .groupby(cat_col)["thread_id"]
                .nunique()
                .sort_values(ascending=False)
                .head(8)
            )
            top_categories = [
                {"name": c, "conversations": int(n), "pct": round(n / prod_convs * 100, 1) if prod_convs else 0}
                for c, n in cat_counts.items()
            ]

            # Sentiments
            sent_counts = {"positivo": 0, "neutral": 0, "negativo": 0}
            if "sentiment" in prod_hdf.columns:
                for s, cnt in prod_hdf["sentiment"].value_counts().items():
                    if s in sent_counts:
                        sent_counts[s] = int(cnt)

            # User phrases — top 5 most frequent human messages for this product
            phrase_df = prod_hdf[prod_hdf["text"].str.strip().str.len() >= 4]
            from .faqs import _is_noise, _is_system_or_survey
            phrase_df = phrase_df[~phrase_df["text"].apply(_is_noise)]
            phrase_df = phrase_df[~phrase_df["text"].apply(_is_system_or_survey)]
            phrase_counts = (
                phrase_df["text"].str.strip()
                .value_counts()
                .head(5)
            )
            user_phrases = [
                {"phrase": p, "count": int(c)}
                for p, c in phrase_counts.items()
            ]

            # Outcome metrics — reuse _enrich_subcategory with product_yaml filter
            outcomes = _enrich_subcategory(
                prod_name, prod_threads, hdf,
                referral_threads, referral_channel_map,
                failure_threads, failure_criteria_map,
                survey_useful, survey_not_useful,
                filter_col="product_yaml",
            )

            products.append({
                "name": prod_name,
                "conversations": int(prod_convs),
                "pct_within_macro": prod_pct,
                "top_categories": top_categories,
                "sentiments": sent_counts,
                "user_phrases": user_phrases,
                **outcomes,
            })

        result.append({
            "macro": macro,
            "total_conversations": int(macro_total),
            "pct": macro_pct,
            "products": products,
        })

    return result


# ---------------------------------------------------------------------------
# Dimension Report (per-product or per-macro-category)
# ---------------------------------------------------------------------------

def get_dimension_report(df: pd.DataFrame,
                         referrals_df: pd.DataFrame = None,
                         failures_df: pd.DataFrame = None,
                         dimension: str = "product",
                         value: str = "") -> dict:
    """
    Build a comprehensive report for a single product (product_yaml) or
    macro-category (macro_yaml).

    dimension: "product" | "category"
    value: the specific product name or macro category name
    """
    if df is None or df.empty or not value:
        return {"dimension": dimension, "value": value, "total_conversations": 0}

    hdf = df[df["type"] == "human"].copy()
    if hdf.empty:
        return {"dimension": dimension, "value": value, "total_conversations": 0}

    # --- Filter by dimension ---
    if dimension == "product":
        filter_col = "product_yaml"
        breakdown_col = "categoria_yaml"
        parent_col = "product_macro_yaml"
        skip_breakdown = {"Encuesta", "Saludos", "Sin Sentido", "Retroalimentación", "Sin Clasificar"}
    else:
        filter_col = "macro_yaml"
        breakdown_col = "product_yaml"
        parent_col = None
        skip_breakdown = SKIP_PRODUCTS

    if filter_col not in hdf.columns:
        return {"dimension": dimension, "value": value, "total_conversations": 0}

    filtered = hdf[hdf[filter_col] == value]
    if filtered.empty:
        return {"dimension": dimension, "value": value, "total_conversations": 0}

    dim_threads = set(filtered["thread_id"].unique())
    n = len(dim_threads)
    total_msgs = int(df[df["thread_id"].isin(dim_threads)].shape[0])

    # Parent (product_macro for products)
    parent = ""
    if parent_col and parent_col in filtered.columns:
        parent = str(filtered[parent_col].mode().iloc[0]) if not filtered[parent_col].isna().all() else ""

    # --- Pre-compute outcome sets ---
    hdf = hdf.sort_index()
    hdf["msg_pos"] = hdf.groupby("thread_id").cumcount()

    referral_threads = set(referrals_df["thread_id"]) if referrals_df is not None and not referrals_df.empty else set()
    referral_channel_map = _build_referral_channel_map(referrals_df)
    failure_threads = set(failures_df["thread_id"]) if failures_df is not None and not failures_df.empty else set()
    failure_criteria_map = (
        failures_df.set_index("thread_id")["criteria"].to_dict()
        if failures_df is not None and not failures_df.empty and "criteria" in failures_df.columns
        else {}
    )
    survey_useful, survey_not_useful = _compute_survey_sets(df)

    # --- KPIs ---
    surveyed_threads = dim_threads & (survey_useful | survey_not_useful)
    failed_threads = dim_threads & failure_threads
    redirected_threads = dim_threads & referral_threads
    self_service_threads = dim_threads - redirected_threads

    kpis = {
        "surveyed": len(surveyed_threads),
        "surveyed_pct": round(len(surveyed_threads) / n * 100, 1) if n else 0.0,
        "failures": len(failed_threads),
        "failure_pct": round(len(failed_threads) / n * 100, 1) if n else 0.0,
        "redirected": len(redirected_threads),
        "redirected_pct": round(len(redirected_threads) / n * 100, 1) if n else 0.0,
        "self_service": len(self_service_threads),
        "self_service_pct": round(len(self_service_threads) / n * 100, 1) if n else 0.0,
    }

    # --- Breakdown (categories if product, products if category) ---
    if breakdown_col in filtered.columns:
        bd_data = filtered[
            filtered[breakdown_col].notna() & (~filtered[breakdown_col].isin(skip_breakdown))
        ]
        bd_counts = (
            bd_data.groupby(breakdown_col)["thread_id"]
            .nunique()
            .sort_values(ascending=False)
            .head(15)
        )
        top_items = [
            {"name": str(name), "conversations": int(cnt),
             "pct": round(cnt / n * 100, 1) if n else 0.0}
            for name, cnt in bd_counts.items()
        ]
    else:
        top_items = []

    # --- Sentiments ---
    sent_counts = {"positivo": 0, "neutral": 0, "negativo": 0}
    if "sentiment" in filtered.columns:
        for s, cnt in filtered["sentiment"].value_counts().items():
            if s in sent_counts:
                sent_counts[s] = int(cnt)

    # --- User phrases ---
    from .faqs import _is_noise, _is_system_or_survey
    phrase_df = filtered[filtered["text"].str.strip().str.len() >= 4]
    phrase_df = phrase_df[~phrase_df["text"].apply(_is_noise)]
    phrase_df = phrase_df[~phrase_df["text"].apply(_is_system_or_survey)]
    phrase_text = phrase_df["text"].str.strip()
    phrase_counts = phrase_text.value_counts().head(10)
    user_phrases = [{"phrase": str(p), "count": int(c)} for p, c in phrase_counts.items()]

    # --- Real user questions (longer phrases showing actual pain points) ---
    questions_df = phrase_df[phrase_df["text"].str.strip().str.split().str.len() >= 4]
    question_counts = questions_df["text"].str.strip().value_counts().head(15)
    user_questions = [{"phrase": str(p), "count": int(c)} for p, c in question_counts.items()]

    # --- Subcategories breakdown (only for category dimension) ---
    subcategories_breakdown = []
    if dimension == "category" and "categoria_yaml" in filtered.columns:
        skip_subs = {"Encuesta", "Saludos", "Sin Sentido", "Retroalimentación", "Sin Clasificar"}
        sub_data = filtered[
            filtered["categoria_yaml"].notna() & (~filtered["categoria_yaml"].isin(skip_subs))
        ]
        sub_counts = (
            sub_data.groupby("categoria_yaml")["thread_id"]
            .nunique()
            .sort_values(ascending=False)
        )
        for sub_name, sub_cnt in sub_counts.items():
            sub_filtered = sub_data[sub_data["categoria_yaml"] == sub_name]
            sub_threads = set(sub_filtered["thread_id"].unique())
            sub_pct = round(sub_cnt / n * 100, 1) if n else 0.0

            # Sub: user questions (>= 3 words, no noise/system)
            sub_phrase_df = sub_filtered[sub_filtered["text"].str.strip().str.len() >= 4]
            sub_phrase_df = sub_phrase_df[~sub_phrase_df["text"].apply(_is_noise)]
            sub_phrase_df = sub_phrase_df[~sub_phrase_df["text"].apply(_is_system_or_survey)]
            sub_q_df = sub_phrase_df[sub_phrase_df["text"].str.strip().str.split().str.len() >= 3]
            sub_q_counts = sub_q_df["text"].str.strip().value_counts().head(10)
            sub_questions = [{"phrase": str(p), "count": int(c)} for p, c in sub_q_counts.items()]

            # Sub: failures
            sub_fail_threads = sub_threads & failure_threads
            sub_fail_count = len(sub_fail_threads)
            sub_fail_pct = round(sub_fail_count / len(sub_threads) * 100, 1) if sub_threads else 0.0

            # Sub: unanswered questions from failed threads
            sub_unanswered = []
            if sub_fail_threads:
                sub_fail_msgs = sub_filtered[sub_filtered["thread_id"].isin(sub_fail_threads)]
                sub_fail_msgs = sub_fail_msgs[sub_fail_msgs["text"].str.strip().str.len() >= 4]
                sub_fail_msgs = sub_fail_msgs[~sub_fail_msgs["text"].apply(_is_system_or_survey)]
                sub_fail_msgs = sub_fail_msgs[~sub_fail_msgs["text"].apply(_is_noise)]
                sub_fail_msgs = sub_fail_msgs[sub_fail_msgs["text"].str.strip().str.split().str.len() >= 3]
                sub_unanswered_counts = sub_fail_msgs["text"].str.strip().value_counts().head(10)
                sub_unanswered = [{"phrase": str(p), "count": int(c)} for p, c in sub_unanswered_counts.items()]

            subcategories_breakdown.append({
                "name": str(sub_name),
                "conversations": int(sub_cnt),
                "pct": sub_pct,
                "user_questions": sub_questions,
                "failures": sub_fail_count,
                "failure_pct": sub_fail_pct,
                "unanswered_questions": sub_unanswered,
            })

    # --- Unanswered user questions (from failed threads, no survey/feedback noise) ---
    unanswered_questions = []
    if failures_df is not None and not failures_df.empty:
        dim_fail_threads = dim_threads & failure_threads
        fail_msgs = filtered[filtered["thread_id"].isin(dim_fail_threads)].copy()
        fail_msgs = fail_msgs[fail_msgs["text"].str.strip().str.len() >= 4]
        fail_msgs = fail_msgs[~fail_msgs["text"].apply(_is_system_or_survey)]
        fail_msgs = fail_msgs[~fail_msgs["text"].apply(_is_noise)]
        fail_msgs = fail_msgs[fail_msgs["text"].str.strip().str.split().str.len() >= 3]
        fail_phrase_counts = fail_msgs["text"].str.strip().value_counts().head(50)
        unanswered_questions = [
            {"phrase": str(p), "count": int(c)} for p, c in fail_phrase_counts.items()
        ]

    # --- Outcome metrics via _enrich_subcategory ---
    outcomes = _enrich_subcategory(
        value, dim_threads, hdf,
        referral_threads, referral_channel_map,
        failure_threads, failure_criteria_map,
        survey_useful, survey_not_useful,
        filter_col=filter_col,
    )

    # --- Failures detail ---
    failure_examples = []
    if failures_df is not None and not failures_df.empty:
        dim_failures = failures_df[failures_df["thread_id"].isin(dim_threads)]
        for _, row in dim_failures.sort_values("fecha", ascending=False).head(15).iterrows():
            fecha = row.get("fecha", "")
            if pd.notna(fecha) and hasattr(fecha, "strftime"):
                fecha = fecha.strftime("%Y-%m-%d")
            else:
                fecha = str(fecha)[:10] if pd.notna(fecha) else ""
            failure_examples.append({
                "thread_id": str(row.get("thread_id", "")),
                "fecha": fecha,
                "last_user_message": str(row.get("last_user_message", ""))[:200],
                "last_ai_message": str(row.get("last_ai_message", ""))[:200],
                "criteria": str(row.get("criteria", "")),
            })

    # --- Sample threads (most recent 50) ---
    sample_data = filtered.sort_values("fecha", ascending=False).drop_duplicates("thread_id").head(50)
    sample_threads = []
    for _, row in sample_data.iterrows():
        fecha = row.get("fecha", "")
        if pd.notna(fecha) and hasattr(fecha, "strftime"):
            fecha = fecha.strftime("%Y-%m-%d")
        else:
            fecha = str(fecha)[:10] if pd.notna(fecha) else ""
        sample_threads.append({
            "thread_id": str(row["thread_id"]),
            "fecha": fecha,
            "first_message": str(row.get("text", ""))[:200],
            "sentiment": str(row.get("sentiment", "neutral")),
        })

    return {
        "dimension": dimension,
        "value": value,
        "parent": parent,
        "total_conversations": n,
        "total_messages": total_msgs,
        "kpis": kpis,
        "sentiments": sent_counts,
        "top_items": top_items,
        "user_phrases": user_phrases,
        "user_questions": user_questions,
        "subcategories": subcategories_breakdown,
        "unanswered_questions": unanswered_questions,
        "failures_detail": {
            "total": outcomes["bot_failures"]["total"],
            "pct": outcomes["bot_failures"]["pct"],
            "by_criteria": outcomes["bot_failures"]["by_criteria"],
            "examples": failure_examples,
        },
        "redirections": outcomes["redirections"],
        "utility": outcomes["utility"],
        "intent_position": outcomes["intent_position"],
        "advisor_escalation": outcomes["advisor_escalation"],
        "underlying_intents": outcomes.get("underlying_intents", []),
        "sample_threads": sample_threads,
    }
