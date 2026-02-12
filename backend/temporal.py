
import pandas as pd

def get_temporal_analysis(df: pd.DataFrame):
    """
    Returns time-series data.
    """
    # Daily volume
    daily_volume = df.groupby(df['fecha'].dt.date).size().to_dict()
    # Convert keys to str for JSON serialization
    daily_volume = {str(k): v for k, v in daily_volume.items()}
    
    # Hourly volume
    hourly_volume = df.groupby('hora').size().to_dict()
    
    # Day of week volume
    # 0 = Monday, 6 = Sunday
    dow_volume = df['fecha'].dt.day_name().value_counts().to_dict()
    
    return {
        "daily_volume": daily_volume,
        "hourly_volume": hourly_volume,
        "day_of_week_volume": dow_volume
    }
