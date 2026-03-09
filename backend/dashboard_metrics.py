import pandas as pd
from .referrals import detect_referrals
from .failures import get_failures_cached


def get_extended_funnel(df: pd.DataFrame, start_date: str = None, end_date: str = None):
    """
    Calculates a comprehensive metrics breakdown for the dashboard.
    Each metric has: count, pct, base (what it's calculated from), and explanation.
    """
    if df is None or df.empty:
        return {"metrics": [], "waste_by_category": []}

    # 1. Date Filtering
    if start_date or end_date:
        if 'fecha' in df.columns:
            mask = pd.Series(True, index=df.index)
            if start_date:
                mask &= (df['fecha'] >= pd.to_datetime(start_date))
            if end_date:
                mask &= (df['fecha'] <= pd.to_datetime(end_date))
            df = df[mask].copy()

    if df.empty:
        return {"metrics": [], "waste_by_category": []}

    # ---------------------------------------------------------------
    # COMPUTATIONS
    # ---------------------------------------------------------------
    total_threads = df['thread_id'].nunique()
    total_messages = len(df)

    # Greeting-only threads: threads where ALL human messages are ≤ 5 words
    human_df = df[df['type'] == 'human']
    human_word_counts = human_df.groupby('thread_id')['text'].apply(
        lambda texts: all(len(str(t).split()) <= 5 for t in texts)
    )
    greeting_only_ids = set(human_word_counts[human_word_counts].index)
    greeting_only = len(greeting_only_ids)

    # Active threads: threads with > 2 human messages (excludes greeting-only)
    human_counts = human_df.groupby('thread_id').size()
    active_ids = set(human_counts[human_counts > 2].index) - greeting_only_ids
    total_active = len(active_ids)

    # Referrals (among active)
    referrals_df = detect_referrals(df)
    ref_threads = set(referrals_df['thread_id'].unique()) if not referrals_df.empty else set()
    active_referred = ref_threads & active_ids
    total_referred = len(active_referred)

    # Self-service (active and NOT referred)
    self_service_ids = active_ids - ref_threads
    self_service_count = len(self_service_ids)

    # Surveys
    s_mask = df['text'].str.contains(r'\[survey\]', case=False, na=False)
    s_df = df[s_mask].copy()
    surveyed_threads = set(s_df['thread_id'].unique())
    total_surveys = len(surveyed_threads)

    t_low = s_df['text'].str.lower()
    is_not = t_low.str.contains("no me fue útil")
    is_use = t_low.str.contains("me fue útil") & ~is_not

    useful_threads = set(s_df[is_use]['thread_id'].unique())
    not_useful_threads = set(s_df[is_not]['thread_id'].unique())
    answered_threads = useful_threads | not_useful_threads

    total_useful = len(useful_threads)
    total_not_useful = len(not_useful_threads)
    total_answered = len(answered_threads)
    total_unanswered = total_surveys - total_answered

    # Bot failures (among active)
    failures_df = get_failures_cached(df)
    failed_threads = set(failures_df['thread_id']) if failures_df is not None and not failures_df.empty else set()
    active_failed = failed_threads & active_ids
    total_failures = len(active_failed)

    # Referral channel breakdown (among active referred)
    CHANNEL_KWS = {
        "Servilínea": ["servilínea", "servilinea", "línea de atención", "linea de atencion", "llamar al", "marcar al"],
        "Digital": ["banca móvil", "banca movil", "banca virtual", "portal", "página web", "app bolívar", "descarga la app"],
        "Oficina": ["oficina", "sucursal", "punto físico"],
    }
    channel_counts: dict[str, int] = {}
    if not referrals_df.empty and "referral_response" in referrals_df.columns:
        for _, row in referrals_df[referrals_df["thread_id"].isin(active_referred)].iterrows():
            txt = str(row.get("referral_response", "")).lower()
            ch = "Otro"
            for channel, kws in CHANNEL_KWS.items():
                if any(kw in txt for kw in kws):
                    ch = channel
                    break
            channel_counts[ch] = channel_counts.get(ch, 0) + 1

    # Failure criteria breakdown (among active failed)
    criteria_counts: dict[str, int] = {}
    if failures_df is not None and not failures_df.empty and "criteria" in failures_df.columns:
        for _, row in failures_df[failures_df["thread_id"].isin(active_failed)].iterrows():
            for crit in str(row.get("criteria", "")).split(","):
                crit = crit.strip()
                if crit:
                    criteria_counts[crit] = criteria_counts.get(crit, 0) + 1

    # ---------------------------------------------------------------
    # PRODUCT vs GENERAL (among active)
    # ---------------------------------------------------------------
    product_thread_ids: set = set()
    if 'product_yaml' in df.columns:
        prod_df = df[(df['type'] == 'human') & df['thread_id'].isin(active_ids)]
        prod_df = prod_df[prod_df['product_yaml'].notna() & (prod_df['product_yaml'] != '') & (prod_df['product_yaml'] != 'Sin Producto')]
        product_thread_ids = set(prod_df['thread_id'].unique())
    total_with_product = len(product_thread_ids & active_ids)
    total_general = total_active - total_with_product

    # ---------------------------------------------------------------
    # CORRELATIONS
    # ---------------------------------------------------------------
    # Referred + bot failure
    referred_and_failed = active_referred & active_failed
    total_referred_failed = len(referred_and_failed)

    # Self-service + useful survey
    self_service_useful = self_service_ids & useful_threads
    total_ss_useful = len(self_service_useful)

    # Not useful + bot failure
    not_useful_and_failed = not_useful_threads & active_failed
    total_nu_failed = len(not_useful_and_failed)

    # Failures that ended in referral
    failed_and_referred = active_failed & active_referred
    total_failed_referred = len(failed_and_referred)

    # Value waste: not useful AND referred
    waste_threads = not_useful_threads & ref_threads
    total_waste = len(waste_threads)

    # ---------------------------------------------------------------
    # METRICS — ordered as user requested
    # ---------------------------------------------------------------
    def pct(n, base):
        return round(n / base * 100, 1) if base > 0 else 0.0

    metrics = [
        {
            "id": "total",
            "label": "Total Conversaciones",
            "count": total_threads,
            "pct": 100.0,
            "base_label": "Base 100%",
            "explanation": f"Total bruto de hilos de chat iniciados. {total_messages:,} mensajes en total.",
            "color": "blue",
        },
        {
            "id": "greeting_only",
            "label": "Solo Saludo",
            "count": greeting_only,
            "pct": pct(greeting_only, total_threads),
            "base_label": f"del total ({total_threads:,})",
            "explanation": "Conversaciones donde todos los mensajes del usuario tienen 5 palabras o menos (saludos, 'ok', 'gracias'). No representan una necesidad real.",
            "color": "gray",
        },
        {
            "id": "active",
            "label": "Conversaciones Activas",
            "count": total_active,
            "pct": pct(total_active, total_threads),
            "base_label": f"del total ({total_threads:,})",
            "explanation": "Hilos con más de 2 mensajes del usuario, excluyendo los de solo saludo. Mide interés real.",
            "color": "indigo",
        },
        {
            "id": "self_service",
            "label": "Auto-servicio",
            "count": self_service_count,
            "pct": pct(self_service_count, total_active),
            "base_label": f"de activas ({total_active:,})",
            "explanation": "Conversaciones activas resueltas sin escalar a humanos (sin redirección a Servilínea, oficina o canal digital).",
            "color": "emerald",
            "correlation": {
                "label": "Confirmadas útiles por encuesta",
                "count": total_ss_useful,
                "pct": pct(total_ss_useful, self_service_count),
            } if self_service_count > 0 else None,
        },
        {
            "id": "referred",
            "label": "Redirigidas",
            "count": total_referred,
            "pct": pct(total_referred, total_active),
            "base_label": f"de activas ({total_active:,})",
            "explanation": "Conversaciones activas donde la IA redirigió al usuario a Servilínea, oficina u otro canal.",
            "color": "orange",
            "breakdown": [{"label": k, "count": v} for k, v in sorted(channel_counts.items(), key=lambda x: -x[1])],
            "correlation": {
                "label": "Redirigidas por fallo de la IA",
                "count": total_referred_failed,
                "pct": pct(total_referred_failed, total_referred),
            } if total_referred > 0 else None,
        },
        {
            "id": "surveyed",
            "label": "Encuestadas",
            "count": total_surveys,
            "pct": pct(total_surveys, total_threads),
            "base_label": f"del total ({total_threads:,})",
            "explanation": "Usuarios que alcanzaron el bloque de encuesta de satisfacción.",
            "color": "purple",
        },
        {
            "id": "answered",
            "label": "Encuestas Contestadas",
            "count": total_answered,
            "pct": pct(total_answered, total_surveys),
            "base_label": f"de encuestadas ({total_surveys:,})",
            "explanation": f"Encuestas con respuesta (útil o no útil). {total_unanswered:,} encuestas fueron ignoradas por el usuario.",
            "color": "violet",
        },
        {
            "id": "useful",
            "label": "Información Útil",
            "count": total_useful,
            "pct": pct(total_useful, total_answered),
            "base_label": f"de contestadas ({total_answered:,})",
            "explanation": "Calificadas como 'Me fue útil'. Indica que la IA resolvió la necesidad.",
            "color": "green",
        },
        {
            "id": "not_useful",
            "label": "Información No Útil",
            "count": total_not_useful,
            "pct": pct(total_not_useful, total_answered),
            "base_label": f"de contestadas ({total_answered:,})",
            "explanation": "Calificadas como 'No me fue útil'. La IA no resolvió la necesidad del usuario.",
            "color": "rose",
            "correlation": {
                "label": "También detectadas como fallo IA",
                "count": total_nu_failed,
                "pct": pct(total_nu_failed, total_not_useful),
            } if total_not_useful > 0 else None,
        },
        {
            "id": "failures",
            "label": "Fallos de la IA",
            "count": total_failures,
            "pct": pct(total_failures, total_active),
            "base_label": f"de activas ({total_active:,})",
            "explanation": "Conversaciones activas donde la IA mostró incapacidad, el usuario repitió su pregunta, o el sentimiento fue predominantemente negativo.",
            "color": "red",
            "breakdown": [{"label": k, "count": v} for k, v in sorted(criteria_counts.items(), key=lambda x: -x[1])],
            "correlation": {
                "label": "Terminaron en redirección",
                "count": total_failed_referred,
                "pct": pct(total_failed_referred, total_failures),
            } if total_failures > 0 else None,
        },
        {
            "id": "waste",
            "label": "Gasto de Valor",
            "count": total_waste,
            "pct": pct(total_waste, total_threads),
            "base_label": f"del total ({total_threads:,})",
            "explanation": "Conversaciones calificadas como 'no útil' Y redirigidas. Doble fallo: la IA no resolvió y escaló al usuario.",
            "color": "red",
        },
        {
            "id": "referred_failed",
            "label": "Redirigidas por Fallo IA",
            "count": total_referred_failed,
            "pct": pct(total_referred_failed, total_active),
            "base_label": f"de activas ({total_active:,})",
            "explanation": "Conversaciones activas donde la IA falló Y redirigió al usuario a otro canal. Indica que la redirección fue causada por incapacidad del bot.",
            "color": "red",
            "correlation": {
                "label": f"del total de redirigidas ({total_referred:,})",
                "count": total_referred_failed,
                "pct": pct(total_referred_failed, total_referred),
            } if total_referred > 0 else None,
        },
        {
            "id": "with_product",
            "label": "Sobre un Producto",
            "count": total_with_product,
            "pct": pct(total_with_product, total_active),
            "base_label": f"de activas ({total_active:,})",
            "explanation": "Conversaciones activas donde el usuario preguntó sobre un producto bancario específico (tarjeta, crédito, cuenta, etc.).",
            "color": "emerald",
        },
        {
            "id": "general",
            "label": "Consultas Generales",
            "count": total_general,
            "pct": pct(total_general, total_active),
            "base_label": f"de activas ({total_active:,})",
            "explanation": "Conversaciones activas sin producto específico identificado. Incluye consultas generales, saludos extendidos, o temas no relacionados a productos.",
            "color": "gray",
        },
    ]

    # ---------------------------------------------------------------
    # WASTE BY CATEGORY (unchanged)
    # ---------------------------------------------------------------
    waste_by_category = []
    if total_waste > 0 and 'categoria_yaml' in df.columns:
        waste_df = df[df['thread_id'].isin(waste_threads)]
        cat_map = waste_df[waste_df['type'] == 'human'].groupby('thread_id')['categoria_yaml'].first().to_dict()
        counts = pd.Series(list(cat_map.values())).value_counts().reset_index()
        counts.columns = ['category', 'count']
        for _, row in counts.head(10).iterrows():
            waste_by_category.append({
                "category": row['category'],
                "count": int(row['count']),
                "pct_of_waste": round(row['count'] / total_waste * 100, 1)
            })

    return {
        "metrics": metrics,
        "waste_by_category": waste_by_category,
    }
