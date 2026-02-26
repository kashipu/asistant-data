
import pandas as pd

def get_conversation_analysis(df: pd.DataFrame, thread_id: str = None):
    """
    Analyzes conversations. If thread_id is provided, returns details for that thread.
    Otherwise, returns aggregate stats.
    """
    if thread_id:
        # Detail view
        # Sort by rowid to ensure relative order from CSV/DB is preserved
        thread_df = df[df['thread_id'] == thread_id].sort_values(['rowid']).copy()
        
        # Convert dates if present
        if 'fecha' in thread_df.columns:
            thread_df['fecha'] = thread_df['fecha'].dt.strftime('%Y-%m-%d').fillna('')
            
        return {
            "messages": thread_df.to_dict(orient='records'),
            "summary": {
                "total_msgs": len(thread_df),
                "user_msgs": len(thread_df[thread_df['type'] == 'human']),
                "bot_msgs": len(thread_df[thread_df['type'] == 'ai']),
                "sentiment_trend": thread_df['sentiment'].tolist(),
                "products": thread_df['product_type'].unique().tolist()
            }
        }
    
    # Aggregate stats
    # Distribution of thread lengths
    thread_lengths = df.groupby('thread_id').size()
    # Bucket lengths
    length_dist = thread_lengths.value_counts().sort_index().to_dict()
    # Convert keys to str
    length_dist = {str(k): v for k, v in length_dist.items()}
    
    # Longest conversations
    longest_threads = thread_lengths.sort_values(ascending=False).head(20)
    longest_threads_data = []
    for tid, length in longest_threads.items():
        # Get first msg data for context
        first_msg = df[df['thread_id'] == tid].iloc[0]
        longest_threads_data.append({
            "thread_id": tid,
            "length": int(length),
            "intencion": first_msg.get('categoria_yaml') or first_msg.get('intencion', 'N/A'),
            "product": first_msg.get('product_type', 'N/A')
        })
        
    return {
        "length_distribution": length_dist,
        "longest_threads": longest_threads_data
    }
