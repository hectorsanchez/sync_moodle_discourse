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
     ```

## 📖 Uso

### Comandos básicos

```bash
# Modo dry-run (por defecto) - solo muestra diferencias
python3 sync_moodle_discourse.py

# Aplicar cambios reales
python3 sync_moodle_discourse.py --apply

# Sincronizar usuario específico (modo dry-run)
python3 sync_moodle_discourse.py --user username

# Sincronizar usuario específico y aplicar cambios
python3 sync_moodle_discourse.py --user username --apply
```

### Modos de operación

| Modo | Descripción | Comando |
|------|-------------|---------|
| **Dry-run** | Muestra diferencias sin aplicar cambios | `python3 sync_moodle_discourse.py` |
| **Apply** | Aplica cambios reales en Discourse | `python3 sync_moodle_discourse.py --apply` |
| **Usuario específico** | Limita sincronización a un usuario | `python3 sync_moodle_discourse.py --user username` |
| **Combinado** | Usuario específico + aplicar cambios | `python3 sync_moodle_discourse.py --user username --apply` |

## 🔧 Funcionamiento

### Proceso de sincronización

1. **Obtención de datos** desde Moodle via API REST
2. **Comparación** con datos actuales en Discourse
3. **Actualización** de campos modificados
4. **Verificación** de cambios aplicados correctamente

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
- No crea usuarios nuevos automáticamente
- Requiere que el SSO esté configurado correctamente

## 🕐 Automatización

### Cron job (Linux/macOS)

Para sincronización automática periódica:

```bash
# Editar crontab
crontab -e

# Ejecutar cada noche a las 02:00
0 2 * * * /ruta/completa/venv/bin/python3 /ruta/al/proyecto/sync_moodle_discourse.py --apply >> /var/log/sync_moodle_discourse.log 2>&1

# Ejecutar cada hora
0 * * * * /ruta/completa/venv/bin/python3 /ruta/al/proyecto/sync_moodle_discourse.py --apply >> /var/log/sync_moodle_discourse.log 2>&1
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

### Logs y debugging

El script proporciona información detallada:
- ✅ Cambios aplicados exitosamente
- ❌ Errores encontrados
- 🔍 Verificación de cambios
- 📝 Comparación de datos antes/después

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

## 📞 Soporte

Para reportar bugs o solicitar features, por favor:

- Abre un issue en GitHub
- Incluye información detallada sobre el problema
- Adjunta logs relevantes si es posible

---

**Nota**: Este script ha sido probado con Discourse 3.5.0.beta8 y versiones posteriores. Para versiones anteriores, pueden requerirse ajustes en la estructura de datos de la API.
