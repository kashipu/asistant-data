import pandas as pd

# Macros considered noise — excluded from FAQs
NOISE_MACROS = {'Sin Clasificar'}

def get_faqs_by_category(df: pd.DataFrame, top_n: int = 5):
    """
    Returns the most frequent exact human phrases per subcategory, grouped by macro.
    Response shape:
    {
      "Transferencias": {
        "Envío de Dinero": [{"phrase": "...", "count": X}, ...],
        ...
      },
      ...
    }
    """
    if df is None or df.empty:
        return {}

    if 'categoria_yaml' not in df.columns:
        return {}

    human_df = df[
        (df['type'] == 'human') &
        (df['text'].str.strip() != '') &
        (df['categoria_yaml'].notnull())
    ].copy()

    # Exclude noise macros if macro_yaml column exists
    if 'macro_yaml' in human_df.columns:
        human_df = human_df[~human_df['macro_yaml'].isin(NOISE_MACROS)]
    else:
        # Fallback: treat categoria_yaml as macro
        human_df['macro_yaml'] = human_df['categoria_yaml']

    if human_df.empty:
        return {}

    human_df['text_clean'] = human_df['text'].str.strip()

    # Count per (macro, subcategory, phrase)
    counts = (
        human_df
        .groupby(['macro_yaml', 'categoria_yaml', 'text_clean'])
        .size()
        .reset_index(name='count')
    )
    counts = counts.sort_values(['macro_yaml', 'categoria_yaml', 'count'], ascending=[True, True, False])

    # Top N per subcategory
    top_per_sub = counts.groupby(['macro_yaml', 'categoria_yaml']).head(top_n).copy()

    # Sort top N by phrase length descending (longer = more descriptive test case)
    top_per_sub['phrase_len'] = top_per_sub['text_clean'].str.len()
    top_per_sub = top_per_sub.sort_values(
        ['macro_yaml', 'categoria_yaml', 'phrase_len'],
        ascending=[True, True, False]
    )

    # Build nested result: { macro: { subcategoria: [phrases] } }
    result = {}
    for (macro, sub), group in top_per_sub.groupby(['macro_yaml', 'categoria_yaml']):
        phrases = (
            group[['text_clean', 'count']]
            .rename(columns={'text_clean': 'phrase'})
            .to_dict(orient='records')
        )
        if macro not in result:
            result[macro] = {}
        result[macro][sub] = phrases

    return result
