# Archivo de configuración para sync_moodle_discourse

ENV = "development"

# Moodle
MOODLE_ENDPOINT = "MOODLE URL ENDPOINT"
MOODLE_TOKEN = "MOODLE TOKEN"

# Discourse
DISCOURSE_URL = "DISCOURE URL"
DISCOURSE_API_KEY = "API KEY"
DISCOURSE_API_USER = "user"  # Usuario admin que genera la API key

# Configuración de procesamiento por lotes
BATCH_SIZE = 10  # Número de usuarios a procesar en cada ejecución (por defecto: 10)