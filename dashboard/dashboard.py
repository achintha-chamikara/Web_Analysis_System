import dash
from dash import dcc, html, dash_table
import plotly.express as px
import pandas as pd
import sqlite3
from urllib.parse import urlparse
from dashboard.advanced_stats import get_advanced_figures


def shorten_url(url):
    path = urlparse(url).path.strip("/")
    if not path:
        return "Home"
    parts = [p for p in path.split("/") if p]
    last_part = parts[-1].replace(".html", "").replace(".htm", "")
    if len(parts) == 1:
        return last_part
    return "/".join(parts[-2:]).replace(".html", "").replace(".htm", "")


def load_data(session_id=None):
    conn = sqlite3.connect("data/website_analysis.db")
    if session_id:
        df = pd.read_sql_query(
            "SELECT * FROM pages WHERE session_id = ?",
            conn,
            params=(session_id,)
        )
        session = pd.read_sql_query(
            "SELECT * FROM crawl_sessions WHERE id = ?",
            conn,
            params=(session_id,)
        )
    else:
        df = pd.read_sql_query("SELECT * FROM pages", conn)
        session = pd.read_sql_query(
            "SELECT * FROM crawl_sessions ORDER BY id DESC LIMIT 1",
            conn
        )
    conn.close()
    return df, session


def create_dashboard():
    df, session = load_data()

    if df.empty:
        app = dash.Dash(__name__)
        app.layout = html.Div([
            html.H1("Website Analysis Dashboard"),
            html.P("No data found in the database.")
        ])
        return app

    df["short_url"] = df["url"].apply(shorten_url)

    # Sort for cleaner charts
    df_load = df.sort_values("load_time_seconds", ascending=False).head(15)
    df_words = df.sort_values("word_count", ascending=False).head(15)
    df_images = df.sort_values("image_count", ascending=False).head(15)
    df_links = df.sort_values("internal_links_count", ascending=False).head(15)

    fig_corr, fig_hist, fig_slow, fig_top_images, fig_stats = get_advanced_figures(df)

    # Simple charts
    fig_load = px.bar(
        df_load,
        x="short_url",
        y="load_time_seconds",
        title="Page Load Times",
        labels={"short_url": "Page", "load_time_seconds": "Load Time (s)"},
        color="load_time_seconds",
        color_continuous_scale="Reds"
    )
    fig_load.update_xaxes(tickangle=-45)
    fig_load.update_layout(margin=dict(l=20, r=20, t=50, b=120), height=500)

    fig_words = px.bar(
        df_words,
        x="short_url",
        y="word_count",
        title="Word Count Per Page",
        labels={"short_url": "Page", "word_count": "Words"},
        color="word_count",
        color_continuous_scale="Blues"
    )
    fig_words.update_xaxes(tickangle=-45)
    fig_words.update_layout(margin=dict(l=20, r=20, t=50, b=120), height=500)

    fig_images = px.bar(
        df_images,
        x="short_url",
        y="image_count",
        title="Images Per Page",
        labels={"short_url": "Page", "image_count": "Images"},
        color="image_count",
        color_continuous_scale="Greens"
    )
    fig_images.update_xaxes(tickangle=-45)
    fig_images.update_layout(margin=dict(l=20, r=20, t=50, b=120), height=500)

    fig_links = px.bar(
        df_links,
        x="short_url",
        y="internal_links_count",
        title="Internal Links Per Page",
        labels={"short_url": "Page", "internal_links_count": "Links"},
        color="internal_links_count",
        color_continuous_scale="Purples"
    )
    fig_links.update_xaxes(tickangle=-45)
    fig_links.update_layout(margin=dict(l=20, r=20, t=50, b=120), height=500)

    status_counts = df["status_code"].value_counts().reset_index()
    status_counts.columns = ["status_code", "count"]
    fig_status = px.pie(
        status_counts,
        values="count",
        names="status_code",
        title="Page Status Codes",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    # Summary values
    website_url = session["website_url"].values[0] if len(session) > 0 else "N/A"
    total_pages = len(df)
    avg_load = round(df["load_time_seconds"].mean(), 3)
    total_images = int(df["image_count"].sum())
    total_links = int(df["internal_links_count"].sum())
    broken_pages = int((df["status_code"] != 200).sum())

    # Raw data table
    table_data = df[[
        "short_url", "status_code", "load_time_seconds",
        "word_count", "image_count", "internal_links_count"
    ]].copy()

    table_data.rename(columns={
        "short_url": "Page",
        "status_code": "Status",
        "load_time_seconds": "Load Time (s)",
        "word_count": "Words",
        "image_count": "Images",
        "internal_links_count": "Links"
    }, inplace=True)

    app = dash.Dash(__name__)

    app.layout = html.Div([
        html.Div([
            html.H1("🌐 Website Analysis Dashboard",
                    style={"color": "white", "margin": "0", "fontSize": "28px"}),
            html.P(f"Analyzing: {website_url}",
                   style={"color": "#aaaaaa", "margin": "5px 0 0 0"})
        ], style={"background": "#1e1e2e", "padding": "20px 30px"}),

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

        dcc.Tabs([
            dcc.Tab(label="Overview", children=[
                html.Div([
                    html.Div([dcc.Graph(figure=fig_status)],
                             style={"background": "white", "borderRadius": "10px", "padding": "10px",
                                    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})
                ], style={"padding": "20px 30px"}),
                html.Div([
                    html.H3("Simple Summary", style={"marginBottom": "10px"}),
                    html.Ul([
                        html.Li("This dashboard shows how the website performs."),
                        html.Li("Use the Page Metrics tab for normal analysis."),
                        html.Li("Use Advanced Statistics only if you want deeper statistical insight.")
                    ])
                ], style={"padding": "0 30px 30px"})
            ]),

            dcc.Tab(label="Page Metrics", children=[
                html.Div([
                    html.Div([dcc.Graph(figure=fig_load)],
                             style={"background": "white", "borderRadius": "10px", "padding": "10px",
                                    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
                    html.Div([dcc.Graph(figure=fig_words)],
                             style={"background": "white", "borderRadius": "10px", "padding": "10px",
                                    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
                ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                          "gap": "15px", "padding": "20px 30px"}),

                html.Div([
                    html.Div([dcc.Graph(figure=fig_images)],
                             style={"background": "white", "borderRadius": "10px", "padding": "10px",
                                    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
                    html.Div([dcc.Graph(figure=fig_links)],
                             style={"background": "white", "borderRadius": "10px", "padding": "10px",
                                    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
                ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                          "gap": "15px", "padding": "0 30px 30px"})
            ]),

            dcc.Tab(label="Advanced Statistics", children=[
                html.Div([
                    html.Div([dcc.Graph(figure=fig_corr)],
                             style={"background": "white", "borderRadius": "10px", "padding": "10px",
                                    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
                    html.Div([dcc.Graph(figure=fig_hist)],
                             style={"background": "white", "borderRadius": "10px", "padding": "10px",
                                    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
                ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                          "gap": "15px", "padding": "20px 30px"}),

                html.Div([
                    html.Div([dcc.Graph(figure=fig_slow)],
                             style={"background": "white", "borderRadius": "10px", "padding": "10px",
                                    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
                    html.Div([dcc.Graph(figure=fig_top_images)],
                             style={"background": "white", "borderRadius": "10px", "padding": "10px",
                                    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
                ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr",
                          "gap": "15px", "padding": "0 30px 20px"}),

                html.Div([
                    html.Div([dcc.Graph(figure=fig_stats)],
                             style={"background": "white", "borderRadius": "10px", "padding": "10px",
                                    "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
                ], style={"padding": "0 30px 30px"})
            ]),

            dcc.Tab(label="Raw Data", children=[
                html.Div([
                    dash_table.DataTable(
                        data=table_data.to_dict("records"),
                        columns=[{"name": i, "id": i} for i in table_data.columns],
                        page_size=15,
                        sort_action="native",
                        filter_action="native",
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "textAlign": "left",
                            "padding": "8px",
                            "fontFamily": "Arial",
                            "fontSize": "14px",
                            "whiteSpace": "normal",
                            "height": "auto"
                        },
                        style_header={
                            "backgroundColor": "#1e1e2e",
                            "color": "white",
                            "fontWeight": "bold"
                        },
                        style_data={
                            "backgroundColor": "white",
                            "color": "black"
                        }
                    )
                ], style={"padding": "20px 30px 30px"})
            ])
        ])
    ], style={"background": "#f8f9fa", "minHeight": "100vh", "fontFamily": "sans-serif"})

    return app