#!/usr/bin/env python3
"""
watcher.py — Monitora WhatsApp via Evolution API e ativa agente de vendas

Poll a cada 3s na Evolution API local buscando mensagens novas.
Filtra grupos, mensagens próprias e formato LID.
Chama agent.handle_message() e envia resposta via Evolution API.

Execução:
  python3 watcher.py                    ← roda indefinidamente
  launchctl load ~/Library/LaunchAgents/com.meuagente.watcher.plist  ← auto-start macOS
"""

import json
import time
import logging
import sys
import traceback
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / "meu-agente" / "watcher.log")
    ]
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))
from agent import handle_message, is_trigger

# ── Configuração (preenchida pelo setup) ──────────────────────────────────────
EVOLUTION_URL = "http://localhost:8080"
EVOLUTION_API_KEY = "{{EVOLUTION_API_KEY}}"
INSTANCE_NAME = "meu-agente"
POLL_INTERVAL = 3  # segundos

STATE_FILE = Path.home() / "meu-agente" / "watcher_state.json"
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


# ── Evolution API ─────────────────────────────────────────────────────────────

def evolution_request(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    url = f"{EVOLUTION_URL}{endpoint}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data else None,
        headers=headers,
        method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        logger.error(f"Evolution API erro: {e}")
        return {}


def fetch_messages(count: int = 20) -> list:
    """Busca últimas mensagens da instância."""
    result = evolution_request(
        f"/chat/findMessages/{INSTANCE_NAME}",
        method="POST",
        data={"count": count}
    )
    # Evolution API v2: {"messages": {"records": [...], "total": N}}
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and "messages" in result:
        messages_data = result["messages"]
        if isinstance(messages_data, dict):
            return messages_data.get("records", [])
        if isinstance(messages_data, list):
            return messages_data
    return []


def send_whatsapp(phone: str, message: str) -> bool:
    """Envia mensagem via Evolution API."""
    result = evolution_request(
        f"/message/sendText/{INSTANCE_NAME}",
        method="POST",
        data={"number": phone, "text": message}
    )
    success = bool(result.get("key") or result.get("id"))
    if success:
        logger.info(f"📤 Enviado para {phone}")
    else:
        logger.error(f"❌ Falha ao enviar para {phone}: {result}")
    return success


# ── Extração de mensagens ─────────────────────────────────────────────────────

def extract_message_data(msg) -> dict:
    """Extrai phone, nome e texto de uma mensagem da Evolution API."""
    if not isinstance(msg, dict):
        return {}

    key = msg.get("key", {})
    if not isinstance(key, dict):
        return {}

    # Ignorar mensagens enviadas por nós
    if key.get("fromMe", False):
        return {}

    remote_jid = key.get("remoteJid", "")

    # Ignorar grupos
    if "@g.us" in remote_jid:
        return {}

    # LID format (novo endereçamento WhatsApp): usar remoteJidAlt com número real
    if key.get("addressingMode") == "lid" and key.get("remoteJidAlt"):
        phone = key["remoteJidAlt"].replace("@s.whatsapp.net", "")
    else:
        phone = remote_jid.replace("@s.whatsapp.net", "").replace("@lid", "")

    push_name = msg.get("pushName", "Lead")

    # Extrair texto de diferentes formatos de mensagem
    message_content = msg.get("message", {})
    if not isinstance(message_content, dict):
        return {}

    text = (
        message_content.get("conversation") or
        (message_content.get("extendedTextMessage") or {}).get("text") or
        ""
    )

    return {
        "id": key.get("id", ""),
        "phone": phone,
        "name": push_name,
        "text": text.strip(),
    }


# ── State ─────────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"seen_ids": [], "last_run": None}


def save_state(state: dict):
    state["last_run"] = datetime.now().isoformat()
    # Manter apenas os últimos 500 IDs para não crescer indefinidamente
    if len(state["seen_ids"]) > 500:
        state["seen_ids"] = state["seen_ids"][-500:]
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── Loop principal ────────────────────────────────────────────────────────────

def watch():
    logger.info("🔍 Watcher iniciado")
    state = load_state()

    while True:
        try:
            messages = fetch_messages(count=20)

            for msg in messages:
                msg_data = extract_message_data(msg)
                if not msg_data or not msg_data.get("phone") or not msg_data.get("text"):
                    continue

                msg_id = msg_data["id"]
                if msg_id in state["seen_ids"]:
                    continue

                state["seen_ids"].append(msg_id)
                phone = msg_data["phone"]
                name = msg_data["name"]
                text = msg_data["text"]

                logger.info(f"📩 {name} ({phone}): {text[:60]}")

                try:
                    response = handle_message(phone, name, text)
                    if response:
                        send_whatsapp(phone, response)
                    else:
                        logger.debug("⏭️  Não é trigger — ignorado")
                except Exception as e:
                    logger.error(f"Erro ao processar mensagem: {e}\n{traceback.format_exc()}")

            save_state(state)
            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            logger.info("⏹️  Watcher encerrado")
            break
        except Exception as e:
            logger.error(f"Erro no loop: {e}\n{traceback.format_exc()}")
            time.sleep(5)


if __name__ == "__main__":
    watch()
