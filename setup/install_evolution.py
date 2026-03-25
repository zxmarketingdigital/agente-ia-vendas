#!/usr/bin/env python3
"""
install_evolution.py — Baixa e configura Evolution API
"""
import subprocess
import json
import secrets
from pathlib import Path

def is_already_running():
    """Verifica se já existe uma Evolution API rodando na porta 8080."""
    try:
        import urllib.request
        response = urllib.request.urlopen("http://localhost:8080/", timeout=3)
        data = json.loads(response.read())
        return "Evolution API" in data.get("message", "")
    except:
        return False


def main():
    print("=" * 60)
    print("📦 Instalando Evolution API")
    print("=" * 60)

    # Verificar se já está rodando
    print("\n🔍 Verificando se já existe uma Evolution API rodando...")
    if is_already_running():
        print("✅ Evolution API já está rodando em localhost:8080!")
        print("   Não é necessário instalar novamente.")
        print("\nProxima etapa:")
        print("  python3 setup/connect_whatsapp.py\n")
        return

    home = Path.home()
    evo_dir = home / "meu-agente" / "evolution-api"

    # 1. Criar diretório
    print(f"\n1️⃣  Criando diretório: {evo_dir}")
    evo_dir.mkdir(parents=True, exist_ok=True)

    # 2. Clonar Evolution API
    print("2️⃣  Clonando Evolution API...")
    repo_url = "https://github.com/EvolutionAPI/evolution-api.git"
    if not (evo_dir / ".git").exists():
        subprocess.run(
            ["git", "clone", repo_url, str(evo_dir)],
            check=False
        )
    else:
        print("   (já clonado)")

    # 3. Criar .env para Evolution API
    print("3️⃣  Criando .env...")
    api_key = secrets.token_urlsafe(32)
    jwt_secret = secrets.token_urlsafe(32)

    env_file = evo_dir / ".env"
    env_content = f"""# Evolution API Configuration
RABBITMQ_ENABLED=false
DB_CONNECTION=sqlite
DB_SAVE_DATA_INSTANCE=true
DB_SAVE_DATA_NEW_MESSAGE=true
DB_URL=file:./evolution.db
LOG_LEVEL=warn
API_KEY={api_key}
API_URL=http://localhost:8080
JWT_SECRET={jwt_secret}
LANGUAGE=pt
"""
    env_file.write_text(env_content)
    print(f"   API Key: {api_key[:16]}...")

    # 4. Docker Compose
    print("4️⃣  Iniciando Docker...")
    subprocess.run(
        ["docker", "compose", "up", "-d"],
        cwd=str(evo_dir),
        check=False
    )

    # 5. Aguardar API
    print("5️⃣  Aguardando Evolution API (até 2 min)...")
    import time
    for i in range(120):
        try:
            import urllib.request
            response = urllib.request.urlopen("http://localhost:8080/health", timeout=2)
            if response.status == 200:
                print("   ✅ Evolution API está pronta!")
                break
        except:
            if i % 10 == 0 and i > 0:
                print(f"   (aguardando... {i}s)")
            time.sleep(1)
    else:
        print("   ⚠️  Timeout — tente: docker logs evolution-api-api-1")

    print("\n" + "=" * 60)
    print("✅ Evolution API instalada!")
    print("=" * 60)
    print(f"\nDiretório: {evo_dir}")
    print(f"API Key salva em: {env_file}")
    print("\nProxima etapa:")
    print("  python3 setup/connect_whatsapp.py\n")

if __name__ == '__main__':
    main()
