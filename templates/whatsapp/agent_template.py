#!/usr/bin/env python3
"""
agent_template.py — Agente WhatsApp completo (v1.0)

Responsabilidades:
1. Detectar trigger phrase em mensagens
2. Carregar/gerenciar sessão de conversa
3. Chamar IA para resposta
4. Detectar intenção de compra e enviar checkout
5. Salvar conversa em SQLite

Use como: python3 agent.py --test
          python3 agent.py --chat PHONE
          Importar em watcher.py
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Carregar templates compartilhados
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from agent_core_template import call_ai, is_purchase_intent, format_checkout_message, SYSTEM_PROMPT, CHECKOUT_LINK
from sessions_template import init_db, load_session, save_session, create_lead, add_message, mark_checkout_sent

# Configurações de trigger ({{placeholders}} preenchidos durante setup)
CHECKOUT_LINK = "{{CHECKOUT_LINK}}"
TRIGGER_EXACT = "{{TRIGGER_EXACT}}"
TRIGGER_KEYWORDS = [
    "{{PRODUCT_NAME}}",
    "dúvida",
    "informação",
    "saiba mais"
]

DB_PATH = "~/.meu-agente/dados.sqlite"


def is_trigger(text: str) -> bool:
    """Verifica se mensagem contém trigger phrase."""
    text_lower = text.lower()

    # Match exato tem prioridade
    if TRIGGER_EXACT.lower() in text_lower:
        return True

    # Verificar keywords
    for keyword in TRIGGER_KEYWORDS:
        if keyword.lower() in text_lower:
            return True

    return False


def handle_message(phone: str, sender_name: str, text: str) -> str:
    """
    Processa mensagem e retorna resposta do agente.

    Args:
        phone: Número do lead (ex: "5585987654321")
        sender_name: Nome do lead
        text: Conteúdo da mensagem

    Returns:
        Resposta do agente (ou None se não é trigger)
    """

    # 1. Verificar trigger
    if not is_trigger(text):
        return None

    # 2. Criar/carregar lead
    lead_id = create_lead(phone, name=sender_name)

    # 3. Carregar sessão existente ou criar nova
    messages = load_session(lead_id) or []

    # 4. Adicionar mensagem do usuário
    user_message = {"role": "user", "content": text}
    messages.append(user_message)
    add_message(lead_id, "user", text)

    # 5. Chamar IA
    response = call_ai(messages)

    # 6. Adicionar resposta do agente
    messages.append({"role": "assistant", "content": response})
    add_message(lead_id, "assistant", response)

    # 7. Salvar sessão
    save_session(lead_id, messages)

    # 8. Verificar intenção de compra
    if is_purchase_intent(text, messages) and len(messages) >= 4:
        response += f"\n\n{format_checkout_message()}"
        mark_checkout_sent(lead_id)

    return response


def test_trigger():
    """Teste de trigger (para setup/test_agent.py)."""
    test_messages = [
        TRIGGER_EXACT,
        "Oi, tenho uma dúvida sobre o produto",
        "Não é trigger"
    ]

    print("Testando triggers:\n")
    for msg in test_messages:
        result = "✅ Detectado" if is_trigger(msg) else "❌ Ignorado"
        print(f"  \"{msg}\" → {result}")

    return True


def main():
    """Interface CLI para teste."""
    import argparse

    parser = argparse.ArgumentParser(description="Agente WhatsApp v1.0")
    parser.add_argument("--test", action="store_true", help="Testa triggers")
    parser.add_argument("--chat", type=str, help="Chat interativo com phone")

    args = parser.parse_args()

    # Inicializar DB
    init_db()

    if args.test:
        test_trigger()
    elif args.chat:
        # Chat interativo
        print(f"\n💬 Chat com {args.chat}")
        print("(Digite 'sair' para encerrar)\n")

        while True:
            msg = input("Você: ").strip()
            if msg.lower() == "sair":
                break

            response = handle_message(
                phone=args.chat,
                sender_name="Teste",
                text=msg
            )

            if response:
                print(f"Agente: {response}\n")
            else:
                print("(Mensagem ignorada — não contém trigger)\n")
    else:
        print("Use: python3 agent.py --test")
        print("     python3 agent.py --chat PHONE")


if __name__ == "__main__":
    main()
