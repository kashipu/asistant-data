import pandas as pd
from typing import Dict, Any
from .engine import DataEngine

def get_qualitative_insights(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Returns high-level qualitative insights for the General Cards section.
    """
    if df.empty:
        return {}
    
    # 1. Mensajes IA vs Humano
    type_counts = df['type'].value_counts()
    human_msgs = int(type_counts.get('human', 0))
    ai_msgs = int(type_counts.get('ai', 0))
    total_msgs = human_msgs + ai_msgs
    
    human_pct = round((human_msgs / total_msgs * 100) if total_msgs > 0 else 0, 1)
    ai_pct = round((ai_msgs / total_msgs * 100) if total_msgs > 0 else 0, 1)

    # 2. Conversaciones Únicas
    unique_threads = int(df['thread_id'].nunique())

    # 3. Horas de más consulta
    peak_hours = []
    if 'hora' in df.columns and not df['hora'].dropna().empty:
        # Get top 3 hours for messages
        # Convert to int to avoid numpy types
        hour_counts = df['hora'].dropna().astype(int).value_counts().head(3)
        peak_hours = [{"hour": int(h), "count": int(c)} for h, c in hour_counts.items()]

    # 4. Resumen General (Top Categoría, Sentimiento, Producto)
    excluded_terms = ['encuesta', 'uncategorized', 'sin intención clara', 'sin intencion clara', 'ninguno', 'nan', 'none']
    
    top_categories = []
    cat_col = 'categoria_yaml' if 'categoria_yaml' in df.columns else 'intencion'
    if cat_col in df.columns and not df[cat_col].dropna().empty:
        cats = df[cat_col].dropna()
        cats = cats[~cats.str.lower().isin(excluded_terms)]
        if not cats.empty:
            cat_counts = cats.value_counts().head(3)
            top_categories = [{"name": str(k), "count": int(v)} for k, v in cat_counts.items()]

    top_sentiments = []
    if 'sentiment' in df.columns and not df['sentiment'].dropna().empty:
        sent_counts = df['sentiment'].value_counts()
        total_sent = sent_counts.sum()
        top_sentiments = [{"name": str(k), "pct": round(v / total_sent * 100, 1)} for k, v in sent_counts.items()]

    top_products = []
    prod_col = 'product_yaml' if 'product_yaml' in df.columns else 'product_type'
    if prod_col in df.columns and not df[prod_col].dropna().empty:
        prods = df[prod_col].dropna()
        prods = prods[~prods.str.lower().isin(excluded_terms)]
        if not prods.empty:
            prod_counts = prods.value_counts().head(3)
            top_products = [{"name": str(k), "count": int(v)} for k, v in prod_counts.items()]

    # 5. Referidos a Canales (Servilínea)
    engine = DataEngine.get_instance()
    referrals_df = engine.get_referrals()
    total_referrals = len(referrals_df) if referrals_df is not None else 0
    referrals_pct = round((total_referrals / unique_threads * 100) if unique_threads > 0 else 0, 1)

    return {
        "messages": {
            "total": total_msgs,
            "human": human_msgs,
            "ai": ai_msgs,
            "human_pct": human_pct,
            "ai_pct": ai_pct
        },
        "conversations": {
            "total": unique_threads
        },
        "peak_hours": peak_hours,
        "summary": {
            "top_categories": top_categories,
            "top_sentiments": top_sentiments,
            "top_products": top_products
        },
        "referrals": {
            "total": total_referrals,
            "pct": referrals_pct
        }
    }


def get_category_insights(df: pd.DataFrame, category: str) -> Dict[str, Any]:
    """
    Returns deep-dive qualitative insights for a specific category.
    """
    if df.empty:
        return {}

    # Identify category column
    cat_col = 'categoria_yaml' if 'categoria_yaml' in df.columns else 'intencion'
    
    # Filter df by category (case insensitive-ish, or exact match)
    cat_df = df[df[cat_col].astype(str).str.strip().str.lower() == category.strip().lower()].copy()

    if cat_df.empty:
        return {
            "category_name": category,
            "error": "No data found for this category"
        }

    # 1. Proporción humana vs total en esta categoría
    type_counts = cat_df['type'].value_counts()
    human_msgs = int(type_counts.get('human', 0))
    ai_msgs = int(type_counts.get('ai', 0))
    total_msgs = human_msgs + ai_msgs
    human_pct = round((human_msgs / total_msgs * 100) if total_msgs > 0 else 0, 1)

    # 2. Mensajes más repetidos (Humanos y IA)
    def get_top_repeated(sub_df, limit=5):
        res = []
        if not sub_df.empty:
            clean_texts = sub_df['text'].str.strip().str.lower()
            msg_counts = clean_texts.value_counts().head(limit)
            for msg, count in msg_counts.items():
                matching_rows = sub_df[sub_df['text'].str.strip().str.lower() == msg]
                original_match = matching_rows['text'].iloc[0]
                thread_id = matching_rows['thread_id'].iloc[0] if 'thread_id' in matching_rows.columns else None
                if count > 1: # Solo repetidos
                    res.append({"text": original_match, "count": int(count), "thread_id": str(thread_id)})
        return res

    human_df = cat_df[cat_df['type'] == 'human']
    ai_df = cat_df[cat_df['type'] == 'ai']
    
    frequent_messages_human = get_top_repeated(human_df)
    frequent_messages_ai = get_top_repeated(ai_df)

    # 3. Subcategorías y Productos
    # Si 'category' es la macro, agrupamos por subcategoría. Si es la sub, tal vez la macro.
    # Usaremos 'categoria_yaml' como subcategoría y 'product_yaml' como producto
    subcategories = []
    if 'categoria_yaml' in cat_df.columns:
        subcat_counts = cat_df['categoria_yaml'].value_counts().head(5)
        subcategories = [{"name": str(k), "count": int(v)} for k, v in subcat_counts.items()]

    products = []
    prod_col = 'product_yaml' if 'product_yaml' in cat_df.columns else 'product_type'
    if prod_col in cat_df.columns:
        prod_counts = cat_df[prod_col].value_counts().head(5)
        products = [{"name": str(k), "count": int(v)} for k, v in prod_counts.items()]

    # 4. Redirecciones a Servilínea
    engine = DataEngine.get_instance()
    referrals_df = engine.get_referrals()
    category_referrals = 0
    if referrals_df is not None and not referrals_df.empty:
        # Filtrar referrals por thread_ids de esta categoría
        cat_thread_ids = set(cat_df['thread_id'].unique())
        cat_refs = referrals_df[referrals_df['thread_id'].isin(cat_thread_ids)]
        category_referrals = len(cat_refs)

    return {
        "category_name": category,
        "messages": {
            "total": total_msgs,
            "human": human_msgs,
            "human_pct": human_pct
        },
        "frequent_messages": frequent_messages_human,
        "frequent_messages_ai": frequent_messages_ai,
        "distribution": {
            "subcategories": subcategories,
            "products": products
        },
        "referrals": {
            "total": category_referrals
        }
    }
