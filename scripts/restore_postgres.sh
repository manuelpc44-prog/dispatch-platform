#!/bin/bash
# Restauración desde un backup generado por backup_postgres.sh.
# Uso: ./restore_postgres.sh archivo_backup.sql.gz
#
# ADVERTENCIA: esto sobreescribe la base de datos actual. Confirma el
# entorno (nunca correr contra producción por error) antes de continuar.

set -euo pipefail

BACKUP_FILE="${1:?Uso: ./restore_postgres.sh archivo_backup.sql.gz}"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "ERROR: no se encontró el archivo $BACKUP_FILE" >&2
  exit 1
fi

read -p "Esto SOBREESCRIBE la base de datos actual (${POSTGRES_DB:-dispatch_db}). ¿Continuar? [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  echo "Cancelado."
  exit 0
fi

echo "Restaurando desde ${BACKUP_FILE}..."

if command -v docker >/dev/null 2>&1 && docker compose ps postgres >/dev/null 2>&1; then
  gunzip -c "$BACKUP_FILE" | docker compose exec -T postgres psql -U "${POSTGRES_USER:-dispatch_user}" "${POSTGRES_DB:-dispatch_db}"
else
  gunzip -c "$BACKUP_FILE" | psql -U "${POSTGRES_USER:-dispatch_user}" -h "${POSTGRES_HOST:-localhost}" "${POSTGRES_DB:-dispatch_db}"
fi

echo "Restauración completada."
