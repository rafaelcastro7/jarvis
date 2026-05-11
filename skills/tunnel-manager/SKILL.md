---
name: tunnel-manager
description: Gestión segura de túneles Cloudflare (trycloudflare.com). Protege la URL activa. Arranca, verifica, y reinicia SOLO Node — nunca cloudflared. Incluye watchdog y restart-server seguros.
tools: Bash, PowerShell, Read, Edit, Write
---

# Tunnel Manager — Cloudflare Quick Tunnels

## REGLA CRÍTICA (aprendida por experiencia)

> **Las quick tunnels de trycloudflare.com son EFÍMERAS e IRRECUPERABLES.**
> Una URL perdida = URL muerta para siempre. No hay forma de recuperarla.
> Si el usuario ya envió una URL a un tercero (MINTIC, cliente, jurado), esa URL NUNCA puede cambiar.
> NUNCA matar cloudflared. SOLO reiniciar Node.

---

## Diagnóstico inicial

```powershell
# Verificar cloudflared activo
Get-Process | Where-Object { $_.ProcessName -like "*cloudflared*" } | Select-Object Id, ProcessName, CPU

# Verificar Node activo
Get-Process | Where-Object { $_.ProcessName -eq "node" } | Select-Object Id, ProcessName

# Verificar puerto del servidor
$PORT = 3055  # leer de .env si existe
Invoke-WebRequest "http://localhost:$PORT/api/health" -UseBasicParsing -TimeoutSec 4
```

---

## Estructura de archivos a crear

### `restart-server.ps1`
```powershell
# Reinicia SOLO Node, verifica cloudflared primero
param()
$ErrorActionPreference = "Continue"
$PORT = 3055

$cf = Get-Process | Where-Object { $_.ProcessName -like "*cloudflared*" }
if (-not $cf) {
  Write-Host "[AVISO] cloudflared no corre. URL del tunel se perdera." -ForegroundColor Yellow
  exit 1
}
Write-Host ("[OK] cloudflared PID " + $cf.Id + " — URL preservada") -ForegroundColor Green

$nodes = Get-Process | Where-Object { $_.ProcessName -eq "node" }
if ($nodes) {
  foreach ($n in $nodes) { Stop-Process -Id $n.Id -Force -ErrorAction SilentlyContinue }
  $cnt = @($nodes).Count
  Write-Host ("[OK] Node detenido (" + $cnt + " proceso(s))") -ForegroundColor Green
  Start-Sleep -Seconds 2
}

Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "npm start > server.log 2>&1") -WindowStyle Hidden
Start-Sleep -Seconds 8

try {
  $r = Invoke-WebRequest "http://localhost:$PORT/api/health" -UseBasicParsing -TimeoutSec 5
  if ($r.Content -like "*ok*") {
    Write-Host "[OK] Servidor activo en http://localhost:$PORT" -ForegroundColor Green
  }
} catch {
  Write-Host "[ERROR] El servidor no respondio. Revisa server.log" -ForegroundColor Red
}
```

### `watchdog.ps1`
```powershell
# Monitoreo cada 15s. Reinicia Node si cae. NUNCA toca cloudflared.
param()
$PORT = 3055
$INTERVAL = 15
$DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

function Test-Server {
  try {
    $r = Invoke-WebRequest "http://localhost:$PORT/api/health" -UseBasicParsing -TimeoutSec 4 -ErrorAction Stop
    return ($r.Content -like "*ok*")
  } catch { return $false }
}

function Restart-Node {
  Set-Location $DIR
  $nodes = Get-Process | Where-Object { $_.ProcessName -eq "node" }
  foreach ($n in $nodes) { Stop-Process -Id $n.Id -Force -ErrorAction SilentlyContinue }
  Start-Sleep -Seconds 2
  Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "npm start > server.log 2>&1") -WindowStyle Hidden
  Start-Sleep -Seconds 8
}

$fail = 0
while ($true) {
  if (Test-Server) {
    $fail = 0
    Write-Host ((Get-Date -Format "HH:mm:ss") + " [OK] Activo") -ForegroundColor Green
  } else {
    $fail++
    if ($fail -ge 2) {
      Write-Host "Reiniciando Node (cloudflared intacto)..." -ForegroundColor Yellow
      Restart-Node; $fail = 0
    }
  }
  Start-Sleep -Seconds $INTERVAL
}
```

### Agregar script en `package.json`
```json
"restart": "powershell -ExecutionPolicy Bypass -File restart-server.ps1"
```

---

## Iniciar túnel por primera vez

```powershell
# Arrancar cloudflared apuntando al puerto del servidor
Start-Process -FilePath "cloudflared" -ArgumentList @("tunnel", "--url", "http://localhost:3055") -RedirectStandardError "tunnel.err" -WindowStyle Hidden
Start-Sleep -Seconds 5

# Obtener URL asignada
Select-String -Path "tunnel.err" -Pattern "trycloudflare.com" | Select-Object -Last 1
```

**GUARDAR LA URL INMEDIATAMENTE** antes de hacer cualquier otra cosa.

---

## Reglas de oro

| Acción | Permitido |
|--------|-----------|
| Matar Node (`npm restart`) | ✅ Siempre |
| Matar cloudflared | ❌ NUNCA |
| `npm run build` + restart | ✅ Con restart-server.ps1 |
| Reiniciar la PC | ⚠️ URL se pierde — iniciar cloudflared primero |
| Quick tunnel para URL crítica | ❌ Usar tunnel con cuenta Cloudflare |

---

## Tunnel permanente (cuando la URL no puede cambiar)

```bash
cloudflared tunnel login
cloudflared tunnel create nombre-proyecto
cloudflared tunnel route dns nombre-proyecto subdominio.tudominio.com
cloudflared tunnel run nombre-proyecto
```

Requiere dominio propio en Cloudflare. La URL es permanente y sobrevive a reinicios.
