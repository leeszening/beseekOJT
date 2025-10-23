from firebase_admin import firestore, storage
from firebase_config import db
import uuid
import base64
import mimetypes


def create_journal(user_id, title, summary, introduction, cover_image_url,
                   start_date, end_date, total_cost, currency, places):
    """
    Creates a new journal entry in the Firestore database.
    """
    try:
        image_url = 'https://via.placeholder.com/150'
        if cover_image_url and cover_image_url.startswith('data:image'):
            header, encoded = cover_image_url.split(",", 1)
            mime_type = header.split(";")[0].split(":")[1]
            
            # Guess the extension based on the mime type
            extension = mimetypes.guess_extension(mime_type)
            if not extension:
                extension = '.png'  # Default to .png if detection fails
            
            image_data = base64.b64decode(encoded)
            
            bucket = storage.bucket()
            blob = bucket.blob(f"cover_images/{uuid.uuid4()}{extension}")
            
            blob.upload_from_string(image_data, content_type=mime_type)
            blob.make_public()
            image_url = blob.public_url

        journals_ref = db.collection('travelJournals')
        journal_data = {
            'user_id': str(user_id),
            'title': title,
            'summary': summary,
            'introduction': introduction,
            'cover_image_url': image_url,
            'start_date': start_date,
            'end_date': end_date,
            'total_cost': total_cost,
            'currency': currency,
            'places': places,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
        }
        update_time, journal_ref = journals_ref.add(journal_data)
        return journal_ref.id
    except Exception as e:
        print(f"An error occurred while creating the journal: {e}")
        return None


def get_journal(journal_id):
    """
    Retrieves a specific journal entry from Firestore.
    """
    try:
        journal_ref = db.collection('travelJournals').document(journal_id)
        journal = journal_ref.get()
        if journal.exists:
            journal_data = journal.to_dict()
            journal_data['id'] = journal.id
            return journal_data
        else:
            return None
    except Exception as e:
        print(f"An error occurred while retrieving the journal: {e}")
        return None


def get_user_journals(user_id):
    """
    Retrieves all journal entries for a specific user, ordered by creation time.
    """
    try:
        journals_ref = db.collection('travelJournals')
        query = journals_ref.where('user_id', '==', str(user_id)).order_by(
            'created_at', direction=firestore.Query.DESCENDING
        )
        results = query.stream()

        journals_list = []
        for doc in results:
            journal_data = doc.to_dict()
            journal_data['id'] = doc.id
            journals_list.append(journal_data)
        return journals_list
    except Exception as e:
        print(f"An error occurred while retrieving user journals: {e}")
        return []


def get_all_journals():
    """
    Retrieves all journal entries, for debugging purposes.
    """
    try:
        journals_ref = db.collection('travelJournals')
        results = journals_ref.stream()
        journals_list = []
        for doc in results:
            journal_data = doc.to_dict()
            journal_data['id'] = doc.id
            journals_list.append(journal_data)
        return journals_list
    except Exception as e:
        print(f"An error occurred while retrieving all journals: {e}")
        return []


def update_journal(journal_id, data):
    """
    Updates an existing journal entry in Firestore.
    """
    try:
        journal_ref = db.collection('travelJournals').document(journal_id)
        data['updated_at'] = firestore.SERVER_TIMESTAMP
        journal_ref.update(data)
        return True
    except Exception as e:
        print(f"An error occurred while updating the journal: {e}")
        return False


def delete_journal(journal_id):
    """
    Deletes a journal entry from Firestore.
    """
    try:
        journal_ref = db.collection('travelJournals').document(journal_id)
        journal_ref.delete()
        return True
    except Exception as e:
        print(f"An error occurred while deleting the journal: {e}")
        return False
