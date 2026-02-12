import pandas as pd

def detect_advisor_requests(df: pd.DataFrame):
    """
    Identifies conversations where the user requested a human advisor.
    
    Criteria:
    - User message contains keywords like 'asesor', 'humano', 'agente'.
    
    Classification:
    - "Inmediato": Request occurs within the first 2 user messages.
    - "Luego de intentar": Request occurs after the 2nd user message.
    """
    
    # 1. Keywords
    advisor_keywords = [
        "asesor", "humano", "persona", "alguien", "contactar", 
        "agente", "ejecutivo", "hablar con", "atención", "atencion"
    ]
    
    # 2. Filter User messages
    user_msgs = df[df['sender_type'] == 'human'].copy()
    
    # 3. Helper to check text
    def has_keyword(text):
        if not isinstance(text, str):
            return False
        text_lower = text.lower()
        return any(k in text_lower for k in advisor_keywords)

    # 4. Mark messages with advisor request
    user_msgs['is_advisor_request'] = user_msgs['text'].apply(has_keyword)
    
    # Filter only those that are requests
    requests = user_msgs[user_msgs['is_advisor_request']]
    
    # Group by thread to get the FIRST request per thread
    # We want to know if it was immediate or not.
    
    results = []
    
    # We need the message index within the thread (user messages only or total? usually total context matters, 
    # but "first 2 user messages" is a good proxy for "start of conversation".)
    # Let's look at the original DF to get the true position if needed, 
    # but grouping by thread and sorting by date is safer.
    
    # Unique threads with requests
    thread_ids = requests['thread_id'].unique()
    
    immediate_count = 0
    after_effort_count = 0
    
    for tid in thread_ids:
        # Get all human messages for this thread, sorted by time/index
        thread_msgs = user_msgs[user_msgs['thread_id'] == tid].sort_index() # Assuming DF index is time-ordered or we should sort by 'timestamp' if available. 
        # But 'engine.py' usually processes raw logs. Let's assume input DF is somewhat ordered or sort it.
        # Ideally we sort by date if available, or assume file order.
        
        # Find the first message that is a request
        first_req = thread_msgs[thread_msgs['is_advisor_request']].iloc[0]
        
        # Determine 0-based index of this message among USER messages
        # "First 2 messages" -> Index 0 or 1.
        
        # Reset index to get position 0, 1, 2...
        thread_msgs_reset = thread_msgs.reset_index(drop=True)
        req_index = thread_msgs_reset[thread_msgs_reset['timestamp'] == first_req['timestamp']].index[0] if 'timestamp' in first_req else -1
        
        if req_index == -1: 
             # Fallback if timestamp missing, match by text and rough position
             # This is tricky if duplicate texts. 
             # Let's just iterate.
             for idx, row in thread_msgs_reset.iterrows():
                 if row['text'] == first_req['text']: # simplistic matching
                     req_index = idx
                     break
        
        # Logic: 
        # Inmediato: If it's the 1st or 2nd thing the user said (Index 0 or 1).
        # Luego de intentar: Index > 1.
        
        request_type = "Inmediato" if req_index <= 1 else "Luego de intentar"
        
        if request_type == "Inmediato":
            immediate_count += 1
        else:
            after_effort_count += 1
            
        results.append({
            "thread_id": tid,
            "date": str(first_req['date']) if 'date' in first_req else "",
            "sample_text": first_req['text'],
            "msg_count": len(thread_msgs), # Count of USER messages or total? User messages is simpler here.
            "request_type": request_type
        })
        
    return {
        "stats": {
            "total": len(results),
            "immediate": immediate_count,
            "after_effort": after_effort_count
        },
        "data": results
    }
