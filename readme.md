# Sync Moodle → Discourse

Script en Python para sincronizar datos de usuarios desde **Moodle** hacia **Discourse** mediante la API REST.

Este script permite mantener actualizados automáticamente los perfiles de usuarios en Discourse con la información más reciente de Moodle, especialmente útil en entornos donde los usuarios se autentican mediante SSO con Moodle.

## ✨ Características

- 🔄 **Sincronización automática** de perfiles de usuario
- 📝 **Actualización de campos**:
  - Nombre completo (`name`)
  - Ubicación (`location`, combinando ciudad y país de Moodle)
  - Biografía (`bio_raw`)
  - Email (`email`, requiere confirmación del usuario en Discourse)
- 🧪 **Modo dry-run** para revisar cambios antes de aplicarlos
- 🎯 **Sincronización selectiva** por usuario específico
- ✅ **Verificación automática** de cambios aplicados
- 🔐 **Soporte para API key de administrador** de Discourse
- 📦 **Procesamiento por lotes** para manejar grandes cantidades de usuarios
- 📊 **Logging detallado en CSV** con timestamp y seguimiento completo
- 🔄 **Normalización automática** de nombres de usuario para cumplir con requisitos de Discourse
- 📈 **Procesamiento secuencial** para evitar duplicados y controlar la carga

## 🚀 Instalación

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

### Comandos básicos

```bash
# Modo dry-run (por defecto) - solo muestra diferencias
python3 sync_moodle_discourse.py

# Aplicar cambios reales
python3 sync_moodle_discourse.py --apply

# Sincronizar usuario específico (modo dry-run)
python3 sync_moodle_discourse.py --user "juan.perez"

# Sincronizar usuario específico y aplicar cambios
python3 sync_moodle_discourse.py --user "juan.perez" --apply
```

### Procesamiento por lotes

```bash
# Procesar 10 usuarios (valor por defecto)
python3 sync_moodle_discourse.py --apply

# Procesar 20 usuarios
python3 sync_moodle_discourse.py --apply --batch-size 20

# Procesar 5 usuarios saltando los primeros 10
python3 sync_moodle_discourse.py --apply --batch-size 5 --offset 10

# Procesar 15 usuarios saltando los primeros 30
python3 sync_moodle_discourse.py --apply --batch-size 15 --offset 30
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
| **Usuario específico** | Limita sincronización a un usuario | `python3 sync_moodle_discourse.py --user username` |
| **Procesamiento por lotes** | Procesa un número específico de usuarios | `python3 sync_moodle_discourse.py --apply --batch-size 20` |
| **Procesamiento secuencial** | Procesa lotes sin duplicados | `python3 sync_moodle_discourse.py --apply --batch-size 10 --offset 50` |

## 🔧 Funcionamiento

### Proceso de sincronización

1. **Obtención de datos** desde Moodle via API REST
2. **Normalización** de nombres de usuario para cumplir con requisitos de Discourse
3. **Comparación** con datos actuales en Discourse
4. **Actualización** de campos modificados
5. **Verificación** de cambios aplicados correctamente
6. **Logging** detallado de todas las acciones en archivo CSV

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

**Formato del archivo**: `sync_log_YYYYMMDD_HHMMSS.csv`

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

## ⚠️ Notas importantes

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

## 📊 Procesamiento por lotes y logging

### Ventajas del procesamiento por lotes

- **Control de carga**: Evita sobrecargar el sistema con muchos usuarios simultáneos
- **Monitoreo**: Permite revisar resultados de cada lote antes de continuar
- **Recuperación**: Si algo falla, puedes continuar desde donde quedaste
- **Flexibilidad**: Ajusta el tamaño del lote según tus necesidades

### Archivos de log generados

Cada ejecución crea un archivo CSV único con formato `sync_log_YYYYMMDD_HHMMSS.csv` que contiene:

```csv
timestamp,original_username,normalized_username,fullname,email,action,status,message,location,country,description
2025-09-16 14:37:53,francois,francois,Francois Soulard,francois@rio20.net,CREATE,DRY_RUN,Usuario creado en modo dry-run,,FR,
2025-09-16 14:38:32,jason.nardi,jason.nardi,Jason Nardi,jason.nardi@ripess.eu,CREATE,DRY_RUN,Usuario creado en modo dry-run,Firenze,IT,
2025-09-16 14:38:54,lauravigoriti,lauravigoriti,Laura Vigoriti,laura.vigoriti@cospe.org,UPDATE,EXISTS,Usuario existe en Discourse, procesando actualizaciones,,IT,
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

## 🕐 Automatización

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

## 🐛 Solución de problemas

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

### Logs y debugging

El script proporciona información detallada:
- ✅ Cambios aplicados exitosamente
- ❌ Errores encontrados
- 🔍 Verificación de cambios
- 📝 Comparación de datos antes/después
- 📊 Archivos CSV con timestamp para cada ejecución
- 🔄 Información de normalización de usernames
- 📦 Estadísticas de procesamiento por lotes

### Análisis de logs CSV

Los archivos CSV generados permiten:
- **Auditoría completa** de todas las acciones realizadas
- **Análisis de errores** por tipo y frecuencia
- **Seguimiento de usuarios** específicos
- **Estadísticas de procesamiento** por lote
- **Identificación de problemas** de normalización

## 🔬 Detalles técnicos

### API Endpoints utilizados

- **Moodle**: `core_user_get_users` via REST API
- **Discourse**: `PUT /u/{username}.json` para actualizaciones

### Estructura de datos

**Importante**: La API de Discourse requiere que los campos se envíen directamente, no envueltos en un objeto `user`:

```python
# ✅ CORRECTO
{"location": "AR", "name": "Usuario"}

# ❌ INCORRECTO  
{"user": {"location": "AR", "name": "Usuario"}}
```

### Verificación de cambios

El script incluye verificación automática para confirmar que los cambios se aplicaron correctamente, comparando los valores esperados con los valores actuales en Discourse.

## 📄 Licencia

Este proyecto está bajo la licencia especificada en el archivo `LICENSE`.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 💡 Ejemplos prácticos

### Ejemplo 1: Procesamiento inicial de 100 usuarios

```bash
# Lote 1: usuarios 0-9
python3 sync_moodle_discourse.py --apply --batch-size 10 --offset 0

# Lote 2: usuarios 10-19
python3 sync_moodle_discourse.py --apply --batch-size 10 --offset 10

# ... continuar hasta el lote 10: usuarios 90-99
python3 sync_moodle_discourse.py --apply --batch-size 10 --offset 90
```

### Ejemplo 2: Procesamiento en paralelo

```bash
# Terminal 1: usuarios 0-49
python3 sync_moodle_discourse.py --apply --batch-size 50 --offset 0

# Terminal 2: usuarios 50-99
python3 sync_moodle_discourse.py --apply --batch-size 50 --offset 50
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

### Ejemplo 4: Procesamiento con monitoreo

```bash
# Procesar con output detallado
python3 sync_moodle_discourse.py --apply --batch-size 20 --offset 0 2>&1 | tee procesamiento_lote_1.log

# Verificar resultados
grep "SUCCESS" sync_log_*.csv | wc -l
grep "ERROR" sync_log_*.csv | wc -l
```

## 📞 Soporte

Para reportar bugs o solicitar features, por favor:

- Abre un issue en GitHub
- Incluye información detallada sobre el problema
- Adjunta logs relevantes si es posible
- Incluye el archivo CSV de log si es relevante

---

**Nota**: Este script ha sido probado con Discourse 3.5.0.beta8 y versiones posteriores. Para versiones anteriores, pueden requerirse ajustes en la estructura de datos de la API.
