# /flask_app/config.py
import os

class Config:
    # ESSENTIAL for Flask sessions, Flask-Session signing, and CSRF (if you add it)
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32) # Use a strong random key

    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app/static/uploads')
    ALLOWED_EXTENSIONS_IMAGE = {'png', 'jpg', 'jpeg'}
    ALLOWED_EXTENSIONS_AUDIO = {'wav', 'mp3'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    INSTANCE_FOLDER_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
    CREDENTIALS_FILE = os.path.join(INSTANCE_FOLDER_PATH, "user_credentials.json")
    WELCOME_VIDEO_FILENAME = "lumar_welcome.mp4"

    # Flask-Session Configuration (can also be set directly in app.config in __init__.py)
    SESSION_TYPE = "filesystem"  # Or "redis", "memcached", "mongodb", "sqlalchemy"
    SESSION_FILE_DIR = os.path.join(INSTANCE_FOLDER_PATH, 'flask_session') # Directory to store session files
    SESSION_PERMANENT = False # Make sessions non-permanent (expire on browser close)
    SESSION_USE_SIGNER = True # Sign the session cookie ID for security
    SESSION_KEY_PREFIX = 'session:' # Optional: prefix for session keys if using Redis/Memcached

    # Ensure necessary folders exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(INSTANCE_FOLDER_PATH, exist_ok=True)
    # Ensure SESSION_FILE_DIR exists if using filesystem type (Flask-Session might create it, but good to be sure)
    if SESSION_TYPE == "filesystem":
        os.makedirs(SESSION_FILE_DIR, exist_ok=True)