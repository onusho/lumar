# /flask_app/app/core/credentials.py
import os
import json
import hashlib
from flask import current_app, flash

def get_credentials_file_path():
    return current_app.config['CREDENTIALS_FILE']

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_credentials():
    creds_file = get_credentials_file_path()
    if os.path.exists(creds_file):
        try:
            with open(creds_file, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            flash("Error reading credentials file. It might be corrupted.", "danger")
            current_app.logger.error(f"JSONDecodeError in credentials file: {creds_file}")
            return {}
        except Exception as e:
            flash(f"Could not load credentials: {e}", "danger")
            current_app.logger.error(f"Error loading credentials file {creds_file}: {e}", exc_info=True)
            return {}
    return {}

def save_credentials(credentials):
    creds_file = get_credentials_file_path()
    try:
        # Ensure instance directory exists before trying to save
        os.makedirs(os.path.dirname(creds_file), exist_ok=True)
        with open(creds_file, 'w') as file:
            json.dump(credentials, file, indent=4)
        return True
    except Exception as e:
        flash(f"Could not save credentials: {e}", "danger")
        current_app.logger.error(f"Error saving credentials to {creds_file}: {e}", exc_info=True)
        return False