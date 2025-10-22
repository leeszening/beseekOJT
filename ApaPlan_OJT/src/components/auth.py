import logging
from firebase_admin import auth, firestore, exceptions
from firebase_config import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def create_user(email, password):
    """
    Creates a new user in Firebase Authentication and stores a corresponding
    record in Firestore.

    Args:
        email (str): The user's email address.
        password (str): The user's password.

    Returns:
        A dictionary with a 'status' ('success' or 'error') and 'data'
        (the user object or an error message).
    """
    try:
        # --- Step 1: Create user in Firebase Authentication ---
        display_name = email.split('@')[0]
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )
        logging.info(f"Successfully created user {user.uid} in Firebase Auth.")

        # --- Step 2: Store user info in Firestore ---
        if not db:
            logging.warning(
                "Firestore client (db) is not initialized. "
                "Skipping user storage."
            )
            # Still a success from the user's perspective.
            return {"status": "success", "data": {"uid": user.uid}}

        try:
            user_ref = db.collection("users").document(user.uid)
            user_ref.set({
                "email": email,
                "created_at": firestore.SERVER_TIMESTAMP,
                "username": display_name,
                "display_name": display_name,
                "avatar_url": ""
            })
            logging.info(
                f"Successfully stored user info for {user.uid} in Firestore."
            )
            return {"status": "success", "data": {"uid": user.uid}}

        except Exception as e:
            # This is a critical error. The user exists in Auth but not in our
            # database. It's often better to handle this with a cleanup task.
            error_message = (
                f"User created in Auth ({user.uid}), but failed to write to "
                f"Firestore: {e}"
            )
            logging.critical(error_message)
            # We return a specific error code that the frontend can use to
            # display a helpful message.
            return {"status": "error", "message": "FIRESTORE_WRITE_FAILED"}

    except exceptions.FirebaseError as e:
        # Handle Firebase-specific authentication errors
        error_message = str(e)
        logging.error(
            f"Firebase Auth Error during user creation: {error_message}"
        )
        return {"status": "error", "message": error_message}
    except Exception as e:
        # Handle other unexpected errors
        logging.error(f"An unexpected error occurred: {e}")
        return {"status": "error", "message": "UNEXPECTED_ERROR"}


def get_user_profile(uid):
    """
    Retrieves a user's profile from Firestore.
    """
    try:
        user_ref = db.collection("users").document(uid)
        user_doc = user_ref.get()
        if user_doc.exists:
            return {"status": "success", "data": user_doc.to_dict()}
        else:
            return {"status": "error", "message": "User not found"}
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return {"status": "error", "message": "UNEXPECTED_ERROR"}


def update_user_profile(uid, profile_data):
    """
    Updates a user's profile in Firestore.
    """
    try:
        user_ref = db.collection("users").document(uid)
        user_ref.update(profile_data)
        return {"status": "success"}
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return {"status": "error", "message": "UNEXPECTED_ERROR"}


def update_user_password(uid, new_password):
    """
    Updates a user's password using their UID.
    This is a privileged operation and should only be done in a secure
    backend environment.
    """
    try:
        auth.update_user(uid, password=new_password)
        logging.info(f"Successfully updated password for user {uid}.")
        return {
            "status": "success",
            "message": "Password updated successfully."
        }
    except exceptions.FirebaseError as e:
        error_message = str(e)
        logging.error(f"Failed to update password for user {uid}: {e}")
        return {"status": "error", "message": error_message}
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return {"status": "error", "message": "UNEXPECTED_ERROR"}
