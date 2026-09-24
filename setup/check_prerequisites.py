#!/usr/bin/env python3
"""
check_prerequisites.py — Verifica se todos os pre-requisitos estao instalados.

Rodado pela IA na Etapa 1 do SETUP.md. Alem de conferir os programas, ele confirma
que estamos DENTRO da pasta do produto e que o clone esta completo — o erro numero 1
dos alunos (13/Ago/26: 8 compradores travados em 7 dias) e' abrir a IA na pasta errada,
e ai ela nao encontra o roteiro e comeca a inventar um bot do zero.

Compativel com Python 3.6+ de proposito: se o aluno tiver um Python antigo, ele precisa
ver a mensagem "sua versao e' antiga", nao um SyntaxError.
"""
import os
import re
import subprocess
import sys
import unicodedata

REPO_URL = "https://github.com/zxmarketingdigital/agente-ia-vendas.git"

WINDOWS = os.name == "nt"

# Como o aluno chama o Python NESTA maquina. No Windows o instalador do python.org
# cria `python`/`py`, nao `python3` — e o alias `python3.exe` do sistema abre a
# Microsoft Store, que e' o erro confuso classico (review 13/Ago/26).
PY_CMD = "python" if WINDOWS else "python3"

# Versao minima de Node por CLI (campo `engines.node` do proprio pacote, conferido
# em 13/Ago/26): codex >=16, claude-code >=22. O piso do produto segue 20 (definido
# quando o Gemini CLI ainda era opcao; ele saiu em 24/Set/26 e o piso foi mantido pra
# nao mudar comportamento). O Claude Code, recomendado, e' avisado a parte abaixo.
NODE_MINIMO = (20,)
NODE_CLAUDE_CODE = (22,)

# Arquivos que provam que este e' o repositorio do produto, e nao uma pasta qualquer.
ARQUIVOS_ESSENCIAIS = [
    "SETUP.md",
    os.path.join("setup", "install_evolution.py"),
    os.path.join("setup", "connect_whatsapp.py"),
    os.path.join("templates", "whatsapp", "agent_template.py"),
    os.path.join("templates", "whatsapp", "watcher_template.py"),
    os.path.join("templates", "shared", "agent_core_template.py"),
    os.path.join("templates", "shared", "sessions_template.py"),
]

# nome exibido, comando, versao minima (None = nao valida versao)
CHECKS = [
    ("Node.js 20+", "node", NODE_MINIMO),
    ("Git", "git", None),
    ("Docker", "docker", None),
]

INSTRUCOES = {
    "python": [
        "Windows: baixe em https://www.python.org/downloads/ (marque 'Add to PATH')",
    ],
    "python3": [
        "macOS:   brew install python3",
        "Linux:   sudo apt install python3 python3-pip python3-venv",
    ],
    "node": [
        "macOS:   brew install node   (ou baixe em https://nodejs.org/en/download)",
        "Linux:   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash",
        "         export NVM_DIR=\"$HOME/.nvm\" && . \"$NVM_DIR/nvm.sh\"   (carrega o nvm nesta sessao)",
        "         nvm install 20",
        "Windows: winget install OpenJS.NodeJS.LTS",
    ],
    "git": [
        "macOS:   brew install git",
        "Linux:   sudo apt install git",
        "Windows: winget install Git.Git",
    ],
    "docker": [
        "macOS/Windows: https://www.docker.com/products/docker-desktop",
        "Linux:         siga https://docs.docker.com/engine/install/ (instala Docker + plugin compose)",
    ],
}


def raiz_do_repo():
    """Raiz do produto, derivada do proprio arquivo — nao do diretorio atual."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def checar_pasta():
    """Confirma que o clone esta completo. Retorna a lista de arquivos faltando."""
    raiz = raiz_do_repo()
    return [rel for rel in ARQUIVOS_ESSENCIAIS
            if not os.path.isfile(os.path.join(raiz, rel))]


def estamos_dentro_da_pasta():
    """O terminal precisa estar DENTRO da pasta, nao so o script.

    As etapas seguintes usam caminhos relativos (`setup/install_evolution.py`,
    `templates/...`). Se a IA chamar este arquivo por caminho absoluto de outro
    diretorio, os arquivos existem mas a Etapa 2 quebra — entao checamos os dois.
    """
    try:
        return os.path.realpath(os.getcwd()) == os.path.realpath(raiz_do_repo())
    except OSError:
        return False


def instrucao_de_clone():
    """Comandos de clone, uma linha por vez.

    Sem `&&` e sem `2>/dev/null`: no PowerShell do Windows o `&&` nao e' operador
    valido (PS 5.1) e `/dev/null` nao existe. Tres linhas separadas funcionam em
    bash, zsh, PowerShell e CMD — e continuam idempotentes: se o clone falhar
    porque a pasta ja existe, o `cd` e a abertura da IA acontecem do mesmo jeito.
    """
    return [
        "git clone %s" % REPO_URL,
        "cd agente-ia-vendas",
    ]


def extrair_versao(texto):
    """Primeiro numero de versao do texto: 'v18.20.4' -> (18, 20, 4)."""
    achado = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", texto or "")
    if not achado:
        return None
    return tuple(int(p) for p in achado.groups() if p is not None)


def rodar(args, timeout=10):
    """Executa e devolve (ok, saida). Nunca levanta excecao."""
    proc = None
    try:
        proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        saida = proc.communicate(timeout=timeout)[0]
        texto = (saida or b"").decode("utf-8", "replace").strip()
        return proc.returncode == 0, texto
    except subprocess.TimeoutExpired:
        # kill() sem wait() deixa processo zumbi — o filho so e' colhido no wait.
        try:
            proc.kill()
            proc.communicate()
        except Exception:
            pass
        return False, "tempo esgotado"
    except (OSError, ValueError):
        return False, ""


def checar_programa(nome, cmd, versao_minima):
    """Retorna (status, detalhe) onde status e' 'ok', 'ausente' ou 'antigo'."""
    ok, saida = rodar([cmd, "--version"])
    if not ok:
        return "ausente", ""

    primeira_linha = saida.split("\n")[0] if saida else "instalado"
    if versao_minima is None:
        return "ok", primeira_linha

    encontrada = extrair_versao(primeira_linha)
    if encontrada is None:
        # Nao conseguimos ler a versao: melhor deixar passar do que travar o aluno
        # por causa de um formato de saida inesperado.
        return "ok", primeira_linha
    if encontrada[:len(versao_minima)] < versao_minima:
        alvo = ".".join(str(n) for n in versao_minima)
        return "antigo", "%s (precisa ser %s ou maior)" % (primeira_linha, alvo)
    return "ok", primeira_linha


def versao_do_node():
    ok, saida = rodar(["node", "--version"])
    return extrair_versao(saida) if ok else None


def docker_esta_rodando():
    """Docker instalado != Docker aberto. Fechado, a Etapa 2 falha com erro confuso.

    30s porque o Docker Desktop recem-aberto demora a responder e um timeout curto
    reprovava quem tinha acabado de abrir o app.
    """
    ok, saida = rodar(["docker", "info"], timeout=30)
    return ok, saida


def docker_compose_v2():
    """A Etapa 2 roda `docker compose up -d` (plugin V2).

    Quem instalou so o `docker-compose` V1 (binario separado, comum no apt antigo)
    passa no `docker info` e quebra depois, na Evolution API.
    """
    ok, _ = rodar(["docker", "compose", "version"], timeout=20)
    return ok


def main():
    print("=" * 60)
    print("Verificando Pre-requisitos")
    print("=" * 60)

    # --- Etapa 0: estamos na pasta do produto? ------------------------------
    faltando_arquivos = checar_pasta()
    if faltando_arquivos:
        print("\n[X] PASTA ERRADA OU CLONE INCOMPLETO")
        print("=" * 60)
        print("\nNao encontrei estes arquivos do produto:")
        for rel in faltando_arquivos:
            print("   - %s" % rel)
        print("\nIA: PARE o setup aqui. Nao crie arquivos, nao instale nada e")
        print("NUNCA construa um agente de WhatsApp do zero. Peca ao usuario para")
        print("fechar a IA (/exit) e colar estas linhas no terminal, UMA POR VEZ:\n")
        for linha in instrucao_de_clone():
            print("   %s" % linha)
        print("\nDepois abrir a IA de novo DENTRO dessa pasta e digitar INICIAR SETUP.")
        sys.exit(2)

    if not estamos_dentro_da_pasta():
        print("\n[X] TERMINAL FORA DA PASTA DO PRODUTO")
        print("=" * 60)
        print("\nOs arquivos existem em:")
        print("   %s" % raiz_do_repo())
        print("mas o terminal esta em:")
        print("   %s" % os.getcwd())
        print("\nAs proximas etapas usam caminhos relativos e vao falhar assim.")
        print("IA: PARE e rode primeiro:\n")
        print("   cd %s\n" % raiz_do_repo())
        sys.exit(2)

    print("\n[OK] Pasta do produto confirmada:")
    print("     %s" % raiz_do_repo())

    # --- Python: conferido pelo interpretador que esta rodando este arquivo --
    ausentes = []
    antigos = []
    if sys.version_info[:2] < (3, 9):
        atual = ".".join(str(n) for n in sys.version_info[:3])
        print("\n%-14s [!]  Python %s (precisa ser 3.9 ou maior)" % ("Python 3.9+:", atual))
        antigos.append(("Python 3.9+", PY_CMD))
    else:
        print("\n%-14s [OK] Python %s" % (
            "Python 3.9+:", ".".join(str(n) for n in sys.version_info[:3])))

    # --- Demais programas ---------------------------------------------------
    for nome, cmd, versao_minima in CHECKS:
        status, detalhe = checar_programa(nome, cmd, versao_minima)
        if status == "ok":
            print("\n%-14s [OK] %s" % (nome + ":", detalhe))
        elif status == "antigo":
            print("\n%-14s [!]  %s" % (nome + ":", detalhe))
            antigos.append((nome, cmd))
        else:
            print("\n%-14s [X]  nao instalado" % (nome + ":"))
            ausentes.append((nome, cmd))

    # --- Docker precisa estar ABERTO, nao so instalado ----------------------
    docker_parado = False
    docker_sem_virtualizacao = False
    docker_wsl_apenas = False
    compose_ausente = False
    if not any(cmd == "docker" for _, cmd in ausentes):
        docker_ok, docker_saida = docker_esta_rodando()
        if docker_ok:
            print("\n%-14s [OK] em execucao" % "Docker ativo:")
            if docker_compose_v2():
                print("\n%-14s [OK] disponivel" % "docker compose:")
            else:
                compose_ausente = True
                print("\n%-14s [X]  plugin V2 ausente" % "docker compose:")
        else:
            docker_parado = True
            docker_saida_normalizada = unicodedata.normalize(
                "NFKD", docker_saida or ""
            ).encode("ascii", "ignore").decode("ascii").lower()
            # "wsl" sozinho (sem termo de virtualizacao/hypervisor junto) e' o caso
            # mais comum e mais simples: Windows limpo que nunca ativou o WSL. NAO
            # e' problema de BIOS — resolve com `wsl --install` + reiniciar. So e'
            # tratado como "falta virtualizacao" (BIOS) quando o texto menciona
            # explicitamente virtualizacao/hypervisor/hyper-v/vmx (achado real:
            # varios compradores caindo na tela "WSL is not installed" do Docker
            # Desktop e o script mandando eles pra BIOS por engano — 22-23/09/26).
            # NOTA (luna-review, 24/09/26, MEDIO aceito — nao ha caso real observado):
            # "hyperv"/"hyper-v" podem, em teoria, vir de um erro de COMPONENTE do Windows
            # ausente (ex.: HCS_E_HYPERV_NOT_INSTALLED) em vez de virtualizacao desligada na
            # BIOS — nesse caso o passo 3 da instrucao de BIOS (`wsl --install` no PowerShell
            # Admin + reiniciar) ainda resolve a maioria das vezes, porque reativa o
            # componente Hyper-V/Virtual Machine Platform junto. Nenhum dos 5 compradores do
            # 15M com defeito de Docker nesta auditoria (20-23/09/26) teve esse texto — todos
            # foram "WSL is not installed"/"There was a problem with WSL" puro. Mantido assim
            # de proposito (ver rule "escopo-sem-trava-inventada": nao ramificar por erro
            # hipotetico sem evidencia real); se aparecer caso real com HCS_E_HYPERV_*,
            # criar um terceiro branch dedicado.
            termos_virtualizacao = (
                "virtualization", "virtualisation", "hypervisor",
                "hyper-v", "hyperv", "vmx",
            )
            docker_sem_virtualizacao = any(
                termo in docker_saida_normalizada for termo in termos_virtualizacao
            )
            docker_wsl_apenas = (
                not docker_sem_virtualizacao and "wsl" in docker_saida_normalizada
            )
            print("\n%-14s [X]  instalado, mas NAO esta em execucao" % "Docker ativo:")

    problemas = ausentes + antigos

    if problemas or docker_parado or compose_ausente:
        print("\n" + "=" * 60)
        print("Faltam dependencias")
        print("=" * 60)

        for nome, cmd in problemas:
            print("\n%s:" % nome)
            for linha in INSTRUCOES.get(cmd, []):
                print("  " + linha)

        if docker_parado:
            if docker_wsl_apenas:
                print("\nDocker Desktop mostrou 'WSL is not installed' / 'There was a problem")
                print("with WSL'. Isto NAO e' problema de BIOS/virtualizacao - e' so o recurso")
                print("WSL que nunca foi ativado neste Windows. E' o erro mais comum de quem")
                print("esta instalando pela primeira vez, resolve em 3 passos:")
                print("  1) Abra o PowerShell como Administrador (clique direito no icone ->")
                print("     'Executar como Administrador')")
                print("  2) Rode: wsl --install")
                print("     (se ja tiver WSL mas desatualizado: wsl --update)")
                print("  3) Reinicie o computador e abra o Docker Desktop de novo - espere o")
                print("     icone da baleia ficar estavel")
                print("Só vá para os passos de BIOS abaixo se a mensagem do Docker Desktop for")
                print("especificamente 'Virtualization support not detected'.")
            elif docker_sem_virtualizacao:
                print("\nDocker Desktop esta instalado mas NAO consegue iniciar: falta suporte a")
                print("virtualizacao. Instalar de novo NAO resolve - o ajuste e' fora do Docker.")
                print("  Windows: 1) reinicie e entre na BIOS/UEFI (tecla F2, F10, DEL ou ESC no")
                print("               boot, varia por fabricante)")
                print("           2) ative 'Intel VT-x' / 'AMD-V' / 'SVM Mode' (fica em Advanced,")
                print("               CPU Configuration ou Security)")
                print("           3) salve, reinicie e rode no PowerShell como Administrador:")
                print("               wsl --install")
                print("           4) reinicie de novo e abra o Docker Desktop")
                print("  macOS:   virtualizacao vem ligada de fabrica; se deu esse erro, e' o app")
                print("           corrompido - desinstale e reinstale o Docker Desktop")
                print("  Linux:   confira com: grep -Eoc '(vmx|svm)' /proc/cpuinfo")
                print("           (0 = desabilitado na BIOS, mesmo passo do Windows)")
                print("  Alternativa sem BIOS (macOS): brew install orbstack - o OrbStack roda os")
                print("  mesmos containers e substitui o Docker Desktop no resto do setup.")
            else:
                print("\nDocker esta instalado, mas o servico nao respondeu.")
                print("  macOS/Windows: abra o app Docker Desktop e espere o icone")
                print("                 da baleia ficar estavel. No Windows, se aparecer")
                print("                 'WSL is not installed', rode 'wsl --install' no")
                print("                 PowerShell como Administrador e reinicie.")
                print("  Linux:         sudo systemctl start docker")

        if compose_ausente:
            print("\nO comando `docker compose` (plugin V2) nao respondeu.")
            print("A Etapa 2 depende dele para subir a Evolution API.")
            print("  Linux:         siga https://docs.docker.com/engine/install/ — o apt padrao")
            print("                 do Ubuntu/Debian NAO tem o pacote docker-compose-plugin")
            print("  macOS/Windows: atualize o Docker Desktop (ja vem com o plugin)")

        print("\nDepois de resolver, rode de novo:")
        print("  %s setup/check_prerequisites.py\n" % PY_CMD)
        sys.exit(1)

    # Aviso, nao bloqueio: so importa para quem escolheu o Claude Code.
    node = versao_do_node()
    if node is not None and node[:1] < NODE_CLAUDE_CODE:
        print("\n[!] Seu Node e' %s. O Codex roda nele, mas o Claude Code"
              % ".".join(str(n) for n in node))
        print("    exige Node %d ou maior — se voce escolheu o Claude Code,"
              % NODE_CLAUDE_CODE[0])
        print("    atualize o Node antes de instalar a CLI.")

    print("\n" + "=" * 60)
    print("[OK] Todos os pre-requisitos estao instalados!")
    print("=" * 60)
    print("\nProxima etapa:")
    print("  %s setup/install_evolution.py\n" % PY_CMD)


if __name__ == "__main__":
    main()
