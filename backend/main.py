
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import pandas as pd
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

app = FastAPI(title="Chatbot Analysis API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
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
    sentiment: Optional[str] = None,
    product: Optional[str] = None,
    search: Optional[str] = None,
    sender_type: Optional[str] = None,
    thread_id: Optional[str] = None,
    exclude_empty: bool = False,
    sort_by: Optional[str] = None,  # 'length_asc', 'length_desc'
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
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
    
    if intencion:
        filtered_df = filtered_df[filtered_df['intencion'] == intencion]
    if sentiment:
        filtered_df = filtered_df[filtered_df['sentiment'] == sentiment]
    if product:
        filtered_df = filtered_df[filtered_df['product_type'] == product]
    if search:
        filtered_df = filtered_df[filtered_df['text'].str.contains(search, case=False, na=False)]
    
    if exclude_empty:
        # Filter out empty or whitespace-only messages
        filtered_df = filtered_df[filtered_df['text'].str.strip() != '']

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
    if 'fecha' in result.columns:
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
    return {
        "intenciones": df['intencion'].dropna().unique().tolist(),
        "productos": df['product_type'].dropna().unique().tolist(),
        "sentimientos": df['sentiment'].dropna().unique().tolist()
    }

@app.get("/api/insights")
def get_insights_endpoint():
    df = DataEngine.get_instance().get_messages()
    return get_insights_data(df)

@app.get("/api/advisors")
def get_advisors_endpoint(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    df = DataEngine.get_instance().get_messages(start_date, end_date)
    return detect_advisor_requests(df)
