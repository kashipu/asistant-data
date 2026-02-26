import sqlite3
import pandas as pd
import yaml
import os
import shutil
import re
from pydantic import BaseModel
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chat_data.db")
YAML_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "categorias.yml")
PRODUCTOS_YAML_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "productos.yml")

class CategorizeRequest(BaseModel):
    message_id: str
    new_category: str
    new_sentiment: Optional[str] = None
    new_product: Optional[str] = None
    original_text: str

def clean_text_for_nlp(text):
    if pd.isna(text): return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s\^\$]', '', text)
    return text.strip()

def get_feedback_messages(page: int = 1, limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    offset = (page - 1) * limit

    query = """
        SELECT
            id, thread_id, text, fecha, sentiment,
            categoria_yaml, macro_yaml,
            product_yaml, product_macro_yaml,
            requires_review
        FROM messages
        WHERE requires_review = 1
        ORDER BY fecha DESC
        LIMIT ? OFFSET ?
    """
    df = pd.read_sql(query, conn, params=(limit, offset))

    count_query = "SELECT COUNT(*) as total FROM messages WHERE requires_review = 1"
    total = pd.read_sql(count_query, conn).iloc[0]['total']

    conn.close()

    # Replace NaN with None so FastAPI can serialize to JSON.
    # df.where() alone doesn't work for float columns — use explicit object cast.
    df = df.astype(object).where(df.notna(), other=None)

    return {
        "data": df.to_dict(orient="records"),
        "total": int(total),
        "page": page,
        "limit": limit
    }

def update_yaml_category(category_name: str, new_keyword: str):
    if not os.path.exists(YAML_PATH):
        return False
        
    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
    categorias = data.get('categorias', [])
    updated = False
    
    clean_kw = clean_text_for_nlp(new_keyword)
    if not clean_kw:
        return False

    for cat in categorias:
        if cat.get('nombre') == category_name:
            if 'palabras_clave' not in cat:
                cat['palabras_clave'] = []
            if clean_kw not in cat['palabras_clave']:
                cat['palabras_clave'].append(clean_kw)
                updated = True
            break
            
    if updated:
        # Create backup just in case if none exists
        backup_path = YAML_PATH.replace('.yml', '_v1_backup.yml')
        if not os.path.exists(backup_path):
             shutil.copy2(YAML_PATH, backup_path)
             
        with open(YAML_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
    return updated

def _get_macro_for_category(category_name: str) -> str:
    """Looks up the macro group for a given category name from categorias.yml."""
    if not os.path.exists(YAML_PATH):
        return category_name
    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    for cat in data.get('categorias', []):
        if cat.get('nombre') == category_name:
            return cat.get('macro', category_name)
    return category_name

def _get_macro_for_product(product_name: str) -> str:
    """Looks up the macro group for a given product name from productos.yml."""
    if not os.path.exists(PRODUCTOS_YAML_PATH):
        return product_name
    with open(PRODUCTOS_YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    for prod in data.get('productos', []):
        if prod.get('nombre') == product_name:
            return prod.get('macro', product_name)
    return product_name

def get_category_options():
    """Returns all category names from categorias.yml."""
    if not os.path.exists(YAML_PATH):
        return []
    with open(YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return [c.get('nombre') for c in data.get('categorias', []) if c.get('nombre')]

def get_product_options():
    """Returns all product names from productos.yml."""
    if not os.path.exists(PRODUCTOS_YAML_PATH):
        return []
    with open(PRODUCTOS_YAML_PATH, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return [p.get('nombre') for p in data.get('productos', []) if p.get('nombre')]

def process_categorization(req: CategorizeRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    macro = _get_macro_for_category(req.new_category)

    # Build SET clause dynamically
    set_parts = ["requires_review = 0", "categoria_yaml = ?", "macro_yaml = ?", "intencion = ?"]
    params = [req.new_category, macro, req.new_category]

    if req.new_sentiment:
        set_parts.append("sentiment = ?")
        params.append(req.new_sentiment)

    if req.new_product:
        product_macro = _get_macro_for_product(req.new_product)
        set_parts.append("product_yaml = ?")
        set_parts.append("product_macro_yaml = ?")
        params.append(req.new_product)
        params.append(product_macro)

    params.append(req.message_id)

    query = f"UPDATE messages SET {', '.join(set_parts)} WHERE id = ?"
    cursor.execute(query, tuple(params))
    conn.commit()
    conn.close()

    # Update YAML to learn for next time
    yaml_updated = update_yaml_category(req.new_category, req.original_text)

    return {"success": True, "yaml_updated": yaml_updated}
