import time
import sys
import pandas as pd
import os
import sqlite3
import yaml
import re
import unicodedata
# try:
#     from pysentimiento import create_analyzer
#     HAS_PYSENTIMIENTO = True
# except ImportError:
HAS_PYSENTIMIENTO = False

import json
import concurrent.futures
from functools import partial

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "data-asistente.csv")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chat_data.db")
YAML_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "categorias.yml")
PRODUCTOS_YAML_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "productos.yml")

# Homologation table: CSV intencion value → (categoria_yaml, macro_yaml)
# Keys are lowercase. Values must match exact names in categorias.yml.
INTENCION_HOMOLOGACION = {
    'saludo / sin intencion clara':                 ('Saludos',                          'Sin Clasificar'),
    'consulta general sobre productos':             ('Solicitud de Información',          'Información'),
    '[evento de retroalimentacion]':                ('Retroalimentación',                 'Sin Clasificar'),
    'retroalimentacion':                            ('Retroalimentación',                 'Sin Clasificar'),
    'problemas con transacciones no monetarias':    ('Funcionalidades Bloqueadas',        'App y Canales'),
    'problemas con transacciones monetarias':       ('Transferencia Fallida / No Llegó',  'Transferencias'),
    'ajustes de seguridad':                         ('Claves y Contraseñas',              'Seguridad y Accesos'),
    'consulta sobre productos contratados':         ('Productos y Cuentas General',       'Cuentas y Productos'),
    'transacciones no monetarias':                  ('Funcionalidades Bloqueadas',        'App y Canales'),
    'transacciones monetarias':                     ('Consulta de Pagos',                 'Pagos'),
    'solicitud de interaccion humana':              ('Canales Físicos / Asesor',          'App y Canales'),
    'disponibilidad y acceso a canales':            ('Canales Físicos / Asesor',          'App y Canales'),
    'asesoria comercial':                           ('Asesoría Comercial',                'Información'),
    'cancelacion de productos':                     ('Apertura / Cancelación de Cuenta',  'Cuentas y Productos'),
    'sospecha de fraude':                           ('Fraude y Robo',                     'Seguridad y Accesos'),
    'ubicacion de canales fisicos o asistidos':     ('Canales Físicos / Asesor',          'App y Canales'),
    'pqr':                                          ('PQR',                               'Información'),
    'reexpedicion o entrega de plastico':           ('Consulta de Tarjetas',              'Tarjetas'),
    'fuera de alcance':                             ('Fuera de Alcance',                  'Sin Clasificar'),
    'estado de mora y cobranza':                    ('Cobros e Intereses',                'Créditos y Préstamos'),
    'seguimiento de radicado':                      ('Seguimiento de Radicado',           'Gestión Personal'),
    'centrales de riesgo':                          ('Centrales de Riesgo',               'Gestión Personal'),
}

def _clean_for_nlp(text):
    if pd.isna(text): return ""
    text = str(text).lower()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def _load_categories():
    if not os.path.exists(YAML_PATH):
        return []
    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get('categorias', [])

def _build_product_homologation():
    """
    Reads productos.yml and builds a dict: alias_lowercase → (nombre, macro).
    Used to homologate CSV product_type/product_detail values to canonical names.
    """
    if not os.path.exists(PRODUCTOS_YAML_PATH):
        return {}
    with open(PRODUCTOS_YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    mapping = {}
    for prod in data.get('productos', []):
        nombre = prod.get('nombre', '')
        macro  = prod.get('macro', nombre)
        for alias in prod.get('aliases', []):
            if alias is not None:
                mapping[str(alias).strip().lower()] = (nombre, macro)
        # Also map the canonical name itself
        mapping[nombre.lower()] = (nombre, macro)
    return mapping

def _load_products():
    """Returns list of product dicts from productos.yml."""
    if not os.path.exists(PRODUCTOS_YAML_PATH):
        return []
    with open(PRODUCTOS_YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data.get('productos', [])

def _match_product_nlp(text, products):
    """
    Returns (nombre, macro) for the first product whose palabras_clave match the text.
    Returns (None, None) if no match.
    """
    if not text or not text.strip():
        return None, None
    clean = _clean_for_nlp(text)
    for prod in products:
        nombre = prod.get('nombre', '')
        macro  = prod.get('macro', nombre)
        for kw in prod.get('palabras_clave', []):
            if not kw:
                continue
            kw_clean = _clean_for_nlp(kw)
            if kw_clean and kw_clean in clean:
                return nombre, macro
    return None, None

# Noise keywords that should be categorized as "Saludos" or "Sin Sentido" without review.
# These are applied BEFORE general keyword matching.
NOISE_KEYWORDS = {
    'saludos': ['hola', 'buen dia', 'buenos dias', 'buenas tardes', 'buenas noches', 'saludos', 'hey', 'hi', 'hello'],
    'agradecimiento': ['gracias', 'muchas gracias', 'mil gracias', 'ok', 'vale', 'listo', 'entendido', 'bien gracias', 'perfecto gracias'],
    'despedida': ['chao', 'adios', 'hasta luego', 'nos vemos', 'bye']
}

# Greeting prefixes to strip before categorizing.  Sorted longest-first so
# "hola buenas tardes" is tried before "hola".
_GREETING_PREFIXES = sorted([
    "hola buenas tardes", "hola buenas noches", "hola buenos dias",
    "hola buen dia", "buenas tardes", "buenas noches", "buenos dias",
    "buen dia", "buenas", "hola", "saludos", "que tal", "como estas",
    "hey", "hi", "hello",
], key=len, reverse=True)

# Short replies that should NOT be propagated as real intent.
# These go to Retroalimentación (Sin Clasificar) instead of whatever the
# AI thought the thread was about.
_SHORT_REPLY_KEYWORDS = {
    'si', 'no', 'si por favor', 'no gracias', 'bueno', 'dale', 'ya',
    'claro', 'correcto', 'exacto', 'eso', 'asi es', 'ajam', 'okey',
    'igualmente', 'super', 'genial', 'excelente', 'obvio', 'porfa',
    'aja', 'listo gracias', 'dale gracias', 'buenas noches', 'buenas tardes',
    'buenos dias', 'buen dia', 'buenas',
}


def _strip_greeting_prefix(text_lower: str) -> str:
    """Remove a leading greeting from text to expose the real intent."""
    for prefix in _GREETING_PREFIXES:
        if text_lower.startswith(prefix):
            remainder = text_lower[len(prefix):].lstrip(' ,.:;!?')
            if remainder:  # only strip if there IS something after the greeting
                return remainder
    return text_lower


def _categorize_text(text, categories):
    """
    Returns (categoria_yaml, macro_yaml, requires_review).
    - categoria_yaml: subcategory name matched, or None
    - macro_yaml: macro group of matched category, or None
    - requires_review: 1 if no match found (needs HITL), 0 otherwise
    """
    if not text or not text.strip():
        return None, None, 0

    original_lower = text.lower().strip()

    # Rule 0: Survey responses — [survey] tag means this is an automated survey vote,
    # NOT a real user intent. Must be caught BEFORE keyword matching to prevent
    # "[survey] No me fue útil la información" from matching "Evaluación General".
    if '[survey]' in original_lower:
        return "Encuesta", "Experiencia", 0

    # Rule 1: Very short messages (noise/junk)
    if len(original_lower) < 3 and not original_lower.isdigit():
        return "Sin Sentido", "Sin Clasificar", 0

    # Rule 2: Explicit Noise Keywords (Greetings/Acknowledgements)
    # MUST be exact match to avoid catching "Hola quiero mi saldo" as Saludos
    for cat_name, keywords in NOISE_KEYWORDS.items():
        if original_lower in keywords:
            if cat_name == 'saludos':
                return "Saludos", "Sin Clasificar", 0
            return "Evaluación General", "Experiencia", 0

    # Rule 2b: Short affirmative/negative replies → Retroalimentación
    if original_lower in _SHORT_REPLY_KEYWORDS:
        return "Retroalimentación", "Sin Clasificar", 0

    # Rule 2c: Strip greeting prefix to expose real intent.
    # "hola buenas quiero transferir" → try matching on "quiero transferir"
    stripped = _strip_greeting_prefix(original_lower)

    # Build cleaned versions for NLP matching
    clean = _clean_for_nlp(stripped)
    clean_original = _clean_for_nlp(original_lower)

    # Rule 3: General Keyword Matching
    # Try matching on stripped text first, then original if different
    texts_to_try = [stripped, original_lower] if stripped != original_lower else [original_lower]
    for try_text in texts_to_try:
        try_clean = _clean_for_nlp(try_text)
        for cat in categories:
            nombre = cat.get('nombre', '')
            macro = cat.get('macro', nombre)
            if nombre in ["Saludos", "Sin Sentido", "Encuesta"]:
                continue
            min_len = cat.get('min_len', 1)
            if len(try_text.strip()) < min_len:
                continue
            for kw in cat.get('palabras_clave', []):
                if not kw:
                    continue
                kw_str = str(kw)
                if kw_str.startswith('^') or kw_str.endswith('$'):
                    try:
                        if re.search(kw_str, try_text):
                            return nombre, macro, 0
                    except re.error:
                        pass
                else:
                    kw_clean = _clean_for_nlp(kw_str)
                    if kw_clean and kw_clean in try_clean:
                        return nombre, macro, 0

    # No match → needs human review
    return None, None, 1

def ingest_data():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Data file not found at {DATA_PATH}")

    print("Loading data from CSV...")
    df = pd.read_csv(DATA_PATH, engine='python', on_bad_lines='skip')

    print("Cleaning data...")
    # Fix encoding in text columns
    text_columns = ['text', 'intencion', 'product_type', 'product_detail', 'segment']
    for col in text_columns:
        if col in df.columns:
            def clean_text(x):
                if pd.isna(x): return ""
                s = str(x).strip()
                if s.lower() == 'nan': return ""
                return s

            df[col] = df[col].apply(clean_text)

    # Normalize sentiment values (keep NaN for now — fillna happens after propagation below)
    if 'sentiment' in df.columns:
        df['sentiment'] = df['sentiment'].replace({'negative': 'negativo'})

    # Fill NaNs in critical columns
    fill_values = {
        'product_type': 'ninguno',
        'product_detail': 'ninguno',
        'intencion': 'sin intencion clara',
        'segment': 'desconocido'
    }
    df = df.fillna(fill_values)

    # Parse dates - crucial for SQLite storage
    if 'fecha' in df.columns:
        # Parse flexibly — CSV may have full timestamps like "2026-02-01 21:00:46.674505 UTC"
        df['fecha'] = pd.to_datetime(df['fecha'], utc=True, errors='coerce')
        # Preserve full timestamp as ISO string for precise ordering
        df['timestamp'] = df['fecha'].dt.strftime('%Y-%m-%d %H:%M:%S')
        # Extract hour BEFORE converting to date string (if hora column is missing or empty)
        if 'hora' in df.columns:
            missing_hora = df['hora'].isna() | (df['hora'] == 0)
            if missing_hora.any():
                df.loc[missing_hora, 'hora'] = df.loc[missing_hora, 'fecha'].dt.hour
        # Store as string YYYY-MM-DD for consistency in SQLite
        df['fecha'] = df['fecha'].dt.strftime('%Y-%m-%d')

    # Ensure numeric columns
    numeric_cols = ['hora', 'input_tokens', 'output_tokens']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # Ensure thread_id is string
    if 'thread_id' in df.columns:
        df['thread_id'] = df['thread_id'].astype(str)

    # ---------------------------------------------------------
    # DEDUPLICATION
    # ---------------------------------------------------------
    initial_len = len(df)
    
    # 1. Deduplicate by ID if exists
    if 'id' in df.columns:
        print("Deduplicating by ID...")
        df = df.drop_duplicates(subset=['id'], keep='first')
        
    # 2. Secondary Deduplication by Content (Thread + Text + Time)
    # This handles cases where different IDs were generated for the same event
    print("Deduplicating by content (thread_id, text, type, fecha, hora)...")
    content_cols = [c for c in ['thread_id', 'text', 'type', 'fecha', 'hora'] if c in df.columns]
    if content_cols:
         df = df.drop_duplicates(subset=content_cols, keep='first')
    
    print(f"Removed {initial_len - len(df)} duplicate records total.")
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # STEP 1: PROPAGATE sentiment and intencion from AI rows to human rows via thread_id
    # The AI message in each thread carries intencion and sentiment — not the human rows.
    # ---------------------------------------------------------
    print("Propagating sentiment from AI messages to human messages via thread_id...")
    if 'sentiment' in df.columns and 'thread_id' in df.columns:
        ai_sent_rows = df[(df['type'] == 'ai') & df['sentiment'].notna()]
        thread_sentiment = ai_sent_rows.groupby('thread_id')['sentiment'].agg(lambda x: x.mode()[0])
        human_mask_sent = df['type'] == 'human'
        # Human rows have no sentiment from CSV — propagate from AI of same thread
        df.loc[human_mask_sent, 'sentiment'] = df.loc[human_mask_sent, 'thread_id'].map(thread_sentiment)
        propagated = df.loc[human_mask_sent, 'sentiment'].notna().sum()
        print(f"  Propagated sentiment to {propagated} human messages")

        # Sentiment Analysis Strategy:
        # 1. Use existing CSV sentiment if present
        # 2. If 'human' and no sentiment: Try AI analysis (fast or local)
        # 3. Final fallback: 'neutral'
        if HAS_PYSENTIMIENTO:
            print("  Running AI/NLP fallback for human messages without sentiment (Parallel)...")
            needs_sent_mask = (df['type'] == 'human') & df['sentiment'].isna() & df['text'].notna()
            texts_to_analyze = df.loc[needs_sent_mask, 'text'].tolist()
            indices_to_analyze = df.loc[needs_sent_mask].index.tolist()

            if texts_to_analyze:
                print(f"  Analyzing {len(texts_to_analyze)} texts with pysentimiento (Fast Analyzer)...")
                try:
                    analyzer = create_analyzer(task="sentiment", lang="es")
                    # Batch processing for efficiency
                    start_time = time.time()
                    results = analyzer.predict(texts_to_analyze)
                    
                    # Map labels: POS -> positivo, NEG -> negativo, NEU -> neutral
                    label_map = {"POS": "positivo", "NEG": "negativo", "NEU": "neutral"}
                    sentiments = [label_map.get(r.output, "neutral") for r in results]
                    
                    df.loc[indices_to_analyze, 'sentiment'] = sentiments
                    elapsed = time.time() - start_time
                    print(f"  pysentimiento complete: {len(sentiments)} messages in {elapsed:.1f}s ({len(sentiments)/elapsed:.1f} msg/s)")
                except Exception as e:
                    print(f"  Error with pysentimiento: {e}. Falling back to minimal parallel AI...")
                    # Small subset fallback or just neutral if it fails
                    df.loc[indices_to_analyze, 'sentiment'] = 'neutral'
                
        df['sentiment'] = df['sentiment'].fillna('neutral')

    # ---------------------------------------------------------
    # STEP 1b: PROPAGATE product_type / product_detail from AI rows to human rows
    # Products are set on AI rows in CSV; human rows have empty values.
    # Strategy:
    #   1. Build thread → product map from AI rows (most frequent per thread)
    #   2. Homologate to canonical product name via productos.yml aliases
    #   3. Fill remaining via keyword NLP on the message text
    # ---------------------------------------------------------
    print("Propagating and homologating products via thread_id...")
    product_homolog = _build_product_homologation()
    products_list   = _load_products()

    df['product_yaml']       = None
    df['product_macro_yaml'] = None

    if 'product_type' in df.columns and 'thread_id' in df.columns:
        human_mask_prod = df['type'] == 'human'

        # STRATEGY: NLP on human text FIRST, then AI thread-level as fallback.
        # This prevents the AI's specific product (e.g. "Crédito de Libre Inversión")
        # from overriding what the human actually said (e.g. "mi crédito" → Crédito General).

        # 1. NLP FIRST: scan human text for product keywords
        if products_list and 'text' in df.columns:
            print("  Running product NLP on human messages (priority)...")
            nlp_results = df.loc[human_mask_prod, 'text'].apply(
                lambda t: pd.Series(_match_product_nlp(t, products_list),
                                    index=['product_yaml', 'product_macro_yaml'])
            )
            df.loc[human_mask_prod, 'product_yaml']       = nlp_results['product_yaml']
            df.loc[human_mask_prod, 'product_macro_yaml'] = nlp_results['product_macro_yaml']
            nlp_matched = int(df.loc[human_mask_prod, 'product_yaml'].notna().sum())
            print(f"  Product NLP matched: {nlp_matched} human messages")

        # 2. AI THREAD FALLBACK: for human messages where NLP found no product
        ai_prod_rows = df[
            (df['type'] == 'ai') &
            df['product_type'].notna() &
            (df['product_type'] != '') &
            (df['product_type'].str.lower() != 'ninguno')
        ]
        thread_product = (
            ai_prod_rows.groupby('thread_id')['product_type']
            .agg(lambda x: x.mode()[0])
        )

        needs_prod_mask = human_mask_prod & df['product_yaml'].isna()
        raw_products = df.loc[needs_prod_mask, 'thread_id'].map(thread_product).str.strip().str.lower()
        prod_nombre  = raw_products.map(lambda v: product_homolog.get(v, (None, None))[0] if pd.notna(v) else None)
        prod_macro   = raw_products.map(lambda v: product_homolog.get(v, (None, None))[1] if pd.notna(v) else None)

        df.loc[needs_prod_mask, 'product_yaml']       = prod_nombre.values
        df.loc[needs_prod_mask, 'product_macro_yaml'] = prod_macro.values

        homologated_prod = int(prod_nombre.notna().sum())
        print(f"  Product thread fallback (from AI): {homologated_prod} human messages")

        # 3. INTRA-THREAD PROPAGATION: if some human msgs in a thread have a product
        #    but others don't, propagate the most frequent product within the thread.
        #    This handles cases like: "CDT" → "un asesor" → "me voy a otro banco"
        #    where "un asesor" should inherit CDT from the same thread's human messages.
        human_with_prod = df[human_mask_prod & df['product_yaml'].notna()]
        if not human_with_prod.empty:
            thread_human_product = (
                human_with_prod.groupby('thread_id')['product_yaml']
                .agg(lambda x: x.mode()[0])
            )
            thread_human_macro = (
                human_with_prod.groupby('thread_id')['product_macro_yaml']
                .agg(lambda x: x.mode()[0])
            )
            still_needs = human_mask_prod & df['product_yaml'].isna()
            mapped_prod = df.loc[still_needs, 'thread_id'].map(thread_human_product)
            mapped_macro = df.loc[still_needs, 'thread_id'].map(thread_human_macro)
            fill_mask = mapped_prod.notna()
            if fill_mask.any():
                indices_to_fill = fill_mask[fill_mask].index
                df.loc[indices_to_fill, 'product_yaml'] = mapped_prod[fill_mask].values
                df.loc[indices_to_fill, 'product_macro_yaml'] = mapped_macro[fill_mask].values
                print(f"  Product intra-thread propagation: {len(indices_to_fill)} human messages")

    print(f"  Products categorized total: {int(df['product_yaml'].notna().sum())} | unmatched: {int(df['product_yaml'].isna().sum())}")
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # STEP 2 & 3 REORDERED: Protected Intent Extraction
    # Strategy:
    #   1. KEYWORD NLP FIRST: Analyze what the human actually typed.
    #   2. PROPAGATION SECOND: If NLP found nothing, fall back to AI-detected intent.
    # ---------------------------------------------------------
    print("Running intent extraction (Keyword NLP -> AI Propagation fallback)...")
    df['categoria_yaml'] = None
    df['macro_yaml'] = None
    df['requires_review'] = 0
    categories = _load_categories()

    # Load ONLY truly manual HITL corrections (reviewed via the feedback panel)
    manual_corrections = {}
    if os.path.exists(DB_PATH) and 'id' in df.columns:
        try:
            conn_prev = sqlite3.connect(DB_PATH)
            # Check if hitl_reviewed column exists
            cols = [r[1] for r in conn_prev.execute("PRAGMA table_info(messages)").fetchall()]
            if 'hitl_reviewed' in cols:
                prev = pd.read_sql("SELECT id, categoria_yaml, macro_yaml FROM messages WHERE hitl_reviewed = 1 AND categoria_yaml IS NOT NULL", conn_prev)
                for _, row in prev.iterrows():
                    manual_corrections[str(row['id'])] = (row['categoria_yaml'], row.get('macro_yaml'))
            conn_prev.close()
        except Exception: pass

    human_mask = df['type'] == 'human'
    
    # 3.1. KEYWORD NLP on human messages (PRIORITY)
    if categories and 'text' in df.columns:
        print("  Running primary keyword NLP on human messages...")
        results = df.loc[human_mask, 'text'].apply(
            lambda t: pd.Series(_categorize_text(t, categories), index=['categoria_yaml', 'macro_yaml', 'requires_review'])
        )
        df.loc[human_mask, 'categoria_yaml'] = results['categoria_yaml']
        df.loc[human_mask, 'macro_yaml'] = results['macro_yaml']
        df.loc[human_mask, 'requires_review'] = results['requires_review'].astype(int)

    # 3.2. AI PROPAGATION FALLBACK (only if NLP failed)
    #   IMPROVEMENT: Only propagate AI intent to messages that have enough
    #   content to plausibly match the intent.  Short/generic replies ("Si",
    #   "No", "Hola", "Buenas") are left uncategorized rather than inheriting
    #   the thread's dominant intent, which was the #1 source of contamination.
    if 'intencion' in df.columns and 'thread_id' in df.columns:
        print("  Filling gaps via AI intent propagation...")
        ai_rows = df[(df['type'] == 'ai') & df['intencion'].notna() & (df['intencion'] != '')]
        thread_intencion = ai_rows.groupby('thread_id')['intencion'].agg(lambda x: x.mode()[0])

        needs_fallback_mask = human_mask & (df['categoria_yaml'].isna() | (df['requires_review'] == 1))

        # Filter out short/generic messages that should NOT receive propagation.
        # These are messages where the text is too short or generic to carry real intent.
        def _is_propagation_worthy(text):
            if pd.isna(text) or not str(text).strip():
                return False
            t = str(text).lower().strip()
            # Too short to be a real question
            if len(t) < 10:
                return False
            # Strip greeting prefix and check remainder
            stripped = _strip_greeting_prefix(t)
            if len(stripped) < 5:
                return False
            # Known filler replies
            if stripped in _SHORT_REPLY_KEYWORDS:
                return False
            return True

        propagation_worthy = df.loc[needs_fallback_mask, 'text'].apply(_is_propagation_worthy)
        eligible_mask = needs_fallback_mask & propagation_worthy

        raw_intenciones = df.loc[eligible_mask, 'thread_id'].map(thread_intencion).str.strip().str.lower()
        cat_series   = raw_intenciones.map(lambda v: INTENCION_HOMOLOGACION.get(v, (None, None))[0] if pd.notna(v) else None)
        macro_series = raw_intenciones.map(lambda v: INTENCION_HOMOLOGACION.get(v, (None, None))[1] if pd.notna(v) else None)

        # Only update if we found a valid homologation
        valid_homolog_mask = cat_series.notna()
        indices_to_update = cat_series[valid_homolog_mask].index

        df.loc[indices_to_update, 'categoria_yaml'] = cat_series[valid_homolog_mask].values
        df.loc[indices_to_update, 'macro_yaml']     = macro_series[valid_homolog_mask].values
        df.loc[indices_to_update, 'requires_review'] = 0

        rejected_count = int(needs_fallback_mask.sum() - eligible_mask.sum())
        print(f"  Rejected {rejected_count} short/generic msgs from AI propagation.")

    # 3.3. Preserve ONLY truly manual HITL corrections (from feedback panel)
    df['hitl_reviewed'] = 0
    if manual_corrections and 'id' in df.columns:
        preserved = 0
        for idx, row in df.iterrows():
            msg_id = str(row.get('id', ''))
            if msg_id in manual_corrections:
                cat, macro = manual_corrections[msg_id]
                df.at[idx, 'categoria_yaml'] = cat
                df.at[idx, 'macro_yaml'] = macro
                df.at[idx, 'requires_review'] = 0
                df.at[idx, 'hitl_reviewed'] = 1
                preserved += 1
        print(f"  Preserved {preserved} true HITL corrections (feedback panel only).")
    
    # Non-human messages: no review needed
    df['requires_review'] = df['requires_review'].fillna(0).astype(int)
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # STEP 3b: SURVEY DETECTION (PROTECTED)
    # Strategy: Only apply "Encuesta" if no real intent was found by previous steps.
    # This ensures that "Quiero abrir cuenta [survey]" stays as "Apertura Cuenta".
    # ---------------------------------------------------------
    print("Detecting survey messages...")
    if 'text' in df.columns:
        # Check for [survey] tag
        survey_mask = df['text'].str.contains(r'\[survey\]', case=False, na=False, regex=True)
        
        # Only apply to messages WITHOUT a valid category yet
        needs_survey_cat = survey_mask & (df['categoria_yaml'].isna() | (df['categoria_yaml'] == 'Sin Sentido'))
        
        survey_count = int(needs_survey_cat.sum())
        if survey_count > 0:
            df.loc[needs_survey_cat, 'categoria_yaml'] = 'Encuesta'
            df.loc[needs_survey_cat, 'macro_yaml']     = 'Experiencia'
            df.loc[needs_survey_cat, 'requires_review'] = 0
            print(f"  Survey messages tagged (as primary intent): {survey_count}")
        
        # Total surveys detected (including those with other intents)
        total_surveys = int(survey_mask.sum())
        print(f"  Total survey tags found: {total_surveys}")

    # AI ROBUST CLASSIFICATION REMOVED (Slow)
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # STEP 4: DETECT Servilínea threads
    # Criteria (OR): AI message mentions "servilínea" OR contains a tel: phone link
    # Result: is_servilinea = 1 propagated to ALL messages in matching threads, 0 otherwise
    # ---------------------------------------------------------
    print("Detecting Servilínea referral threads...")
    df['is_servilinea'] = 0

    if 'text' in df.columns and 'thread_id' in df.columns:
        servilinea_keywords = ['servilínea', 'servilinea', 'línea de atención', 'linea de atencion']
        ai_text = df[df['type'] == 'ai']['text'].astype(str).str.lower()

        # Criterion 1: bot mentions servilínea by name
        kw_pattern = '|'.join(servilinea_keywords)
        has_kw = ai_text.str.contains(kw_pattern, regex=True, na=False)

        # Criterion 2: bot includes a tel: phone link
        has_tel = ai_text.str.contains(r'tel:\+?[\d]', regex=True, na=False)

        servilinea_ai_idx = df[df['type'] == 'ai'].index[has_kw | has_tel]
        servilinea_threads = df.loc[servilinea_ai_idx, 'thread_id'].unique()

        df.loc[df['thread_id'].isin(servilinea_threads), 'is_servilinea'] = 1

        print(f"  Servilínea threads detected: {len(servilinea_threads)}")
        print(f"  Total messages flagged: {int(df['is_servilinea'].sum())}")
    # ---------------------------------------------------------

    print(f"Persisting {len(df)} records to SQLite at {DB_PATH}...")

    conn = sqlite3.connect(DB_PATH)
    # Use replace to overwrite existing data for now
    df.to_sql('messages', conn, if_exists='replace', index=False)

    # Create indexes for performance
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_thread_id ON messages (thread_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fecha ON messages (fecha)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON messages (type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requires_review ON messages (requires_review)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_servilinea ON messages (is_servilinea)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_yaml ON messages (product_yaml)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON messages (timestamp)")
    conn.commit()
    conn.close()

    print("Ingestion complete.")
    
    # usage = ai_client.get_usage_report() # REMOVED
    
    summary_report = {
        "total_records": len(df),
        "human_messages": int((df['type'] == 'human').sum()),
        "ai_messages": int((df['type'] == 'ai').sum()),
        "categorized_total": int((df.loc[df['type'] == 'human', 'requires_review'] == 0).sum()),
        "needs_review": int((df.loc[df['type'] == 'human', 'requires_review'] == 1).sum())
    }

    print("\n" + "="*40)
    print("       FINAL INGESTION REPORT")
    print("="*40)
    print(f"Total Records:      {summary_report['total_records']}")
    print(f"Human Messages:     {summary_report['human_messages']}")
    print(f"AI Messages:        {summary_report['ai_messages']}")
    print(f"Successfully Categorized: {summary_report['categorized_total']}")
    print(f"Needs Manual Review:      {summary_report['needs_review']}")
    
    print(f"Successfully Categorized: {summary_report['categorized_total']}")
    print(f"Needs Manual Review:      {summary_report['needs_review']}")
    print("="*40 + "\n")

    return summary_report

if __name__ == "__main__":
    ingest_data()
