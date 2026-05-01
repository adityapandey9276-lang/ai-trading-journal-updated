# 💰 THE MONEY PUZZELS — AI Trading Journal

> **Production-level multi-user AI Trading Journal with advanced analytics, ML predictions, and a premium dark gold UI.**

---

## 🚀 Quick Start (Local)

```bash
# 1. Clone / copy the project folder
cd trading_journal

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

Open http://localhost:8501 in your browser.

**Default Admin Login:**
- Email: `admin@themoneypuzzels.com`
- Password: `Admin@123`

---

## ☁️ Deploy to Streamlit Cloud

1. Push this folder to a GitHub repository.
2. Go to https://share.streamlit.io → **New App**.
3. Select your repo and set **Main file** to `app.py`.
4. Click **Deploy**.

> The SQLite database is created automatically on first run.  
> For persistent cloud storage, use Supabase (see below).

---

## 🗄️ Supabase / PostgreSQL (Cloud DB)

1. Create a free project at https://supabase.com
2. Get your connection string: `postgresql://...`
3. In Streamlit Cloud → **Secrets**, add:

```toml
DATABASE_URL = "postgresql://user:pass@host:5432/dbname"
```

4. Update `utils/database.py` to use `psycopg2` with `os.getenv("DATABASE_URL")`.

---

## 📁 Project Structure

```
trading_journal/
├── app.py                    # Main entry + sidebar router
├── requirements.txt
├── .streamlit/
│   └── config.toml           # Dark gold theme
├── pages/
│   ├── login.py              # Auth (login + signup)
│   ├── dashboard.py          # Main KPI dashboard
│   ├── trade_log.py          # Log + history + AI predictor
│   ├── analytics.py          # Deep analytics
│   ├── ai_insights.py        # AI/ML insights + mistake detection
│   ├── admin.py              # Admin panel + leaderboard
│   └── profile.py            # Profile + data export
├── utils/
│   ├── database.py           # SQLite CRUD + alerts engine
│   ├── auth.py               # Session management
│   └── charts.py             # Plotly chart library
└── models/
    └── ai_engine.py          # ML model + insights engine
```

---

## 🧠 AI Features

| Feature | Description |
|---|---|
| Win Probability | GBM model trained on your trades, predicts % chance of win |
| Best Setup | Finds your highest-scoring symbol/timeframe/strategy combo |
| Worst Setup | Identifies setups draining your account |
| Mistake Detection | Overtrading, revenge trading, low-confidence trades |
| Performance Insights | Best day, hour, direction, profit factor |
| Smart Alerts | Auto-generated alerts for overtrading & losing streaks |

---

## 🔐 Security Notes

- Passwords are SHA-256 hashed (upgrade to `bcrypt` for production)
- Each user sees only their own trades
- Admin role required for team views
- Sessions managed via `st.session_state`

---

## 📊 Data Schema

**users**: id · email · password_hash · role · full_name · created_at · last_login  
**trades**: id · user_id · date · symbol · timeframe · strategy · direction · entry · sl · tp · lot · result · pnl · rr · confidence · notes · created_at  
**alerts**: id · user_id · type · message · is_read · created_at

---

## © 2025 THE MONEY PUZZELS — All Rights Reserved
