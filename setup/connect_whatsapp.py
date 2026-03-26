#!/usr/bin/env python3
"""
connect_whatsapp.py — Conecta número WhatsApp via QR Code
"""
import json
import time
from pathlib import Path

# Evolution API local — apikey padrão (definida no docker-compose)
EVOLUTION_API_KEY = "your-api-key"  # substituído pelo install_evolution.py se necessário

def _get_api_key():
    """Lê apikey do .env gerado pelo install_evolution.py, se existir."""
    env_file = Path.home() / ".openclaw" / "evolution-api" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("AUTHENTICATION_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"')
    # Fallback: tenta a apikey padrão da instalação existente
    return EVOLUTION_API_KEY

def call_api(endpoint, method="GET", data=None):
    """Faz chamada HTTP para Evolution API com apikey obrigatório."""
    import urllib.request
    import urllib.error

    url = f"http://localhost:8080{endpoint}"
    api_key = _get_api_key()

    headers = {
        "Content-Type": "application/json",
        "apikey": api_key,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data else None,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read())
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=" * 60)
    print("📱 Conectando WhatsApp")
    print("=" * 60)

    instance_name = "meu-agente"

    # 1. Verificar se instância já existe
    print(f"\n1️⃣  Verificando instância: {instance_name}")
    existing = call_api(f"/instance/fetchInstances", method="GET")
    instances = existing if isinstance(existing, list) else []
    # Evolution API v2: campo "name" direto; v1: dentro de "instance.instanceName"
    instance_names = [
        i.get("name", "") or i.get("instance", {}).get("instanceName", "")
        for i in instances
    ]

    if instance_name in instance_names:
        print(f"   ✅ Instância já existe: {instance_name}")
    else:
        print(f"   Criando instância...")
        result = call_api("/instance/create", method="POST", data={
            "instanceName": instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        })
        if "error" in result and "already" not in str(result.get("error", "")):
            print(f"   ❌ Erro ao criar instância: {result['error']}")
            return
        print(f"   ✅ Instância criada")

    # 2. Gerar QR Code
    print("\n2️⃣  Gerando QR Code...")
    qr_result = call_api(f"/instance/connect/{instance_name}", method="GET")

    # Evolution API v2: base64 direto; v1: dentro de "qrcode.base64" ou string
    qr_data = qr_result.get("base64")
    if not qr_data:
        qrcode_field = qr_result.get("qrcode")
        if isinstance(qrcode_field, dict):
            qr_data = qrcode_field.get("base64")
        elif isinstance(qrcode_field, str):
            qr_data = qrcode_field

    if qr_data:
        # Salvar QR Code como imagem PNG e abrir no visualizador
        import base64, subprocess, tempfile, os
        img_path = Path(tempfile.gettempdir()) / "agente-qrcode.png"
        try:
            img_bytes = base64.b64decode(qr_data.split(",")[-1])
            img_path.write_bytes(img_bytes)
            subprocess.Popen(["open", str(img_path)])
            print(f"   ✅ QR Code aberto na tela!")
            print(f"   📱 Abra o WhatsApp no celular → Configurações → Aparelhos Conectados → Conectar Aparelho")
        except Exception:
            print(f"   QR Code (cole em um decoder online): {str(qr_data)[:200]}")
    else:
        print(f"   ⚠️  Resposta inesperada: {qr_result}")

    # 3. Aguardar conexão
    print("\n3️⃣  Aguardando scan do QR Code (até 90s)...")
    for i in range(90):
        status_result = call_api(f"/instance/connectionState/{instance_name}", method="GET")
        state = status_result.get("instance", {}).get("state", "") or status_result.get("state", "")

        if state == "open":
            print(f"   ✅ WhatsApp conectado!")
            break

        if i % 15 == 0 and i > 0:
            print(f"   (aguardando... {i}s)")
        time.sleep(1)
    else:
        print("   ⚠️  Timeout — se o QR Code expirou, rode novamente")

    print("\n" + "=" * 60)
    print("✅ WhatsApp conectado!")
    print("=" * 60)
    print(f"\nInstância: {instance_name}")
    print("\nProxima etapa:")
    print("  python3 setup/test_api.py\n")

if __name__ == '__main__':
    main()
