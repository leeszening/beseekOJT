import logging
from datetime import datetime, timezone
from firebase_admin import firestore, storage
from firebase_config import db
import uuid
import base64
import mimetypes
import pycountry

DEFAULT_COVER_IMAGE = 'https://via.placeholder.com/150'


def _format_document_timestamps(doc_data):
    """
    Recursively converts Firestore timestamps to ISO 8601 strings.
    """
    if not doc_data:
        return doc_data

    # Format top-level timestamps
    for field in ['created_at', 'updated_at']:
        if field in doc_data and hasattr(doc_data[field], 'isoformat'):
            doc_data[field] = doc_data[field].isoformat()

    # Format timestamps in nested 'journalPlaces'
    if 'journalPlaces' in doc_data and isinstance(doc_data['journalPlaces'], list):
        for place in doc_data['journalPlaces']:
            if isinstance(place, dict):
                for field in ['created_at', 'updated_at']:
                    if field in place and hasattr(place[field], 'isoformat'):
                        place[field] = place[field].isoformat()
    return doc_data


def create_journal(user_id, title, summary, introduction, cover_image_url,
                   start_date, end_date, total_cost, currency):
    """
    Creates a new journal entry in the Firestore database.
    """
    try:
        image_url = DEFAULT_COVER_IMAGE
        if cover_image_url and cover_image_url.startswith('data:image'):
            header, encoded = cover_image_url.split(",", 1)
            mime_type = header.split(";")[0].split(":")[1]
            
            extension = mimetypes.guess_extension(mime_type) or '.png'
            
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
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'journalPlaces': [],
        }
        _, journal_ref = journals_ref.add(journal_data)
        return journal_ref.id
    except Exception as e:
        logging.error(f"An error occurred while creating the journal: {e}")
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
            return _format_document_timestamps(journal_data)
        else:
            return None
    except Exception as e:
        logging.error(f"An error occurred while retrieving the journal: {e}")
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
            journals_list.append(_format_document_timestamps(journal_data))
        return journals_list
    except Exception as e:
        logging.error(f"An error occurred while retrieving user journals: {e}")
        return []


def get_all_journals():
    """
    Retrieves all journal entries, for debugging purposes.
    """
    try:
        journals_ref = db.collection('travelJournals')
        results = journals_ref.stream()
        journals_list = [doc.to_dict() | {'id': doc.id} for doc in results]
        return journals_list
    except Exception as e:
        logging.error(f"An error occurred while retrieving all journals: {e}")
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
        logging.error(f"An error occurred while updating the journal: {e}")
        return False


def add_place(journal_id, place_data):
    """
    Adds a new place to the 'journalPlaces' array within a journal document.
    """
    if not journal_id:
        logging.error("`journal_id` is missing.")
        return None

    try:
        journal_ref = db.collection('travelJournals').document(journal_id)
        
        # Check if the journal document exists before attempting to update it
        journal_doc = journal_ref.get()
        if not journal_doc.exists:
            logging.error(f"Journal with ID '{journal_id}' not found.")
            return None

        place_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        new_place = place_data.copy()
        new_place.update({
            'place_id': place_id,
            'created_at': now,
            'updated_at': now
        })

        journal_ref.update({
            'journalPlaces': firestore.ArrayUnion([new_place]),
            'updated_at': firestore.SERVER_TIMESTAMP
        })

        logging.info(f"Successfully added place '{place_id}' to journal '{journal_id}'.")
        return place_id

    except Exception as e:
        logging.error(f"An error occurred while adding a place to journal '{journal_id}': {e}", exc_info=True)
        return None


def delete_journal(journal_id):
    """
    Deletes a journal entry from Firestore.
    """
    try:
        journal_ref = db.collection('travelJournals').document(journal_id)
        journal_ref.delete()
        return True
    except Exception as e:
        logging.error(f"An error occurred while deleting the journal: {e}")
        return False


def get_currency_data():
    currency_data = []
    for country in pycountry.countries:
        try:
            currency = pycountry.currencies.get(numeric=country.numeric)
            if currency:
                # The 'flag' attribute was removed in pycountry 23.12.11.
                # This is the new recommended way to get the flag emoji.
                flag = "".join(
                    chr(ord(c.lower()) + 127397) for c in country.alpha_2
                )
                currency_data.append(f"{flag} {currency.alpha_3}")
        except (AttributeError, KeyError):
            continue
    return sorted(list(set(currency_data)))
