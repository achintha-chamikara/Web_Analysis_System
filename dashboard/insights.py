import pandas as pd


def safe_div(a, b, default=0):
    try:
        return a / b if b != 0 else default
    except Exception:
        return default


def build_insights(df):
    if df.empty:
        return {}

    df = df.copy()

    # Clean numeric columns
    for col in ["load_time_seconds", "word_count", "image_count", "internal_links_count", "status_code"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Basic derived scores
    df["content_score"] = df["word_count"] + (df["image_count"] * 5)
    df["link_score"] = df["internal_links_count"]

    # Faster pages get higher speed score
    df["speed_score"] = df["load_time_seconds"].apply(lambda x: safe_div(100, x if x > 0 else 0.01))

    # SEO score: simple sample logic
    df["seo_score"] = 0
    if "title" in df.columns:
        df["seo_score"] += df["title"].fillna("").apply(lambda x: 20 if len(str(x).strip()) > 10 else 5)
    if "meta_description" in df.columns:
        df["seo_score"] += df["meta_description"].fillna("").apply(lambda x: 20 if len(str(x).strip()) > 50 else 5)
    df["seo_score"] += df["h1_tags"].fillna("").apply(lambda x: 15 if str(x).strip() not in ["", "[]"] else 0)

    # Technical health score
    df["technical_health_score"] = 100
    df.loc[df["status_code"] != 200, "technical_health_score"] -= 40
    df.loc[df["load_time_seconds"] > df["load_time_seconds"].median(), "technical_health_score"] -= 10

    # Overall importance score
    df["importance_score"] = (
        df["content_score"] * 0.3 +
        df["link_score"] * 0.2 +
        df["speed_score"] * 0.2 +
        df["seo_score"] * 0.2 +
        df["technical_health_score"] * 0.1
    )

    def top_pages(col, n=5, ascending=False):
        cols = [c for c in ["url", "title", col] if c in df.columns]
        return df.sort_values(col, ascending=ascending)[cols].head(n).to_dict("records")

    return {
        "total_pages": len(df),
        "avg_load_time": round(df["load_time_seconds"].mean(), 3),
        "broken_pages": int((df["status_code"] != 200).sum()),
        "avg_seo_score": round(df["seo_score"].mean(), 2),
        "avg_technical_health": round(df["technical_health_score"].mean(), 2),
        "top_fastest_pages": top_pages("load_time_seconds", n=5, ascending=True),
        "top_slowest_pages": top_pages("load_time_seconds", n=5, ascending=False),
        "top_content_pages": top_pages("word_count", n=5, ascending=False),
        "top_image_pages": top_pages("image_count", n=5, ascending=False),
        "top_link_pages": top_pages("internal_links_count", n=5, ascending=False),
        "top_important_pages": top_pages("importance_score", n=5, ascending=False),
    }