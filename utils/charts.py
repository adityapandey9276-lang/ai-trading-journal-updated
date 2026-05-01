"""
Plotly chart helpers — all using the Money Puzzels dark gold theme.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

GOLD   = "#FFD700"
GREEN  = "#00E676"
RED    = "#FF1744"
BG     = "#0D1117"
GRID   = "rgba(255,215,0,0.06)"
FONT   = "Rajdhani"

_layout = dict(
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    font=dict(family=FONT, color="#F0F0F0", size=13),
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, showline=False),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, showline=False),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=GRID),
    hoverlabel=dict(bgcolor="#050810", font_color="#FFD700"),
)

def equity_curve(df: pd.DataFrame, title="Equity Curve"):
    df = df.copy().sort_values("date")
    df["cumPnL"] = df["pnl"].cumsum()
    df["color"]  = df["pnl"].apply(lambda x: GREEN if x >= 0 else RED)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["cumPnL"],
        mode="lines", line=dict(color=GOLD, width=2.5),
        fill="tozeroy", fillcolor="rgba(255,215,0,0.07)",
        name="Equity",
        hovertemplate="<b>%{x}</b><br>PnL: $%{y:.2f}<extra></extra>",
    ))
    # Add trade dots
    wins  = df[df["result"]=="WIN"]
    losses= df[df["result"]=="LOSS"]
    fig.add_trace(go.Scatter(x=wins["date"],   y=wins["cumPnL"],   mode="markers", marker=dict(color=GREEN, size=7, symbol="circle"), name="Win"))
    fig.add_trace(go.Scatter(x=losses["date"], y=losses["cumPnL"], mode="markers", marker=dict(color=RED,   size=7, symbol="x"),      name="Loss"))
    fig.update_layout(**_layout, title=dict(text=title, font=dict(color=GOLD, family="Orbitron", size=14)))
    return fig

def pnl_bar(df: pd.DataFrame, group_by="date", title="Daily PnL"):
    grp = df.groupby(group_by)["pnl"].sum().reset_index()
    colors = [GREEN if v >= 0 else RED for v in grp["pnl"]]
    fig = go.Figure(go.Bar(
        x=grp[group_by], y=grp["pnl"], marker_color=colors,
        hovertemplate="<b>%{x}</b><br>PnL: $%{y:.2f}<extra></extra>",
    ))
    fig.update_layout(**_layout, title=dict(text=title, font=dict(color=GOLD, family="Orbitron", size=14)))
    return fig

def win_rate_gauge(win_rate: float):
    color = GREEN if win_rate >= 55 else (GOLD if win_rate >= 40 else RED)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=win_rate,
        number=dict(suffix="%", font=dict(color=color, family="Orbitron", size=36)),
        gauge=dict(
            axis=dict(range=[0,100], tickcolor="#555"),
            bar=dict(color=color),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            steps=[
                dict(range=[0,40],   color="rgba(255,23,68,0.15)"),
                dict(range=[40,60],  color="rgba(255,215,0,0.1)"),
                dict(range=[60,100], color="rgba(0,230,118,0.15)"),
            ],
            threshold=dict(line=dict(color=GOLD, width=3), thickness=.75, value=win_rate),
        ),
        title=dict(text="Win Rate", font=dict(color="#8A8A9A", family="Rajdhani")),
    ))
    fig.update_layout(paper_bgcolor=BG, font=dict(family=FONT), margin=dict(l=20,r=20,t=40,b=20), height=260)
    return fig

def strategy_heatmap(df: pd.DataFrame):
    pivot = df.pivot_table(values="pnl", index="strategy", columns="symbol", aggfunc="sum", fill_value=0)
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0,"#FF1744"],[0.5,"#0D1117"],[1,"#00E676"]],
        text=np.round(pivot.values,1),
        texttemplate="%{text}",
        hovertemplate="Strategy: %{y}<br>Symbol: %{x}<br>PnL: $%{z:.2f}<extra></extra>",
        showscale=True,
        colorbar=dict(tickcolor="#555", outlinecolor="#555"),
    ))
    fig.update_layout(**_layout, title=dict(text="Strategy × Symbol PnL Heatmap", font=dict(color=GOLD, family="Orbitron", size=14)))
    return fig

def drawdown_chart(df: pd.DataFrame):
    df = df.copy().sort_values("date")
    df["cumPnL"] = df["pnl"].cumsum()
    df["peak"]   = df["cumPnL"].cummax()
    df["dd"]     = df["cumPnL"] - df["peak"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["dd"],
        fill="tozeroy", fillcolor="rgba(255,23,68,0.15)",
        line=dict(color=RED, width=1.5),
        name="Drawdown",
        hovertemplate="<b>%{x}</b><br>Drawdown: $%{y:.2f}<extra></extra>",
    ))
    fig.update_layout(**_layout, title=dict(text="Drawdown Analysis", font=dict(color=GOLD, family="Orbitron", size=14)))
    return fig

def symbol_pie(df: pd.DataFrame):
    s = df.groupby("symbol").size().reset_index(name="count")
    fig = go.Figure(go.Pie(
        labels=s["symbol"], values=s["count"],
        hole=.55,
        marker=dict(colors=[GOLD,"#B8960C","#FFE566","#7D6400","#FFF176","#F9A825"]),
        textfont=dict(family=FONT),
        hovertemplate="%{label}: %{value} trades<extra></extra>",
    ))
    fig.update_layout(paper_bgcolor=BG, font=dict(family=FONT, color="#F0F0F0"),
                      margin=dict(l=10,r=10,t=40,b=10),
                      title=dict(text="Trades by Symbol", font=dict(color=GOLD, family="Orbitron", size=14)),
                      legend=dict(bgcolor="rgba(0,0,0,0)"),
                      annotations=[dict(text="Symbols", x=0.5, y=0.5, showarrow=False, font=dict(color=GOLD, size=14))])
    return fig

def leaderboard_bar(data: list):
    """data: list of dicts with email, total_pnl, win_rate, trades"""
    if not data:
        return go.Figure()
    df = pd.DataFrame(data).sort_values("total_pnl", ascending=True)
    colors = [GREEN if v >= 0 else RED for v in df["total_pnl"]]
    fig = go.Figure(go.Bar(
        x=df["total_pnl"], y=df["email"],
        orientation="h", marker_color=colors,
        hovertemplate="<b>%{y}</b><br>Total PnL: $%{x:.2f}<extra></extra>",
    ))
    fig.update_layout(**_layout, title=dict(text="Team Leaderboard", font=dict(color=GOLD, family="Orbitron", size=14)))
    return fig

def monthly_performance(df: pd.DataFrame):
    df = df.copy()
    df["month"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")
    grp = df.groupby("month")["pnl"].sum().reset_index()
    colors = [GREEN if v >= 0 else RED for v in grp["pnl"]]
    fig = go.Figure(go.Bar(
        x=grp["month"], y=grp["pnl"], marker_color=colors,
        hovertemplate="<b>%{x}</b><br>PnL: $%{y:.2f}<extra></extra>",
    ))
    fig.update_layout(**_layout, title=dict(text="Monthly Performance", font=dict(color=GOLD, family="Orbitron", size=14)))
    return fig
