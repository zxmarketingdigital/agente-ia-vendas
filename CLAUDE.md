# 🤖 Agente IA de Vendas — Setup em 15 minutos

Bem-vindo! Este é um **agente de vendas IA que responde no WhatsApp** do seu lead. Sem código complicado, sem servidor — tudo funciona localmente ou na nuvem.

**O que você vai conseguir em 15 minutos:**
- ✅ Agente respondendo na sua conta WhatsApp
- ✅ IA entendendo o seu produto automaticamente
- ✅ Histórico de conversas salvo localmente
- ✅ Lead recebe link de checkout quando está pronto

---

## 📋 Pré-requisitos (1-2 min)

Precisa ter instalado:
- **Python 3.9+** → verifique: `python3 --version`
- **Node.js 18+** (para Evolution API) → verifique: `node --version`
- **Docker** (para Evolution API) → verifique: `docker --version`
- **Git** → verifique: `git --version`

Se faltar algo, execute:
```bash
python3 setup/check_prerequisites.py
```
Ele vai mostrar exatamente o que instalar.

---

## 🚀 Setup em 7 Etapas

### Etapa 1 — Pré-requisitos ✓ (1 min)

```bash
python3 setup/check_prerequisites.py
```

Se alguma coisa faltar, ele vai te mostrar como instalar. Quando tudo estiver OK, continua.

---

### Etapa 2 — Instalar Evolution API (2-4 min)

Vamos usar Evolution API (gratuita, open-source) para conectar ao WhatsApp:

```bash
python3 setup/install_evolution.py
```

Isso vai:
1. Baixar Evolution API em `~/meu-agente/evolution-api/`
2. Criar arquivo `.env` com chaves automáticas
3. Iniciar Docker Compose
4. Esperar a API ficar pronta (aguarde ~1 min)

Quando vir `✓ Evolution API rodando em localhost:8080`, continua para próxima.

---

### Etapa 3 — Conectar seu WhatsApp (3 min)

Agora vamos conectar seu número WhatsApp:

```bash
python3 setup/connect_whatsapp.py
```

Ele vai:
1. Criar uma instância chamada "meu-agente"
2. Gerar um **QR Code** e abrir uma janela
3. Pedir para você **escanear com seu celular** (aquele código do WhatsApp Web)
4. Depois confirma automaticamente

⚠️ **Use um número pessoal.** Não precisa ser número empresarial.

---

### Etapa 4 — Escolher Provedor de IA (2 min)

Escolha um:

**A) OpenAI (gpt-5.4-mini) — recomendado**
- Custo: ~0.01¢ por conversa
- [Pegar API key](https://platform.openai.com/api-keys)

**B) Google Gemini**
- Custo: ~0.00005¢ por conversa
- [Pegar API key](https://makersuite.google.com/app/apikey)

**C) Anthropic Claude**
- Custo: ~0.02¢ por conversa
- [Pegar API key](https://console.anthropic.com/)

Cole sua chave:
```bash
python3 setup/test_api.py --provider openai --key sk-...
```

Se vir `✅ API funcionando`, perfeito!

---

### Etapa 5 — Informações do Seu Produto (2 min)

Cole as informações do seu produto/serviço aqui:

**Nome do produto:**
```
Ex: Curso Agência IA 2026
```

**Link de checkout:**
```
Ex: https://pay.hotmart.com/N103378266N?checkoutMode=10
```

**Trigger phrase (exato):**
```
Ex: Olá! Tenho uma dúvida sobre o Plano IA 2026.
```

Claude vai gerar um prompt automático baseado nessas infos.

**Conteúdo da sua LP (cola aqui):**
```
Cole todo o texto da sua landing page aqui — título, benefícios, preço, etc.
O agente vai aprender sobre seu produto a partir disso.
```

---

### Etapa 6 — Gerar Arquivos (1 min)

Claude vai preencher todos os arquivos com suas infos:

```bash
# Isso vai ser gerado automaticamente
~/meu-agente/agent.py         ← Agente IA
~/meu-agente/watcher.py       ← Monitora mensagens
~/meu-agente/.env             ← Configurações
```

---

### Etapa 7 — Testar (1 min)

```bash
python3 setup/test_agent.py
```

Ele vai:
1. Iniciar o watcher
2. Simular uma mensagem do seu lead
3. Agente responde automaticamente
4. Tudo salvo no banco de dados SQLite

Se vir `✅ Agente respondendo corretamente`, está pronto!

---

## ✨ Como Usar Depois

Agora o agente está ativo 24/7. Quando alguém enviar a mensagem trigger:

```
"Olá! Tenho uma dúvida sobre o Plano IA 2026."
```

O agente:
1. **Detecta** a trigger
2. **Responde com uma pergunta BANT** (estilo consultivo)
3. **Salva a conversa** em SQLite (local, seguro)
4. **Envia o link de checkout** quando achar que a pessoa está pronta

Tudo automático! 🎯

---

## 🔧 Troubleshooting

### "Docker não está rodando"
```bash
docker ps
```
Se falhar, abra o app Docker desktop.

### "QR Code não aparece"
```bash
python3 setup/connect_whatsapp.py
```
A imagem PNG vai estar em `/tmp/qrcode.png`. Abre manualmente lá.

### "Agente não responde"
Verifique:
1. Evolution API rodando: `curl localhost:8080/health`
2. Trigger phrase exata (case-sensitive!)
3. API key funciona: `python3 setup/test_api.py`

---

## 📚 Próximos Passos

- **v1.1** → Widget para sua landing page (em breve)
- **v1.2** → Dashboard com métricas dos leads (em breve)

---

## 💬 Suporte

Encontrou um problema?
- Verifique troubleshooting acima
- Abra uma issue no repo GitHub
- Ou mande mensagem para Rafael

---

**Status:** v1.0 (WhatsApp only) ✅ Produção
**Última atualização:** março 2026
