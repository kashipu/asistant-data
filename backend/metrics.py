
import pandas as pd

def get_general_kpis(df: pd.DataFrame):
    """
    Calculates general KPIs from the DataFrame.
    """
    total_conversations = df['thread_id'].nunique()
    total_messages = len(df)
    
    # Messages by type
    if 'type' in df.columns:
        messages_by_type = df['type'].value_counts().to_dict()
    else:
        messages_by_type = {}

    # Avg messages per conversation
    avg_messages_per_thread = total_messages / total_conversations if total_conversations > 0 else 0
    
    # Median messages per conversation
    msgs_per_thread = df.groupby('thread_id').size()
    median_messages_per_thread = float(msgs_per_thread.median())

    # Total users
    if 'client_ip' in df.columns:
        total_users = df['client_ip'].nunique()
        avg_conversations_per_user = total_conversations / total_users if total_users > 0 else 0
    else:
        total_users = 0
        avg_conversations_per_user = 0

    # Token usage
    total_input_tokens = df['input_tokens'].sum() if 'input_tokens' in df.columns else 0
    total_output_tokens = df['output_tokens'].sum() if 'output_tokens' in df.columns else 0

    # Avg tokens per AI message
    ai_msgs = df[df['type'] == 'ai']
    avg_input_tokens = ai_msgs['input_tokens'].mean() if len(ai_msgs) > 0 else 0
    avg_output_tokens = ai_msgs['output_tokens'].mean() if len(ai_msgs) > 0 else 0

    return {
        "total_conversations": int(total_conversations),
        "total_messages": int(total_messages),
        "messages_by_type": messages_by_type,
        "avg_messages_per_thread": round(avg_messages_per_thread, 2),
        "median_messages_per_thread": round(median_messages_per_thread, 2),
        "total_users": int(total_users),
        "avg_conversations_per_user": round(avg_conversations_per_user, 2),
        "total_input_tokens": int(total_input_tokens),
        "total_output_tokens": int(total_output_tokens),
        "avg_input_tokens_per_ai_msg": round(avg_input_tokens, 2),
        "avg_output_tokens_per_ai_msg": round(avg_output_tokens, 2)
    }
