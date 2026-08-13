# Backups (Fase 18)

## Backup manual

```bash
./scripts/backup_postgres.sh ./backups
```

Genera `./backups/dispatch_db_<timestamp>.sql.gz` y purga backups con más
de 30 días (configurable con `RETENTION_DAYS`).

## Backup automático (cron)

```cron
0 2 * * * cd /ruta/a/dispatch-platform && ./scripts/backup_postgres.sh /ruta/a/backups >> /var/log/dispatch-backup.log 2>&1
```

Backup diario a las 2 AM. Para retención semanal además de la diaria,
considera copiar el backup del domingo a un directorio `weekly/` con mayor
retención, o subir los backups a un bucket externo (S3/GCS) con su propia
política de ciclo de vida.

## Restauración

```bash
./scripts/restore_postgres.sh ./backups/dispatch_db_20260101_020000.sql.gz
```

Pide confirmación explícita antes de sobreescribir la base de datos actual.

**Verificado en este proyecto:** se probó el ciclo completo backup →
restauración a una base de datos separada, confirmando que los datos
(despachos, usuarios, etc.) se recuperan correctamente — ver el reporte de
Fase 18 en la conversación de desarrollo.

## Qué NO cubre este backup

- Los archivos de evidencia de entregas (`/tmp/dispatch-uploads` en
  desarrollo) — en producción, si se migra a un bucket de object storage
  (recomendado, ver nota en `app/api/deliveries.py`), ese bucket debe tener
  su propia política de backup/versionado independiente de este script.
- Redis (solo contiene caché de posición en vivo y cola de Celery — datos
  no críticos que se regeneran solos, no se recomienda invertir en backup).
