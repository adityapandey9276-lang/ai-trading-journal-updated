"""
Database layer — SQLite with admin approval system.
"""
import os, sqlite3, hashlib
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "trading_journal.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        email         TEXT    UNIQUE NOT NULL,
        password_hash TEXT    NOT NULL,
        role          TEXT    NOT NULL DEFAULT 'user',
        status        TEXT    NOT NULL DEFAULT 'pending',
        full_name     TEXT    DEFAULT '',
        created_at    TEXT    NOT NULL,
        last_login    TEXT
    )""")

    # Migrate: add status column if missing
    cols = [row[1] for row in c.execute("PRAGMA table_info(users)").fetchall()]
    if "status" not in cols:
        c.execute("ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'approved'")
        conn.commit()

    c.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL,
        date       TEXT    NOT NULL,
        symbol     TEXT    NOT NULL,
        timeframe  TEXT    NOT NULL,
        strategy   TEXT    NOT NULL,
        direction  TEXT    NOT NULL DEFAULT 'LONG',
        entry      REAL    NOT NULL,
        sl         REAL    NOT NULL,
        tp         REAL    NOT NULL,
        lot        REAL    NOT NULL,
        result     TEXT    NOT NULL,
        pnl        REAL    NOT NULL,
        rr         REAL,
        confidence INTEGER DEFAULT 5,
        notes      TEXT    DEFAULT '',
        screenshot TEXT    DEFAULT '',
        created_at TEXT    NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL,
        type       TEXT    NOT NULL,
        message    TEXT    NOT NULL,
        is_read    INTEGER DEFAULT 0,
        created_at TEXT    NOT NULL
    )""")

    conn.commit()

    admin = c.execute("SELECT id FROM users WHERE role='admin'").fetchone()
    if not admin:
        pw = hash_password("Aditya+0309@#")
        c.execute("INSERT INTO users (email,password_hash,role,status,full_name,created_at) VALUES (?,?,?,?,?,?)",
                  ("adityapandey9276@gmail.com", pw, "admin", "approved", "Admin", datetime.now().isoformat()))
        conn.commit()
    else:
        c.execute("UPDATE users SET status='approved' WHERE role='admin'")
        conn.commit()

    conn.close()

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def verify_password(pw: str, hashed: str) -> bool:
    return hash_password(pw) == hashed

def create_user(email, password, full_name="", role="user"):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (email,password_hash,role,status,full_name,created_at) VALUES (?,?,?,?,?,?)",
            (email.lower().strip(), hash_password(password), role, "pending", full_name, datetime.now().isoformat())
        )
        conn.commit()
        return True, "Account created! Awaiting admin approval before you can login."
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_conn()
    u = conn.execute("SELECT * FROM users WHERE email=?", (email.lower().strip(),)).fetchone()
    conn.close()
    return dict(u) if u else None

def get_all_users():
    conn = get_conn()
    rows = conn.execute("SELECT id,email,full_name,role,status,created_at,last_login FROM users ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_pending_users():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id,email,full_name,created_at FROM users WHERE status='pending' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_user_status(user_id: int, status: str):
    conn = get_conn()
    conn.execute("UPDATE users SET status=? WHERE id=? AND role != 'admin'", (status, user_id))
    conn.commit()
    conn.close()

def update_last_login(user_id):
    conn = get_conn()
    conn.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def update_profile(user_id, full_name, new_password=None):
    conn = get_conn()
    if new_password:
        conn.execute("UPDATE users SET full_name=?, password_hash=? WHERE id=?",
                     (full_name, hash_password(new_password), user_id))
    else:
        conn.execute("UPDATE users SET full_name=? WHERE id=?", (full_name, user_id))
    conn.commit()
    conn.close()

def calc_pnl(entry: float, sl: float, tp: float, lot: float, direction: str, result: str):
    """Auto-calculate PnL and R:R from trade parameters."""
    try:
        if entry <= 0 or sl <= 0 or tp <= 0 or lot <= 0:
            return 0.0, 0.0
        if direction == "LONG":
            risk_pts   = abs(entry - sl)
            reward_pts = abs(tp - entry)
        else:
            risk_pts   = abs(sl - entry)
            reward_pts = abs(entry - tp)
        rr  = round(reward_pts / risk_pts, 2) if risk_pts > 0 else 0.0
        if result == "WIN":
            pnl = round(lot * reward_pts * 100, 2)
        elif result == "LOSS":
            pnl = round(-lot * risk_pts * 100, 2)
        else:
            pnl = 0.0
        return pnl, rr
    except Exception:
        return 0.0, 0.0

def add_trade(user_id, date, symbol, timeframe, strategy, direction,
              entry, sl, tp, lot, result, pnl, rr, confidence, notes):
    conn = get_conn()
    conn.execute("""
        INSERT INTO trades
        (user_id,date,symbol,timeframe,strategy,direction,entry,sl,tp,lot,result,pnl,rr,confidence,notes,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (user_id, date, symbol, timeframe, strategy, direction,
          entry, sl, tp, lot, result, pnl, rr, confidence, notes, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    _check_alerts(user_id)

def get_trades(user_id=None, limit=None):
    conn = get_conn()
    if user_id:
        rows = conn.execute("SELECT * FROM trades WHERE user_id=? ORDER BY date DESC", (user_id,)).fetchall()
    else:
        rows = conn.execute(
            "SELECT t.*,u.email FROM trades t JOIN users u ON t.user_id=u.id ORDER BY t.date DESC"
        ).fetchall()
    conn.close()
    result = [dict(r) for r in rows]
    return result[:limit] if limit else result

def delete_trade(trade_id, user_id):
    conn = get_conn()
    conn.execute("DELETE FROM trades WHERE id=? AND user_id=?", (trade_id, user_id))
    conn.commit()
    conn.close()

def _check_alerts(user_id):
    trades = get_trades(user_id)
    if not trades:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    today_trades = [t for t in trades if t["date"] == today]
    if len(today_trades) >= 5:
        _add_alert(user_id, "OVERTRADE", f"⚠️ You've placed {len(today_trades)} trades today. Consider stopping.")
    recent = trades[:5]
    if all(t["result"] == "LOSS" for t in recent) and len(recent) == 5:
        _add_alert(user_id, "STREAK", "🔴 5 consecutive losses detected. Take a break and review your strategy.")

def _add_alert(user_id, atype, msg):
    conn = get_conn()
    today = datetime.now().strftime("%Y-%m-%d")
    exists = conn.execute(
        "SELECT id FROM alerts WHERE user_id=? AND type=? AND created_at LIKE ?",
        (user_id, atype, f"{today}%")
    ).fetchone()
    if not exists:
        conn.execute("INSERT INTO alerts (user_id,type,message,created_at) VALUES (?,?,?,?)",
                     (user_id, atype, msg, datetime.now().isoformat()))
        conn.commit()
    conn.close()

def get_alerts(user_id, unread_only=True):
    conn = get_conn()
    q = "SELECT * FROM alerts WHERE user_id=?"
    if unread_only:
        q += " AND is_read=0"
    q += " ORDER BY created_at DESC LIMIT 10"
    rows = conn.execute(q, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_alerts_read(user_id):
    conn = get_conn()
    conn.execute("UPDATE alerts SET is_read=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
