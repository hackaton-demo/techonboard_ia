#!/bin/bash
set -e

echo "🚀 TechOnboard Demo Setup"
echo "=================================="

# ---------------------------------------------------------------------------
# Verificar dependencias
# ---------------------------------------------------------------------------
echo ""
echo "Verificando dependencias..."

command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker es requerido pero no esta instalado."; exit 1; }
echo "  [OK] Docker encontrado: $(docker --version)"

# Verificar docker-compose (v1 o v2 integrado en docker)
if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
    echo "  [OK] docker-compose encontrado: $(docker-compose --version)"
elif docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
    echo "  [OK] docker compose (v2) encontrado: $(docker compose version)"
else
    echo "ERROR: docker-compose no encontrado. Instala Docker Compose v2."
    exit 1
fi

# ---------------------------------------------------------------------------
# Copiar .env si no existe
# ---------------------------------------------------------------------------
echo ""
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "  [OK] Creado .env desde .env.example"
        echo "  IMPORTANTE: Edita .env con tus credenciales reales antes de continuar."
        echo ""
        read -p "  Presiona ENTER cuando hayas configurado .env, o Ctrl+C para cancelar... " _
    else
        echo "  AVISO: .env.example no encontrado. Continuando sin .env..."
    fi
else
    echo "  [OK] .env ya existe, usando el existente."
fi

# ---------------------------------------------------------------------------
# Levantar base de datos y Redis primero
# ---------------------------------------------------------------------------
echo ""
echo "Levantando PostgreSQL y Redis..."
$COMPOSE_CMD up -d db redis

# ---------------------------------------------------------------------------
# Esperar a que PostgreSQL este listo
# ---------------------------------------------------------------------------
echo ""
echo "Esperando a que PostgreSQL este disponible..."
MAX_ATTEMPTS=30
ATTEMPT=0
until $COMPOSE_CMD exec -T db pg_isready -U techonboard >/dev/null 2>&1; do
    ATTEMPT=$((ATTEMPT + 1))
    if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
        echo "ERROR: PostgreSQL no respondio despues de ${MAX_ATTEMPTS} intentos."
        echo "Revisa los logs con: $COMPOSE_CMD logs db"
        exit 1
    fi
    echo "  Intento ${ATTEMPT}/${MAX_ATTEMPTS}..."
    sleep 2
done
echo "  [OK] PostgreSQL listo."

# ---------------------------------------------------------------------------
# Esperar a que Redis este listo
# ---------------------------------------------------------------------------
echo ""
echo "Verificando Redis..."
ATTEMPT=0
until $COMPOSE_CMD exec -T redis redis-cli ping >/dev/null 2>&1; do
    ATTEMPT=$((ATTEMPT + 1))
    if [ $ATTEMPT -ge 15 ]; then
        echo "ERROR: Redis no respondio."
        exit 1
    fi
    sleep 1
done
echo "  [OK] Redis listo."

# ---------------------------------------------------------------------------
# Levantar backend, worker Celery y frontend
# ---------------------------------------------------------------------------
echo ""
echo "Levantando backend, Celery worker y frontend..."
$COMPOSE_CMD up -d backend celery_worker frontend

# Esperar a que el backend este disponible
echo ""
echo "Esperando a que el backend este disponible..."
ATTEMPT=0
until curl -sf http://localhost:8000/health >/dev/null 2>&1; do
    ATTEMPT=$((ATTEMPT + 1))
    if [ $ATTEMPT -ge 30 ]; then
        echo "  AVISO: Backend no respondio en /health despues de 60s."
        echo "  Continuando de todos modos..."
        break
    fi
    sleep 2
done
if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    echo "  [OK] Backend disponible."
fi

# ---------------------------------------------------------------------------
# Migraciones
# ---------------------------------------------------------------------------
echo ""
echo "Ejecutando migraciones de base de datos..."
$COMPOSE_CMD exec -T backend alembic upgrade head
echo "  [OK] Migraciones aplicadas."

# ---------------------------------------------------------------------------
# Seed de datos de demo
# ---------------------------------------------------------------------------
echo ""
echo "Cargando datos de demo..."
$COMPOSE_CMD exec -T backend python scripts/seed_demo_data.py
echo "  [OK] Datos de demo cargados."

# ---------------------------------------------------------------------------
# Resultado final
# ---------------------------------------------------------------------------
echo ""
echo "=================================="
echo "  TechOnboard listo!"
echo ""
echo "  Frontend:    http://localhost:3000"
echo "  Backend API: http://localhost:8000/api/v1"
echo "  API Docs:    http://localhost:8000/docs"
echo "  Adminer DB:  http://localhost:8080 (si esta habilitado)"
echo ""
echo "  Comandos utiles:"
echo "    make logs          — Ver logs en tiempo real"
echo "    make backend-shell — Acceder al contenedor del backend"
echo "    make test          — Ejecutar tests"
echo "    make down          — Detener todos los servicios"
echo "=================================="
