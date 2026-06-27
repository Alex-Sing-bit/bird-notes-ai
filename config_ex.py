# Change name of this file to config.py
# And put your data

import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

CSRF_ENABLED = True
SECRET_KEY = 'your-secret-key' # your secret key

GOOGLE_CLIENT_ID = 'your_id.apps.googleusercontent.com' # your google client id
GOOGLE_CLIENT_SECRET = 'YOUR-SECRET-KEY' # your google secret key
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

CHROMA_DB_PATH = os.path.join(basedir, 'data', 'my_birds_database')
BIRDS_DATA_PATH = os.path.join(basedir, 'data', 'wikipedia_birds.csv')

EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-small"


PASSAGE_PREFIX = "passage: "
QUERY_PREFIX = "query: "

GEMINI_API_KEY = 'gemini-api-key' # your gemini api key

# Your answer settings

CHUNK_SIZE = 384

CHROMA_COLLECTION_NAME = "birds_knowledge"

DEFAULT_SEARCH_RESULTS = 10
