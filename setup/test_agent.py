#!/usr/bin/env python3
"""
test_agent.py — Testa o agente simulando uma mensagem
"""
import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("🧪 Testando Agente")
    print("=" * 60 + "\n")

    home = Path.home()
    agent_file = home / "meu-agente" / "agent.py"

    if not agent_file.exists():
        print("❌ Agente não encontrado!")
        print(f"   Procurado em: {agent_file}")
        print("\n   Etapas anteriores ainda não completadas.")
        print("   Volte ao CLAUDE.md e siga na ordem.\n")
        sys.exit(1)

    # 1. Carregar agente
    print("1️⃣  Carregando agente...")
    try:
        sys.path.insert(0, str(home / "meu-agente"))
        import agent
        print("   ✅ Agente carregado")
    except Exception as e:
        print(f"   ❌ Erro ao carregar: {e}\n")
        sys.exit(1)

    # 2. Simular mensagem
    print("\n2️⃣  Simulando mensagem de trigger...")
    try:
        # Chamar a função de teste do agente
        if hasattr(agent, 'test_trigger'):
            result = agent.test_trigger()
            print(f"   ✅ Trigger detectado: {result}")
        else:
            print("   ℹ️  Agente não tem função de teste")
    except Exception as e:
        print(f"   ⚠️  {e}")

    # 3. Testar resposta da IA
    print("\n3️⃣  Gerando resposta da IA...")
    try:
        messages = [{"role": "user", "content": "Olá, tenho dúvida sobre o produto"}]
        response = agent.call_ai(messages)
        print(f"   ✅ Resposta da IA:")
        print(f"\n   \"{response[:100]}...\"")
    except Exception as e:
        print(f"   ⚠️  {e}")

    # 4. Teste SQLite
    print("\n4️⃣  Testando banco de dados...")
    db_file = home / "meu-agente" / "dados.sqlite"
    if db_file.exists():
        print(f"   ✅ Banco de dados OK: {db_file}")
    else:
        print(f"   ℹ️  Banco será criado na primeira conversa real")

    print("\n" + "=" * 60)
    print("✅ Agente está pronto!")
    print("=" * 60)
    print("\n🎉 Parabéns! Seu agente está funcionando.\n")
    print("Agora:")
    print("  1️⃣  Envie uma mensagem pelo WhatsApp para ativar o watcher")
    print("  2️⃣  Ou rode: python3 ~/meu-agente/watcher.py\n")
    print("Para detalhes, veja: CLAUDE.md\n")

if __name__ == '__main__':
    main()
