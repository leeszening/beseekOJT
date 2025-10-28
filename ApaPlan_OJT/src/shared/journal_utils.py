from firebase_admin import firestore


# Assume db is initialized elsewhere, e.g., in your main app file
# db = firestore.client()


@firestore.transactional
def add_place_to_journal_transaction(transaction, db, journal_ref, place_data):
    """
    A transactional function to add a place to a journal.
    """
    google_place_id = place_data.get('google_place_id')
    if not google_place_id:
        raise ValueError("google_place_id is required")

    place_ref = db.collection('places').document(google_place_id)

    try:
        place_snapshot = place_ref.get(transaction=transaction)
        if not place_snapshot.exists:
            transaction.set(place_ref, {
                'name': place_data.get('name'),
                'address': place_data.get('address')
            })

        new_journal_place_ref = journal_ref.collection('journalPlaces').document()
        transaction.set(new_journal_place_ref, {
            'place_ref': place_ref,
            'description': place_data.get('description'),
            'date_visited': place_data.get('date_visited'),
            'cost': place_data.get('cost'),
            'created_at': firestore.SERVER_TIMESTAMP
        })
        return True, new_journal_place_ref.id
    except Exception as e:
        print(f"Error in transaction: {e}")
        return False, None


def add_place_to_journal(journal_id, place_data):
    """
    Adds a place to a journal, creating the place if it doesn't exist.
    This function is a wrapper for the transactional function.
    """
    db = firestore.client()
    journal_ref = db.collection('travelJournals').document(journal_id)
    transaction = db.transaction()
    success, new_id = add_place_to_journal_transaction(
        transaction, db, journal_ref, place_data
    )

    if success:
        return {"status": "success", "journal_place_id": new_id}
    else:
        return {"status": "error", "message": "Failed to add place to journal."}


def get_journal_with_details(journal_id):
    """
    Fetches a journal and all its associated place details efficiently,
    handling both referenced and embedded place data.
    """
    db = firestore.client()
    journal_ref = db.collection('travelJournals').document(journal_id)
    journal_snapshot = journal_ref.get()

    if not journal_snapshot.exists:
        return None

    journal_data = journal_snapshot.to_dict()
    journal_data['id'] = journal_snapshot.id
    
    journal_places = []
    places_sub_collection = list(journal_ref.collection('journalPlaces').stream())

    # Separate documents with and without place_ref
    docs_with_ref = []
    for doc in places_sub_collection:
        if 'place_ref' in doc.to_dict():
            docs_with_ref.append(doc)
        else:
            # For docs without a ref, just add them to the list
            place_data = doc.to_dict()
            place_data['id'] = doc.id
            journal_places.append(place_data)

    # Process documents that have a place_ref
    if docs_with_ref:
        place_refs = [doc.to_dict().get('place_ref') for doc in docs_with_ref]
        
        # Fetch all referenced place documents in a single batch
        place_snapshots = db.collection('places').where(
            firestore.FieldPath.document_id(), 'in', [ref.id for ref in place_refs]
        ).stream()
        
        places_by_id = {snap.id: snap.to_dict() for snap in place_snapshots}

        # Combine the data
        for place_doc in docs_with_ref:
            place_data = place_doc.to_dict()
            place_ref = place_data.get('place_ref')
            
            if place_ref and place_ref.id in places_by_id:
                place_details = places_by_id[place_ref.id]
                combined_data = {**place_details, **place_data}
                combined_data['id'] = place_doc.id
                journal_places.append(combined_data)

    journal_data['journalPlaces'] = journal_places
    return journal_data


def update_journal_place(journal_id, journal_place_id, update_data):
    """
    Updates a specific place document in a journal's sub-collection.
    """
    db = firestore.client()
    journal_place_ref = (db.collection('travelJournals')
                         .document(journal_id)
                         .collection('journalPlaces')
                         .document(journal_place_id))

    # Add an 'updated_at' timestamp to the update data
    update_with_timestamp = {
        **update_data,
        'updated_at': firestore.SERVER_TIMESTAMP
    }

    try:
        journal_place_ref.update(update_with_timestamp)
        return {"status": "success"}
    except Exception as e:
        print(f"Error updating document: {e}")
        return {"status": "error", "message": str(e)}


def delete_journal_place(journal_id, journal_place_id):
    """
    Deletes a specific place document from a journal's sub-collection.
    """
    db = firestore.client()
    journal_place_ref = (db.collection('travelJournals')
                         .document(journal_id)
                         .collection('journalPlaces')
                         .document(journal_place_id))

    try:
        journal_place_ref.delete()
        return {"status": "success"}
    except Exception as e:
        print(f"Error deleting document: {e}")
        return {"status": "error", "message": str(e)}


def create_journal(user_id, title, description, privacy, cover_image_url, start_date, end_date, places, journal_entries):
    """
    Creates a new journal document in Firestore.
    """
    db = firestore.client()
    try:
        journal_ref = db.collection('travelJournals').document()
        journal_ref.set({
            'user_id': user_id,
            'title': title,
            'description': description,
            'privacy': privacy,
            'cover_image_url': cover_image_url,
            'start_date': start_date,
            'end_date': end_date,
            'places': places or [],
            'journal_entries': journal_entries or [],
            'created_at': firestore.SERVER_TIMESTAMP
        })
        return journal_ref.id
    except Exception as e:
        print(f"Error creating journal: {e}")
        return None


def get_user_journals(user_id):
    """
    Fetches all journals for a given user.
    """
    db = firestore.client()
    try:
        journals_query = db.collection('travelJournals').where('user_id', '==', user_id).stream()
        journals = []
        for journal in journals_query:
            journal_data = journal.to_dict()
            journal_data['id'] = journal.id
            journals.append(journal_data)
        return journals
    except Exception as e:
        print(f"Error getting user journals: {e}")
        return []


def get_journal(journal_id):
    """
    Fetches a single journal by its ID.
    """
    db = firestore.client()
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
        print(f"Error getting journal: {e}")
        return None


def update_journal(journal_id, update_data):
    """
    Updates a journal document in Firestore.
    """
    db = firestore.client()
    try:
        journal_ref = db.collection('travelJournals').document(journal_id)
        journal_ref.update(update_data)
        return True
    except Exception as e:
        print(f"Error updating journal: {e}")
        return False


def add_place(journal_id, place_data):
    """
    Adds a place to the journal's 'journalPlaces' subcollection.
    """
    db = firestore.client()
    journal_ref = db.collection('travelJournals').document(journal_id)
    
    # Create a new document in the 'journalPlaces' subcollection
    new_place_ref = journal_ref.collection('journalPlaces').document()
    
    # Prepare the data for the new document
    # Note: This structure assumes 'place_ref' is not used or will be handled differently.
    # If 'places' collection integration is needed, this needs to be more complex.
    place_document_data = {
        'name': place_data.get('name'),
        'address': place_data.get('address'),
        'date': place_data.get('date'),
        'notes': place_data.get('notes'),
        'created_at': firestore.SERVER_TIMESTAMP
    }
    
    try:
        new_place_ref.set(place_document_data)
        return new_place_ref.id
    except Exception as e:
        print(f"Error adding place to subcollection: {e}")
        return None


def get_currency_data():
    """
    Returns a list of currencies for the autocomplete input.
    """
    return [
        "🇺🇸 USD", "🇪🇺 EUR", "🇯🇵 JPY", "🇬🇧 GBP", "🇦🇺 AUD",
        "🇨🇦 CAD", "🇨🇭 CHF", "🇨🇳 CNY", "🇸🇪 SEK", "🇳🇿 NZD",
        "🇲🇾 MYR"
    ]
