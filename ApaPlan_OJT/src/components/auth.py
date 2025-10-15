import requests
from flask import session
from shared.config import API_KEY

def sign_in_user(email, password):
    """Signs in a user with email and password."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    resp = requests.post(url, json=payload).json()
    return resp

def create_user(email, password):
    """Creates a new user account."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    resp = requests.post(url, json=payload).json()
    return resp

def send_password_reset_email(email):
    """Sends a password reset email to the user."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={API_KEY}"
    payload = {"requestType": "PASSWORD_RESET", "email": email}
    resp = requests.post(url, json=payload).json()
    return resp

def update_user_password(id_token, new_password):
    """Updates the user's password."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={API_KEY}"
    payload = {"idToken": id_token, "password": new_password, "returnSecureToken": True}
    resp = requests.post(url, json=payload).json()
    return resp
