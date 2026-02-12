
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import base64
from nltk.corpus import stopwords
import nltk

# Ensure stopwords are downloaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

stop_words_es = set(stopwords.words('spanish'))
# Custom stopwords based on requirements
custom_stop = {"banco", "hola", "buenos", "días", "gracias", "favor", "quiero", "necesito", "cuenta", "por", "para", "que", "los", "las", "una", "uno"}
stop_words_es.update(custom_stop)

def generate_wordcloud_image(df: pd.DataFrame, intencion=None, sentiment=None):
    """
    Generates a word cloud image from human messages.
    Returns base64 encoded image string.
    """
    # Filter human messages
    human_msgs = df[df['type'] == 'human']
    
    if intencion:
        human_msgs = human_msgs[human_msgs['intencion'] == intencion]
    if sentiment:
        human_msgs = human_msgs[human_msgs['sentiment'] == sentiment]
        
    text = " ".join(human_msgs['text'].astype(str).tolist()).lower()
    
    if not text.strip():
        return None
        
    wc = WordCloud(width=800, height=400, background_color='white', stopwords=stop_words_es).generate(text)
    
    # Convert to image
    img = io.BytesIO()
    wc.to_image().save(img, format='PNG')
    img.seek(0)
    
    return base64.b64encode(img.getvalue()).decode('utf-8')

def get_top_bigrams(df: pd.DataFrame):
     # Placeholder for bigram logic if needed later
     return []
