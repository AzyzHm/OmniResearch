import secrets

jwt_secret = secrets.token_urlsafe(32)
print(jwt_secret)