#!/usr/bin/env python3
"""
check_prerequisites.py — Verifica se todos os pré-requisitos estão instalados
"""
import subprocess
import sys
from pathlib import Path

def check_command(cmd, name, min_version=None):
    """Verifica se um comando está instalado e sua versão."""
    try:
        result = subprocess.run(
            [cmd, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        version = result.stdout.split('\n')[0] if result.stdout else "instalado"
        print(f"  ✅ {name}: {version}")
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def main():
    print("=" * 60)
    print("🔍 Verificando Pré-requisitos")
    print("=" * 60)

    checks = [
        ('python3', 'Python 3.9+'),
        ('node', 'Node.js 18+'),
        ('git', 'Git'),
        ('docker', 'Docker'),
    ]

    missing = []
    for cmd, name in checks:
        print(f"\n{name}:", end=" ")
        if not check_command(cmd, name):
            print(f"  ❌ {name} NÃO instalado!")
            missing.append((name, cmd))

    if missing:
        print("\n" + "=" * 60)
        print("❌ Faltam dependências!")
        print("=" * 60)

        for name, cmd in missing:
            print(f"\n📦 {name}:")
            if 'Python' in name:
                print("  macOS: brew install python3")
                print("  Linux: sudo apt install python3 python3-pip")
                print("  Windows: scoop install python")
            elif 'Node' in name:
                print("  macOS: brew install node")
                print("  Linux: curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash")
                print("  Windows: scoop install nodejs")
            elif 'Git' in name:
                print("  macOS: brew install git")
                print("  Linux: sudo apt install git")
                print("  Windows: scoop install git")
            elif 'Docker' in name:
                print("  macOS/Windows: https://www.docker.com/products/docker-desktop")
                print("  Linux: sudo apt install docker.io docker-compose")

        print("\nDepois de instalar, rode novamente:")
        print("  python3 setup/check_prerequisites.py\n")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ Todos os pré-requisitos estão instalados!")
    print("=" * 60)
    print("\nProxima etapa:")
    print("  python3 setup/install_evolution.py\n")

if __name__ == '__main__':
    main()
