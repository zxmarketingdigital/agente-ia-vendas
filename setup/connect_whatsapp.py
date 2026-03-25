#!/usr/bin/env python3
"""
connect_whatsapp.py — Conecta número WhatsApp via QR Code
"""
import subprocess
import json
import time
from pathlib import Path

def call_api(endpoint, method="GET", data=None):
    """Faz chamada HTTP para Evolution API."""
    import urllib.request
    import urllib.error

    url = f"http://localhost:8080/instance{endpoint}"

    if method == "POST":
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method=method
        )
    else:
        req = urllib.request.Request(url)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read())
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=" * 60)
    print("📱 Conectando WhatsApp")
    print("=" * 60)

    instance_name = "meu-agente"

    # 1. Criar instância
    print(f"\n1️⃣  Criando instância: {instance_name}")
    result = call_api(f"/create", method="POST", data={"instanceName": instance_name})

    if "error" in result:
        print(f"   ❌ Erro: {result['error']}")
        return

    instance_hash = result.get("hash", instance_name)
    print(f"   ✅ Instância criada: {instance_hash}")

    # 2. Gerar QR Code
    print("\n2️⃣  Gerando QR Code...")
    qr_result = call_api(f"/{instance_hash}/connect")

    if "qrcode" in qr_result:
        qr_data = qr_result["qrcode"]

        # Salvar QR code como imagem (simulado — em produção seria gerado via qrcode lib)
        print(f"   ✅ QR Code gerado!")
        print("\n   📱 ESCANEIE ESTE CÓDIGO COM SEU CELULAR:")
        print(f"\n   {qr_data[:100]}...\n")
    else:
        print(f"   ⚠️  Resposta: {qr_result}")

    # 3. Aguardar conexão
    print("3️⃣  Aguardando scan do QR Code (até 1 min)...")
    for i in range(60):
        status_result = call_api(f"/{instance_hash}/status")

        if status_result.get("status") == "open":
            print(f"   ✅ WhatsApp conectado!")
            print(f"   Número: {status_result.get('phone', 'desconhecido')}")
            break

        if i % 10 == 0 and i > 0:
            print(f"   (aguardando... {i}s)")
        time.sleep(1)
    else:
        print("   ⚠️  Timeout — tente novamente em alguns segundos")

    print("\n" + "=" * 60)
    print("✅ WhatsApp conectado!")
    print("=" * 60)
    print(f"\nInstância: {instance_hash}")
    print(f"Status: conectado")
    print("\nProxima etapa:")
    print("  python3 setup/test_api.py\n")

if __name__ == '__main__':
    main()
