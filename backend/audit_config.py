import pandas as pd
import yaml
import os
from backend.ai_client import ai_client

# Paths
CATEGORIAS_PATH = "categorias.yml"
PRODUCTOS_PATH = "productos.yml"
CSV_PATH = "data/data-asistente.csv"

def run_audit():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found at {CSV_PATH}")
        return

    # 1. Load Data Sample
    df = pd.read_csv(CSV_PATH, usecols=['intencion', 'product_type', 'product_detail', 'text'], engine='python', on_bad_lines='skip')
    sample = df.sample(min(100, len(df))).to_csv(index=False)

    # 2. Load Configs
    with open(CATEGORIAS_PATH, 'r', encoding='utf-8') as f:
        cat_yml = f.read()
    with open(PRODUCTOS_PATH, 'r', encoding='utf-8') as f:
        prod_yml = f.read()

    # 3. Request AI Audit
    print("Requesting AI Audit from Gemini...")
    report = ai_client.audit_config(cat_yml[:5000], prod_yml[:5000], sample) # Truncated YAMLs to fit context if needed
    
    with open('AI_AUDIT_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("Audit complete. Report saved to AI_AUDIT_REPORT.md")

if __name__ == "__main__":
    run_audit()
