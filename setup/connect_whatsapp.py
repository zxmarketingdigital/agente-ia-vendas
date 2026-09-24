#!/usr/bin/env python3
"""Conecta o WhatsApp do agente pela Evolution API."""
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


def _positive_int(value, default):
    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


EVO_DIR = Path(os.environ.get("ZX_EVO_DIR") or Path.home() / "meu-agente" / "evolution-api")
EVO_PORT = _positive_int(os.environ.get("ZX_EVO_PORT") or 8080, 8080)


def _get_api_key():
    """Lê a chave da Evolution gerada pelo instalador."""
    env_file = EVO_DIR / ".env"
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []
    for name in ("AUTHENTICATION_API_KEY", "API_KEY"):
        for line in lines:
            if line.startswith(f"{name}="):
                value = line.split("=", 1)[1].strip().strip('"')
                if value:
                    return value
    return None


def call_api(endpoint, method="GET", data=None, timeout=10):
    """Faz uma chamada autenticada à Evolution API local."""
    api_key = _get_api_key()
    if not api_key:
        return {"error": "Chave da Evolution não encontrada", "status": 401}
    request = urllib.request.Request(
        f"http://localhost:{EVO_PORT}{endpoint}",
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers={"Content-Type": "application/json", "apikey": api_key},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {error.code}: {body[:300]}", "status": error.code}
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as error:
        return {"error": str(error)}


def _open_qr_code(path):
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=True)
        elif os.name == "nt":
            os.startfile(str(path))
        else:
            subprocess.run(["xdg-open", str(path)], check=True)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def main():
    print("=" * 60)
    print("📱 Conectando WhatsApp")
    print("=" * 60)

    if not _get_api_key():
        print("❌ Não encontrei a chave da Evolution. Rode antes: python3 setup/install_evolution.py")
        return 1

    instance_name = "meu-agente"
    print(f"\n1️⃣  Verificando instância: {instance_name}")
    existing = call_api("/instance/fetchInstances")
    if isinstance(existing, dict) and existing.get("status") in (401, 403):
        print("❌ A chave da Evolution não confere — rode python3 setup/install_evolution.py de novo.")
        return 1
    instances = existing if isinstance(existing, list) else []
    instance_names = [
        item.get("name", "") or item.get("instance", {}).get("instanceName", "")
        for item in instances
        if isinstance(item, dict)
    ]
    if instance_name in instance_names:
        print(f"   ✅ Instância já existe: {instance_name}")
    else:
        print("   Criando instância...")
        created = call_api(
            "/instance/create",
            method="POST",
            data={"instanceName": instance_name, "qrcode": True, "integration": "WHATSAPP-BAILEYS"},
        )
        if not isinstance(created, dict) or ("error" in created and "already" not in str(created["error"]).lower()):
            error_message = created.get("error", "resposta inesperada") if isinstance(created, dict) else str(created)
            print(f"   ❌ Erro ao criar instância: {error_message}")
            return 1
        print("   ✅ Instância criada")

    print("\n2️⃣  Gerando QR Code...")
    qr_result = call_api(f"/instance/connect/{instance_name}")
    qr_data = qr_result.get("base64") if isinstance(qr_result, dict) else None
    if not qr_data and isinstance(qr_result, dict):
        qrcode_field = qr_result.get("qrcode")
        qr_data = qrcode_field.get("base64") if isinstance(qrcode_field, dict) else qrcode_field
    if not qr_data:
        print("   ❌ Não consegui gerar o QR Code. Rode este passo novamente.")
        return 1

    try:
        qr_bytes = base64.b64decode(str(qr_data).split(",")[-1])
        file_descriptor, img_name = tempfile.mkstemp(prefix="agente-qrcode-", suffix=".png")
        img_path = Path(img_name)
        with os.fdopen(file_descriptor, "wb") as image_file:
            image_file.write(qr_bytes)
    except (ValueError, OSError) as error:
        print(f"   ❌ Não consegui salvar o QR Code: {error}")
        return 1
    if _open_qr_code(img_path):
        print("   ✅ QR Code aberto na tela!")
    else:
        print(f"   Abra manualmente o QR Code salvo em: {img_path}")
    print("   📱 No celular: WhatsApp → Configurações → Aparelhos conectados → Conectar aparelho.")

    print("\n3️⃣  Aguardando o scan do QR Code (até 90s)...")
    deadline = time.monotonic() + 90
    last_progress = 0
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        status_result = call_api(f"/instance/connectionState/{instance_name}", timeout=remaining)
        state = ""
        if isinstance(status_result, dict):
            state = status_result.get("instance", {}).get("state", "") or status_result.get("state", "")
        if state == "open":
            print("\n" + "=" * 60)
            print("✅ WhatsApp conectado!")
            print("=" * 60)
            print(f"\nInstância: {instance_name}")
            print(f"EVOLUTION_API_KEY para o watcher: veja AUTHENTICATION_API_KEY em {EVO_DIR}/.env")
            print("\nPróxima etapa:")
            print("  python3 setup/test_api.py")
            return 0
        elapsed = int(90 - max(0, deadline - time.monotonic()))
        if elapsed >= last_progress + 15:
            print(f"   (aguardando... {elapsed}s)")
            last_progress = elapsed
        time.sleep(min(1, max(0, deadline - time.monotonic())))

    print("❌ O QR Code expirou ou não foi escaneado a tempo. Rode este passo novamente.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
