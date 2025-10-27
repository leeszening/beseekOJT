import re
from firebase_admin import auth

def get_user_info(id_token):
    """Fetches user information from Firebase Auth."""
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        user = auth.get_user(uid)
        return user
    except Exception:
        return None

def handle_auth_error(error_message):
    """
    Maps Firebase authentication error messages to user-friendly messages.
    Uses regex to find known error codes within the message for robustness.
    """
    error_map = {
        # Sign-in errors
        "EMAIL_NOT_FOUND": "❌ No account found with this email.",
        "USER_DISABLED": "⚠️ This account has been disabled.",
        "INVALID_LOGIN_CREDENTIALS": "❌ Invalid email or password.",

        # Sign-up errors
        "EMAIL_EXISTS": "📧 This email is already registered.",
        "ALREADY_EXISTS": "📧 This email is already registered.",
        "OPERATION_NOT_ALLOWED": (
            "🚫 Password sign-in is disabled for this project."
        ),
        "TOO_MANY_ATTEMPTS_TRY_LATER": (
            "🔒 We have blocked all requests from this device due to unusual "
            "activity. Try again later."
        ),
        "TOO_MANY_REQUESTS": (
            "🔒 We have blocked all requests from this device due to unusual "
            "activity. Try again later."
        ),
        "INVALID_EMAIL": "📬 The email address is not valid.",
        "INVALID_PASSWORD": "🔑 The password must be at least 8 characters long.",
        
        # Password reset errors
        "EXPIRED_OOB_CODE": (
            "🔑 The password reset link has expired. "
            "Please request a new one."
        ),
        "INVALID_OOB_CODE": (
            "🔑 The password reset link is invalid. "
            "It may have already been used."
        ),

        # General errors
        "PASSWORD_DOES_NOT_MEET_REQUIREMENTS": (
            "🔒 The password does not meet the requirements."
        ),
        "CREDENTIAL_TOO_OLD_LOGIN_AGAIN": (
            "🔑 Your session has expired. Please log in again."
        ),
        "TOKEN_EXPIRED": "🔑 Your session has expired. Please log in again.",
        "INVALID_ID_TOKEN": "🔑 Your session is invalid. Please log in again.",
        "USER_NOT_FOUND": "❌ The user account was not found.",
        
        # Custom errors
        "FIRESTORE_WRITE_FAILED": (
            "⚠️ Your account was created, but we couldn't save your "
            "details. Please contact support."
        ),
    }

    # Special handling for password requirements to give more specific feedback
    if "PASSWORD_DOES_NOT_MEET_REQUIREMENTS" in error_message:
        # Extract the specific requirements from the message
        match = re.search(r"\[(.*)\]", error_message)
        if match:
            requirements = match.group(1).replace(", ", "\n- ")
            return f"🔒 Password requirements not met:\n- {requirements}"
        else:
            return error_map["PASSWORD_DOES_NOT_MEET_REQUIREMENTS"]

    # Use regex to find a known error code in the message
    for code, friendly_message in error_map.items():
        # Use word boundaries (\b) to avoid partial matches
        if re.search(rf"\b{code}\b", error_message):
            return friendly_message

    # If no specific error is found, return the generic message
    return f"❌ An unexpected error occurred: {error_message}"
