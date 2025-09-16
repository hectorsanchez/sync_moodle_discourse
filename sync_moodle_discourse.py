import requests
import argparse
import settings  # importamos la config desde settings.py
import os
import time
import re
from country_codes import get_country_name
from tqdm import tqdm


def normalize_username(username):
    """
    Normaliza el nombre de usuario de Moodle para cumplir con los requisitos de Discourse.
    
    Discourse requiere que los nombres de usuario solo contengan:
    - Números (0-9)
    - Letras (a-z, A-Z)
    - Guiones (-)
    - Puntos (.)
    - Guiones bajos (_)
    
    Args:
        username (str): Nombre de usuario original de Moodle
        
    Returns:
        str: Nombre de usuario normalizado para Discourse
    """
    if not username or not username.strip():
        return 'user'
    
    # Convertir a minúsculas para consistencia
    normalized = username.lower().strip()
    
    # Reemplazar espacios y caracteres no permitidos con guiones bajos
    # Permitir solo: letras, números, guiones, puntos y guiones bajos
    normalized = re.sub(r'[^a-z0-9\-._]', '_', normalized)
    
    # Eliminar múltiples guiones bajos consecutivos
    normalized = re.sub(r'_+', '_', normalized)
    
    # Eliminar guiones bajos al inicio y final
    normalized = normalized.strip('_')
    
    # Asegurar que no esté vacío
    if not normalized:
        normalized = 'user'
    
    # Asegurar que no empiece con número (algunos sistemas no lo permiten)
    if normalized[0].isdigit():
        normalized = 'u' + normalized
    
    return normalized


def load_excluded_users():
    """Carga la lista de usuarios excluidos desde el archivo excluded_users.txt"""
    excluded_users = set()
    excluded_file = "excluded_users.txt"
    
    if not os.path.exists(excluded_file):
        print(f"⚠️ Archivo {excluded_file} no encontrado, creando uno por defecto...")
        # Crear archivo por defecto
        with open(excluded_file, 'w', encoding='utf-8') as f:
            f.write("# Lista de usuarios excluidos de la sincronización\n")
            f.write("# Un usuario por línea, comentarios con #\n")
            f.write("# Los usuarios listados aquí NO se crearán ni actualizarán en Discourse\n\n")
            f.write("# Usuarios del sistema\n")
            f.write("guest\n")
            f.write("admin\n")
            f.write("root\n\n")
            f.write("# Usuarios de prueba (ejemplos)\n")
            f.write("# testuser\n")
            f.write("# demo\n")
            f.write("# example\n\n")
            f.write("# Agregar más usuarios según sea necesario\n")
        print(f"✅ Archivo {excluded_file} creado con configuración por defecto")
    
    try:
        with open(excluded_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Ignorar líneas vacías y comentarios
                if line and not line.startswith('#'):
                    excluded_users.add(line.lower())  # Convertir a minúsculas para comparación
    except Exception as e:
        print(f"⚠️ Error leyendo {excluded_file}: {e}")
    
    return excluded_users


def is_user_excluded(username, excluded_users):
    """Verifica si un usuario está en la lista de excluidos"""
    return username.lower() in excluded_users


def get_moodle_users(filter_username=None, limit=None):
    """Obtiene usuarios desde Moodle. Si filter_username está definido, solo devuelve ese."""
    params = {
        "wstoken": settings.MOODLE_TOKEN,
        "wsfunction": "core_user_get_users",
        "moodlewsrestformat": "json",
        "criteria[0][key]": "email",
        "criteria[0][value]": "%"
    }
    r = requests.get(settings.MOODLE_ENDPOINT, params=params)
    r.raise_for_status()
    users = r.json().get("users", [])

    if filter_username:
        return [u for u in users if u.get("username") == filter_username]
    
    # Aplicar límite si se especifica
    if limit and limit > 0:
        users = users[:limit]
    
    return users


def get_discourse_user(username, user_cache=None):
    """Obtiene datos actuales del usuario en Discourse"""
    # Si tenemos caché, usarlo primero
    if user_cache and username in user_cache:
        return user_cache[username]
    
    url = f"{settings.DISCOURSE_URL}/u/{username}.json"
    headers = {
        "Api-Key": settings.DISCOURSE_API_KEY,
        "Api-Username": settings.DISCOURSE_API_USER
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        user_data = r.json().get("user", {})
        # Guardar en caché si se proporciona
        if user_cache is not None:
            user_cache[username] = user_data
        return user_data
    return {}


def is_field_empty(value):
    """Verifica si un campo está vacío (None, string vacío, o solo espacios)"""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def should_update_field(moodle_value, discourse_value):
    """Determina si un campo debe ser actualizado basado en si está vacío en Discourse"""
    # Si el campo en Discourse está vacío y tenemos un valor en Moodle, actualizar
    if is_field_empty(discourse_value) and not is_field_empty(moodle_value):
        return True
    # Si ambos campos tienen contenido, no actualizar (preservar el de Discourse)
    if not is_field_empty(discourse_value) and not is_field_empty(moodle_value):
        return False
    # Si ambos están vacíos, no actualizar
    if is_field_empty(discourse_value) and is_field_empty(moodle_value):
        return False
    # Si Discourse tiene contenido pero Moodle está vacío, no actualizar
    if not is_field_empty(discourse_value) and is_field_empty(moodle_value):
        return False
    return False


def update_discourse_user_profile(username, updates, discourse_user=None, dry_run=True):
    """Actualiza el perfil del usuario en Discourse usando el endpoint correcto"""
    if dry_run:
        if not discourse_user:
            print(f"⚠️ Usuario {username} no encontrado en Discourse")
            return

        print(f"\n📝 [Dry-run] Comparando usuario: {username}")
        for key, new_value in updates.items():
            old_value = discourse_user.get(key)
            if should_update_field(new_value, old_value):
                print(f"   - {key}: '{old_value}' → '{new_value}' (actualizando campo vacío)")
            elif old_value != new_value:
                print(f"   - {key}: '{old_value}' → '{new_value}' (NO actualizando - campo ya tiene contenido)")
        return

    # Para actualizar el perfil, usamos la estructura correcta descubierta
    # Los campos deben enviarse directamente, no envueltos en {'user': ...}
    url = f"{settings.DISCOURSE_URL}/u/{username}.json"
    headers = {
        "Api-Key": settings.DISCOURSE_API_KEY,
        "Api-Username": settings.DISCOURSE_API_USER,
        "Content-Type": "application/json"
    }
    
    # Enviar cada campo por separado para asegurar que se aplique
    for key, value in updates.items():
        data = {key: value}
        print(f"Actualizando {key} para {username}...")
        
        r = requests.put(url, headers=headers, json=data)
        if r.status_code == 200:
            print(f"✅ {key} actualizado para {username}")
        else:
            print(f"❌ Error actualizando {key} de {username}: {r.status_code} - {r.text}")

    # Verificar que los cambios se aplicaron
    verify_changes(username, updates)


def update_discourse_user_bio(username, bio_raw, discourse_user=None, dry_run=True):
    """Actualiza la biografía del usuario en Discourse"""
    if not discourse_user:
        print(f"⚠️ Usuario {username} no encontrado en Discourse, saltando biografía")
        return
        
    url = f"{settings.DISCOURSE_URL}/u/{username}/preferences/about"
    headers = {
        "Api-Key": settings.DISCOURSE_API_KEY,
        "Api-Username": settings.DISCOURSE_API_USER,
        "Content-Type": "application/json"
    }

    if dry_run:
        old_bio = discourse_user.get("bio_raw", "")
        if should_update_field(bio_raw, old_bio):
            print(f"   - bio_raw: '{old_bio}' → '{bio_raw}' (actualizando campo vacío)")
        elif old_bio != bio_raw:
            print(f"   - bio_raw: '{old_bio}' → '{bio_raw}' (NO actualizando - campo ya tiene contenido)")
        return

    try:
        r = requests.put(url, headers=headers, json={"bio_raw": bio_raw})
        if r.status_code == 200:
            print(f"✅ Biografía actualizada para {username}")
        elif r.status_code == 403:
            print(f"⚠️ Sin permisos para actualizar biografía de {username} (403)")
        else:
            print(f"❌ Error actualizando biografía de {username}: {r.status_code} - {r.text[:200]}")
    except Exception as e:
        print(f"❌ Excepción actualizando biografía de {username}: {e}")


def update_discourse_email(username, new_email, discourse_user=None, dry_run=True):
    """Actualiza el email en Discourse (requiere confirmación del usuario)"""
    if not discourse_user:
        print(f"⚠️ Usuario {username} no encontrado en Discourse, saltando email")
        return
        
    url = f"{settings.DISCOURSE_URL}/u/{username}/preferences/email"
    headers = {
        "Api-Key": settings.DISCOURSE_API_KEY,
        "Api-Username": settings.DISCOURSE_API_USER,
        "Content-Type": "application/json"
    }

    if dry_run:
        discourse_email = discourse_user.get("email", "")
        if should_update_field(new_email, discourse_email):
            print(f"   - [Dry-run] Email cambiaría a: {new_email} (requiere confirmación del usuario)")
        elif discourse_email != new_email:
            print(f"   - [Dry-run] Email NO cambiaría: {discourse_email} (ya tiene contenido)")
        return

    try:
        r = requests.put(url, headers=headers, json={"email": new_email})
        if r.status_code == 200:
            print(f"✅ Email actualizado para {username} → {new_email} (pendiente confirmación)")
        elif r.status_code == 403:
            print(f"⚠️ Sin permisos para actualizar email de {username} (403)")
        else:
            print(f"❌ Error actualizando email de {username}: {r.status_code} - {r.text[:200]}")
    except Exception as e:
        print(f"❌ Excepción actualizando email de {username}: {e}")


def verify_changes(username, expected_updates):
    """Verifica que los cambios se hayan aplicado correctamente"""
    print(f"🔍 Verificando cambios para {username}...")
    discourse_user = get_discourse_user(username)
    
    if not discourse_user:
        print(f"⚠️ No se pudo verificar {username} - usuario no encontrado")
        return
    
    for key, expected_value in expected_updates.items():
        actual_value = discourse_user.get(key)
        if actual_value == expected_value:
            print(f"   ✅ {key}: '{actual_value}' (correcto)")
        else:
            print(f"   ❌ {key}: esperado '{expected_value}', actual '{actual_value}'")


def get_all_discourse_users():
    """Obtiene todos los usuarios de Discourse para comparación"""
    url = f"{settings.DISCOURSE_URL}/admin/users/list/active.json"
    headers = {
        "Api-Key": settings.DISCOURSE_API_KEY,
        "Api-Username": settings.DISCOURSE_API_USER
    }
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"⚠️ Error obteniendo usuarios de Discourse: {r.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error obteniendo usuarios de Discourse: {e}")
        return []


def build_discourse_user_cache(moodle_usernames):
    """Construye un caché de usuarios de Discourse solo para los usuarios de Moodle"""
    print("🔄 Construyendo caché de usuarios de Discourse...")
    user_cache = {}
    
    # Obtener todos los usuarios de Discourse una vez
    all_discourse_users = get_all_discourse_users()
    if not all_discourse_users:
        return user_cache
    
    # Crear un diccionario de usuarios de Discourse por username
    discourse_users_dict = {}
    for user in all_discourse_users:
        username = user.get("username")
        if username:
            discourse_users_dict[username] = user
    
    # Para cada usuario de Moodle, verificar si existe en Discourse y obtener datos completos
    for username in moodle_usernames:
        if username in discourse_users_dict:
            # Intentar obtener datos completos del usuario
            try:
                user_data = get_discourse_user(username)
                if user_data and user_data.get("id"):  # Verificar que tiene ID válido
                    user_cache[username] = user_data
                    print(f"   ✅ Usuario {username} encontrado en Discourse con datos completos")
                else:
                    print(f"   ⚠️ Usuario {username} existe pero sin datos completos, se creará nuevo")
            except Exception as e:
                print(f"   ⚠️ Usuario {username} existe pero error al obtener datos: {e}, se creará nuevo")
        else:
            print(f"   ⚠️ Usuario {username} no encontrado en Discourse")
    
    print(f"✅ Caché construido: {len(user_cache)} usuarios de Discourse encontrados")
    return user_cache


def user_exists_in_discourse(username, discourse_users=None):
    """Verifica si un usuario existe en Discourse"""
    if discourse_users is None:
        discourse_users = get_all_discourse_users()
    
    return any(user.get("username") == username for user in discourse_users)


def get_moodle_groups_for_user(username):
    """Obtiene los grupos de Moodle para un usuario específico"""
    params = {
        "wstoken": settings.MOODLE_TOKEN,
        "wsfunction": "core_group_get_course_user_groups",
        "moodlewsrestformat": "json",
        "userid": username  # Necesitamos el ID del usuario
    }
    
    try:
        r = requests.get(settings.MOODLE_ENDPOINT, params=params)
        if r.status_code == 200:
            groups = r.json().get("groups", [])
            return [group.get("name") for group in groups]
        else:
            print(f"⚠️ Error obteniendo grupos de Moodle para {username}: {r.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error obteniendo grupos de Moodle para {username}: {e}")
        return []


def create_discourse_user(username, moodle_data, dry_run=True):
    """Crea un nuevo usuario en Discourse"""
    # Normalizar el nombre de usuario para cumplir con los requisitos de Discourse
    original_username = username
    normalized_username = normalize_username(username)
    
    if original_username != normalized_username:
        print(f"   🔄 Normalizando username: '{original_username}' → '{normalized_username}'")
    
    if dry_run:
        print(f"   - [Dry-run] CREARÍA nuevo usuario: {normalized_username}")
        print(f"     Datos: {moodle_data.get('fullname')} - {moodle_data.get('email')}")
        if original_username != normalized_username:
            print(f"     Username original: {original_username}")
        return True
    
    url = f"{settings.DISCOURSE_URL}/users.json"
    headers = {
        "Api-Key": settings.DISCOURSE_API_KEY,
        "Api-Username": settings.DISCOURSE_API_USER,
        "Content-Type": "application/json"
    }

    # Construir datos del usuario usando el username normalizado
    user_data = {
        "name": moodle_data.get("fullname", normalized_username),
        "username": normalized_username,
        "email": moodle_data.get("email", f"{normalized_username}@example.com"),
        "password": f"TempPass{normalized_username}123!"  # Password temporal para SSO
    }
    
    try:
        print(f"🆕 Creando usuario: {normalized_username}")
        r = requests.post(url, headers=headers, json=user_data)
        
        if r.status_code == 200:
            response = r.json()
            if response.get("success"):
                print(f"✅ Usuario {normalized_username} creado exitosamente")
                if original_username != normalized_username:
                    print(f"   Username original: {original_username}")
                print(f"   Nota: Usuario creado inactivo, requiere activación por email")
                return True
            else:
                print(f"❌ Error creando usuario {normalized_username}: {response.get('message', 'Error desconocido')}")
                return False
        else:
            print(f"❌ Error creando usuario {normalized_username}: {r.status_code} - {r.text}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción creando usuario {normalized_username}: {e}")
        return False


def sync_user_groups(username, moodle_groups, dry_run=True):
    """Sincroniza grupos del usuario basado en grupos de Moodle"""
    if not moodle_groups:
        return

    if dry_run:
        print(f"   - [Dry-run] Sincronizaría grupos: {', '.join(moodle_groups)}")
        return

    # Nota: La sincronización de grupos requiere endpoints adicionales
    # Por ahora solo mostramos qué grupos se sincronizarían
    print(f"📋 Grupos de Moodle para {username}: {', '.join(moodle_groups)}")
    print(f"   Nota: Sincronización de grupos requiere implementación adicional")


def main(dry_run=True, filter_username=None, force_recreate=False, batch_size=None):
    # Cargar lista de usuarios excluidos
    excluded_users = load_excluded_users()
    if excluded_users:
        print(f"🚫 Usuarios excluidos: {', '.join(sorted(excluded_users))}")
    
    # Usar batch_size si no se especifica un usuario específico
    limit = batch_size if not filter_username else None
    moodle_users = get_moodle_users(filter_username, limit=limit)
    
    if not moodle_users:
        if filter_username:
            print(f"⚠️ No se encontró el usuario {filter_username} en Moodle")
        else:
            print(f"⚠️ No se encontraron usuarios en Moodle")
        return

    # Obtener usuarios de Discourse para comparación
    discourse_users = get_all_discourse_users()
    print(f"📊 Usuarios en Moodle: {len(moodle_users)}")
    print(f"📊 Usuarios en Discourse: {len(discourse_users)}")
    
    # Mostrar información del lote
    if batch_size and not filter_username:
        print(f"📦 Procesando lote de {len(moodle_users)} usuarios (límite: {batch_size})")
    elif filter_username:
        print(f"👤 Procesando usuario específico: {filter_username}")
    else:
        print(f"📦 Procesando todos los usuarios disponibles")

    # Construir caché de usuarios de Discourse (usar usernames normalizados)
    moodle_usernames = [normalize_username(mu.get("username")) for mu in moodle_users if mu.get("username")]
    user_cache = build_discourse_user_cache(moodle_usernames)

    # Inicializar estadísticas
    stats = {
        'total': len(moodle_users),
        'procesados': 0,
        'creados': 0,
        'actualizados': 0,
        'excluidos': 0,
        'errores': 0
    }
    
    start_time = time.time()
    last_summary_time = start_time

    # Crear barra de progreso
    progress_bar = tqdm(total=stats['total'], desc="Sincronizando usuarios", unit="usuario")

    for i, mu in enumerate(moodle_users):
        original_username = mu.get("username")
        normalized_username = normalize_username(original_username)
        fullname = mu.get("fullname")
        city = mu.get("city")
        country = mu.get("country")
        description = mu.get("description")
        email = mu.get("email")

        # Actualizar barra de progreso
        progress_bar.set_postfix({
            'Usuario': normalized_username[:20] + '...' if len(normalized_username) > 20 else normalized_username,
            'Procesados': f"{i+1}/{stats['total']}"
        })

        # Verificar si el usuario está en la lista de excluidos (usar username original)
        if is_user_excluded(original_username, excluded_users):
            stats['excluidos'] += 1
            progress_bar.update(1)
            continue

        # Obtener datos del usuario de Discourse desde el caché (usar username normalizado)
        discourse_user = user_cache.get(normalized_username, {})
        user_exists = bool(discourse_user)

        if not user_exists or force_recreate:
            # Usuario no existe en Discourse o forzar recreación
            if force_recreate and user_exists:
                print(f"🔄 Forzando recreación del usuario {normalized_username}...")
            else:
                print(f"🆕 Usuario {normalized_username} no existe en Discourse, creando...")
                if original_username != normalized_username:
                    print(f"   Username original: {original_username}")
            
            if create_discourse_user(original_username, mu, dry_run=dry_run):
                stats['creados'] += 1
                # Obtener grupos de Moodle para este usuario (usar username original)
                moodle_groups = get_moodle_groups_for_user(original_username)
                sync_user_groups(normalized_username, moodle_groups, dry_run=dry_run)
            else:
                stats['errores'] += 1
                progress_bar.update(1)
                continue
        else:
            # Usuario existe, procesar actualizaciones
            print(f"🔄 Usuario {normalized_username} existe en Discourse, actualizando...")
            stats['actualizados'] += 1

        # Construcción del location con conversión de código de país
        location = None
        country_name = get_country_name(country) if country else None
        
        if city and country_name:
            location = f"{city}, {country_name}"
        elif country_name:
            location = country_name
        elif city:
            location = city

        # Solo actualizar campos que estén vacíos en Discourse
        profile_updates = {}
        if fullname and should_update_field(fullname, discourse_user.get("name")):
            profile_updates["name"] = fullname
        if location and should_update_field(location, discourse_user.get("location")):
            profile_updates["location"] = location

        if profile_updates:
            update_discourse_user_profile(normalized_username, profile_updates, discourse_user, dry_run=dry_run)

        # Actualizar biografía solo si está vacía en Discourse
        if description and should_update_field(description, discourse_user.get("bio_raw")):
            update_discourse_user_bio(normalized_username, description, discourse_user, dry_run=dry_run)

        # Actualizar email solo si está vacío en Discourse
        discourse_email = discourse_user.get("email")
        if email and should_update_field(email, discourse_email):
            update_discourse_email(normalized_username, email, discourse_user, dry_run=dry_run)

        stats['procesados'] += 1
        progress_bar.update(1)

        # Mostrar resumen cada 50 usuarios o cada 5 minutos
        current_time = time.time()
        if (i + 1) % 50 == 0 or (current_time - last_summary_time) > 300:
            elapsed = current_time - start_time
            avg_time_per_user = elapsed / (i + 1)
            remaining_users = stats['total'] - (i + 1)
            estimated_remaining = (remaining_users * avg_time_per_user) / 60  # en minutos
            
            print(f"\n📈 RESUMEN INTERMEDIO:")
            print(f"   Progreso: {i+1}/{stats['total']} ({((i+1)/stats['total'])*100:.1f}%)")
            print(f"   Tiempo transcurrido: {elapsed/60:.1f} min")
            print(f"   Tiempo estimado restante: {estimated_remaining:.1f} min")
            print(f"   Usuarios creados: {stats['creados']}")
            print(f"   Usuarios actualizados: {stats['actualizados']}")
            print(f"   Usuarios excluidos: {stats['excluidos']}")
            print(f"   Errores: {stats['errores']}")
            last_summary_time = current_time

    # Cerrar barra de progreso
    progress_bar.close()
    
    # Mostrar resumen final
    total_time = time.time() - start_time
    print(f"\n🎉 SINCRONIZACIÓN COMPLETADA")
    print(f"⏱️  Tiempo total: {total_time/60:.1f} minutos")
    print(f"📊 Estadísticas finales:")
    print(f"   Total procesados: {stats['procesados']}")
    print(f"   Usuarios creados: {stats['creados']}")
    print(f"   Usuarios actualizados: {stats['actualizados']}")
    print(f"   Usuarios excluidos: {stats['excluidos']}")
    print(f"   Errores: {stats['errores']}")
    if stats['procesados'] > 0:
        print(f"   Tiempo promedio por usuario: {total_time/stats['procesados']:.2f} segundos")
    else:
        print(f"   Tiempo promedio por usuario: N/A (no se procesaron usuarios)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sincroniza datos de usuarios Moodle -> Discourse")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica los cambios en lugar de solo mostrar (por defecto es dry-run)"
    )
    parser.add_argument(
        "--user",
        help="Sincroniza solo un usuario específico (por username)"
    )
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Fuerza la recreación de usuarios existentes en Discourse"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=settings.BATCH_SIZE,
        help=f"Número de usuarios a procesar en esta ejecución (por defecto: {settings.BATCH_SIZE})"
    )
    args = parser.parse_args()

    main(dry_run=not args.apply, filter_username=args.user, force_recreate=args.force_recreate, batch_size=args.batch_size)

