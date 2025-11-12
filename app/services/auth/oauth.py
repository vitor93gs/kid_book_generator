from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

# Load environment variables
config = Config(".env")

oauth = OAuth(config)

# Register Google OAuth
oauth.register(
    name='google',
    client_id=config('GOOGLE_CLIENT_ID'),
    client_secret=config('GOOGLE_CLIENT_SECRET'),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={
        'scope': 'openid email profile'
    }
)