
import pandas as pd
import os
import sqlite3
import yaml
import re
import unicodedata

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

def _categorize_text(text, categories):
    """
    Returns (categoria_yaml, macro_yaml, requires_review).
    - categoria_yaml: subcategory name matched, or None
    - macro_yaml: macro group of matched category, or None
    - requires_review: 1 if no match found (needs HITL), 0 otherwise
    """
    if not text or not text.strip():
        return None, None, 0

    clean = _clean_for_nlp(text)
    original_lower = text.lower().strip()

    for cat in categories:
        nombre = cat.get('nombre', '')
        macro = cat.get('macro', nombre)
        min_len = cat.get('min_len', 1)
        if len(text.strip()) < min_len:
            continue

        for kw in cat.get('palabras_clave', []):
            if not kw:
                continue
            kw_clean = _clean_for_nlp(kw)
            # Support regex anchors (^, $) using original lowercase text
            if kw.startswith('^') or kw.endswith('$'):
                try:
                    if re.search(kw, original_lower):
                        return nombre, macro, 0
                except re.error:
                    pass
            elif kw_clean and kw_clean in clean:
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
        # First ensure datetime
        df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d', errors='coerce')
        # Store as string YYYY-MM-DD for consistency in SQLite
        # SQLite doesn't have a native date type, text is standard.
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

    # Now fill remaining NaNs with neutral (rows with no matching thread)
    if 'sentiment' in df.columns:
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
        # Build thread → product_type map from AI rows
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

        human_mask_prod = df['type'] == 'human'

        # Map raw CSV product value per thread and homologate
        raw_products = df.loc[human_mask_prod, 'thread_id'].map(thread_product).str.strip().str.lower()
        prod_nombre  = raw_products.map(lambda v: product_homolog.get(v, (None, None))[0] if pd.notna(v) else None)
        prod_macro   = raw_products.map(lambda v: product_homolog.get(v, (None, None))[1] if pd.notna(v) else None)

        df.loc[human_mask_prod, 'product_yaml']       = prod_nombre.values
        df.loc[human_mask_prod, 'product_macro_yaml'] = prod_macro.values

        homologated_prod = prod_nombre.notna().sum()
        print(f"  Homologated products (CSV to YAML): {homologated_prod} human messages")

        # NLP fallback: human rows still without product → scan their text
        if products_list and 'text' in df.columns:
            needs_prod_mask = human_mask_prod & df['product_yaml'].isna()
            nlp_results = df.loc[needs_prod_mask, 'text'].apply(
                lambda t: pd.Series(_match_product_nlp(t, products_list),
                                    index=['product_yaml', 'product_macro_yaml'])
            )
            df.loc[needs_prod_mask, 'product_yaml']       = nlp_results['product_yaml']
            df.loc[needs_prod_mask, 'product_macro_yaml'] = nlp_results['product_macro_yaml']
            nlp_matched = df.loc[needs_prod_mask, 'product_yaml'].notna().sum()
            print(f"  Product NLP fallback matched: {nlp_matched} additional messages")

    print(f"  Products categorized total: {int(df['product_yaml'].notna().sum())} | unmatched: {int(df['product_yaml'].isna().sum())}")
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # STEP 2: HOMOLOGATE via thread_id — the AI message carries intencion,
    # we propagate it to all human messages of the same thread.
    # ---------------------------------------------------------
    print("Homologating CSV intenciones (via thread_id) to YAML categories...")
    df['categoria_yaml'] = None
    df['macro_yaml'] = None
    df['requires_review'] = 0

    if 'intencion' in df.columns and 'thread_id' in df.columns:
        # Build thread → intencion map from AI rows (most frequent intencion per thread)
        # Note: after cleaning, empty strings replace NaN, so filter both
        ai_rows = df[(df['type'] == 'ai') & df['intencion'].notna() & (df['intencion'] != '')]
        thread_intencion = (
            ai_rows.groupby('thread_id')['intencion']
            .agg(lambda x: x.mode()[0])
        )

        # Map to human messages vectorially
        human_mask_step1 = df['type'] == 'human'
        raw_intenciones = df.loc[human_mask_step1, 'thread_id'].map(thread_intencion).str.strip().str.lower()

        # Apply homologation map
        cat_series   = raw_intenciones.map(lambda v: INTENCION_HOMOLOGACION.get(v, (None, None))[0] if pd.notna(v) else None)
        macro_series = raw_intenciones.map(lambda v: INTENCION_HOMOLOGACION.get(v, (None, None))[1] if pd.notna(v) else None)

        df.loc[human_mask_step1, 'categoria_yaml'] = cat_series.values
        df.loc[human_mask_step1, 'macro_yaml']     = macro_series.values

        homologated = cat_series.notna().sum()
        print(f"  Homologated from CSV via thread: {homologated} messages")
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # STEP 3: KEYWORD NLP → fill remaining human messages without category
    # ---------------------------------------------------------
    print("Running keyword NLP for uncategorized messages...")
    categories = _load_categories()

    # Load existing manual HITL corrections from DB (requires_review = 0 set by user)
    manual_corrections = {}  # {id: (categoria_yaml, macro_yaml)}
    if os.path.exists(DB_PATH) and 'id' in df.columns:
        try:
            conn_prev = sqlite3.connect(DB_PATH)
            prev = pd.read_sql(
                "SELECT id, categoria_yaml, macro_yaml FROM messages WHERE requires_review = 0 AND categoria_yaml IS NOT NULL",
                conn_prev
            )
            conn_prev.close()
            for _, row in prev.iterrows():
                manual_corrections[str(row['id'])] = (row['categoria_yaml'], row.get('macro_yaml'))
            print(f"  Loaded {len(manual_corrections)} existing HITL corrections to preserve.")
        except Exception:
            pass  # DB might not exist yet or lack the column

    if categories and 'text' in df.columns and 'type' in df.columns:
        # Only run keyword NLP on human messages that still have no category after homologation
        human_mask = df['type'] == 'human'
        needs_nlp_mask = human_mask & df['categoria_yaml'].isna()

        results = df.loc[needs_nlp_mask, 'text'].apply(
            lambda t: pd.Series(_categorize_text(t, categories), index=['categoria_yaml', 'macro_yaml', 'requires_review'])
        )
        df.loc[needs_nlp_mask, 'categoria_yaml'] = results['categoria_yaml']
        df.loc[needs_nlp_mask, 'macro_yaml'] = results['macro_yaml']
        df.loc[needs_nlp_mask, 'requires_review'] = results['requires_review'].astype(int)

        # Non-human messages: no category, no review needed
        df['categoria_yaml'] = df['categoria_yaml'] if 'categoria_yaml' in df.columns else None
        df['macro_yaml'] = df['macro_yaml'] if 'macro_yaml' in df.columns else None
        df['requires_review'] = df['requires_review'].fillna(0).astype(int)

        # Preserve manual HITL corrections: if this message_id was manually categorized, keep it
        if manual_corrections and 'id' in df.columns:
            preserved = 0
            for idx, row in df.iterrows():
                msg_id = str(row.get('id', ''))
                if msg_id in manual_corrections:
                    cat, macro = manual_corrections[msg_id]
                    df.at[idx, 'categoria_yaml'] = cat
                    df.at[idx, 'macro_yaml'] = macro
                    df.at[idx, 'requires_review'] = 0
                    preserved += 1
            print(f"  Preserved {preserved} manual HITL corrections.")

        matched = int((df.loc[human_mask, 'requires_review'] == 0).sum())
        unmatched = int((df.loc[human_mask, 'requires_review'] == 1).sum())
        print(f"  Categorized: {matched} | Needs HITL review: {unmatched}")
    else:
        df['categoria_yaml'] = None
        df['macro_yaml'] = None
        df['requires_review'] = 0
        print("  Warning: no categories loaded or missing columns — skipping NLP step.")
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # STEP 3b: SURVEY DETECTION
    # Mensajes con "[survey]" reciben categoría fija "Encuesta" / macro "Encuestas".
    # Se aplica a CUALQUIER tipo de mensaje (human, ai, tool) que contenga el tag.
    # Sobreescribe lo asignado por STEP 3 (NLP) para esos mensajes.
    # ---------------------------------------------------------
    print("Detecting survey messages...")
    if 'text' in df.columns:
        survey_mask = df['text'].str.contains(r'\[survey\]', case=False, na=False, regex=True)
        survey_count = int(survey_mask.sum())
        if survey_count > 0:
            df.loc[survey_mask, 'categoria_yaml'] = 'Encuesta'
            df.loc[survey_mask, 'macro_yaml']     = 'Encuestas'
            df.loc[survey_mask, 'requires_review'] = 0
            print(f"  Survey messages tagged: {survey_count}")
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
    conn.commit()
    conn.close()

    print("Ingestion complete.")

if __name__ == "__main__":
    ingest_data()
