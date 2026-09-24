#!/usr/bin/env python3
"""Instala a Evolution API v2 para o agente de vendas."""
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


def _positive_int(value, default):
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


EVO_DIR = Path(os.environ.get("ZX_EVO_DIR") or Path.home() / "meu-agente" / "evolution-api")
EVO_PORT = _positive_int(os.environ.get("ZX_EVO_PORT") or 8080, 8080)
EVO_PROJECT = os.environ.get("ZX_EVO_PROJECT") or "meu-agente-evolution"
EVO_IMAGE = "evoapicloud/evolution-api:v2.3.7"
PG_IMAGE = "postgres:15"
WAIT_SECONDS = _positive_int(os.environ.get("ZX_EVO_WAIT_TIMEOUT") or 600, 600)


def _request_json(path, api_key=None):
    headers = {"apikey": api_key} if api_key else {}
    request = urllib.request.Request(f"http://localhost:{EVO_PORT}{path}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, json.loads(body)
    except Exception:
        return None, None


def evolution_ok():
    """Confirma que a API que responde nesta porta é a Evolution."""
    status, data = _request_json("/")
    return status == 200 and isinstance(data, dict) and "Evolution API" in str(data.get("message", ""))


def _read_env(path):
    values = {}
    if not path.exists():
        return values
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip('"')
    except OSError:
        pass
    return values


def _key_is_valid(api_key):
    status, _ = _request_json("/instance/fetchInstances", api_key)
    return status == 200


def _is_new_format():
    env_values = _read_env(EVO_DIR / ".env")
    compose_file = EVO_DIR / "docker-compose.yml"
    try:
        compose_text = compose_file.read_text(encoding="utf-8")
    except OSError:
        compose_text = ""
    return env_values.get("DATABASE_PROVIDER") == "postgresql" and EVO_IMAGE in compose_text


def _run(command, **kwargs):
    try:
        return subprocess.run(command, check=False, **kwargs)
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"   Não consegui executar {' '.join(command)}: {error}")
        return None


def _docker_is_ready():
    if not shutil.which("docker"):
        print("❌ Não encontrei o Docker. Instale e abra o Docker Desktop antes de continuar.")
        return False

    info = _run(["docker", "info"], timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not info or info.returncode != 0:
        print("❌ O Docker não está pronto. Abra o Docker Desktop e espere a baleia ficar estável.")
        return False

    compose = _run(["docker", "compose", "version"], timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not compose or compose.returncode != 0:
        print("❌ O Docker Compose v2 não está disponível. No Linux, instale o plugin 'docker compose'.")
        return False
    return True


def _archive_old_installation():
    print("\n🔄 Encontrei uma instalação antiga da Evolution. Vou guardá-la antes de recriar.")
    _run(["docker", "compose", "down", "--remove-orphans"], cwd=str(EVO_DIR), timeout=120)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archived = EVO_DIR.with_name(f"{EVO_DIR.name}.antigo-{timestamp}")
    suffix = 1
    while archived.exists():
        archived = EVO_DIR.with_name(f"{EVO_DIR.name}.antigo-{timestamp}-{suffix}")
        suffix += 1
    EVO_DIR.rename(archived)
    print(f"   Instalação anterior guardada em: {archived}")


def _write_files(api_key, pg_password):
    EVO_DIR.mkdir(parents=True, exist_ok=True)
    env_file = EVO_DIR / ".env"
    env_file.write_text(
        f"""# Gerado por setup/install_evolution.py — nao edite a mao
# A Evolution API v2 NAO suporta SQLite: o banco dela e Postgres (container ao lado).
SERVER_TYPE=http
SERVER_PORT=8080
SERVER_URL=http://localhost:{EVO_PORT}
AUTHENTICATION_API_KEY={api_key}
AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES=true
POSTGRES_PASSWORD={pg_password}
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=postgresql://evolution:{pg_password}@postgres:5432/evolution?schema=evolution_api
DATABASE_CONNECTION_CLIENT_NAME=meu_agente
DATABASE_SAVE_DATA_INSTANCE=true
DATABASE_SAVE_DATA_NEW_MESSAGE=true
DATABASE_SAVE_MESSAGE_UPDATE=true
DATABASE_SAVE_DATA_CONTACTS=true
DATABASE_SAVE_DATA_CHATS=true
CACHE_REDIS_ENABLED=false
CACHE_LOCAL_ENABLED=true
DEL_INSTANCE=false
CONFIG_SESSION_PHONE_CLIENT=Meu Agente
CONFIG_SESSION_PHONE_NAME=Chrome
LOG_LEVEL=ERROR,WARN
LOG_BAILEYS=error
""",
        encoding="utf-8",
    )
    if os.name != "nt":
        try:
            os.chmod(env_file, 0o600)
        except OSError:
            pass

    compose_file = EVO_DIR / "docker-compose.yml"
    compose_file.write_text(
        f"""# Gerado por setup/install_evolution.py
name: {EVO_PROJECT}
services:
  evolution-api:
    image: {EVO_IMAGE}
    restart: unless-stopped
    env_file: .env
    ports:
      - \"127.0.0.1:{EVO_PORT}:8080\"
    volumes:
      - evolution_instances:/evolution/instances
    depends_on:
      postgres:
        condition: service_healthy
  postgres:
    image: {PG_IMAGE}
    restart: unless-stopped
    environment:
      POSTGRES_DB: evolution
      POSTGRES_USER: evolution
      POSTGRES_PASSWORD: {pg_password}
    healthcheck:
      test: [\"CMD-SHELL\", \"pg_isready -U evolution -d evolution\"]
      interval: 5s
      timeout: 5s
      retries: 20
    volumes:
      - postgres_data:/var/lib/postgresql/data
volumes:
  evolution_instances:
  postgres_data:
""",
        encoding="utf-8",
    )
    if os.name != "nt":
        try:
            os.chmod(compose_file, 0o600)
        except OSError:
            pass
    return env_file


def _show_logs(lines, service=None):
    command = ["docker", "compose", "-p", EVO_PROJECT, "logs", "--tail", str(lines)]
    if service:
        command.append(service)
    print(f"   Comando: {' '.join(command)}")
    _run(command, cwd=str(EVO_DIR), timeout=120)


def main():
    print("=" * 60)
    print("📦 Instalando Evolution API")
    print("=" * 60)

    if not _docker_is_ready():
        return 1

    env_values = _read_env(EVO_DIR / ".env")
    if evolution_ok():
        if _is_new_format() and env_values.get("AUTHENTICATION_API_KEY") and _key_is_valid(env_values["AUTHENTICATION_API_KEY"]):
            print(f"✅ A Evolution API deste agente já está rodando em localhost:{EVO_PORT}.")
            print("\nPróxima etapa:")
            print("  python3 setup/connect_whatsapp.py")
            return 0
        print(f"❌ Já existe OUTRA Evolution API na porta {EVO_PORT} que não foi criada por este setup.")
        print("   Pare esse container no Docker Desktop e rode este instalador novamente.")
        return 1

    if EVO_DIR.exists() and not _is_new_format():
        _archive_old_installation()

    env_values = _read_env(EVO_DIR / ".env")
    api_key = env_values.get("AUTHENTICATION_API_KEY") or secrets.token_hex(24)
    pg_password = env_values.get("POSTGRES_PASSWORD") or secrets.token_hex(16)
    env_file = _write_files(api_key, pg_password)

    print("\n🐳 Iniciando Evolution API e o banco Postgres...")
    started = _run(
        ["docker", "compose", "-p", EVO_PROJECT, "up", "-d"],
        cwd=str(EVO_DIR),
        timeout=1800,
    )
    if not started or started.returncode != 0:
        print("❌ A Evolution não conseguiu iniciar. Últimas mensagens do Docker:")
        _show_logs(50)
        return 1

    print(f"\n⏳ Aguardando a Evolution API ficar pronta (até {WAIT_SECONDS}s)...")
    started_at = time.monotonic()
    last_progress = 0
    while time.monotonic() - started_at < WAIT_SECONDS:
        elapsed = int(time.monotonic() - started_at)
        if evolution_ok() and _key_is_valid(api_key):
            print(f"✅ Evolution API pronta: levou {elapsed}s (teto {WAIT_SECONDS}s).")
            print(f"   Diretório: {EVO_DIR}")
            print(f"   Chave em AUTHENTICATION_API_KEY no {env_file} ({api_key[:6]}...)")
            print("\nPróxima etapa:")
            print("  python3 setup/connect_whatsapp.py")
            return 0
        if elapsed >= last_progress + 20:
            print(f"   (aguardando... {elapsed}s)")
            last_progress = elapsed
        time.sleep(2)

    elapsed = int(time.monotonic() - started_at)
    print(f"❌ A Evolution não ficou pronta: levou {elapsed}s (teto {WAIT_SECONDS}s).")
    print("Últimas mensagens da Evolution:")
    _show_logs(40, "evolution-api")
    return 1


if __name__ == "__main__":
    sys.exit(main())
