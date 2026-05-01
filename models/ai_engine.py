"""
AI engine — win probability, best setup, mistake detection, insights.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings("ignore")

# ─── Feature engineering ─────────────────────────────────────
def build_features(df: pd.DataFrame):
    le_sym = LabelEncoder()
    le_tf  = LabelEncoder()
    le_str = LabelEncoder()
    le_dir = LabelEncoder()

    X = pd.DataFrame()
    X["symbol"]    = le_sym.fit_transform(df["symbol"].astype(str))
    X["timeframe"] = le_tf.fit_transform(df["timeframe"].astype(str))
    X["strategy"]  = le_str.fit_transform(df["strategy"].astype(str))
    X["direction"] = le_dir.fit_transform(df["direction"].astype(str)) if "direction" in df.columns else 0
    X["lot"]       = df["lot"].astype(float)
    X["rr"]        = df["rr"].fillna(1.5).astype(float)
    X["confidence"]= df["confidence"].fillna(5).astype(float)
    X["hour"]      = pd.to_datetime(df["date"]).dt.hour.fillna(9)
    X["dayofweek"] = pd.to_datetime(df["date"]).dt.dayofweek.fillna(0)
    y = (df["result"] == "WIN").astype(int)
    return X, y, (le_sym, le_tf, le_str, le_dir)

# ─── Train model ─────────────────────────────────────────────
def train_model(df: pd.DataFrame):
    if len(df) < 10:
        return None, None, None
    X, y, encoders = build_features(df)
    if y.nunique() < 2:
        return None, None, None
    model = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)
    model.fit(X, y)
    return model, encoders, X.columns.tolist()

# ─── Predict probability ─────────────────────────────────────
def predict_win_prob(model, encoders, feature_names, symbol, timeframe, strategy, direction, lot, rr, confidence, date_str):
    if model is None:
        return None
    le_sym, le_tf, le_str, le_dir = encoders
    try:
        row = {
            "symbol":    _safe_encode(le_sym, symbol),
            "timeframe": _safe_encode(le_tf, timeframe),
            "strategy":  _safe_encode(le_str, strategy),
            "direction": _safe_encode(le_dir, direction),
            "lot":       float(lot),
            "rr":        float(rr),
            "confidence":float(confidence),
            "hour":      pd.to_datetime(date_str).hour if date_str else 9,
            "dayofweek": pd.to_datetime(date_str).dayofweek if date_str else 0,
        }
        X_pred = pd.DataFrame([row])[feature_names]
        prob = model.predict_proba(X_pred)[0][1]
        return round(prob * 100, 1)
    except Exception:
        return None

def _safe_encode(le, val):
    try:
        return le.transform([val])[0]
    except ValueError:
        return 0

# ─── Best Setup ───────────────────────────────────────────────
def best_setup(df: pd.DataFrame):
    if len(df) < 5:
        return None
    grp = df.groupby(["symbol","timeframe","strategy"]).agg(
        trades=("result","count"),
        wins=("result", lambda x: (x=="WIN").sum()),
        total_pnl=("pnl","sum"),
    ).reset_index()
    grp = grp[grp["trades"] >= 3]
    if grp.empty:
        return None
    grp["win_rate"] = grp["wins"] / grp["trades"] * 100
    grp["score"]    = grp["win_rate"] * 0.5 + grp["total_pnl"].clip(lower=0) * 0.5
    best = grp.sort_values("score", ascending=False).iloc[0]
    return best.to_dict()

# ─── Worst Setup ──────────────────────────────────────────────
def worst_setup(df: pd.DataFrame):
    if len(df) < 5:
        return None
    grp = df.groupby(["symbol","timeframe","strategy"]).agg(
        trades=("result","count"),
        wins=("result", lambda x: (x=="WIN").sum()),
        total_pnl=("pnl","sum"),
    ).reset_index()
    grp = grp[grp["trades"] >= 3]
    if grp.empty:
        return None
    grp["win_rate"] = grp["wins"] / grp["trades"] * 100
    worst = grp.sort_values(["total_pnl","win_rate"]).iloc[0]
    return worst.to_dict()

# ─── Mistake Detection ────────────────────────────────────────
def detect_mistakes(df: pd.DataFrame):
    mistakes = []
    if df.empty:
        return mistakes

    # Overtrading
    daily = df.groupby("date").size()
    overtrade_days = daily[daily >= 5]
    if not overtrade_days.empty:
        mistakes.append({
            "type":    "⚠️ Overtrading",
            "level":   "danger",
            "detail":  f"You traded 5+ times on {len(overtrade_days)} day(s). High trade frequency correlates with lower win rates.",
            "days":    overtrade_days.index.tolist(),
        })

    # Low confidence trades
    if "confidence" in df.columns:
        low_conf = df[df["confidence"] <= 3]
        if len(low_conf) > 0:
            low_win = (low_conf["result"]=="WIN").mean() * 100
            mistakes.append({
                "type":   "🎯 Low Confidence Trades",
                "level":  "warning",
                "detail": f"{len(low_conf)} trades placed with confidence ≤3. Win rate on these: {low_win:.0f}%",
            })

    # Revenge trading
    results = df.sort_values("date")["result"].tolist()
    for i in range(len(results)-2):
        if results[i] == results[i+1] == "LOSS" and i+2 < len(results):
            if df.iloc[i+2]["lot"] > df.iloc[i]["lot"] * 1.5:
                mistakes.append({
                    "type":   "😡 Possible Revenge Trading",
                    "level":  "danger",
                    "detail": "After 2 consecutive losses, lot size increased significantly.",
                })
                break

    # Trading on losing days
    daily_pnl = df.groupby("date")["pnl"].sum()
    losing_days_more_trades = []
    for day, pnl in daily_pnl.items():
        day_trades = df[df["date"]==day]
        if pnl < 0 and len(day_trades) > 3:
            losing_days_more_trades.append(day)
    if losing_days_more_trades:
        mistakes.append({
            "type":   "📉 Overtrading on Losing Days",
            "level":  "warning",
            "detail": f"On {len(losing_days_more_trades)} losing day(s) you placed 4+ trades. Stop-loss discipline needed.",
        })

    return mistakes

# ─── Performance Insights ─────────────────────────────────────
def performance_insights(df: pd.DataFrame):
    insights = []
    if len(df) < 5:
        return insights

    # Best day of week
    df2 = df.copy()
    df2["dow"] = pd.to_datetime(df2["date"]).dt.day_name()
    by_dow = df2.groupby("dow")["pnl"].sum().sort_values(ascending=False)
    if not by_dow.empty:
        best_day = by_dow.index[0]
        insights.append(f"📅 Best trading day: **{best_day}** (${by_dow.iloc[0]:.2f} total PnL)")

    # Best hour
    df2["hour"] = pd.to_datetime(df2["date"], errors="coerce").dt.hour
    by_hour = df2.groupby("hour")["pnl"].sum().sort_values(ascending=False)
    if not by_hour.empty and by_hour.iloc[0] > 0:
        bh = int(by_hour.index[0])
        insights.append(f"🕐 Best trading hour: **{bh:02d}:00** (${by_hour.iloc[0]:.2f} total PnL)")

    # Direction
    if "direction" in df.columns:
        by_dir = df.groupby("direction").agg(wr=("result",lambda x:(x=="WIN").mean()*100)).reset_index()
        best_dir = by_dir.sort_values("wr", ascending=False).iloc[0]
        insights.append(f"📍 Better direction: **{best_dir['direction']}** ({best_dir['wr']:.0f}% win rate)")

    # Avg RR
    if "rr" in df.columns:
        avg_rr = df["rr"].mean()
        insights.append(f"⚖️ Average R:R ratio: **{avg_rr:.2f}**")

    # Profit factor
    gross_profit = df[df["pnl"] > 0]["pnl"].sum()
    gross_loss   = abs(df[df["pnl"] < 0]["pnl"].sum())
    if gross_loss > 0:
        pf = gross_profit / gross_loss
        insights.append(f"💹 Profit Factor: **{pf:.2f}** {'✅' if pf > 1.5 else '⚠️'}")

    return insights

# ─── Stats Summary ────────────────────────────────────────────
def compute_stats(df: pd.DataFrame):
    if df.empty:
        return {}
    total = len(df)
    wins  = (df["result"]=="WIN").sum()
    losses= (df["result"]=="LOSS").sum()
    wr    = wins/total*100 if total > 0 else 0
    total_pnl   = df["pnl"].sum()
    avg_win     = df[df["result"]=="WIN"]["pnl"].mean()  if wins  else 0
    avg_loss    = df[df["result"]=="LOSS"]["pnl"].mean() if losses else 0
    best_trade  = df["pnl"].max()
    worst_trade = df["pnl"].min()
    cum = df.sort_values("date")["pnl"].cumsum()
    peak= cum.cummax()
    max_dd = (cum - peak).min()
    return dict(
        total=total, wins=int(wins), losses=int(losses),
        win_rate=round(wr,1), total_pnl=round(total_pnl,2),
        avg_win=round(avg_win,2), avg_loss=round(avg_loss,2),
        best_trade=round(best_trade,2), worst_trade=round(worst_trade,2),
        max_drawdown=round(max_dd,2),
    )
