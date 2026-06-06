from passlib.hash import django_pbkdf2_sha256

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return django_pbkdf2_sha256.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return django_pbkdf2_sha256.hash(password)
