# Pré-requisitos por Sistema Operacional

## macOS (Recomendado)

### Python 3.9+
```bash
brew install python3
python3 --version  # Deve ser 3.9 ou maior
```

### Node.js 18+
```bash
brew install node
node --version
```

### Docker
Baixe em: https://www.docker.com/products/docker-desktop

Depois de instalar, abra o app Docker desktop.

### Git
```bash
brew install git
git --version
```

## Linux (Ubuntu/Debian)

### Python 3.9+
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version
```

### Node.js 18+
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
node --version
```

### Docker
```bash
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
docker --version
```

### Git
```bash
sudo apt install git
git --version
```

## Windows (WSL2 recomendado)

Use WSL2 para ter Linux dentro do Windows:

```powershell
wsl --install ubuntu
```

Depois siga as instruções do Linux acima.

## Verificar Tudo de Vez

```bash
python3 setup/check_prerequisites.py
```

Se tudo estiver OK, continua com:

```bash
python3 setup/install_evolution.py
```
