import requests
import argparse
import settings  # importamos la config desde settings.py


def get_moodle_users(filter_username=None):
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
    return users


def get_discourse_user(username):
    """Obtiene datos actuales del usuario en Discourse"""
    url = f"{settings.DISCOURSE_URL}/u/{username}.json"
    headers = {
        "Api-Key": settings.DISCOURSE_API_KEY,
        "Api-Username": settings.DISCOURSE_API_USER
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json().get("user", {})
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


def update_discourse_user_profile(username, updates, dry_run=True):
    """Actualiza el perfil del usuario en Discourse usando el endpoint correcto"""
    if dry_run:
        discourse_user = get_discourse_user(username)
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


def update_discourse_user_bio(username, bio_raw, dry_run=True):
    """Actualiza la biografía del usuario en Discourse"""
    url = f"{settings.DISCOURSE_URL}/u/{username}/preferences/about"
    headers = {
        "Api-Key": settings.DISCOURSE_API_KEY,
        "Api-Username": settings.DISCOURSE_API_USER,
        "Content-Type": "application/json"
    }

    if dry_run:
        discourse_user = get_discourse_user(username)
        old_bio = discourse_user.get("bio_raw", "")
        if should_update_field(bio_raw, old_bio):
            print(f"   - bio_raw: '{old_bio}' → '{bio_raw}' (actualizando campo vacío)")
        elif old_bio != bio_raw:
            print(f"   - bio_raw: '{old_bio}' → '{bio_raw}' (NO actualizando - campo ya tiene contenido)")
        return

    r = requests.put(url, headers=headers, json={"bio_raw": bio_raw})
    if r.status_code == 200:
        print(f"✅ Biografía actualizada para {username}")
    else:
        print(f"❌ Error actualizando biografía de {username}: {r.status_code} - {r.text}")


def update_discourse_email(username, new_email, dry_run=True):
    """Actualiza el email en Discourse (requiere confirmación del usuario)"""
    url = f"{settings.DISCOURSE_URL}/u/{username}/preferences/email"
    headers = {
        "Api-Key": settings.DISCOURSE_API_KEY,
        "Api-Username": settings.DISCOURSE_API_USER,
        "Content-Type": "application/json"
    }

    if dry_run:
        discourse_user = get_discourse_user(username)
        discourse_email = discourse_user.get("email", "")
        if should_update_field(new_email, discourse_email):
            print(f"   - [Dry-run] Email cambiaría a: {new_email} (requiere confirmación del usuario)")
        elif discourse_email != new_email:
            print(f"   - [Dry-run] Email NO cambiaría: {discourse_email} (ya tiene contenido)")
        return

    r = requests.put(url, headers=headers, json={"email": new_email})
    if r.status_code == 200:
        print(f"✅ Email actualizado para {username} → {new_email} (pendiente confirmación)")
    else:
        print(f"❌ Error actualizando email {username}: {r.status_code} - {r.text}")


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


def main(dry_run=True, filter_username=None):
    moodle_users = get_moodle_users(filter_username)
    if not moodle_users:
        print(f"⚠️ No se encontró el usuario {filter_username} en Moodle")
        return

    for mu in moodle_users:
        username = mu.get("username")
        fullname = mu.get("fullname")
        city = mu.get("city")
        country = mu.get("country")
        description = mu.get("description")
        email = mu.get("email")

        # Construcción del location
        location = None
        if city and country:
            location = f"{city}, {country}"
        elif country:
            location = country
        elif city:
            location = city

        # Obtener datos actuales del usuario en Discourse para comparar
        discourse_user = get_discourse_user(username)
        if not discourse_user:
            print(f"⚠️ Usuario {username} no encontrado en Discourse, saltando...")
            continue

        # Solo actualizar campos que estén vacíos en Discourse
        profile_updates = {}
        if fullname and should_update_field(fullname, discourse_user.get("name")):
            profile_updates["name"] = fullname
        if location and should_update_field(location, discourse_user.get("location")):
            profile_updates["location"] = location

        if profile_updates:
            update_discourse_user_profile(username, profile_updates, dry_run=dry_run)

        # Actualizar biografía solo si está vacía en Discourse
        if description and should_update_field(description, discourse_user.get("bio_raw")):
            update_discourse_user_bio(username, description, dry_run=dry_run)

        # Actualizar email solo si está vacío en Discourse
        discourse_email = discourse_user.get("email")
        if email and should_update_field(email, discourse_email):
            update_discourse_email(username, email, dry_run=dry_run)


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
    args = parser.parse_args()

    main(dry_run=not args.apply, filter_username=args.user)

