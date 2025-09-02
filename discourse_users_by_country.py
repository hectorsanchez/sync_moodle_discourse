#!/usr/bin/env python3
"""
Script para obtener usuarios de Discourse agrupados por país
Muestra estadísticas y distribución geográfica de los usuarios
"""

import requests
import settings
from collections import defaultdict, Counter
import json


def get_all_discourse_users():
    """Obtiene todos los usuarios de Discourse"""
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
            print(f"❌ Error obteniendo usuarios de Discourse: {r.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error obteniendo usuarios de Discourse: {e}")
        return []


def get_user_details(username):
    """Obtiene detalles completos de un usuario específico"""
    url = f"{settings.DISCOURSE_URL}/u/{username}.json"
    headers = {
        "Api-Key": settings.DISCOURSE_API_KEY,
        "Api-Username": settings.DISCOURSE_API_USER
    }
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json().get("user", {})
        else:
            return {}
    except Exception as e:
        print(f"⚠️ Error obteniendo detalles de {username}: {e}")
        return {}


def extract_country_from_location(location):
    """Extrae el país de la ubicación del usuario"""
    if not location:
        return "Sin ubicación"
    
    # Si la ubicación contiene una coma, tomar la última parte (país)
    if "," in location:
        parts = location.split(",")
        country = parts[-1].strip()
        return country
    
    # Si no hay coma, asumir que es solo el país
    return location.strip()


def group_users_by_country():
    """Agrupa usuarios por país"""
    print("🔍 Obteniendo usuarios de Discourse...")
    users = get_all_discourse_users()
    
    if not users:
        print("❌ No se pudieron obtener usuarios")
        return
    
    print(f"📊 Total de usuarios encontrados: {len(users)}")
    print("🔍 Obteniendo detalles de ubicación...")
    
    # Diccionario para agrupar por país
    users_by_country = defaultdict(list)
    country_stats = Counter()
    
    for i, user in enumerate(users, 1):
        username = user.get("username", "N/A")
        print(f"   Procesando {i}/{len(users)}: {username}")
        
        # Obtener detalles completos del usuario
        user_details = get_user_details(username)
        location = user_details.get("location", "")
        name = user_details.get("name", username)
        email = user_details.get("email", "Sin email")
        active = user_details.get("active", False)
        
        # Extraer país de la ubicación
        country = extract_country_from_location(location)
        
        # Crear objeto de usuario con información relevante
        user_info = {
            "username": username,
            "name": name,
            "email": email,
            "location": location,
            "active": active,
            "country": country
        }
        
        # Agrupar por país
        users_by_country[country].append(user_info)
        country_stats[country] += 1
    
    return users_by_country, country_stats


def print_country_statistics(users_by_country, country_stats):
    """Imprime estadísticas por país"""
    print("\n" + "="*80)
    print("📊 ESTADÍSTICAS POR PAÍS")
    print("="*80)
    
    # Ordenar países por número de usuarios (descendente)
    sorted_countries = sorted(country_stats.items(), key=lambda x: x[1], reverse=True)
    
    total_users = sum(country_stats.values())
    
    print(f"🌍 Total de países: {len(country_stats)}")
    print(f"👥 Total de usuarios: {total_users}")
    print()
    
    for country, count in sorted_countries:
        percentage = (count / total_users) * 100
        print(f"🇺🇳 {country}: {count} usuarios ({percentage:.1f}%)")
    
    print("\n" + "="*80)


def print_detailed_users_by_country(users_by_country):
    """Imprime lista detallada de usuarios por país"""
    print("👥 USUARIOS DETALLADOS POR PAÍS")
    print("="*80)
    
    # Ordenar países alfabéticamente
    for country in sorted(users_by_country.keys()):
        users = users_by_country[country]
        print(f"\n🌍 {country} ({len(users)} usuarios)")
        print("-" * 50)
        
        for user in users:
            status = "✅ Activo" if user["active"] else "❌ Inactivo"
            print(f"  👤 {user['username']} ({user['name']})")
            print(f"     📧 {user['email']}")
            print(f"     📍 {user['location']}")
            print(f"     {status}")
            print()


def export_to_json(users_by_country, filename="discourse_users_by_country.json"):
    """Exporta los datos a un archivo JSON"""
    try:
        # Convertir defaultdict a dict normal para JSON
        export_data = dict(users_by_country)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Datos exportados a: {filename}")
    except Exception as e:
        print(f"❌ Error exportando datos: {e}")


def export_to_csv(users_by_country, filename="discourse_users_by_country.csv"):
    """Exporta los datos a un archivo CSV"""
    try:
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Escribir encabezados
            writer.writerow(['Username', 'Name', 'Email', 'Location', 'Country', 'Active'])
            
            # Escribir datos
            for country, users in users_by_country.items():
                for user in users:
                    writer.writerow([
                        user['username'],
                        user['name'],
                        user['email'],
                        user['location'],
                        user['country'],
                        user['active']
                    ])
        
        print(f"💾 Datos exportados a: {filename}")
    except Exception as e:
        print(f"❌ Error exportando CSV: {e}")


def main():
    """Función principal"""
    print("🚀 Script de análisis de usuarios de Discourse por país")
    print("="*60)
    
    # Obtener y agrupar usuarios
    users_by_country, country_stats = group_users_by_country()
    
    if not users_by_country:
        print("❌ No se encontraron usuarios para analizar")
        return
    
    # Mostrar estadísticas
    print_country_statistics(users_by_country, country_stats)
    
    # Mostrar usuarios detallados
    print_detailed_users_by_country(users_by_country)
    
    # Exportar datos
    print("\n💾 Exportando datos...")
    export_to_json(users_by_country)
    export_to_csv(users_by_country)
    
    print("\n✅ Análisis completado!")


if __name__ == "__main__":
    main()
