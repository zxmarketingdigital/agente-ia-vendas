"""
sessions_template.py — Gerencia SQLite de sessões e conversas

Usa SQLite para persistência local segura. Sessões expiram após 30 min.
"""

import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime

DB_PATH = "~/.meu-agente/dados.sqlite"


def _db():
    """Context manager para conexão SQLite."""
    db_file = Path(DB_PATH).expanduser()
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Cria tabelas se não existem."""
    conn = _db()
    cursor = conn.cursor()

    # Tabela de sessões (conversas ativas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            messages_json TEXT NOT NULL,
            last_activity INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Tabela de leads (CRM)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            name TEXT,
            phone TEXT UNIQUE,
            email TEXT,
            source TEXT,
            first_msg TEXT,
            sent_checkout INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Tabela de mensagens (histórico completo)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            ts INTEGER NOT NULL,
            FOREIGN KEY(lead_id) REFERENCES leads(id)
        )
    """)

    conn.commit()
    conn.close()


def load_session(session_id: str):
    """Carrega sessão ativa ou retorna None se expirada."""
    conn = _db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT messages_json, last_activity FROM sessions WHERE id = ?",
        (session_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    # Verificar expiração (30 min = 1800 segundos)
    if time.time() - row["last_activity"] > 1800:
        return None

    return json.loads(row["messages_json"])


def save_session(session_id: str, messages: list):
    """Salva ou atualiza sessão."""
    conn = _db()
    cursor = conn.cursor()
    now = int(time.time())

    cursor.execute(
        """
        INSERT INTO sessions (id, messages_json, last_activity, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            messages_json = ?,
            last_activity = ?
        """,
        (
            session_id,
            json.dumps(messages),
            now,
            datetime.now().isoformat(),
            json.dumps(messages),
            now
        )
    )
    conn.commit()
    conn.close()


def delete_session(session_id: str):
    """Deleta sessão expirada."""
    conn = _db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()


def cleanup_expired_sessions():
    """Remove todas as sessões expiradas."""
    conn = _db()
    cursor = conn.cursor()
    now = int(time.time())

    cursor.execute(
        "DELETE FROM sessions WHERE ? - last_activity > 1800",
        (now,)
    )
    conn.commit()
    conn.close()


def create_lead(phone: str, name: str = None, email: str = None, source: str = "whatsapp"):
    """Cria ou atualiza lead no CRM."""
    conn = _db()
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    lead_id = f"{source}_{phone}"

    cursor.execute(
        """
        INSERT INTO leads (id, phone, name, email, source, first_msg, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = COALESCE(?, name),
            email = COALESCE(?, email),
            updated_at = ?
        """,
        (
            lead_id, phone, name, email, source, "", now,
            name, email, now
        )
    )
    conn.commit()
    conn.close()

    return lead_id


def add_message(lead_id: str, role: str, content: str):
    """Adiciona mensagem ao histórico."""
    conn = _db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO messages (lead_id, role, content, ts) VALUES (?, ?, ?, ?)",
        (lead_id, role, content, int(time.time()))
    )
    conn.commit()
    conn.close()


def mark_checkout_sent(lead_id: str):
    """Marca que checkout foi enviado para o lead."""
    conn = _db()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE leads SET sent_checkout = 1, updated_at = ? WHERE id = ?",
        (datetime.now().isoformat(), lead_id)
    )
    conn.commit()
    conn.close()


def get_lead_history(lead_id: str, limit: int = 50):
    """Retorna histórico de conversas do lead."""
    conn = _db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT role, content, ts FROM messages WHERE lead_id = ? ORDER BY ts DESC LIMIT ?",
        (lead_id, limit)
    )
    messages = cursor.fetchall()
    conn.close()

    return [
        {"role": m["role"], "content": m["content"], "ts": m["ts"]}
        for m in messages
    ]


def get_stats():
    """Retorna estatísticas do CRM."""
    conn = _db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM leads")
    total_leads = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as sent FROM leads WHERE sent_checkout = 1")
    checkout_sent = cursor.fetchone()["sent"]

    cursor.execute(
        "SELECT COUNT(*) as today FROM leads WHERE created_at > datetime('now', '-1 day')"
    )
    leads_today = cursor.fetchone()["today"]

    conn.close()

    return {
        "total_leads": total_leads,
        "checkout_sent": checkout_sent,
        "leads_today": leads_today,
        "conversion_rate": f"{(checkout_sent / total_leads * 100):.1f}%" if total_leads > 0 else "0%"
    }
