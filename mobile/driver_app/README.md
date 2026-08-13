# Despacho — App del Chofer (Flutter)

Estado: Fase 17 — Tests escritos (`test/`) siguiendo la sección 42 del
prompt: cola offline (idempotencia, sincronización), login (widget test),
GPS sync. **No pudieron ejecutarse en este entorno** — misma limitación de
Dart SDK ya documentada. Ejecuta `flutter test` en un entorno real antes de
confiar en ellos.

## Nota sobre las pruebas de esta fase

El código de esta app se escribió pero **no se pudo compilar ni ejecutar en el
entorno de desarrollo usado para este proyecto**, porque el Dart SDK se
descarga desde `storage.googleapis.com`, un dominio sin acceso de red en ese
sandbox. Se hizo una revisión estática manual (balance de sintaxis, imports
verificados contra el sistema de archivos, tipos consistentes con las
respuestas reales de la API que sí probamos en las Fases 3–8), pero **no
reemplaza `flutter analyze` ni `flutter test`**. Antes de dar esto por
terminado, corre en un entorno con Flutter instalado:

```bash
flutter pub get
flutter analyze
flutter test        # si se agregan tests (pendiente)
flutter run          # con un emulador o dispositivo conectado
```

Si `flutter analyze` marca errores, es información nueva — repórtalos y se
corrigen antes de avanzar a Fase 11, tal como exige el protocolo de fases.

## Configuración de la URL del backend

Por defecto la app apunta a `http://10.0.2.2:8000/api` (la IP que usa el
emulador Android para llegar al `localhost` de la máquina host). Para apuntar
a otro backend:

```bash
flutter run --dart-define=API_BASE_URL=https://tu-servidor.com/api
```

(Nota: `API_BASE_URL` ya usa `String.fromEnvironment(...)`, así que
`--dart-define=API_BASE_URL=...` sobreescribe correctamente el valor en tiempo
de build. Aun así, valida esto con Flutter real — no se pudo compilar aquí.)

## Estructura

```
lib/
├── models/         # Espejo de los esquemas Pydantic del backend
├── services/        # ApiClient (Dio + interceptor de refresh de token)
├── repositories/     # AuthRepository, ShipmentRepository
├── providers/         # AuthProvider (ChangeNotifier)
├── screens/            # LoginScreen, HomeScreen, ShipmentsScreen
└── widgets/             # StatusBadge (misma paleta que el panel web)
```

## Usuarios de prueba (mismo seed del backend)

```
chofer1@dispatchplatform.cl / Password123!
chofer2@dispatchplatform.cl / Password123!
```

## GPS en segundo plano (Fase 11)

- `lib/services/gps_tracking_service.dart` — solicita permisos en dos pasos
  (Android 10+ requiere primero "mientras se usa la app" y luego "todo el
  tiempo" en un segundo paso), inicia el foreground service
  (`flutter_foreground_task`) y aplica la estrategia de frecuencia de
  `docs/gps.md` (distancia O tiempo, con heartbeat cada 60s detenido / 120s
  con batería baja).
- `lib/services/local_gps_queue.dart` — cola SQLite append-only, `client_uuid`
  como clave primaria (idempotencia del lado del dispositivo, espejo de la
  idempotencia por `client_uuid` que ya probamos en el backend en Fase 8).
- `lib/services/gps_sync_service.dart` — hace flush de la cola cada 20s hacia
  `POST /tracking/location`; si falla (sin red), las posiciones quedan en la
  cola para el próximo intento — nunca se pierden.

**Puntos que requieren validación en un dispositivo/emulador real** (no
pudieron probarse aquí):
- El flujo real de los dos diálogos de permiso de Android 10+/11+ (Geolocator
  puede requerir llevar al usuario a Ajustes en algunos fabricantes).
- Que el foreground service sobreviva con la pantalla apagada y la app en
  segundo plano prolongado (Doze mode) — especialmente en fabricantes con
  gestión de batería agresiva (Xiaomi, Huawei, Samsung), como ya se advirtió
  en `docs/risks-security-scalability.md`.
- El nombre exacto de la clase del servicio Android declarada en
  `AndroidManifest.xml` contra la versión real de `flutter_foreground_task`.

