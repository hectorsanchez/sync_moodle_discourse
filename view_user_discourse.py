import requests
import settings

# Verificar usuario, agregar el nombre de usuario en la siguiente linea
username = 'usuario'
url = f'{settings.DISCOURSE_URL}/u/{username}.json'
headers = {
    'Api-Key': settings.DISCOURSE_API_KEY,
    'Api-Username': settings.DISCOURSE_API_USER
}

r = requests.get(url, headers=headers)
if r.status_code == 200:
    user = r.json().get('user', {})
    print(f'  Username: {user.get("username")}')
    print(f'  Name: {user.get("name")}')
    print(f'  Location: {user.get("location")}')
    print(f'  Bio: {user.get("bio_ra")}')
    print(f'  Email: {user.get("email")}')
    print(f'  Active: {user.get("active")}')
    print(f'  ID: {user.get("id")}')
else:
    print(f'Error: {r.status_code} - {r.text}')
