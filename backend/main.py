
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import pandas as pd
from fastapi import BackgroundTasks
from .engine import DataEngine
from .metrics import get_general_kpis
from .failures import detect_failures 
from .referrals import detect_referrals
from .categorical import get_categorical_analysis
from .temporal import get_temporal_analysis
from .text_analysis import generate_wordcloud_image
from .conversations import get_conversation_analysis
from .summary import get_general_summary, get_uncategorized_threads, get_survey_stats
from .advisors import detect_advisor_requests
from .insights import get_insights_data
from .feedback import get_feedback_messages, process_categorization, CategorizeRequest, get_category_options, get_product_options
from .faqs import get_faqs_by_category
from .ingest import ingest_data
from .category_insights import get_qualitative_insights, get_category_insights
from .category_discovery import run_category_discovery
from .reports import get_volume_report, get_survey_utility_analysis
from .gaps_analysis import analyze_gaps_and_referrals
from .dashboard_metrics import get_extended_funnel
from .reports_deep import get_kpis_detailed, get_categories_detailed, get_failures_detailed, get_category_threads, get_products_detailed
import time

app = FastAPI(title="Chatbot Analysis API")


# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/analysis/conversations")
def get_conversations_endpoint(thread_id: Optional[str] = None):
    df = DataEngine.get_instance().get_messages()
    return get_conversation_analysis(df, thread_id=thread_id)

@app.get("/api/analysis/categorical")
def get_categorical_endpoint():
    df = DataEngine.get_instance().get_messages()
    return get_categorical_analysis(df)

@app.get("/api/analysis/temporal")
def get_temporal_endpoint():
    df = DataEngine.get_instance().get_messages()
    return get_temporal_analysis(df)

@app.get("/api/analysis/wordcloud")
def get_wordcloud_endpoint(intencion: Optional[str] = None):
    df = DataEngine.get_instance().get_messages()
    img_base64 = generate_wordcloud_image(df, intencion=intencion)
    return {"image": img_base64}


@app.get("/api/summary")
def get_summary_endpoint(start_date: Optional[str] = None, end_date: Optional[str] = None):
    df = DataEngine.get_instance().get_messages()
    return get_general_summary(df, start_date=start_date, end_date=end_date)

@app.get("/api/analysis/uncategorized")
def get_uncategorized_endpoint(page: int = 1, limit: int = 20, start_date: Optional[str] = None, end_date: Optional[str] = None):
    df = DataEngine.get_instance().get_messages()
    return get_uncategorized_threads(df, page=page, limit=limit, start_date=start_date, end_date=end_date)

@app.get("/api/analysis/surveys")
def get_surveys_endpoint(start_date: Optional[str] = None, end_date: Optional[str] = None):
    df = DataEngine.get_instance().get_messages()
    return get_survey_stats(df, start_date=start_date, end_date=end_date)

@app.get("/api/reports/volumes")
def get_report_volumes_endpoint(start_date: Optional[str] = None, end_date: Optional[str] = None):
    df = DataEngine.get_instance().get_messages(start_date=start_date, end_date=end_date)
    return get_volume_report(df)

@app.get("/api/reports/surveys/logic")
def get_report_surveys_logic_endpoint(start_date: Optional[str] = None, end_date: Optional[str] = None):
    df = DataEngine.get_instance().get_messages(start_date=start_date, end_date=end_date)
    return get_survey_utility_analysis(df)


@app.get("/api/kpis")
def get_kpis_endpoint():
    df = DataEngine.get_instance().get_messages()
    return get_general_kpis(df)

@app.get("/api/failures")
def get_failures_endpoint(page: int = 1, limit: int = 20, start_date: Optional[str] = None, end_date: Optional[str] = None):
    failures_df = DataEngine.get_instance().get_failures()
    
    # Filter by Date
    if (start_date or end_date) and not failures_df.empty and 'fecha' in failures_df.columns:
        mask = pd.Series(True, index=failures_df.index)
        if start_date:
            mask &= (failures_df['fecha'] >= start_date)
        if end_date:
            mask &= (failures_df['fecha'] <= end_date)
        failures_df = failures_df[mask]

    # Pagination
    total = len(failures_df)
    start = (page - 1) * limit
    end = start + limit
    
    data = failures_df.iloc[start:end].to_dict(orient="records")
    
    return {
        "data": data,
        "total": total,
        "page": page,
        "limit": limit
    }

@app.post("/api/admin/ingest")
def trigger_ingest_endpoint():
    """Triggers data ingestion and memory reload."""
    report = ingest_data()
    DataEngine.get_instance().reload()
    return {"status": "success", "report": report}


@app.get("/api/referrals")
def get_referrals_endpoint(page: int = 1, limit: int = 20, start_date: Optional[str] = None, end_date: Optional[str] = None):
    referrals_df = DataEngine.get_instance().get_referrals()
    
    # Filter by Date
    if (start_date or end_date) and not referrals_df.empty and 'fecha' in referrals_df.columns:
        mask = pd.Series(True, index=referrals_df.index)
        if start_date:
            mask &= (referrals_df['fecha'] >= start_date)
        if end_date:
            mask &= (referrals_df['fecha'] <= end_date)
        referrals_df = referrals_df[mask]

    # Pagination
    total = len(referrals_df)
    start = (page - 1) * limit
    end = start + limit
    
    data = referrals_df.iloc[start:end].to_dict(orient="records")
    
    return {
        "data": data,
        "total": total,
        "page": page,
        "limit": limit
    }

@app.get("/api/messages")
def get_messages_endpoint(
    page: int = 1,
    limit: int = 20,
    intencion: Optional[str] = None,
    macro_categoria: Optional[str] = None,
    sentiment: Optional[str] = None,
    product: Optional[str] = None,
    search: Optional[str] = None,
    sender_type: Optional[str] = None,
    thread_id: Optional[str] = None,
    exclude_empty: bool = False,
    sort_by: Optional[str] = None,  # 'length_asc', 'length_desc'
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    survey_result: Optional[str] = None # 'useful', 'not_useful'
):
    engine = DataEngine.get_instance()
    df = engine.get_messages()
    
    # Pre-filter by date if provided (Optimization)
    if start_date or end_date:
        if 'fecha' in df.columns:
             mask = pd.Series(True, index=df.index)
             if start_date: mask &= (df['fecha'] >= start_date)
             if end_date: mask &= (df['fecha'] <= end_date)
             df = df[mask]
    
    filtered_df = df.copy()

    # Calculate Thread Metadata (Length, Servilinea) BEFORE filtering rows if we want to sort by them
    # Because row filtering (e.g. sender_type=human) shouldn't affect "conversation length" logic usually,
    # but here we might just want to sort the resulting rows?
    # No, "sort by conversation length" implies we sort the messages based on their thread's total length.
    
    # Pre-calc thread lengths using Engine
    # thread_lengths = df.groupby('thread_id').size() # REMOVE
    
    # Pre-calc Servilínea status per thread using Engine
    # referrals_df = detect_referrals(df) # REMOVE
    # servilinea_threads = ... # REMOVE

    # Apply Filters for Rows
    if sender_type:
         filtered_df = filtered_df[filtered_df['type'] == sender_type]
    elif not thread_id and not search and not intencion and not sentiment and not product:
         # Default view: show only human messages to avoid clutter
         filtered_df = filtered_df[filtered_df['type'] == 'human']

    if thread_id:
        filtered_df = filtered_df[filtered_df['thread_id'] == thread_id]
        filtered_df = filtered_df.sort_values(by=['rowid'])
    
    if macro_categoria:
        if 'macro_yaml' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['macro_yaml'] == macro_categoria]
    if intencion:
        # Filter on categoria_yaml (YAML source of truth); fallback to intencion for compatibility
        if 'categoria_yaml' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['categoria_yaml'] == intencion]
        else:
            filtered_df = filtered_df[filtered_df['intencion'] == intencion]
    if sentiment:
        filtered_df = filtered_df[filtered_df['sentiment'] == sentiment]
    if product:
        if 'product_yaml' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['product_yaml'] == product]
        else:
            filtered_df = filtered_df[filtered_df['product_type'] == product]
    if search:
        # Search match either text or thread_id
        text_match = filtered_df['text'].str.contains(search, case=False, na=False)
        thread_match = filtered_df['thread_id'].str.contains(search, case=False, na=False)
        filtered_df = filtered_df[text_match | thread_match]
    
    if exclude_empty:
        # Filter out empty or whitespace-only messages
        filtered_df = filtered_df[filtered_df['text'].str.strip() != '']

    if survey_result:
        # 1. Identify threads with the specific survey result
        # Logic from reports.py: Identify survey messages and their result
        survey_mask = df['text'].str.contains(r'\[survey\]', case=False, na=False)
        survey_df = df[survey_mask].copy()

        def classify_survey(text):
            text = str(text).lower()
            if "no me fue útil" in text: return "not_useful"
            if "me fue útil" in text: return "useful"
            return "unknown"

        survey_df['survey_status'] = survey_df['text'].apply(classify_survey)
        
        # Filter threads that have at least one message matching the requested status
        matching_threads = survey_df[survey_df['survey_status'] == survey_result]['thread_id'].unique()
        filtered_df = filtered_df[filtered_df['thread_id'].isin(matching_threads)]

    # Apply Sorting
    if sort_by in ['length_asc', 'length_desc']:
        # Map lengths using Engine cache (fast)
        # filtered_df['thread_length'] = filtered_df['thread_id'].map(thread_lengths) # OLD
        filtered_df['thread_length'] = filtered_df['thread_id'].map(lambda x: engine.get_thread_length(x))
        
        ascending = sort_by == 'length_asc'
        filtered_df = filtered_df.sort_values(by=['thread_length', 'rowid'], ascending=[ascending, True])

    start = (page - 1) * limit
    end = start + limit
    
    result = filtered_df.iloc[start:end].copy()

    # Enrich Result with Metadata
    # Use Engine for fast lookups on the PAGINATED result only
    result['thread_length'] = result['thread_id'].apply(lambda x: engine.get_thread_length(x))
    result['is_servilinea'] = result['thread_id'].apply(lambda x: engine.is_servilinea(x))

    # Convert dates to string for JSON serialization
    if 'fecha' in result.columns and pd.api.types.is_datetime64_any_dtype(result['fecha']):
        result['fecha'] = result['fecha'].dt.strftime('%Y-%m-%d').fillna('')
    
    return {
        "data": result.to_dict(orient="records"),
        "total": len(filtered_df),
        "page": page,
        "limit": limit
    }

@app.get("/api/options")
def get_filter_options():
    df = DataEngine.get_instance().get_messages()
    import yaml
    import os
    yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "categorias.yml")
    
    macros = set()
    macro_to_sub = {} # {macro: [sub1, sub2]}
    all_subcategories = []

    if os.path.exists(yaml_path):
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            for c in data.get('categorias', []):
                m = c.get('macro', 'Sin Clasificar')
                s = c.get('nombre')
                if not s: continue
                
                macros.add(m)
                if m not in macro_to_sub: macro_to_sub[m] = []
                if s not in macro_to_sub[m]: macro_to_sub[m].append(s)
                if s not in all_subcategories: all_subcategories.append(s)

    # Products from second YAML
    products = []
    prod_yaml_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "productos.yml")
    if os.path.exists(prod_yaml_path):
        with open(prod_yaml_path, 'r', encoding='utf-8') as f:
            p_data = yaml.safe_load(f)
            products = [p.get('nombre') for p in p_data.get('productos', []) if p.get('nombre')]

    return {
        "macros": sorted(list(macros)),
        "macro_to_sub": macro_to_sub,
        "intenciones": sorted(all_subcategories),
        "productos": sorted(products),
        "sentimientos": ["positivo", "neutral", "negativo"]
    }

@app.get("/api/insights")
def get_insights_endpoint():
    df = DataEngine.get_instance().get_messages()
    return get_insights_data(df)

@app.get("/api/insights/qualitative")
def get_qualitative_insights_endpoint():
    df = DataEngine.get_instance().get_messages()
    return get_qualitative_insights(df)

@app.get("/api/insights/category")
def get_category_insights_endpoint(categoria: str):
    df = DataEngine.get_instance().get_messages()
    return get_category_insights(df, categoria)

@app.get("/api/advisors")
def get_advisors_endpoint(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    df = DataEngine.get_instance().get_messages(start_date, end_date)
    return detect_advisor_requests(df)

@app.get("/api/feedbacks")
def api_get_feedbacks(page: int = 1, limit: int = 20):
    return get_feedback_messages(page=page, limit=limit)

@app.post("/api/feedbacks/categorize")
def api_post_categorize(req: CategorizeRequest):
    return process_categorization(req)

@app.get("/api/feedbacks/options")
def api_get_feedback_options():
    """Returns available categories and products for the HITL review form."""
    return {
        "categories": get_category_options(),
        "products": get_product_options(),
        "sentiments": ["positivo", "neutral", "negativo"]
    }

@app.get("/api/faqs")
def api_get_faqs(top_n: int = 5):
    """
    Returns the top most frequent phrases per category (Test Cases).
    """
    df = DataEngine.get_instance().get_messages()
    return get_faqs_by_category(df, top_n)

@app.post("/api/etl/run")
def api_run_etl(background_tasks: BackgroundTasks):
    """
    Triggers the ETL pipeline to re-process data asynchronously.
    """
    engine = DataEngine.get_instance()
    status = engine.get_etl_status()
    
    if status["is_running"]:
        return {"message": "ETL process is already running."}
        
    engine.update_etl_state({
        "is_running": True,
        "start_time": time.time()
    })

    def task_wrapper():
        try:
            ingest_data()
            engine.reload()
            engine.update_etl_state({"last_status": "success"})
        except Exception as e:
            print(f"ETL failed: {e}")
            engine.update_etl_state({"last_status": "error"})
        finally:
            engine.update_etl_state({
                "is_running": False,
                "start_time": None
            })
            
    background_tasks.add_task(task_wrapper)
    return {"message": "ETL process started in the background."}

@app.get("/api/config/category-discovery")
def api_category_discovery():
    """
    Runs the category discovery analysis and returns a structured report with:
    - Cross-category keyword duplicates
    - Intra-category keyword duplicates
    - Singleton macros (only one subcategory)
    - CSV intenciones not covered by the YAML
    - Categories with zero real matches in the DB
    - Top terms from unclassified messages (suggested new keywords)
    - Overall coverage stats
    """
    df = DataEngine.get_instance().get_messages()
    return run_category_discovery(df=df)


@app.get("/api/etl/status")
def api_get_etl_status():
    engine = DataEngine.get_instance()
    status = engine.get_etl_status()
    
    elapsed = 0
    if status["is_running"] and status["start_time"]:
        elapsed = int(time.time() - status["start_time"])
    
    return {
        "is_running": status["is_running"],
        "elapsed_seconds": elapsed,
        "last_status": status["last_status"]
    }

@app.get("/api/analysis/gaps")
def get_gaps_endpoint(start_date: Optional[str] = None, end_date: Optional[str] = None):
    df = DataEngine.get_instance().get_messages(start_date, end_date)
    return analyze_gaps_and_referrals(df)

@app.get("/api/dashboard/funnel")
def get_funnel_endpoint(start_date: Optional[str] = None, end_date: Optional[str] = None):
    df = DataEngine.get_instance().get_messages(start_date, end_date)
    return get_extended_funnel(df, start_date, end_date)

@app.get("/api/info/data-period")
def get_data_period_endpoint():
    return DataEngine.get_instance().get_data_period()


@app.get("/api/reports/kpis-detailed")
def api_kpis_detailed(start_date: str = None, end_date: str = None):
    df = DataEngine.get_instance().get_messages(start_date, end_date)
    return get_kpis_detailed(df, start_date, end_date)


@app.get("/api/reports/categories-detailed")
def api_categories_detailed(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    engine = DataEngine.get_instance()
    df = engine.get_messages(start_date, end_date)
    return get_categories_detailed(df, engine.get_referrals(), engine.get_failures())


@app.get("/api/reports/products-detailed")
def api_products_detailed(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    engine = DataEngine.get_instance()
    df = engine.get_messages(start_date, end_date)
    return get_products_detailed(df, engine.get_referrals(), engine.get_failures())


@app.get("/api/reports/category-threads")
def api_category_threads(
    macro: str = Query(...),
    subcategory: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
    cross_category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    exclude_greetings: bool = Query(False),
):
    engine = DataEngine.get_instance()
    df = engine.get_messages(start_date, end_date)
    return get_category_threads(
        df,
        referrals_df=engine.get_referrals(),
        failures_df=engine.get_failures(),
        macro=macro,
        subcategory=subcategory,
        product=product,
        cross_category=cross_category,
        page=page,
        limit=limit,
        exclude_greetings=exclude_greetings,
    )


@app.get("/api/reports/failures-detailed")
def api_failures_detailed(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    engine = DataEngine.get_instance()
    df = engine.get_messages(start_date, end_date)
    failures_df = engine.get_failures()
    if (start_date or end_date) and failures_df is not None and not failures_df.empty and "fecha" in failures_df.columns:
        mask = pd.Series(True, index=failures_df.index)
        if start_date:
            mask &= failures_df["fecha"].astype(str) >= start_date
        if end_date:
            mask &= failures_df["fecha"].astype(str) <= end_date
        failures_df = failures_df[mask]
    return get_failures_detailed(df, failures_df)


@app.get("/api/reports/export/markdown")
def api_export_markdown():
    """Genera el informe ejecutivo en Markdown y lo devuelve como archivo descargable."""
    from fastapi.responses import Response
    from datetime import datetime
    from .metrics import get_general_kpis
    from .temporal import get_temporal_analysis
    from .categorical import get_categorical_analysis
    from .summary import get_survey_stats
    from .reports import get_volume_report, get_survey_utility_analysis

    df = DataEngine.get_instance().get_messages()
    period = DataEngine.get_instance().get_data_period()
    failures_df = DataEngine.get_instance().get_failures()
    referrals_df = DataEngine.get_instance().get_referrals()

    generated_at = datetime.now()
    kpis = get_general_kpis(df)
    funnel_data = get_extended_funnel(df)
    fk = funnel_data.get("kpis", {})
    temporal = get_temporal_analysis(df)
    categorical = get_categorical_analysis(df)
    survey_stats = get_survey_stats(df)
    volume_rpt = get_volume_report(df)
    survey_util = get_survey_utility_analysis(df)

    def N(n, d=0):
        if n is None: return "—"
        if isinstance(n, float): return f"{n:,.{d}f}"
        return f"{int(n):,}"

    def pct_s(v, t): return f"{v/t*100:.1f}%" if t else "0.0%"

    def md_tbl(rows, headers):
        if not rows: return "_Sin datos._\n"
        sep = "|" + "|".join(["---"] * len(headers)) + "|"
        h = "| " + " | ".join(headers) + " |"
        lines = [h, sep] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
        return "\n".join(lines) + "\n"

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

    # Top macros
    top_macros = categorical.get("top_macros", {})
    macro_rows = sorted(top_macros.items(), key=lambda x: x[1], reverse=True)[:10]
    m_total = sum(top_macros.values())
    macro_table = md_tbl([[k, N(v), f"{v/m_total*100:.1f}%"] for k,v in macro_rows], ["Macrocategoría", "Mensajes", "%"])

    # Top intents
    top_intents = categorical.get("top_intents", {})
    intent_rows = sorted(top_intents.items(), key=lambda x: x[1], reverse=True)[:15]
    i_total = sum(top_intents.values())
    intent_table = md_tbl([[k, N(v), f"{v/i_total*100:.1f}%"] for k,v in intent_rows], ["Subcategoría", "Mensajes", "%"])

    # Volume report top 20
    vol_rows = [[r.get("macro_yaml","—"), r.get("categoria_yaml","—"), r.get("product_yaml","—"), N(r.get("count",0)), f"{r.get('percentage',0):.2f}%"] for r in volume_rpt[:20]]
    vol_table = md_tbl(vol_rows, ["Macro", "Categoría", "Producto", "Mensajes", "%"])

    # Survey utility top 10
    util_rows = [[r.get("macro","—"), r.get("categoria","—"), N(r.get("useful",0)), N(r.get("not_useful",0)), N(r.get("total",0)), f"{r.get('utility_rate',0):.1f}%"] for r in survey_util[:10]]
    util_table = md_tbl(util_rows, ["Macro", "Categoría", "Útil", "No útil", "Total", "% Utilidad"])

    # Failures summary
    fail_n = len(failures_df) if failures_df is not None and not failures_df.empty else 0

    content = f"""# Informe Ejecutivo — Asistente Virtual

**Período:** {period.get('start','N/A')} — {period.get('end','N/A')}
**Generado:** {generated_at.strftime('%Y-%m-%d %H:%M:%S')}
**Fuente:** data/chat_data.db · {N(total_msgs)} mensajes · {N(total_convs)} conversaciones

---

## Resumen Ejecutivo

| Indicador | Valor |
|---|---|
| Total conversaciones | {N(total_convs)} |
| Usuarios únicos | {N(fk.get('unique_users',0))} |
| Tasa de abandono | {abandon_rate:.1f}% |
| Auto-servicio | {self_svc:.1f}% |
| Índice de utilidad | {utility:.1f}% |
| Gasto de valor | {N(waste_count)} conv. ({waste_pct:.1f}%) |

---

## 1. KPIs Operacionales

| KPI | Valor |
|---|---|
| Total mensajes | {N(total_msgs)} |
| Mensajes humanos | {N(by_type.get('human',0))} ({pct_s(by_type.get('human',0), total_msgs)}) |
| Mensajes bot (AI) | {N(by_type.get('ai',0))} ({pct_s(by_type.get('ai',0), total_msgs)}) |
| Promedio msgs/conv | {kpis.get('avg_messages_per_thread',0):.2f} |
| Abandono (≤1 msg humano) | {N(abandon_n)} ({abandon_rate:.1f}%) |
| Auto-servicio | {fk.get('self_service_rate',0):.1f}% |
| Encuestas respondidas | {N(total_surveys)} |
| Índice de utilidad | {utility:.1f}% |
| Tokens entrada (total) | {N(kpis.get('total_input_tokens',0))} |
| Tokens salida (total) | {N(kpis.get('total_output_tokens',0))} |

---

## 2. Distribución de Categorías

### Macrocategorías

{macro_table}

### Top 15 Subcategorías

{intent_table}

---

## 3. Calidad y Fricción

| Métrica | Valor |
|---|---|
| Conversaciones con fallo | {N(fail_n)} ({pct_s(fail_n, total_convs)}) |
| Conversaciones derivadas | {N(int(total_convs * ref_rate / 100) if total_convs else 0)} ({ref_rate:.1f}%) |
| Gasto de valor | {N(waste_count)} ({waste_pct:.1f}%) |

---

## 4. Utilidad por Categoría (Encuestas)

{util_table}

---

## 5. Reporte de Volumen Detallado

{vol_table}

---
*Generado automáticamente por el endpoint /api/reports/export/markdown — {generated_at.strftime('%Y-%m-%d %H:%M')}*
"""

    filename = f"informe_ejecutivo_{generated_at.strftime('%Y%m%d_%H%M%S')}.md"
    return Response(
        content=content.encode("utf-8"),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

