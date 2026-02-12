import pandas as pd
from typing import Dict, Any, List
from .metrics import get_general_kpis
from .categorical import get_categorical_analysis
from .referrals import detect_referrals

def get_insights_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Aggregates data for the Insights dashboard.
    """
    if df.empty:
        return {}

    # 1. General Stats
    # Re-use existing KPI logic but ensure we return what the frontend needs
    kpis = get_general_kpis(df)
    
    # 2. Categorical Analysis
    cats = get_categorical_analysis(df)
    
    # 3. Referrals Analysis
    referrals_df = detect_referrals(df)
    
    # Top Referral Reasons
    top_reasons = []
    if not referrals_df.empty:
        # Group by customer_request and count
        reason_counts = referrals_df['customer_request'].value_counts().head(10)
        for reason, count in reason_counts.items():
            top_reasons.append({"reason": reason, "count": int(count)})
            
    # Recent Redirections (Sample)
    recent_redirections = []
    if not referrals_df.empty:
        # Get last 5
        sample = referrals_df.tail(10).iloc[::-1] # Reverse to show newest first? 
        # Assuming the DF is sorted by time. If not, we might need to sort.
        # referrals_df preserves original order.
        recent_redirections = sample[['thread_id', 'customer_request', 'referral_response', 'intencion']].to_dict(orient='records')

    # 4. Empty Messages
    # Threads with at least one empty message (excluding known system messages if any, but sticking to simple check)
    empty_threads = df[df['text'].str.strip() == '']['thread_id'].nunique()

    return {
        "kpis": kpis,
        "top_intents": cats.get('top_intents', {}),
        "sentiments": cats.get('sentiment_distribution', {}),
        "empty_threads": int(empty_threads),
        "referrals": {
            "total": len(referrals_df),
            "top_reasons": top_reasons,
            "recent": recent_redirections
        }
    }
