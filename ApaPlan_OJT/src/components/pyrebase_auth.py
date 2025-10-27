from firebase_config import pyrebase_auth as auth


def sign_in_user(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return {"status": "success", "data": user}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def send_password_reset_email_pyrebase(email):
    try:
        auth.send_password_reset_email(email)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
