#!/bin/bash
# Backup de PostgreSQL (sección 41 del prompt). Pensado para correr:
#   - dentro de un cron del host, o
#   - como un contenedor propio en docker-compose.prod.yml con un cron interno.
#
# Uso: ./backup_postgres.sh [directorio_destino]
# Requiere las mismas variables que .env: POSTGRES_USER, POSTGRES_DB, y
# que 'docker compose exec postgres pg_dump' sea alcanzable (o pg_dump local
# si se corre fuera de Docker apuntando a DATABASE_URL).

set -euo pipefail

BACKUP_DIR="${1:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="dispatch_db_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "Generando backup en ${BACKUP_DIR}/${FILENAME}..."

if command -v docker >/dev/null 2>&1 && docker compose ps postgres >/dev/null 2>&1; then
  # Backup vía el contenedor de Docker Compose (uso normal en producción)
  docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-dispatch_user}" "${POSTGRES_DB:-dispatch_db}" \
    | gzip > "${BACKUP_DIR}/${FILENAME}"
else
  # Fallback: pg_dump directo (desarrollo local sin Docker)
  pg_dump -U "${POSTGRES_USER:-dispatch_user}" -h "${POSTGRES_HOST:-localhost}" "${POSTGRES_DB:-dispatch_db}" \
    | gzip > "${BACKUP_DIR}/${FILENAME}"
fi

echo "Backup completado: ${BACKUP_DIR}/${FILENAME} ($(du -h "${BACKUP_DIR}/${FILENAME}" | cut -f1))"

echo "Purgando backups con más de ${RETENTION_DAYS} días..."
find "$BACKUP_DIR" -name "dispatch_db_*.sql.gz" -mtime "+${RETENTION_DAYS}" -delete

echo "Backups actuales en ${BACKUP_DIR}:"
ls -lh "$BACKUP_DIR" | grep dispatch_db || echo "  (ninguno todavía)"
