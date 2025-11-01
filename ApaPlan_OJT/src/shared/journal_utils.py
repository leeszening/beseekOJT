import os
from firebase_admin import firestore, storage
from google.cloud.firestore_v1.document import DocumentReference
from datetime import datetime
import base64
import uuid
import re
import io
import logging
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


def get_journal_with_details(journal_id):
    """
    Fetches a journal by its ID and sanitizes it for client-side display.
    This is a wrapper around get_journal to provide a sanitized version
    of the journal data.
    """
    journal_data = get_journal(journal_id)
    if not journal_data:
        return None

    journal_data["journalPlaces"] = []  # Maintain original behavior
    return _sanitize_for_json(journal_data)


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


@firestore.transactional
def _create_place_if_not_exists(transaction, place_ref, place_data):
    """
    Checks if a place document exists and creates it if it doesn't, within a transaction.
    """
    place_snapshot = place_ref.get(transaction=transaction)
    if not place_snapshot.exists:
        # Extract general place information
        location = place_data.get("location", {})
        general_place_data = {
            "name": place_data.get("name"),
            "address": place_data.get("address"),
            "coordinates": firestore.GeoPoint(
                location.get("lat", 0), location.get("lng", 0)
            ),
            "google_place_id": place_data.get("place_id"),
            "website": place_data.get("website"),
            "rating": place_data.get("rating"),
            "user_ratings_total": place_data.get("user_ratings_total"),
            "utc_offset_minutes": place_data.get("utc_offset_minutes"),
            "price_level": place_data.get("price_level"),
            "types": place_data.get("types"),
            "created_at": firestore.SERVER_TIMESTAMP,
        }
        transaction.set(place_ref, general_place_data)


def save_places_to_journal(journal_id, places_data):
    """
    Saves multiple places to a journal using batched writes for improved performance.
    """
    db = firestore.client()
    try:
        journal_places_ref = (
            db.collection("travelJournals")
            .document(journal_id)
            .collection("journalPlaces")
        )
        batch = db.batch()

        for place_data in places_data:
            place_id = place_data.get("place_id")
            if not place_id:
                continue

            # Create a reference to the place document
            place_ref = db.collection("places").document(place_id)

            # Use a transaction to create the place if it doesn't exist
            transaction = db.transaction()
            _create_place_if_not_exists(transaction, place_ref, place_data)

            # Determine the order for the new place
            query = journal_places_ref.where("date", "==", place_data["date"])
            places_on_date = list(query.stream())
            order = len(places_on_date) + 1

            # Create a new document reference for the journal place
            new_journal_place_ref = journal_places_ref.document()

            # Prepare the document data
            journal_place_doc = {
                "placeRef": place_ref,
                "order": order,
                **place_data,
            }
            batch.set(new_journal_place_ref, journal_place_doc)

        # Commit the batch
        batch.commit()
        return True
    except Exception as e:
        print(f"Error saving places to journal: {e}")
        return False


def fetch_all_journal_places(journal_id):
    """
    Fetches all places for a journal, ordered by date and then by the 'order' field.
    This version is optimized to avoid N+1 queries by batching place detail fetches.
    """
    db = firestore.client()
    try:
        journal_places_ref = (
            db.collection("travelJournals")
            .document(journal_id)
            .collection("journalPlaces")
        )
        query = journal_places_ref.order_by("date").order_by("order").stream()

        journal_places_data = []
        place_refs = []
        for doc in query:
            data = doc.to_dict()
            data['journal_place_doc_id'] = doc.id
            journal_places_data.append(data)
            if 'placeRef' in data and isinstance(data['placeRef'], DocumentReference):
                place_refs.append(data['placeRef'])

        place_details = {}
        if place_refs:
            # Use get_all for efficient batch fetching
            place_docs = db.get_all(place_refs)
            for doc in place_docs:
                if doc.exists:
                    place_details[doc.reference.path] = doc.to_dict()

        places_with_details = []
        for jp_data in journal_places_data:
            place_ref = jp_data.get("placeRef")
            if place_ref and place_ref.path in place_details:
                combined_data = {**place_details[place_ref.path], **jp_data}
                places_with_details.append(combined_data)
            else:
                # Handle cases where placeRef is missing or the document doesn't exist
                print(f"Skipping journal place with missing or invalid placeRef: {jp_data.get('journal_place_doc_id')}")

        return places_with_details
    except Exception as e:
        print(f"Error fetching all journal places for journal {journal_id}: {e}")
        return []


def fetch_journal_places(journal_id, date):
    """
    Fetches all places for a specific day in a journal, ordered by the 'order' field.
    It also fetches the details of each place from the 'places' collection.
    """
    db = firestore.client()
    try:
        journal_places_ref = (
            db.collection("travelJournals")
            .document(journal_id)
            .collection("journalPlaces")
        )
        query = (
            journal_places_ref.where("date", "==", date).order_by("order").stream()
        )

        places_with_details = []
        for journal_place_doc in query:
            journal_place_data = journal_place_doc.to_dict()
            place_ref = journal_place_data.get("placeRef")

            if place_ref and isinstance(place_ref, DocumentReference):
                place_doc = place_ref.get()
                if place_doc.exists:
                    place_data = place_doc.to_dict()
                    # Combine journal place data (like order, notes) with place details
                    combined_data = {**place_data, **journal_place_data}
                    combined_data['journal_place_doc_id'] = journal_place_doc.id
                    places_with_details.append(combined_data)
            else:
                # Handle cases where placeRef is missing or not a DocumentReference
                # You might want to log this or handle it as an error
                print(f"Skipping journal place with missing or invalid placeRef: {journal_place_doc.id}")

        return places_with_details
    except Exception as e:
        print(f"Error fetching journal places for date {date}: {e}")
        return []
