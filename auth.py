from storage import load_users

def authenticate(username, password):
    users = load_users()
    for user in users:
        if user.username == username and user.password == password:
            return True
    return False
