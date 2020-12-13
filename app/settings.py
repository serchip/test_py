from dotenv import load_dotenv
import os
from urllib.parse import urlparse

load_dotenv()
POSTGRES_CONNECT: str = urlparse(os.environ.get('POSTGRES_CONNECT_URL', '//test_user:password@db:5432/test_db'))

DEBUG = os.getenv("DEBUG", True)
API_PREFIX = '/v1'
PROJECT_NAME = 'web-api'
VERSION = '0.1'
