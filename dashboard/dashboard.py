import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import sqlite3
from urllib.parse import urlparse

def shorten_url(url):
    path = urlparse(url).path
    if path == "" or path == "/":
        return "Home"
    parts = [p for p in path.split("/") if p]
    return "/" + "/".join(parts[-2:]) if len(parts) > 1 else "/" + parts[0]

def load_data(session_id=None):
    conn = sqlite3.connect("data/website_analysis.db")
    if session_id:
        df = pd.read_sql_query("SELECT * FROM pages WHERE session_id = ?", conn, params=(session_id,))
        session = pd.read_sql_query("SELECT * FROM crawl_sessions WHERE id = ?", conn, params=(session_id,))
    else:
        df = pd.read_sql_query("SELECT * FROM pages", conn)
        session = pd.read_sql_query("SELECT * FROM crawl_sessions ORDER BY id DESC LIMIT 1", conn)
    conn.close()
    return df, session

def create_dashboard():
    df, session = load_data()

    df["short_url"] = df["url"].apply(shorten_url)

    # Charts
    fig_load = px.bar(df, x="short_url", y="load_time_seconds",
                      title="Page Load Times",
                      labels={"short_url": "Page", "load_time_seconds": "Load Time (s)"},
                      color="load_time_seconds", color_continuous_scale="reds")
    fig_load.update_xaxes(tickangle=45)

    fig_words = px.bar(df, x="short_url", y="word_count",
                       title="Word Count Per Page",
                       labels={"short_url": "Page", "word_count": "Words"},
                       color="word_count", color_continuous_scale="blues")
    fig_words.update_xaxes(tickangle=45)

    fig_images = px.bar(df, x="short_url", y="image_count",
                        title="Images Per Page",
                        labels={"short_url": "Page", "image_count": "Images"},
                        color="image_count", color_continuous_scale="greens")
    fig_images.update_xaxes(tickangle=45)

    fig_links = px.bar(df, x="short_url", y="internal_links_count",
                       title="Internal Links Per Page",
                       labels={"short_url": "Page", "internal_links_count": "Links"},
                       color="internal_links_count", color_continuous_scale="purples")
    fig_links.update_xaxes(tickangle=45)

    status_counts = df["status_code"].value_counts().reset_index()
    status_counts.columns = ["status_code", "count"]
    fig_status = px.pie(status_counts, values="count", names="status_code",
                        title="Page Status Codes",
                        color_discrete_sequence=px.colors.qualitative.Set3)

    # Summary values
    website_url = session["website_url"].values[0] if len(session) > 0 else "N/A"
    total_pages = len(df)
    avg_load = round(df["load_time_seconds"].mean(), 3)
    total_images = int(df["image_count"].sum())
    total_links = int(df["internal_links_count"].sum())
    broken_pages = int((df["status_code"] != 200).sum())

    app = dash.Dash(__name__)

    app.layout = html.Div([

        # Header
        html.Div([
            html.H1("🌐 Website Analysis Dashboard",
                    style={"color": "white", "margin": "0", "fontSize": "28px"}),
            html.P(f"Analyzing: {website_url}",
                   style={"color": "#aaaaaa", "margin": "5px 0 0 0"})
        ], style={"background": "#1e1e2e", "padding": "20px 30px"}),

        # Summary cards
        html.Div([
            html.Div([html.H3(total_pages, style={"margin": "0", "color": "#7c3aed"}),
                      html.P("Total Pages", style={"margin": "0", "color": "#666"})],
                     style={"background": "white", "padding": "20px", "borderRadius": "10px",
                            "textAlign": "center", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),

            html.Div([html.H3(f"{avg_load}s", style={"margin": "0", "color": "#0ea5e9"}),
                      html.P("Avg Load Time", style={"margin": "0", "color": "#666"})],
                     style={"background": "white", "padding": "20px", "borderRadius": "10px",
                            "textAlign": "center", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),

            html.Div([html.H3(total_images, style={"margin": "0", "color": "#10b981"}),
                      html.P("Total Images", style={"margin": "0", "color": "#666"})],
                     style={"background": "white", "padding": "20px", "borderRadius": "10px",
                            "textAlign": "center", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),

            html.Div([html.H3(total_links, style={"margin": "0", "color": "#f59e0b"}),
                      html.P("Total Links", style={"margin": "0", "color": "#666"})],
                     style={"background": "white", "padding": "20px", "borderRadius": "10px",
                            "textAlign": "center", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),

            html.Div([html.H3(broken_pages, style={"margin": "0", "color": "#ef4444"}),
                      html.P("Broken Pages", style={"margin": "0", "color": "#666"})],
                     style={"background": "white", "padding": "20px", "borderRadius": "10px",
                            "textAlign": "center", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),

        ], style={"display": "grid", "gridTemplateColumns": "repeat(5, 1fr)",
                  "gap": "15px", "padding": "20px 30px", "background": "#f8f9fa"}),

        # Charts row 1
        html.Div([
            html.Div([dcc.Graph(figure=fig_load)],
                     style={"background": "white", "borderRadius": "10px", "padding": "10px",
                            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
            html.Div([dcc.Graph(figure=fig_words)],
                     style={"background": "white", "borderRadius": "10px", "padding": "10px",
                            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
        ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                  "gap": "15px", "padding": "0 30px 20px"}),

        # Charts row 2
        html.Div([
            html.Div([dcc.Graph(figure=fig_images)],
                     style={"background": "white", "borderRadius": "10px", "padding": "10px",
                            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
            html.Div([dcc.Graph(figure=fig_links)],
                     style={"background": "white", "borderRadius": "10px", "padding": "10px",
                            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
        ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                  "gap": "15px", "padding": "0 30px 20px"}),

        # Status pie chart
        html.Div([
            html.Div([dcc.Graph(figure=fig_status)],
                     style={"background": "white", "borderRadius": "10px", "padding": "10px",
                            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
        ], style={"padding": "0 30px 30px"}),

    ], style={"background": "#f8f9fa", "minHeight": "100vh", "fontFamily": "sans-serif"})

    return app