from firebase_admin import firestore
from firebase_config import db


def create_journal(user_id, title, summary, introduction, cover_image_url,
                   start_date, end_date, total_cost, currency, places):
    """
    Creates a new journal entry in the Firestore database.
    """
    try:
        journals_ref = db.collection('journals')
        journal_data = {
            'userId': str(user_id),  # Ensure userId is stored as a string
            'title': title,
            'summary': summary,
            'introduction': introduction,
            'cover_image_url': cover_image_url,
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
        journal_ref = db.collection('journals').document(journal_id)
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
        journals_ref = db.collection('journals')
        query = journals_ref.where('userId', '==', str(user_id))
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
        journals_ref = db.collection('journals')
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
        journal_ref = db.collection('journals').document(journal_id)
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
        journal_ref = db.collection('journals').document(journal_id)
        journal_ref.delete()
        return True
    except Exception as e:
        print(f"An error occurred while deleting the journal: {e}")
        return False
