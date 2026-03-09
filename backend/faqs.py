import pandas as pd
import re
import unicodedata

# Macros considered noise — excluded from FAQs
NOISE_MACROS = {'Sin Clasificar'}

# Individual noise tokens — if a phrase is composed ENTIRELY of these words
# (in any combination), it's noise.  e.g. "Hola buenas tardes" → all tokens
# are noise → filtered out.  "Hola necesito un CDT" → "necesito","un","cdt"
# are NOT noise tokens → phrase is kept.
_NOISE_TOKENS = {
    # greetings
    'hola', 'buenas', 'buenos', 'buen', 'dias', 'dia', 'tardes', 'noches',
    'saludos', 'hey', 'hi', 'hello',
    # affirmative / filler
    'si', 'no', 'ok', 'okey', 'vale', 'listo', 'entendido', 'perfecto',
    'dale', 'claro', 'correcto', 'exacto', 'ya', 'bueno', 'ajam', 'aja',
    'super', 'genial', 'excelente', 'obvio', 'bien',
    # thanks / farewell
    'gracias', 'muchas', 'porfa', 'por', 'favor', 'igualmente',
    'chao', 'adios', 'hasta', 'luego', 'bye', 'nos', 'vemos',
    # roles (not intents)
    'asesor', 'agente',
}


def _normalize(text: str) -> str:
    """Lowercase + strip accents for noise comparison."""
    text = text.lower().strip()
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    return text


def _is_noise(text: str) -> bool:
    """Returns True if the phrase is composed entirely of noise tokens."""
    norm = _normalize(text)
    # Remove non-alphanumeric (punctuation, emojis)
    norm = re.sub(r'[^a-z0-9\s]', '', norm)
    tokens = norm.split()
    if not tokens:
        return True
    return all(t in _NOISE_TOKENS for t in tokens)


def get_faqs_by_category(df: pd.DataFrame, top_n: int = 5):
    """
    Returns the most frequent exact human phrases per subcategory, grouped by macro.
    Filters out noise phrases (greetings, fillers) that don't represent real intents.
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

    # Filter out noise phrases (greetings, fillers, thanks — even combined)
    human_df = human_df[~human_df['text'].apply(_is_noise)]
    # Also filter phrases shorter than 4 characters (e.g., "si", "no", "ok")
    human_df = human_df[human_df['text'].str.strip().str.len() >= 4]

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
