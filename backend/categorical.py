
import pandas as pd

def get_categorical_analysis(df: pd.DataFrame):
    """
    Returns data for categorical charts.
    """
    # Top Intents
    top_intents = df['intencion'].value_counts().head(20).to_dict()
    
    # Top Products
    top_products = df['product_type'].value_counts().head(10).to_dict()
    
    # Sentiment Distribution
    sentiment_dist = df['sentiment'].value_counts().to_dict()
    
    # Cross: Sentiment x Intention (Stack bar data)
    # We want top 10 intents and their sentiment breakdown
    top_10_intents_list = df['intencion'].value_counts().head(10).index
    sentiment_x_intent = df[df['intencion'].isin(top_10_intents_list)].groupby(['intencion', 'sentiment']).size().unstack(fill_value=0)
    sentiment_x_intent_data = sentiment_x_intent.to_dict(orient='index') # {intent: {pos: 10, neg: 5}}
    
    return {
        "top_intents": top_intents,
        "top_products": top_products,
        "sentiment_distribution": sentiment_dist,
        "sentiment_by_intent": sentiment_x_intent_data
    }
