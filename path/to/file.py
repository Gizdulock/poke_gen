def authenticate_user(username: str, password: str) -> bool:
    if username == "admin" and password == "password":
        return True
    return False