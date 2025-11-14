import json
import urllib.request
from jose import jwt
from django.conf import settings

COGNITO_POOL_ID = settings.COGNITO_USER_POOL_ID
COGNITO_REGION = settings.COGNITO_REGION
COGNITO_APP_CLIENT_ID = settings.COGNITO_APP_CLIENT_ID

JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_POOL_ID}/.well-known/jwks.json"

_jwks = None

def get_jwks():
    global _jwks
    if _jwks is None:
        with urllib.request.urlopen(JWKS_URL) as f:
            _jwks = json.loads(f.read().decode("utf-8"))
    return _jwks

def verify_cognito_token(token: str):
    jwks = get_jwks()
    headers = jwt.get_unverified_header(token)
    kid = headers["kid"]

    key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
    if key is None:
        raise ValueError("No matching JWK")

    claims = jwt.decode(
        token,
        key,
        algorithms=[key["alg"]],
        audience=COGNITO_APP_CLIENT_ID,
        issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_POOL_ID}",
    )

    return claims
