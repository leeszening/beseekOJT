import os
from firebase_admin import firestore, storage
from google.cloud.firestore_v1.document import DocumentReference
from datetime import datetime
import base64
import uuid
import re
import io
from cachetools import cached, TTLCache, keys
from cachetools.keys import hashkey

# Cache for journal data, with a TTL of 5 minutes
journal_cache = TTLCache(maxsize=100, ttl=300)

# Cache for user profiles, with a TTL of 5 minutes
user_profile_cache = TTLCache(maxsize=100, ttl=300)


def clear_journal_cache(journal_id):
    """Clears the cache for a specific journal."""
    key = hashkey(journal_id)
    if key in journal_cache:
        del journal_cache[key]


def _sanitize_for_json(data):
    """
    Recursively sanitizes Firestore data types for JSON serialization.
    """
    if isinstance(data, dict):
        return {k: _sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_sanitize_for_json(i) for i in data]
    elif isinstance(data, DocumentReference):
        return data.path
    elif isinstance(data, datetime):
        return data.isoformat()
    return data


# Assume db is initialized elsewhere, e.g., in your main app file
# db = firestore.client()


@firestore.transactional
def add_place_to_journal_transaction(transaction, db, journal_ref, place_data):
    """
    A transactional function to add a place to a journal.
    """
    google_place_id = place_data.get("google_place_id")
    if not google_place_id:
        raise ValueError("google_place_id is required")

    place_ref = db.collection("places").document(google_place_id)

    try:
        place_snapshot = place_ref.get(transaction=transaction)
        if not place_snapshot.exists:
            transaction.set(
                place_ref,
                {
                    "name": place_data.get("name"),
                    "address": place_data.get("address"),
                },
            )

        new_journal_place_ref = journal_ref.collection(
            "journalPlaces"
        ).document()
        transaction.set(
            new_journal_place_ref,
            {
                "place_ref": place_ref,
                "description": place_data.get("description"),
                "date_visited": place_data.get("date_visited"),
                "cost": place_data.get("cost"),
                "created_at": firestore.SERVER_TIMESTAMP,
            },
        )
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
    journal_ref = db.collection("travelJournals").document(journal_id)
    transaction = db.transaction()
    success, new_id = add_place_to_journal_transaction(
        transaction, db, journal_ref, place_data
    )

    if success:
        clear_journal_cache(journal_id)
        return {"status": "success", "journal_place_id": new_id}
    else:
        return {"status": "error", "message": "Failed to add place to journal."}


@cached(journal_cache)
def get_journal_with_details(journal_id):
    """
    Fetches a journal and all its associated place details efficiently,
    handling both referenced and embedded place data.
    """
    db = firestore.client()
    journal_ref = db.collection("travelJournals").document(journal_id)
    journal_snapshot = journal_ref.get()

    if not journal_snapshot.exists:
        return None

    journal_data = journal_snapshot.to_dict()
    journal_data["id"] = journal_snapshot.id

    journal_places = []
    places_sub_collection = list(journal_ref.collection("journalPlaces").stream())

    # Separate documents with and without place_ref
    docs_with_ref = []
    for doc in places_sub_collection:
        if "place_ref" in doc.to_dict():
            docs_with_ref.append(doc)
        else:
            # For docs without a ref, just add them to the list
            place_data = doc.to_dict()
            place_data["id"] = doc.id
            journal_places.append(place_data)

    # Process documents that have a place_ref
    if docs_with_ref:
        place_refs = [doc.to_dict().get("place_ref") for doc in docs_with_ref]

        # Fetch all referenced place documents in a single batch
        place_snapshots = db.collection("places").where(
            "__name__", "in", [ref.id for ref in place_refs]
        ).stream()

        places_by_id = {snap.id: snap.to_dict() for snap in place_snapshots}

        # Combine the data
        for place_doc in docs_with_ref:
            place_data = place_doc.to_dict()
            place_ref = place_data.get("place_ref")

            if place_ref and place_ref.id in places_by_id:
                place_details = places_by_id[place_ref.id]
                combined_data = {**place_details, **place_data}
                combined_data["id"] = place_doc.id
                journal_places.append(combined_data)

    journal_data["journalPlaces"] = journal_places
    return _sanitize_for_json(journal_data)


def update_journal_place(journal_id, journal_place_id, update_data):
    """
    Updates a specific place document in a journal's sub-collection.
    """
    db = firestore.client()
    journal_place_ref = (
        db.collection("travelJournals")
        .document(journal_id)
        .collection("journalPlaces")
        .document(journal_place_id)
    )

    # Add an 'updated_at' timestamp to the update data
    update_with_timestamp = {
        **update_data,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }

    try:
        journal_place_ref.update(update_with_timestamp)
        clear_journal_cache(journal_id)
        return {"status": "success"}
    except Exception as e:
        print(f"Error updating document: {e}")
        return {"status": "error", "message": str(e)}


def delete_journal_place(journal_id, journal_place_id):
    """
    Deletes a specific place document from a journal's sub-collection.
    """
    db = firestore.client()
    journal_place_ref = (
        db.collection("travelJournals")
        .document(journal_id)
        .collection("journalPlaces")
        .document(journal_place_id)
    )

    try:
        journal_place_ref.delete()
        clear_journal_cache(journal_id)
        return {"status": "success"}
    except Exception as e:
        print(f"Error deleting document: {e}")
        return {"status": "error", "message": str(e)}


def create_journal(
    user_id,
    title,
    description,
    privacy,
    cover_image_url,
    start_date,
    days,
    places,
    journal_entries,
):
    """
    Creates a new journal document in Firestore.
    """
    db = firestore.client()
    try:
        journal_ref = db.collection("travelJournals").document()
        journal_ref.set(
            {
                "user_id": user_id,
                "title": title,
                "description": description,
                "privacy": privacy,
                "cover_image_url": cover_image_url,
                "start_date": start_date,
                "days": days,
                "places": places or [],
                "journal_entries": journal_entries or [],
                "created_at": firestore.SERVER_TIMESTAMP,
                "status": "draft",  # Set default status to draft
            }
        )
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
        journals_query = db.collection("travelJournals").where(
            "user_id", "==", user_id
        ).stream()
        journals = []
        for journal in journals_query:
            journal_data = journal.to_dict()
            journal_data["id"] = journal.id
            journals.append(journal_data)
        return journals
    except Exception as e:
        print(f"Error getting user journals: {e}")
        return []


def get_all_user_profiles():
    """
    Fetches all user profiles from the Firestore 'users' collection.
    """
    db = firestore.client()
    try:
        users_query = db.collection("users").stream()
        users = {}
        for user in users_query:
            user_data = user.to_dict()
            users[user.id] = user_data
        return users
    except Exception as e:
        print(f"Error getting all user profiles: {e}")
        return {}


@cached(user_profile_cache, key=lambda user_ids: keys.hashkey(tuple(sorted(user_ids))))
def get_user_profiles_by_ids(user_ids):
    """
    Fetches specific user profiles from the Firestore 'users' collection by their IDs.
    Caches the results. The user_ids list is converted to a sorted tuple to be hashable.
    """
    db = firestore.client()
    users = {}
    # Ensure user_ids is a list of unique strings
    unique_user_ids = list(set(filter(None, user_ids)))

    if not unique_user_ids:
        return users

    # Firestore 'in' queries are limited to 30 items per query.
    # We need to batch the requests if there are more than 30 user_ids.
    for i in range(0, len(unique_user_ids), 30):
        batch_ids = unique_user_ids[i:i + 30]
        try:
            users_query = db.collection("users").where("__name__", "in", batch_ids).stream()
            for user in users_query:
                user_data = user.to_dict()
                users[user.id] = user_data
        except Exception as e:
            print(f"Error getting user profiles by IDs: {e}")
    return users


def get_all_journals():
    """
    Fetches all public journals from all users.
    """
    db = firestore.client()
    try:
        journals_query = db.collection("travelJournals").where("status", "==", "public").stream()
        journals = []
        for journal in journals_query:
            journal_data = journal.to_dict()
            journal_data["id"] = journal.id
            journals.append(journal_data)
        return journals
    except Exception as e:
        print(f"Error getting all journals: {e}")
        return []


def get_journal(journal_id):
    """
    Fetches a single journal by its ID.
    """
    db = firestore.client()
    try:
        journal_ref = db.collection("travelJournals").document(journal_id)
        journal = journal_ref.get()
        if journal.exists:
            journal_data = journal.to_dict()
            journal_data["id"] = journal.id
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
        journal_ref = db.collection("travelJournals").document(journal_id)
        journal_ref.update(update_data)
        clear_journal_cache(journal_id)
        return True
    except Exception as e:
        print(f"Error updating journal: {e}")
        return False


def add_place(journal_id, place_data):
    """
    Adds a place to a journal, using auto-generated IDs for the 'places'
    collection and preventing duplicates.
    """
    db = firestore.client()
    journal_ref = db.collection("travelJournals").document(journal_id)
    place_name = place_data.get("name")
    place_address = place_data.get("address")

    if not all([place_name, place_address]):
        print("Error: Place name and address are required.")
        return None

    try:
        places_collection = db.collection("places")
        # Query for an existing place to avoid duplicates
        existing_places = list(
            places_collection.where("name", "==", place_name)
            .where("address", "==", place_address)
            .limit(1)
            .stream()
        )

        if existing_places:
            place_ref = existing_places[0].reference
        else:
            # If no existing place is found, create a new one
            new_place_data = {"name": place_name, "address": place_address}
            _, place_ref = db.collection("places").add(new_place_data)

        # Add the place reference to the journal's subcollection
        new_journal_place_ref = journal_ref.collection("journalPlaces").document()
        new_journal_place_ref.set(
            {
                "place_ref": place_ref,
                "date": place_data.get("date"),
                "notes": place_data.get("notes"),
                "created_at": firestore.SERVER_TIMESTAMP,
            }
        )
        clear_journal_cache(journal_id)
        return new_journal_place_ref.id

    except Exception as e:
        print(f"Error adding place with auto-ID: {e}")
        return None


def get_currency_data():
    """
    Returns a list of currencies for the autocomplete input.
    """
    return [
        "🇺🇸 USD",
        "🇪🇺 EUR",
        "🇯🇵 JPY",
        "🇬🇧 GBP",
        "🇦🇺 AUD",
        "🇨🇦 CAD",
        "🇨🇭 CHF",
        "🇨🇳 CNY",
        "🇸🇪 SEK",
        "🇳🇿 NZD",
        "🇲🇾 MYR",
    ]


def upload_cover_image(journal_id, contents, filename):
    """
    Uploads a cover image to Firebase Storage and updates the journal.
    This version uses an in-memory file for more robust uploading.
    """
    try:
        bucket_name = os.getenv("STORAGE_BUCKET")
        if not bucket_name:
            raise ValueError("STORAGE_BUCKET environment variable is not set.")

        content_type, content_string = contents.split(",")
        decoded_bytes = base64.b64decode(content_string)
        in_mem_file = io.BytesIO(decoded_bytes)

        bucket = storage.bucket(bucket_name)
        file_extension = filename.split(".")[-1] if "." in filename else "jpg"
        destination_blob_name = (
            f"journal_covers/{journal_id}/{uuid.uuid4()}.{file_extension}"
        )

        blob = bucket.blob(destination_blob_name)
        in_mem_file.seek(0)
        blob.upload_from_file(in_mem_file, content_type=content_type)
        blob.make_public()

        public_url = blob.public_url
        update_journal(journal_id, {"cover_image_url": public_url})

        return public_url
    except Exception as e:
        print(f"FATAL: Error uploading cover image: {e}")
        return None


def delete_journal(journal_id):
    """
    Deletes a journal and its sub-collections from Firestore.
    """
    db = firestore.client()
    journal_ref = db.collection("travelJournals").document(journal_id)

    try:
        # Recursively delete sub-collections
        for collection_ref in journal_ref.collections():
            for doc in collection_ref.stream():
                doc.reference.delete()

        # Delete the journal document itself
        journal_ref.delete()
        return True
    except Exception as e:
        print(f"Error deleting journal: {e}")
        return False


def delete_places_outside_date_range(journal_id, start_date_str, end_date_str):
    """
    Deletes places from a journal that are outside the given date range.
    """
    db = firestore.client()
    journal_ref = db.collection("travelJournals").document(journal_id)
    places_ref = journal_ref.collection("journalPlaces")

    try:
        start_date = datetime.fromisoformat(start_date_str.split('T')[0])
        end_date = datetime.fromisoformat(end_date_str.split('T')[0])

        places_snapshot = places_ref.stream()
        for place in places_snapshot:
            place_data = place.to_dict()
            place_date_str = place_data.get("date")
            if place_date_str:
                place_date = datetime.fromisoformat(place_date_str.split('T')[0])
                if not (start_date <= place_date <= end_date):
                    place.reference.delete()
        
        clear_journal_cache(journal_id)
        return True
    except Exception as e:
        print(f"Error deleting places outside date range: {e}")
        return False


def delete_place(journal_id, place_id):
    """
    Deletes a specific place from a journal's sub-collection.
    """
    db = firestore.client()
    try:
        place_ref = (
            db.collection("travelJournals")
            .document(journal_id)
            .collection("journalPlaces")
            .document(place_id)
        )
        place_ref.delete()
        clear_journal_cache(journal_id)
        return True
    except Exception as e:
        print(f"Error deleting place: {e}")
        return False


def delete_cover_image(journal_id):
    """
    Deletes a cover image from Firebase Storage and updates the journal.
    """
    try:
        bucket_name = os.getenv("STORAGE_BUCKET")
        if not bucket_name:
            raise ValueError("STORAGE_BUCKET environment variable is not set.")

        journal_data = get_journal(journal_id)
        image_url = journal_data.get("cover_image_url")

        if image_url:
            match = re.search(
                r"storage\.googleapis\.com/[^/]+/(.*)", image_url
            )
            if match:
                blob_name = match.group(1)
                bucket = storage.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                if blob.exists():
                    blob.delete()

        update_journal(journal_id, {"cover_image_url": None})
        return True
    except Exception as e:
        print(f"FATAL: Error deleting cover image: {e}")
        return False
