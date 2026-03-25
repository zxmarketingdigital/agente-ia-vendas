#!/usr/bin/env python3
"""
watcher_template.py — Monitora WhatsApp e ativa agente

Responsabilidades:
1. Poll de ~/.zapi-whatsapp/messages.json a cada 3s
2. Detectar mensagens novas
3. Chamar agent.handle_message()
4. Enviar resposta via Z-API
5. Manter state em JSON

Execução:
  python3 watcher.py                    ← roda indefinidamente
  launchctl load ~/Library/LaunchAgents/com.zxlab.meu-agente-watcher.plist  ← auto-start macOS
"""

import json
import time
import logging
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar agente
sys.path.insert(0, str(Path(__file__).parent))
from agent import handle_message

# Configurações
MESSAGES_FILE = Path.home() / ".zapi-whatsapp" / "messages.json"
STATE_FILE = Path.home() / ".zxlab-mission-control" / "meu-agente-watcher.json"
LOGS_DIR = Path.home() / ".zxlab-mission-control" / "logs"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state():
    """Carrega último índice processado."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_index": -1, "last_run": None}


def save_state(state):
    """Salva estado atual."""
    state["last_run"] = datetime.now().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def send_whatsapp(phone: str, message: str) -> bool:
    """Envia mensagem via Z-API."""
    try:
        # Chamaria Z-API aqui em produção
        # Por agora, loga apenas
        logger.info(f"📤 Resposta para {phone}: {message[:50]}...")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao enviar: {e}")
        return False


def load_messages():
    """Carrega lista de mensagens do arquivo."""
    if not MESSAGES_FILE.exists():
        logger.warning(f"Arquivo não encontrado: {MESSAGES_FILE}")
        return []

    try:
        return json.loads(MESSAGES_FILE.read_text())
    except json.JSONDecodeError:
        logger.error(f"JSON inválido em {MESSAGES_FILE}")
        return []


def process_message(message_data):
    """Processa uma mensagem e ativa agente se necessário."""
    try:
        phone = message_data.get("phone", "unknown")
        sender_name = message_data.get("sender_name", "Lead")
        text = message_data.get("text", "")

        if not text:
            return

        logger.info(f"📩 Mensagem de {sender_name} ({phone}): {text[:50]}...")

        # Chamar agente
        response = handle_message(phone, sender_name, text)

        if response:
            logger.info(f"✅ Agente respondeu")
            send_whatsapp(phone, response)
        else:
            logger.debug(f"⏭️  Não é trigger — ignorado")

    except Exception as e:
        logger.error(f"Erro ao processar: {e}")


def watch():
    """Loop principal do watcher."""
    logger.info("🔍 Watcher iniciado")
    state = load_state()

    while True:
        try:
            messages = load_messages()
            current_index = len(messages) - 1

            # Processar mensagens novas
            if current_index > state["last_index"]:
                for i in range(state["last_index"] + 1, current_index + 1):
                    if i < len(messages):
                        process_message(messages[i])

                state["last_index"] = current_index
                save_state(state)

            time.sleep(3)  # Poll a cada 3 segundos

        except KeyboardInterrupt:
            logger.info("⏹️  Watcher encerrado")
            break
        except Exception as e:
            logger.error(f"Erro no loop: {e}")
            time.sleep(5)


if __name__ == "__main__":
    watch()
