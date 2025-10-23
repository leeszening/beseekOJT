import os
from dotenv import load_dotenv

# Load environment variables from .env file only in local development
if 'K_SERVICE' not in os.environ:
    load_dotenv()

# This module now only serves as a placeholder for the db client.
# The initialization is handled in the main application entry point (src/main.py)
# to ensure correct startup order.
db = None
