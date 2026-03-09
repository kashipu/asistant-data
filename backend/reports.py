import pandas as pd

def get_volume_report(df: pd.DataFrame):
    """
    Returns volume stats for human messages grouped by macro, category and product.
    """
    if df is None or df.empty:
        return []
    
    human_df = df[df['type'] == 'human'].copy()
    if human_df.empty:
        return []
    
    # Ensure columns exist and fill NAs for grouping
    for col in ['macro_yaml', 'categoria_yaml', 'product_yaml']:
        if col not in human_df.columns:
            human_df[col] = "N/A"
    
    human_df['macro_yaml'] = human_df['macro_yaml'].fillna('Sin Clasificar')
    human_df['categoria_yaml'] = human_df['categoria_yaml'].fillna('Sin Categoría')
    human_df['product_yaml'] = human_df['product_yaml'].fillna('N/A')
    
    group_cols = ['macro_yaml', 'categoria_yaml', 'product_yaml']
    volumes = human_df.groupby(group_cols).size().reset_index(name='count')
    
    total_human = len(human_df)
    volumes['percentage'] = (volumes['count'] / total_human * 100).round(2)
    
    # Sort by count descending
    volumes = volumes.sort_values('count', ascending=False)
    
    return volumes.to_dict(orient='records')

def get_survey_utility_analysis(df: pd.DataFrame):
    """
    Correlates survey results with thread categories to find friction points.
    Identifies WHERE the chatbot is being useful or not.
    """
    if df is None or df.empty:
        return []

    # 1. Identify survey messages and their result
    if 'text' not in df.columns:
        return []
        
    survey_mask = df['text'].str.contains(r'\[survey\]', case=False, na=False)
    survey_df = df[survey_mask].copy()
    
    if survey_df.empty:
        return []

    def classify_survey(text):
        text = str(text).lower()
        if "no me fue útil" in text: return "not_useful"
        if "me fue útil" in text: return "useful"
        return "unknown"

    survey_df['status'] = survey_df['text'].apply(classify_survey)
    survey_df = survey_df[survey_df['status'] != "unknown"]

    if survey_df.empty:
        return []

    # 2. Get the predominant category for each thread with a survey
    survey_threads = survey_df['thread_id'].unique()
    
    thread_cats = {}
    human_mask = (df['thread_id'].isin(survey_threads)) & (df['type'] == 'human')
    relevant_df = df[human_mask].copy()
    
    if not relevant_df.empty:
        # Pre-fill NAs for modes
        for col in ['categoria_yaml', 'macro_yaml', 'product_yaml']:
            if col not in relevant_df.columns:
                relevant_df[col] = "N/A"
            relevant_df[col] = relevant_df[col].fillna("N/A")

        grouped = relevant_df.groupby('thread_id')
        for tid, group in grouped:
            cat_mode = group['categoria_yaml'].mode()
            macro_mode = group['macro_yaml'].mode()
            prod_mode = group['product_yaml'].mode()
            
            thread_cats[tid] = {
                "categoria": cat_mode.iloc[0] if not cat_mode.empty else "Sin Categoría",
                "macro": macro_mode.iloc[0] if not macro_mode.empty else "Sin Clasificar",
                "producto": prod_mode.iloc[0] if not prod_mode.empty else "N/A"
            }

    # 3. Join survey status with thread categories
    results = []
    for _, row in survey_df.iterrows():
        tid = row['thread_id']
        cats = thread_cats.get(tid, {"categoria": "Sin Categoría", "macro": "Sin Clasificar", "producto": "N/A"})
        results.append({
            "thread_id": tid,
            "status": row['status'],
            "macro": cats['macro'],
            "categoria": cats['categoria'],
            "producto": cats['producto']
        })

    if not results:
        return []
        
    res_df = pd.DataFrame(results)
    
    # 4. Aggregate: Useful vs Not Useful per Category/Product
    pivot = res_df.groupby(['macro', 'categoria', 'producto', 'status']).size().unstack(fill_value=0)
    
    # Ensure columns exist
    for col in ['useful', 'not_useful']:
        if col not in pivot.columns:
            pivot[col] = 0
            
    pivot['total'] = pivot['useful'] + pivot['not_useful']
    pivot['utility_rate'] = (pivot['useful'] / pivot['total'] * 100).round(2)
    
    pivot = pivot.reset_index().sort_values('total', ascending=False)
    
    return pivot.to_dict(orient='records')
