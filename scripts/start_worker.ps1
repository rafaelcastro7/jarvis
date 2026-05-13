# start_worker.ps1 - Script para iniciar el worker de Celery en Windows
Write-Host "Iniciando Worker de Celery para Jarvis..." -ForegroundColor Cyan
Write-Host "Asegúrate de que Redis esté corriendo (por ejemplo, Memurai o vía WSL) en localhost:6379." -ForegroundColor Yellow

# En Windows, Celery requiere el pool 'solo' o 'gevent' ya que no soporta os.fork()
celery -A src.tasks worker --loglevel=info --pool=solo
