# /flask_app/app/core/clients.py
from flask import session, flash, current_app, request, redirect, url_for
import os
from functools import wraps
# These imports now point to where your files are (assuming app/core/)
from .retriever import RetrieverClient
from .chat import Chat

_user_clients_cache = {} # username: {'retriever': obj, 'chat': obj, 'folder_path': str}

def get_retriever_client():
    if 'username' not in session or 'folder_path' not in session:
        flash("User or folder path not found in session. Please log in again.", "warning")
        return None

    username = session['username']
    current_folder_path = session['folder_path']

    if not current_folder_path or not os.path.isdir(current_folder_path):
        flash(f"Folder path '{current_folder_path}' is not set or invalid. Please update it.", "danger")
        session.pop('clients_initialized', None)
        return None

    cached_client_info = _user_clients_cache.get(username)

    if not cached_client_info or cached_client_info['folder_path'] != current_folder_path:
        current_app.logger.info(f"Initializing RetrieverClient for {username} with folder: {current_folder_path}")
        try:
            # Your RetrieverClient __init__ calls DatabaseClient __init__
            # which calls __generate_collection and potentially __data_ingestion.
            # This can take time and might raise exceptions.
            retriever = RetrieverClient(current_folder_path)
            chat_instance = Chat() # Assuming your Chat class model default is okay.
            
            _user_clients_cache[username] = {
                'retriever': retriever,
                'chat': chat_instance,
                'folder_path': current_folder_path
            }
            session['clients_initialized'] = True
            current_app.logger.info(f"RetrieverClient and Chat initialized and cached for {username}")
        except Exception as e:
            current_app.logger.error(f"Error initializing clients for {username} (folder: {current_folder_path}): {e}", exc_info=True)
            flash(f"Error initializing document processing engine for folder '{os.path.basename(current_folder_path)}'. Check server logs. Details: {str(e)[:100]}...", "danger")
            session.pop('clients_initialized', None)
            if username in _user_clients_cache:
                del _user_clients_cache[username]
            return None
    
    return _user_clients_cache[username]['retriever']


def get_chat_client():
    if 'username' not in session:
        current_app.logger.warning("get_chat_client called without 'username' in session.")
        return None 

    username = session['username']
    cached_info = _user_clients_cache.get(username)
    
    if not cached_info or not session.get('clients_initialized') or cached_info.get('folder_path') != session.get('folder_path'):
        current_app.logger.info(f"Chat client for {username} requires re-initialization. Attempting...")
        if get_retriever_client() is None: 
            current_app.logger.warning(f"Failed to re-initialize clients for {username} when getting chat client.")
            return None
            
    final_cached_info = _user_clients_cache.get(username)
    if final_cached_info and 'chat' in final_cached_info:
        return final_cached_info['chat']
    else:
        current_app.logger.error(f"Chat client still not available for {username} after initialization attempt.")
        # flash("Chat service is currently unavailable. Please try again or check folder settings.", "danger") # Avoid too many flashes
        return None


def clear_user_clients(username):
    if username in _user_clients_cache:
        retriever_to_clear = _user_clients_cache[username].get('retriever')
        if retriever_to_clear and hasattr(retriever_to_clear, 'close_database_connection'):
            try:
                retriever_to_clear.close_database_connection()
            except Exception as e:
                current_app.logger.error(f"Error closing DB connection for {username} on client clear: {e}")

        # If Chat class had a close/cleanup method, call it here too.
        # chat_to_clear = _user_clients_cache[username].get('chat')
        # if chat_to_clear and hasattr(chat_to_clear, 'cleanup'):
        #     chat_to_clear.cleanup()

        del _user_clients_cache[username]
        current_app.logger.info(f"Cleared cached clients for user: {username}")
    session.pop('clients_initialized', None)


def ensure_clients_initialized():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            retriever_ok = get_retriever_client() is not None
            chat_ok = get_chat_client() is not None 

            if not retriever_ok or not chat_ok:
                if request.endpoint != 'main.change_folder_page':
                     if not any(m[0] == 'danger' for m in session.get('_flashes', [])): # Check category more reliably
                        flash("Document engine or chat service not ready. Please verify your folder path or check server logs.", "warning")
                     return redirect(url_for('main.change_folder_page'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator