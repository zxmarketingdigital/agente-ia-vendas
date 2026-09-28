# watcher_supervisor.ps1 — equivalente Windows do LaunchAgent do macOS
#
# Mantém o watcher.py rodando: religa sozinho se o processo cair, e garante
# que o Evolution API (Docker) esteja de pé antes de iniciar o watcher.
#
# Registrado via Agendador de Tarefas do Windows com gatilho "ao fazer logon",
# equivalente ao RunAtLoad + KeepAlive do launchagent_template.plist.

$agentDir      = "{{HOME}}\meu-agente"
$evolutionDir  = "$agentDir\evolution-api"
$supervisorLog = "$agentDir\watcher-supervisor.log"

function Log($msg) {
    "$(Get-Date -Format o) $msg" | Out-File -FilePath $supervisorLog -Append -Encoding utf8
}

Log "Supervisor iniciado."

# Garante que o Evolution API (Docker) esteja rodando antes do watcher.
# Não bloqueia o watcher se falhar — só registra o aviso e segue.
if (Test-Path $evolutionDir) {
    try {
        Push-Location $evolutionDir
        docker compose up -d *>> $supervisorLog
        Pop-Location
        Log "Evolution API verificado/iniciado."
    } catch {
        Log "Aviso: nao foi possivel iniciar o Evolution API automaticamente: $_"
    }
}

# Loop de supervisao: reinicia o watcher.py sozinho se ele cair (equivalente ao KeepAlive)
while ($true) {
    Log "Iniciando watcher.py..."
    try {
        python "$agentDir\watcher.py"
        Log "watcher.py encerrou (codigo de saida $LASTEXITCODE). Reiniciando em 10s..."
    } catch {
        Log "watcher.py falhou: $_. Reiniciando em 10s..."
    }
    Start-Sleep -Seconds 10
}
