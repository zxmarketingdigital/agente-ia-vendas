# Agente IA de Vendas 🤖

Um **agente de vendas IA que responde no WhatsApp** sem código complicado. Setup em 15 minutos.

## ⚡ Quick Start

Cole no terminal as três linhas da IA que você escolheu — ela faz o resto:

```bash
# Gemini (grátis) — a opção recomendada
npm install -g @google/gemini-cli
git clone https://github.com/zxmarketingdigital/agente-ia-vendas.git
cd agente-ia-vendas
gemini
```

```bash
# Codex
npm install -g @openai/codex
git clone https://github.com/zxmarketingdigital/agente-ia-vendas.git
cd agente-ia-vendas
codex
```

```bash
# Claude Code — exige assinatura Claude Pro (~US$20/mês)
npm install -g @anthropic-ai/claude-code
git clone https://github.com/zxmarketingdigital/agente-ia-vendas.git
cd agente-ia-vendas
claude
```

> **A primeira linha instala a IA — não pule.** Ela é o que faz o comando `gemini`
> (ou `codex`/`claude`) existir no seu terminal. Se você já instalou antes, rodar de novo
> não quebra nada: o `npm install -g` apenas atualiza.
>
> **Erro `npm: command not found` ou `'npm' não é reconhecido`?** Falta o Node.js — instale
> a versão **LTS mais recente** em [nodejs.org](https://nodejs.org) e cole as linhas de novo
> (piso: Node 20; o Claude Code exige 22).
>
> **Instalou e o terminal ainda diz `'gemini' não é reconhecido`?** É o PATH antigo da
> sessão: **feche e reabra o terminal**, e cole a partir do `cd`. Atalho pra destravar na
> hora: `npx @google/gemini-cli`. Detalhes em [pré-requisitos](docs/prerequisitos.md).

> **Funciona no macOS, no Linux e no Windows** (PowerShell, CMD ou Git Bash) — são três
> linhas independentes de propósito, sem `&&` nem `2>/dev/null`, que não existem em todos
> os terminais.
>
> Já rodou isso antes e a pasta `agente-ia-vendas` já existe? Sem problema — cole de novo.
> A primeira linha vai reclamar que a pasta já existe (`destination path already exists`),
> **ignore esse aviso**: as duas linhas seguintes continuam normalmente de onde você parou.

A IA abre automaticamente **dentro da pasta clonada** e conduz o setup por você.

> 👉 **Assim que ela abrir, digite `INICIAR SETUP` e aperte Enter.** Na maioria das vezes ela
> já começa sozinha — se isso acontecer, ótimo, pode ignorar. Mas se você vir só a tela de
> boas-vindas da IA (algo como *"Tips for getting started: 1. Create GEMINI.md files..."*),
> é ela esperando você: digite `INICIAR SETUP` que o setup começa.

> 🛑 **O `cd agente-ia-vendas` não é opcional.** Se você abrir a IA fora dessa pasta, ela
> não encontra o roteiro do produto e começa a inventar um bot do zero (perguntando qual
> biblioteca usar, rodando `npm init`, etc.). Se isso acontecer, feche com `/exit` e cole o
> comando acima de novo.

## 📋 O que você vai ter

- ✅ Agente respondendo em tempo real no WhatsApp
- ✅ IA treinada com seu conteúdo (BANT methodology)
- ✅ Histórico de conversas salvo localmente
- ✅ Lead recebe checkout quando está pronto
- ✅ Sem servidor complicado — tudo local + Evolution API

## 🏗️ Arquitetura

### Stack
- **Evolution API** — Conexão com WhatsApp (open-source, gratuito)
- **SQLite** — histórico de conversas do agente (a Evolution API usa Postgres próprio, criado automaticamente no Docker)
- **Python 3.9+** — Lógica do agente
- **Multi-IA** — OpenAI, Gemini ou Anthropic

### Fluxo

```
Usuário envia trigger
    ↓
Watcher detecta via Evolution API (polling a cada 3s)
    ↓
IA responde (BANT consultivo)
    ↓
Resposta enviada via Evolution API
    ↓
Conversa salva em SQLite (30 min TTL)
    ↓
Se purchase intent → envia checkout link
```

## 📁 Estrutura

```
agente-ia-vendas/
├── SETUP.md                           ← ROTEIRO CANÔNICO do setup (corrija aqui)
├── CLAUDE.md                          ← porta de entrada do Claude Code  ─┐
├── GEMINI.md                          ← porta de entrada do Gemini CLI   ─┼→ apontam p/ SETUP.md
├── AGENTS.md                          ← porta de entrada do Codex CLI    ─┘
├── README.md                          ← Documentação técnica
│
├── setup/
│   ├── check_prerequisites.py         ← Verifica dependências
│   ├── install_evolution.py           ← Instala Evolution API
│   ├── connect_whatsapp.py            ← Conecta WhatsApp via QR Code
│   ├── test_api.py                    ← Testa chave de IA
│   └── test_agent.py                  ← Simula conversa
│
├── templates/
│   ├── whatsapp/
│   │   ├── agent_template.py          ← Agente WhatsApp ({{placeholders}})
│   │   ├── watcher_template.py        ← Watcher (polling messages.json)
│   │   └── launchagent_template.plist ← Auto-restart macOS
│   │
│   └── shared/
│       ├── agent_core_template.py     ← Lógica IA (reutilizável)
│       └── sessions_template.py       ← SQLite operations
│
└── docs/
    ├── prerequisitos.md               ← Requisitos por SO
    └── guia.html                      ← Guia visual do setup
```

## 🎯 Exemplo de Uso

Seu lead envia:
> "Olá! Tenho uma dúvida sobre o Plano IA 2026."

Agente responde (2-3 segundos depois):
> "Oi! 👋 Que legal! O Plano IA 2026 foi feito pra quem quer construir negócio de IA do zero. Qual é sua dúvida específica? Estou aqui pra ajudar."

Depois de conversa consultiva (BANT):
> "Ótimo! Passei todas as suas infos aqui. Deixa eu enviar nosso checkout pra você dar uma olhada:
> [LINK_DE_COMPRA]"

Tudo automático, integrado com WhatsApp. ✨

## 🔐 Segurança

- **Sem dados na nuvem** — tudo local (Evolution API + SQLite)
- **Sem credenciais no código** — usa `.env`
- **Sessões com TTL** — conversas expiram após 30 min de inatividade
- **Open source** — veja exatamente o que funciona

## 🚀 Deploy (Optional)

Para rodas 24/7:
- **macOS/Linux:** LaunchAgent automático roda na inicialização
- **VPS:** Docker Compose em qualquer servidor
- **Docker:** o `docker-compose.yml` da Evolution é gerado pelo `setup/install_evolution.py`

## 📊 Versões Futuras

- **v1.1** — Widget flutuante para sua landing page
- **v1.2** — Dashboard com métricas dos leads

## 📚 Documentação

- [Pré-requisitos por SO](docs/prerequisitos.md)
- [Guia visual do setup](docs/guia.html)

## 💬 Suporte

Travou? A tabela **"Problemas que travam o aluno ANTES do setup começar"** no fim do
[SETUP.md](SETUP.md) cobre os erros mais comuns (console do Node, PowerShell bloqueando
scripts no Windows, `EACCES` do npm no Mac, permissões de pasta do macOS).

Se não resolver, cole o erro na [IA de Suporte](https://suporte.zxlab.com.br/hub).

## 📄 Licença

MIT — use livremente em produção.

---

**Feito por [ZX LAB](https://zxlab.com.br)**
Março 2026 | v1.0
