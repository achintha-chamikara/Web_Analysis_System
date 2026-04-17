import pandas as pd


def build_insights(df):
    if df.empty:
        return {}

    df = df.copy()

    df["content_score"] = df["word_count"].fillna(0) + (df["image_count"].fillna(0) * 5)
    df["link_score"] = df["internal_links_count"].fillna(0)
    df["speed_score"] = (1 / df["load_time_seconds"].replace(0, 0.01)) * 100

    df["importance_score"] = (
        df["content_score"] * 0.4 +
        df["link_score"] * 0.3 +
        df["speed_score"] * 0.3
    )

    def top_pages(col, n=5, ascending=False):
        cols = ["url", "title", col]
        return df.sort_values(col, ascending=ascending)[cols].head(n).to_dict("records")

    return {
        "total_pages": len(df),
        "avg_load_time": round(df["load_time_seconds"].mean(), 3),
        "broken_pages": int((df["status_code"] != 200).sum()),
        "top_fastest_pages": top_pages("load_time_seconds", n=5, ascending=True),
        "top_slowest_pages": top_pages("load_time_seconds", n=5, ascending=False),
        "top_content_pages": top_pages("word_count", n=5, ascending=False),
        "top_image_pages": top_pages("image_count", n=5, ascending=False),
        "top_link_pages": top_pages("internal_links_count", n=5, ascending=False),
        "top_important_pages": top_pages("importance_score", n=5, ascending=False),
    }