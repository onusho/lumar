# /flask_app/app/core/utils.py
from flask import current_app

def allowed_file(filename, file_type='image'):
    if not filename: return False # Handle None or empty filename
    if file_type == 'image':
        extensions = current_app.config['ALLOWED_EXTENSIONS_IMAGE']
    elif file_type == 'audio':
        extensions = current_app.config['ALLOWED_EXTENSIONS_AUDIO']
    else:
        return False # Unknown file_type for this checker
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions