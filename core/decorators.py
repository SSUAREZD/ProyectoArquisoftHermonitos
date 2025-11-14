from functools import wraps
from django.http import JsonResponse
from core.auth_cognito import verify_cognito_token

def require_auth(required_role=None):
    def wrapper(func):
        @wraps(func)
        def decorated(request, *args, **kwargs):
            auth = request.META.get('HTTP_AUTHORIZATION', '')

            if not auth.startswith("Bearer "):
                return JsonResponse({"detail": "Token requerido"}, status=401)

            token = auth.replace("Bearer ", "").strip()

            try:
                claims = verify_cognito_token(token)
            except Exception:
                return JsonResponse({"detail": "Token inválido"}, status=401)

            # optional: check group
            if required_role:
                groups = claims.get("cognito:groups", [])
                if required_role not in groups:
                    return JsonResponse({"detail": "No autorizado"}, status=403)

            request.cognito_claims = claims
            return func(request, *args, **kwargs)
        return decorated
    return wrapper
