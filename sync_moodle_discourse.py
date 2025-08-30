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


def update_discourse_email(username, new_email, dry_run=True):
    """Actualiza el email en Discourse (requiere confirmación del usuario)"""
    url = f"{settings.DISCOURSE_URL}/u/{username}/preferences/email"
    headers = {
        "Api-Key": settings.DISCOURSE_API_KEY,
        "Api-Username": settings.DISCOURSE_API_USER,
        "Content-Type": "application/json"
    }

    if dry_run:
        print(f"   - [Dry-run] Email cambiaría a: {new_email} (requiere confirmación del usuario)")
        return

    r = requests.put(url, headers=headers, json={"email": new_email})
    if r.status_code == 200:
        print(f"✅ Email actualizado para {username} → {new_email} (pendiente confirmación)")
    else:
        print(f"❌ Error actualizando email {username}: {r.status_code} - {r.text}")


def update_discourse_user(username, updates, dry_run=True):
    url = f"{settings.DISCOURSE_URL}/u/{username}.json"
    headers = {
        "Api-Key": settings.DISCOURSE_API_KEY,
        "Api-Username": settings.DISCOURSE_API_USER,
        "Content-Type": "application/json"
    }

    if dry_run:
        discourse_user = get_discourse_user(username)
        if not discourse_user:
            print(f"⚠️ Usuario {username} no encontrado en Discourse")
            return

        print(f"\n📝 [Dry-run] Comparando usuario: {username}")
        for key, new_value in updates.items():
            old_value = discourse_user.get(key)
            if old_value != new_value:
                print(f"   - {key}: '{old_value}' → '{new_value}'")
        return

    r = requests.put(url, headers=headers, json={"user": updates})
    if r.status_code == 200:
        print(f"✅ Actualizado {username} ({updates})")
    else:
        print(f"❌ Error con {username}: {r.status_code} - {r.text}")


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

        updates = {}
        if fullname:
            updates["name"] = fullname
        if location:
            updates["location"] = location
        if description:
            updates["bio_raw"] = description

        if updates:
            update_discourse_user(username, updates, dry_run=dry_run)

        discourse_user = get_discourse_user(username)
        discourse_email = discourse_user.get("email")
        if email and discourse_email != email:
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

