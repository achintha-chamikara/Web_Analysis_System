import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def get_advanced_figures(df):
    # Correlation scatter plot
    fig_corr = px.scatter(
        df,
        x="word_count",
        y="load_time_seconds",
        hover_data=["short_url"],
        title="Word Count vs Load Time",
        labels={
            "word_count": "Word Count",
            "load_time_seconds": "Load Time (s)"
        },
        color="load_time_seconds",
        color_continuous_scale="Reds"
    )

    # Add trendline safely only if statsmodels exists
    try:
        fig_corr = px.scatter(
            df,
            x="word_count",
            y="load_time_seconds",
            hover_data=["short_url"],
            title="Word Count vs Load Time",
            labels={
                "word_count": "Word Count",
                "load_time_seconds": "Load Time (s)"
            },
            color="load_time_seconds",
            color_continuous_scale="Reds",
            trendline="ols"
        )
    except Exception:
        pass

    # Load time histogram
    fig_hist = px.histogram(
        df,
        x="load_time_seconds",
        title="Load Time Distribution",
        labels={"load_time_seconds": "Load Time (s)"},
        color_discrete_sequence=["#7c3aed"],
        nbins=20
    )

    # Top 5 slowest pages
    top_slow = df.nlargest(5, "load_time_seconds")[["short_url", "load_time_seconds"]]
    fig_slow = px.bar(
        top_slow,
        x="load_time_seconds",
        y="short_url",
        orientation="h",
        title="Top 5 Slowest Pages",
        labels={"short_url": "Page", "load_time_seconds": "Load Time (s)"},
        color="load_time_seconds",
        color_continuous_scale="Reds"
    )

    # Top 5 pages with most images
    top_images = df.nlargest(5, "image_count")[["short_url", "image_count"]]
    fig_top_images = px.bar(
        top_images,
        x="image_count",
        y="short_url",
        orientation="h",
        title="Top 5 Pages with Most Images",
        labels={"short_url": "Page", "image_count": "Image Count"},
        color="image_count",
        color_continuous_scale="Greens"
    )

    # Stats summary table
    stats = pd.DataFrame({
        "Metric": [
            "Mean Load Time", "Max Load Time", "Min Load Time",
            "Mean Word Count", "Max Word Count", "Total Images",
            "Total Links"
        ],
        "Value": [
            f"{df['load_time_seconds'].mean():.3f}s",
            f"{df['load_time_seconds'].max():.3f}s",
            f"{df['load_time_seconds'].min():.3f}s",
            f"{df['word_count'].mean():.0f}",
            f"{df['word_count'].max()}",
            f"{df['image_count'].sum()}",
            f"{df['internal_links_count'].sum()}"
        ]
    })

    fig_stats = go.Figure(data=[go.Table(
        header=dict(
            values=["Metric", "Value"],
            fill_color="#1e1e2e",
            font=dict(color="white", size=13),
            align="left"
        ),
        cells=dict(
            values=[stats["Metric"], stats["Value"]],
            fill_color=[["#f8f9fa", "white"] * len(stats)],
            font=dict(size=12),
            align="left",
            height=30
        )
    )])
    fig_stats.update_layout(title="Advanced Statistics Summary")

    return fig_corr, fig_hist, fig_slow, fig_top_images, fig_stats