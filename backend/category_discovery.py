from __future__ import annotations

"""
category_discovery.py
---------------------
Analiza el CSV de datos y el YAML de categorías para:
1. Detectar keywords duplicadas entre categorías distintas.
2. Detectar keywords duplicadas dentro de la misma categoría.
3. Detectar intenciones del CSV que no tienen cobertura en el YAML.
4. Detectar macros con una sola subcategoría (candidatas a simplificar).
5. Sugerir categorías nuevas basadas en intenciones frecuentes sin cubrir.
6. Calcular cobertura real: qué % de mensajes humanos quedan sin clasificar.
"""

import os
import re
import unicodedata
from collections import defaultdict

import pandas as pd
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
YAML_PATH = os.path.join(BASE_DIR, "categorias.yml")
DATA_PATH = os.path.join(BASE_DIR, "data", "data-asistente.csv")

NOISE_MACROS = {"Sin Clasificar", "Encuestas", "Otros"}


# ── helpers ──────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase, remove accents, strip punctuation."""
    text = str(text).lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    text = re.sub(r"[^\w\s]", " ", text)
    return text.strip()


def _load_yaml() -> list[dict]:
    if not os.path.exists(YAML_PATH):
        return []
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("categorias", [])


def _load_csv_sample(max_rows: int = 50_000) -> pd.DataFrame | None:
    if not os.path.exists(DATA_PATH):
        return None
    try:
        df = pd.read_csv(DATA_PATH, nrows=max_rows, low_memory=False)
        return df
    except Exception:
        return None


# ── análisis 1: keywords duplicadas entre categorías ─────────────────────────

def _find_cross_duplicates(categories: list[dict]) -> list[dict]:
    """
    Returns list of {keyword, categories: [name1, name2, ...]}
    for every keyword that appears in 2+ categories.
    """
    kw_to_cats: dict[str, list[str]] = defaultdict(list)
    for cat in categories:
        name = cat.get("nombre", "?")
        for kw in cat.get("palabras_clave", []) or []:
            if kw and not kw.startswith("^"):   # skip regex-style entries
                key = _normalize(kw)
                kw_to_cats[key].append(name)

    duplicates = []
    for kw, cats in kw_to_cats.items():
        unique_cats = list(dict.fromkeys(cats))  # preserve order, dedupe
        if len(unique_cats) > 1:
            duplicates.append({"keyword": kw, "categories": unique_cats})

    duplicates.sort(key=lambda x: len(x["categories"]), reverse=True)
    return duplicates


# ── análisis 2: keywords duplicadas dentro de la misma categoría ─────────────

def _find_intra_duplicates(categories: list[dict]) -> list[dict]:
    """
    Returns list of {category, keyword, count} where count > 1.
    """
    results = []
    for cat in categories:
        name = cat.get("nombre", "?")
        seen: dict[str, int] = defaultdict(int)
        for kw in cat.get("palabras_clave", []) or []:
            if kw:
                seen[_normalize(kw)] += 1
        for kw, cnt in seen.items():
            if cnt > 1:
                results.append({"category": name, "keyword": kw, "count": cnt})
    return results


# ── análisis 3: macros con una sola subcategoría ─────────────────────────────

def _find_singleton_macros(categories: list[dict]) -> list[dict]:
    macro_to_cats: dict[str, list[str]] = defaultdict(list)
    for cat in categories:
        macro = cat.get("macro", "?")
        macro_to_cats[macro].append(cat.get("nombre", "?"))

    return [
        {"macro": macro, "subcategory": cats[0]}
        for macro, cats in macro_to_cats.items()
        if len(cats) == 1
    ]


# ── análisis 4: intenciones del CSV sin cobertura en YAML ────────────────────

def _find_uncovered_intenciones(
    df: pd.DataFrame, categories: list[dict]
) -> list[dict]:
    """
    Uses the `intencion` column from the CSV (pre-labeled by the bot) and checks
    whether each distinct value is already handled by the INTENCION_HOMOLOGACION
    table in ingest.py or matches any category name/keyword.
    Returns intenciones sorted by frequency that have NO coverage.
    """
    if df is None or "intencion" not in df.columns:
        return []

    # Build a set of all category names + keywords (normalized)
    covered: set[str] = set()
    for cat in categories:
        covered.add(_normalize(cat.get("nombre", "")))
        covered.add(_normalize(cat.get("macro", "")))
        for kw in cat.get("palabras_clave", []) or []:
            if kw:
                covered.add(_normalize(kw))

    # Try to import the homologation table from ingest
    try:
        from .ingest import INTENCION_HOMOLOGACION
    except ImportError:
        try:
            import sys
            sys.path.append(os.path.dirname(__file__))
            from ingest import INTENCION_HOMOLOGACION
        except ImportError:
            INTENCION_HOMOLOGACION = {}

    homologated = {_normalize(k) for k in INTENCION_HOMOLOGACION}

    human_df = df[df["type"] == "human"] if "type" in df.columns else df
    freq = human_df["intencion"].dropna().str.lower().value_counts()

    uncovered = []
    for intencion, count in freq.items():
        key = _normalize(intencion)
        if key not in covered and key not in homologated:
            uncovered.append({"intencion": intencion, "count": int(count)})

    return uncovered  # already sorted by frequency desc


# ── análisis 5: cobertura real sobre mensajes humanos ────────────────────────

def _compute_coverage(df: pd.DataFrame) -> dict:
    """
    Computes what % of human messages have a categoria_yaml assigned.
    Also shows breakdown by macro.
    """
    if df is None or df.empty:
        return {}

    human = df[df["type"] == "human"] if "type" in df.columns else df
    total = len(human)
    if total == 0:
        return {"total_human_messages": 0, "coverage_pct": 0}

    has_yaml = "categoria_yaml" in human.columns
    if has_yaml:
        classified = human["categoria_yaml"].notna().sum()
        unclassified = total - classified

        macro_counts: dict = {}
        if "macro_yaml" in human.columns:
            macro_counts = (
                human[human["macro_yaml"].notna() & ~human["macro_yaml"].isin(NOISE_MACROS)]
                ["macro_yaml"]
                .value_counts()
                .head(15)
                .to_dict()
            )
        return {
            "total_human_messages": int(total),
            "classified": int(classified),
            "unclassified": int(unclassified),
            "coverage_pct": round(classified / total * 100, 1),
            "by_macro": macro_counts,
        }

    # Fallback: use intencion column
    has_intent = "intencion" in human.columns
    if has_intent:
        classified = human["intencion"].notna().sum()
        return {
            "total_human_messages": int(total),
            "classified": int(classified),
            "unclassified": int(total - classified),
            "coverage_pct": round(classified / total * 100, 1),
            "note": "Based on `intencion` column (categoria_yaml not found in DB)",
        }

    return {"total_human_messages": int(total), "coverage_pct": None}


# ── análisis 6: términos frecuentes en mensajes no clasificados ───────────────

def _top_unclassified_terms(df: pd.DataFrame, top_n: int = 30) -> list[dict]:
    """
    Finds the most common words/bigrams in human messages that are unclassified
    (categoria_yaml is null or macro is in NOISE_MACROS).
    Useful to discover new category keywords.
    """
    if df is None or df.empty or "text" not in df.columns:
        return []

    human = df[df["type"] == "human"] if "type" in df.columns else df

    if "categoria_yaml" in human.columns:
        uncat = human[human["categoria_yaml"].isna()]
    elif "macro_yaml" in human.columns:
        uncat = human[human["macro_yaml"].isin(NOISE_MACROS)]
    else:
        return []

    if uncat.empty:
        return []

    # Tokenize and count
    stop_words = {
        "de", "la", "el", "en", "que", "y", "a", "los", "del", "se",
        "las", "un", "por", "con", "una", "su", "para", "es", "al",
        "lo", "como", "mas", "pero", "sus", "me", "mi", "si", "no",
        "le", "ya", "o", "fue", "este", "ha", "te", "cuando", "muy",
        "sin", "sobre", "esto", "o", "eso", "esta", "entre", "ser",
    }

    word_freq: dict[str, int] = defaultdict(int)
    bigram_freq: dict[str, int] = defaultdict(int)

    for text in uncat["text"].dropna():
        tokens = _normalize(str(text)).split()
        tokens = [t for t in tokens if len(t) > 2 and t not in stop_words]
        for t in tokens:
            word_freq[t] += 1
        for i in range(len(tokens) - 1):
            bigram_freq[f"{tokens[i]} {tokens[i+1]}"] += 1

    combined = {**word_freq, **bigram_freq}
    top = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [{"term": t, "count": c} for t, c in top]


# ── análisis 7: categorías sin impacto real en el CSV ────────────────────────

def _find_empty_categories(df: pd.DataFrame, categories: list[dict]) -> list[dict]:
    """
    Returns categories that exist in the YAML but have ZERO matches in the DB.
    """
    if df is None or df.empty or "categoria_yaml" not in df.columns:
        return []

    used = set(df["categoria_yaml"].dropna().unique())
    empty = []
    for cat in categories:
        name = cat.get("nombre", "")
        if name and name not in used:
            empty.append({
                "category": name,
                "macro": cat.get("macro", "?"),
                "keyword_count": len(cat.get("palabras_clave", []) or []),
            })
    return empty


# ── punto de entrada principal ────────────────────────────────────────────────

def run_category_discovery(df: pd.DataFrame | None = None) -> dict:
    """
    Runs all discovery analyses and returns a structured report.
    `df` can be passed from the DataEngine to avoid re-reading the CSV.
    If None, reads a sample from disk.
    """
    categories = _load_yaml()

    if df is None:
        df = _load_csv_sample()

    cross_dupes = _find_cross_duplicates(categories)
    intra_dupes = _find_intra_duplicates(categories)
    singleton_macros = _find_singleton_macros(categories)
    uncovered_intenciones = _find_uncovered_intenciones(df, categories)
    coverage = _compute_coverage(df)
    top_unclassified = _top_unclassified_terms(df, top_n=30)
    empty_cats = _find_empty_categories(df, categories)

    return {
        "summary": {
            "total_categories": len(categories),
            "cross_keyword_duplicates": len(cross_dupes),
            "intra_keyword_duplicates": len(intra_dupes),
            "singleton_macros": len(singleton_macros),
            "uncovered_intenciones": len(uncovered_intenciones),
            "empty_categories": len(empty_cats),
            "coverage": coverage,
        },
        "cross_keyword_duplicates": cross_dupes,
        "intra_keyword_duplicates": intra_dupes,
        "singleton_macros": singleton_macros,
        "uncovered_intenciones": uncovered_intenciones,
        "empty_categories": empty_cats,
        "top_unclassified_terms": top_unclassified,
    }
