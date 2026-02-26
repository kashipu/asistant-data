
import pandas as pd

NOISE_MACROS = {'Sin Clasificar'}

def get_categorical_analysis(df: pd.DataFrame):
    """
    Returns data for categorical charts.
    Uses categoria_yaml + macro_yaml (from DB/YAML) as the source of truth.
    """
    if df is None or df.empty:
        return {"top_intents": {}, "top_products": {}, "sentiment_distribution": {}, "sentiment_by_intent": {}}

    # Work only with human messages that have a category
    has_cat = 'categoria_yaml' in df.columns and 'macro_yaml' in df.columns
    if has_cat:
        human_df = df[
            (df['type'] == 'human') &
            df['categoria_yaml'].notna() &
            ~df['macro_yaml'].isin(NOISE_MACROS)
        ].copy()
        cat_col = 'categoria_yaml'
    else:
        # Fallback to intencion if YAML columns missing
        human_df = df[df['type'] == 'human'].copy()
        cat_col = 'intencion'

    # Top subcategories (up to 20)
    top_intents = human_df[cat_col].value_counts().head(20).to_dict()

    # Top macros
    top_macros = {}
    if has_cat:
        top_macros = human_df['macro_yaml'].value_counts().head(10).to_dict()

    # Top Products
    noise = ['', 'ninguno', 'nan', 'none', 'desconocido']
    valid_products_df = df[~df['product_type'].str.lower().isin(noise)]
    top_products = valid_products_df['product_type'].value_counts().head(10).to_dict()

    # Sentiment Distribution (all messages)
    sentiment_dist = df['sentiment'].value_counts().to_dict()

    # Cross: Sentiment x Subcategory (top 10 subcategories)
    top_10_list = human_df[cat_col].value_counts().head(10).index
    cross_df = human_df[human_df[cat_col].isin(top_10_list)]
    sentiment_x_intent = cross_df.groupby([cat_col, 'sentiment']).size().unstack(fill_value=0)
    sentiment_x_intent_data = sentiment_x_intent.to_dict(orient='index')

    return {
        "top_intents": top_intents,
        "top_macros": top_macros,
        "top_products": top_products,
        "sentiment_distribution": sentiment_dist,
        "sentiment_by_intent": sentiment_x_intent_data,
    }
