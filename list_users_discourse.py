import requests
import settings

# Verificar lista actualizada de usuarios en Discourse
url = f'{settings.DISCOURSE_URL}/admin/users/list/active.json'
headers = {
    'Api-Key': settings.DISCOURSE_API_KEY,
    'Api-Username': settings.DISCOURSE_API_USER
}

r = requests.get(url, headers=headers)
if r.status_code == 200:
    users = r.json()
    print(f'Total de usuarios en Discourse: {len(users)}')
    print('\nUsuarios encontrados:')
    for user in users:
        username = user.get('username', 'N/A')
        name = user.get('name', 'N/A')
        active = user.get('active', 'N/A')
        print(f'  - {username} ({name}) - Active: {active}')
else:
    print(f'Error: {r.status_code} - {r.text}')
