
import pandas as pd

def get_temporal_analysis(df: pd.DataFrame):
    """
    Returns time-series data and heatmap.
    """
    if df is None or df.empty:
        return {
            "daily_volume": {},
            "hourly_volume": {},
            "day_of_week_volume": {},
            "heatmap": []
        }
    
    # Heatmap: Day of Week vs Hour
    # 0=Monday, 6=Sunday
    heatmap_df = df.copy()
    heatmap_df['day_index'] = heatmap_df['fecha'].dt.dayofweek
    heatmap_data = heatmap_df.groupby(['day_index', 'hora']).size().reset_index(name='count')
    
    # Map day index to names
    days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    heatmap_list = [
        {
            "day": days[int(row['day_index'])],
            "hour": int(row['hora']),
            "count": int(row['count'])
        }
        for _, row in heatmap_data.iterrows()
    ]

    # Daily volume
    daily_volume = df.groupby(df['fecha'].dt.date).size().to_dict()
    # Convert keys to str for JSON serialization
    daily_volume = {str(k): v for k, v in daily_volume.items()}
    
    # Hourly volume
    hourly_volume = df.groupby('hora').size().to_dict()
    
    # Day of week volume
    dow_volume = df['fecha'].dt.day_name().value_counts().to_dict()
    
    return {
        "daily_volume": daily_volume,
        "hourly_volume": hourly_volume,
        "day_of_week_volume": dow_volume,
        "heatmap": heatmap_list
    }
