#!/usr/bin/env python3
"""
test_api.py — Testa chave de IA (OpenAI, Gemini, Anthropic)
"""
import sys
import argparse
import json

def test_openai(api_key):
    """Testa OpenAI API."""
    import urllib.request
    import urllib.error

    url = "https://api.openai.com/v1/chat/completions"
    data = {
        "model": "gpt-5.4-mini",
        "messages": [{"role": "user", "content": "Responda com 'IA funcionando!' apenas."}],
        "max_completion_tokens": 50
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read())
            message = result["choices"][0]["message"]["content"]
            return True, message
    except Exception as e:
        return False, str(e)

def test_gemini(api_key):
    """Testa Google Gemini API."""
    import urllib.request
    import urllib.error

    url = f"https://generativelanguage.googleapis.com/v1beta/openai/chat/completions?key={api_key}"
    data = {
        "model": "gemini-2.5-flash",
        "messages": [{"role": "user", "content": "Responda com 'IA funcionando!' apenas."}],
        "max_completion_tokens": 50
    }

    headers = {"Content-Type": "application/json"}

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read())
            message = result["choices"][0]["message"]["content"]
            return True, message
    except Exception as e:
        return False, str(e)

def test_anthropic(api_key):
    """Testa Anthropic API."""
    import urllib.request
    import urllib.error

    url = "https://api.anthropic.com/v1/messages"
    data = {
        "model": "claude-opus-4-6",
        "max_tokens": 50,
        "messages": [{"role": "user", "content": "Responda com 'IA funcionando!' apenas."}]
    }

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read())
            message = result["content"][0]["text"]
            return True, message
    except Exception as e:
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(description="Testa chave de IA")
    parser.add_argument("--provider", choices=["openai", "gemini", "anthropic"], required=True)
    parser.add_argument("--key", required=True)

    args = parser.parse_args()

    print("=" * 60)
    print(f"🧪 Testando {args.provider.upper()}")
    print("=" * 60 + "\n")

    if args.provider == "openai":
        success, message = test_openai(args.key)
    elif args.provider == "gemini":
        success, message = test_gemini(args.key)
    else:  # anthropic
        success, message = test_anthropic(args.key)

    if success:
        print(f"✅ API funcionando!")
        print(f"   Resposta: {message}\n")
        print("Proxima etapa:")
        print("  python3 setup/test_agent.py\n")
    else:
        print(f"❌ Erro na API:")
        print(f"   {message}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
