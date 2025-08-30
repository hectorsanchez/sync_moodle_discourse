# Sync Moodle → Discourse

Script en Python para sincronizar datos de usuarios desde **Moodle** hacia **Discourse**.

Permite mantener actualizados campos como:

- Nombre completo (`name`)
- Ubicación (`location`, combinando ciudad y país de Moodle)
- Biografía (`bio_raw`)
- Email (`email`, requiere confirmación por parte del usuario en Discourse)

---

## 📦 Requerimientos

- Python 3.7 o superior  
- Librería `requests` instalada:
  ```bash
  pip install requests

## Recomendado utilizar con virtual env

python3 -m venv path/to/venv
cd path/to/venv
source bin/activate  
python3 -m pip install requests  


▶️ Uso

Ejecutar el script principal:

python3 sync_moodle_discourse.py

Modos

Dry-run (por defecto):
Muestra las diferencias encontradas sin aplicar cambios.

python3 sync_moodle_discourse.py


Aplicar cambios:
Sincroniza realmente los usuarios en Discourse.

python3 sync_moodle_discourse.py --apply


Un solo usuario:
Limita la sincronización a un username específico (ejemplo: jdoe).

python3 sync_moodle_discourse.py --user jdoe


En modo aplicado:

python3 sync_moodle_discourse.py --user jdoe --apply

📌 Notas importantes

La actualización de email en Discourse envía un correo de confirmación al nuevo email.
El cambio no queda activo hasta que el usuario lo confirma.

Si un usuario de Moodle no existe en Discourse, se ignora (no crea usuarios nuevos).

Puede ejecutarse manualmente o integrarse en un cron job para sincronización periódica.

Ejemplo de cron (ejecuta cada noche a las 02:00 en modo aplicado):

0 2 * * * /usr/bin/python3 /ruta/al/proyecto/sync_moodle_discourse.py --apply >> /var/log/sync_moodle_discourse.log 2>&1
