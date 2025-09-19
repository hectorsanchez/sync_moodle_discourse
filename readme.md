# Sync Moodle → Discourse

Script en Python para sincronizar datos de usuarios desde **Moodle** hacia **Discourse** mediante la API REST.

Este script permite mantener actualizados automáticamente los perfiles de usuarios en Discourse con la información más reciente de Moodle, especialmente útil en entornos donde los usuarios se autentican mediante SSO con Moodle.

## Características

- **Sincronización automática** de perfiles de usuario
- **Actualización de campos**:
  - Nombre completo (`name`)
  - Ubicación (`location`, combinando ciudad y país de Moodle)
  - Biografía (`bio_raw`)
  - Email (`email`, requiere confirmación del usuario en Discourse)
- **Activación automática de usuarios** con parámetro `--activate-users`
- **Modo dry-run** para revisar cambios antes de aplicarlos
- **Sincronización selectiva** por usuario específico
- **Verificación automática** de cambios aplicados
- **Soporte para API key de administrador** de Discourse
- **Procesamiento por lotes** para manejar grandes cantidades de usuarios
- **Logging detallado en CSV** con timestamp y seguimiento completo
- **Nombres de archivo diferenciados** por modo de ejecución (dryrun/apply) y entorno (development/production)
- **Normalización automática** de nombres de usuario para cumplir con requisitos de Discourse
- **Procesamiento secuencial** para evitar duplicados y controlar la carga

## Instalación

### Requisitos previos

- Python 3.7 o superior
- Acceso a la API REST de Moodle
- API key de administrador de Discourse

### Configuración

1. **Clonar o descargar** el repositorio:
   ```bash
   git clone <repository-url>
   cd sync_moodle_discourse
   ```

2. **Crear entorno virtual** (recomendado):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install requests
   ```

4. **Configurar credenciales**:
   - Copiar `settings.example.py` a `settings.py`
   - Editar `settings.py` con tus credenciales:
   - Configurar la variable `ENV` ("development" o "production")

### Configuración por entornos

El script soporta diferentes configuraciones para desarrollo y producción:

- **`settings.py`** - Configuración por defecto (desarrollo)
- **`settings_dev.py`** - Configuración específica de desarrollo
- **`settings_prod.py`** - Configuración específica de producción

La variable `ENV` en cada archivo determina el entorno y se incluye en el nombre de los archivos de log.
     ```python
     # Moodle
     MOODLE_ENDPOINT = "https://tu-moodle.com/webservice/rest/server.php"
     MOODLE_TOKEN = "tu-token-moodle"
     
     # Discourse
     DISCOURSE_URL = "https://tu-discourse.com"
     DISCOURSE_API_KEY = "tu-api-key-discourse"
     DISCOURSE_API_USER = "admin"  # Usuario admin que genera la API key
     
     # Configuración de procesamiento por lotes
     BATCH_SIZE = 10  # Número de usuarios a procesar en cada ejecución (por defecto: 10)
     ```

## 📖 Uso

### Parámetros disponibles

| Parámetro | Descripción | Valor por defecto | Ejemplo |
|-----------|-------------|-------------------|---------|
| `--apply` | Aplica cambios reales (sin esto es dry-run) | `False` | `--apply` |
| `--user USER` | Sincroniza solo un usuario específico | `None` | `--user "juan.perez"` |
| `--force-recreate` | Fuerza la recreación de usuarios existentes | `False` | `--force-recreate` |
| `--batch-size N` | Número de usuarios a procesar en esta ejecución | `10` (desde settings.py) | `--batch-size 20` |
| `--offset N` | Número de usuarios a saltar desde el inicio | `0` | `--offset 50` |
| `--activate-users` | Activa y aprueba automáticamente los usuarios creados | `False` | `--activate-users` |

### Comandos básicos

```bash
# Modo dry-run (por defecto) - solo muestra diferencias
python3 sync_moodle_discourse.py

# Aplicar cambios reales
python3 sync_moodle_discourse.py --apply

# Aplicar cambios y activar usuarios automáticamente
python3 sync_moodle_discourse.py --apply --activate-users

# Sincronizar usuario específico (modo dry-run)
python3 sync_moodle_discourse.py --user "juan.perez"

# Sincronizar usuario específico y aplicar cambios
python3 sync_moodle_discourse.py --user "juan.perez" --apply

# Sincronizar usuario específico, aplicar cambios y activar
python3 sync_moodle_discourse.py --user "juan.perez" --apply --activate-users
```

### Procesamiento por lotes

```bash
# Procesar 10 usuarios (valor por defecto)
python3 sync_moodle_discourse.py --apply

# Procesar 20 usuarios con activación automática
python3 sync_moodle_discourse.py --apply --batch-size 20 --activate-users

# Procesar 5 usuarios saltando los primeros 10
python3 sync_moodle_discourse.py --apply --batch-size 5 --offset 10

# Procesar 15 usuarios saltando los primeros 30 con activación
python3 sync_moodle_discourse.py --apply --batch-size 15 --offset 30 --activate-users

# Procesar todos los usuarios con activación automática (recomendado para migración masiva)
python3 sync_moodle_discourse.py --apply --activate-users
```

### Ejemplo de procesamiento secuencial para 700 usuarios

```bash
# Lote 1: usuarios 0-9
python3 sync_moodle_discourse.py --apply --batch-size 10 --offset 0

# Lote 2: usuarios 10-19
python3 sync_moodle_discourse.py --apply --batch-size 10 --offset 10

# Lote 3: usuarios 20-29
python3 sync_moodle_discourse.py --apply --batch-size 10 --offset 20

# ... continuar hasta el lote 70: usuarios 690-699
python3 sync_moodle_discourse.py --apply --batch-size 10 --offset 690
```

### Modos de operación

| Modo | Descripción | Comando |
|------|-------------|---------|
| **Dry-run** | Muestra diferencias sin aplicar cambios | `python3 sync_moodle_discourse.py` |
| **Apply** | Aplica cambios reales en Discourse | `python3 sync_moodle_discourse.py --apply` |
| **Apply + Activación** | Aplica cambios y activa usuarios automáticamente | `python3 sync_moodle_discourse.py --apply --activate-users` |
| **Usuario específico** | Limita sincronización a un usuario | `python3 sync_moodle_discourse.py --user username` |
| **Procesamiento por lotes** | Procesa un número específico de usuarios | `python3 sync_moodle_discourse.py --apply --batch-size 20` |
| **Procesamiento secuencial** | Procesa lotes sin duplicados | `python3 sync_moodle_discourse.py --apply --batch-size 10 --offset 50` |

## Funcionamiento

### Proceso de sincronización

1. **Obtención de datos** desde Moodle via API REST
2. **Normalización** de nombres de usuario para cumplir con requisitos de Discourse
3. **Comparación** con datos actuales en Discourse
4. **Actualización** de campos modificados
5. **Verificación** de cambios aplicados correctamente
6. **Logging** detallado de todas las acciones en archivo CSV

### Activación automática de usuarios

Cuando se usa el parámetro `--activate-users`, el script:

1. **Crea el usuario** en Discourse (si no existe)
2. **Obtiene el ID** del usuario recién creado
3. **Aprueba el usuario** usando la API de administrador (`/admin/users/{id}/approve`)
4. **Activa el usuario** usando la API de administrador (`/admin/users/{id}/activate`)
5. **Verifica la activación** para confirmar que el usuario está listo para usar

**Beneficios:**
- Los usuarios quedan **listos para usar** inmediatamente
- No requieren **activación manual** por email
- Perfecto para **migraciones masivas** de usuarios
- **Control total** sobre cuándo activar usuarios

### Normalización de nombres de usuario

El script normaliza automáticamente los nombres de usuario de Moodle para cumplir con los requisitos de Discourse:

- **Caracteres permitidos**: letras, números, guiones (-), puntos (.) y guiones bajos (_)
- **Conversión**: espacios y caracteres especiales se reemplazan con guiones bajos
- **Ejemplos**:
  - `"margherita cospe"` → `"margherita_cospe"`
  - `"user@domain.com"` → `"user_domain.com"`
  - `"user!@#$%name"` → `"user_name"`

### Logging detallado

Cada ejecución genera un archivo CSV con timestamp que incluye:

- **Timestamp** de cada acción
- **Username original** y normalizado
- **Datos del usuario** (nombre, email, ubicación)
- **Acción realizada** (CREATE, UPDATE, EXCLUDE, ERROR)
- **Estado** (SUCCESS, ERROR, DRY_RUN, etc.)
- **Mensaje descriptivo** de la acción
- **Activación** (YES/NO) - Indica si el usuario fue activado automáticamente

#### Nombres de archivo diferenciados

Los archivos de log incluyen el entorno y modo de ejecución en el nombre:

- **`sync_log_development_dryrun_YYYYMMDD_HHMMSS.csv`** - Ejecuciones en modo dry-run en desarrollo
- **`sync_log_development_apply_YYYYMMDD_HHMMSS.csv`** - Ejecuciones reales en desarrollo
- **`sync_log_production_dryrun_YYYYMMDD_HHMMSS.csv`** - Ejecuciones en modo dry-run en producción
- **`sync_log_production_apply_YYYYMMDD_HHMMSS.csv`** - Ejecuciones reales en producción

Esto permite identificar fácilmente:
- **Qué logs corresponden a pruebas** vs **cambios reales** en la base de datos
- **En qué entorno** se ejecutó cada log (development/production)

**Formato del archivo**: `sync_log_{entorno}_{modo}_{YYYYMMDD_HHMMSS}.csv`

### Campos sincronizados

| Campo Moodle | Campo Discourse | Descripción |
|--------------|----------------|-------------|
| `fullname` | `name` | Nombre completo del usuario |
| `city` + `country` | `location` | Ubicación combinada (ej: "Buenos Aires, AR") |
| `description` | `bio_raw` | Biografía del usuario |
| `email` | `email` | Dirección de correo (requiere confirmación) |

### Lógica de ubicación

El script combina inteligentemente los campos de ciudad y país:
- **Si hay ciudad y país**: `"Ciudad, País"` (ej: "Buenos Aires, AR")
- **Si solo hay país**: `"País"` (ej: "AR")
- **Si solo hay ciudad**: `"Ciudad"` (ej: "Buenos Aires")

## Notas importantes

### Seguridad y permisos

- **API Key de Discourse**: Debe ser generada por un usuario administrador
- **Permisos**: La API key debe tener permisos para modificar perfiles de usuario
- **SSO**: Los usuarios deben existir previamente en Discourse (el script no crea usuarios nuevos)

### Confirmación de email

- La actualización de email en Discourse envía un correo de confirmación
- El cambio no se activa hasta que el usuario confirme el nuevo email
- Este es un mecanismo de seguridad estándar de Discourse

### Limitaciones

- Solo sincroniza usuarios que ya existen en Discourse
- No crea usuarios nuevos automáticamente (solo en modo dry-run se muestra qué se crearía)
- Requiere que el SSO esté configurado correctamente
- La normalización de nombres de usuario es determinística pero puede causar colisiones si dos usuarios diferentes se normalizan al mismo username

## Procesamiento por lotes y logging

### Ventajas del procesamiento por lotes

- **Control de carga**: Evita sobrecargar el sistema con muchos usuarios simultáneos
- **Monitoreo**: Permite revisar resultados de cada lote antes de continuar
- **Recuperación**: Si algo falla, puedes continuar desde donde quedaste
- **Flexibilidad**: Ajusta el tamaño del lote según tus necesidades

### Archivos de log generados

Cada ejecución crea un archivo CSV único con formato `sync_log_YYYYMMDD_HHMMSS.csv` que contiene:

```csv
timestamp,original_username,normalized_username,fullname,email,
```

### Tipos de acciones registradas

| Acción | Descripción | Estados posibles |
|--------|-------------|------------------|
| `CREATE` | Usuario nuevo en Discourse | `DRY_RUN`, `SUCCESS`, `ERROR`, `EXCEPTION` |
| `UPDATE` | Usuario existente actualizado | `EXISTS`, `SUCCESS`, `ERROR` |
| `EXCLUDE` | Usuario excluido de procesamiento | `EXCLUDED` |

### Estrategia recomendada para grandes volúmenes

Para procesar 700+ usuarios de forma eficiente:

1. **Empezar con lotes pequeños** (10-20 usuarios) para probar
2. **Revisar logs** después de cada lote
3. **Aumentar tamaño del lote** si todo funciona bien (hasta 50-100)
4. **Procesar en horarios de baja actividad**
5. **Mantener logs** para auditoría y seguimiento

## Automatización

### Cron job (Linux/macOS)

Para sincronización automática periódica:

```bash
# Editar crontab
crontab -e

# Ejecutar cada noche a las 02:00 (procesar 50 usuarios)
0 2 * * * /ruta/completa/venv/bin/python3 /ruta/al/proyecto/sync_moodle_discourse.py --apply --batch-size 50 >> /var/log/sync_moodle_discourse.log 2>&1

# Ejecutar cada hora (procesar 10 usuarios)
0 * * * * /ruta/completa/venv/bin/python3 /ruta/al/proyecto/sync_moodle_discourse.py --apply --batch-size 10 >> /var/log/sync_moodle_discourse.log 2>&1

# Ejecutar cada 30 minutos (procesar 5 usuarios)
*/30 * * * * /ruta/completa/venv/bin/python3 /ruta/al/proyecto/sync_moodle_discourse.py --apply --batch-size 5 >> /var/log/sync_moodle_discourse.log 2>&1
```

### Task Scheduler (Windows)

1. Abrir "Programador de tareas"
2. Crear tarea básica
3. Configurar para ejecutar el script con parámetros `--apply`
4. Establecer frecuencia deseada

## Solución de problemas

### Problemas comunes

| Problema | Solución |
|----------|----------|
| **Error 401/403** | Verificar API key y permisos de usuario |
| **Error 404** | Verificar URL de Discourse y existencia del usuario |
| **Cambios no se aplican** | Verificar estructura de datos de la API (ver sección técnica) |
| **Usuario no encontrado** | Verificar que el usuario existe en Discourse |
| **Error de normalización** | Verificar que el username normalizado no cause colisiones |
| **Lotes muy grandes** | Reducir `--batch-size` para evitar timeouts |
| **Procesamiento lento** | Usar `--offset` para procesar en paralelo diferentes rangos |
| **Logs no se generan** | Verificar permisos de escritura en el directorio del script |

### Análisis de logs CSV

Los archivos CSV generados permiten:
- **Auditoría completa** de todas las acciones realizadas
- **Análisis de errores** por tipo y frecuencia
- **Seguimiento de usuarios** específicos
- **Estadísticas de procesamiento** por lote
- **Identificación de problemas** de normalización

#### Comandos útiles para análisis

```bash
# Ver todos los logs
ls -la sync_log_*.csv

# Ver solo logs de desarrollo
ls -la sync_log_development_*.csv

# Ver solo logs de producción
ls -la sync_log_production_*.csv

# Ver solo logs de ejecución real (apply) en desarrollo
ls -la sync_log_development_apply_*.csv

# Ver solo logs de pruebas (dry-run) en producción
ls -la sync_log_production_dryrun_*.csv

# Contar usuarios creados en ejecuciones reales de desarrollo
grep "CREATE,SUCCESS" sync_log_development_apply_*.csv | wc -l

# Ver errores en ejecuciones reales de producción
grep "ERROR" sync_log_production_apply_*.csv

# Ver usuarios excluidos en todos los entornos
grep "EXCLUDE" sync_log_*.csv

# Ver solo usuarios activados
grep "activated,YES" sync_log_*.csv

# Contar usuarios activados
grep "activated,YES" sync_log_*.csv | wc -l

# Ver usuarios creados sin activar
grep "CREATE,SUCCESS" sync_log_*.csv | grep "activated,NO"

# Ver usuarios activados en desarrollo
grep "activated,YES" sync_log_development_*.csv
```

## Detalles técnicos

### API Endpoints utilizados

- **Moodle**: `core_user_get_users` via REST API
- **Discourse**: `PUT /u/{username}.json` para actualizaciones

### Estructura de datos

**Importante**: La API de Discourse requiere que los campos se envíen directamente, no envueltos en un objeto `user`:

```python
# CORRECTO
{"location": "AR", "name": "Usuario"}

# INCORRECTO  
{"user": {"location": "AR", "name": "Usuario"}}
```

### Verificación de cambios

El script incluye verificación automática para confirmar que los cambios se aplicaron correctamente, comparando los valores esperados con los valores actuales en Discourse.

## Licencia

Este proyecto está bajo la licencia especificada en el archivo `LICENSE`.

## Ejemplos prácticos

### Ejemplo 1: Procesamiento inicial de 100 usuarios con activación

```bash
# Lote 1: usuarios 0-9 (con activación automática)
python3 sync_moodle_discourse.py --apply --batch-size 10 --offset 0 --activate-users

# Lote 2: usuarios 10-19 (con activación automática)
python3 sync_moodle_discourse.py --apply --batch-size 10 --offset 10 --activate-users

# ... continuar hasta el lote 10: usuarios 90-99
python3 sync_moodle_discourse.py --apply --batch-size 10 --offset 90 --activate-users
```

### Ejemplo 2: Procesamiento en paralelo con activación

```bash
# Terminal 1: usuarios 0-49 (con activación automática)
python3 sync_moodle_discourse.py --apply --batch-size 50 --offset 0 --activate-users

# Terminal 2: usuarios 50-99 (con activación automática)
python3 sync_moodle_discourse.py --apply --batch-size 50 --offset 50 --activate-users
```

### Ejemplo 3: Análisis de logs

```bash
# Ver todos los logs generados
ls -la sync_log_*.csv

# Ver el último log
tail -f sync_log_20250916_143748.csv

# Contar usuarios procesados en un log
wc -l sync_log_20250916_143748.csv
```

### Ejemplo 4: Procesamiento con monitoreo y activación

```bash
# Procesar con output detallado y activación automática
python3 sync_moodle_discourse.py --apply --batch-size 20 --offset 0 --activate-users 2>&1 | tee procesamiento_lote_1.log

# Verificar resultados
grep "SUCCESS" sync_log_*.csv | wc -l
grep "ERROR" sync_log_*.csv | wc -l
grep "ACTIVATE" sync_log_*.csv | wc -l  # Contar activaciones
```

### Ejemplo 5: Migración masiva de 700 usuarios

```bash
# Opción 1: Procesamiento secuencial con activación automática
for i in {0..69}; do
    offset=$((i * 10))
    echo "Procesando lote $((i + 1)): usuarios $offset-$((offset + 9))"
    python3 sync_moodle_discourse.py --apply --batch-size 10 --offset $offset --activate-users
    sleep 5  # Pausa entre lotes para evitar sobrecarga
done

# Opción 2: Procesamiento en paralelo (2 terminales)
# Terminal 1: usuarios 0-349
python3 sync_moodle_discourse.py --apply --batch-size 350 --offset 0 --activate-users

# Terminal 2: usuarios 350-699
python3 sync_moodle_discourse.py --apply --batch-size 350 --offset 350 --activate-users

# Opción 3: Procesamiento completo de una vez (solo si el servidor puede manejarlo)
python3 sync_moodle_discourse.py --apply --activate-users
```

---

**Nota**: Este script ha sido probado con Discourse 3.5.0.beta8 y versiones posteriores. Para versiones anteriores, pueden requerirse ajustes en la estructura de datos de la API.
