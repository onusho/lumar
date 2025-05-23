# /flask_app/app/main/routes.py
from flask import (render_template, redirect, url_for, flash, request, session,
                   current_app, send_from_directory, abort, jsonify)
from werkzeug.utils import secure_filename
import os
import time
import base64
from . import bp
from ..core.clients import get_retriever_client, get_chat_client, clear_user_clients, ensure_clients_initialized
from ..core.credentials import load_credentials, save_credentials
from ..core.utils import allowed_file
from functools import wraps

# === Decorators ===
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login_signup_page'))
        return f(*args, **kwargs)
    return decorated_function

# === Routes ===
@bp.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('.main_app_page'))
    if 'viewed_front_page_timestamp' not in session:
        session['viewed_front_page_timestamp'] = time.time()
        return render_template('main/welcome.html', auto_proceed=True)
    elapsed_time = time.time() - session.get('viewed_front_page_timestamp', time.time())
    if not session.get('viewed_front_page') and elapsed_time > 7:
         session['viewed_front_page'] = True
         return redirect(url_for('auth.login_signup_page'))
    if session.get('viewed_front_page'):
         return redirect(url_for('auth.login_signup_page'))
    return render_template('main/welcome.html', auto_proceed=False)


@bp.route('/proceed_to_login')
def proceed_to_login():
    session['viewed_front_page'] = True
    return redirect(url_for('auth.login_signup_page'))

@bp.route('/app', methods=['GET'])
@login_required
@ensure_clients_initialized()
def main_app_page():
    active_tab = session.get('active_tab', 'search')
    return render_template('main/app_dashboard.html',
                           active_tab=active_tab,
                           chat_messages=session.get('chat_messages', []),
                           search_results_data=session.get('search_results'))

@bp.route('/app/set_active_tab/<tab_name>', methods=['POST'])
@login_required
def set_active_tab(tab_name):
    if tab_name in ['search', 'chat']:
        session['active_tab'] = tab_name
        return jsonify({"status": "success", "active_tab": tab_name}), 200
    return jsonify({"status": "error", "message": "Invalid tab"}), 400

@bp.route('/change_folder', methods=['GET', 'POST'])
@login_required
def change_folder_page():
    if request.method == 'POST':
        new_folder_path = request.form.get('folder_path')
        if not new_folder_path:
            flash("Folder path cannot be empty.", "warning")
        elif os.path.isdir(new_folder_path):
            credentials = load_credentials()
            username = session['username']
            if username in credentials:
                credentials[username]['folder_path'] = new_folder_path
                if save_credentials(credentials):
                    session['folder_path'] = new_folder_path
                    clear_user_clients(username) 
                    flash("Folder path updated. Document engine will re-initialize on next use.", "success")
                    return redirect(url_for('.main_app_page'))
            else:
                flash("Error: User not found in credentials.", "danger")
        else:
            flash(f"Invalid folder path: '{new_folder_path}'.", "danger")
    return render_template('main/change_folder.html')


@bp.route('/app/search', methods=['POST'])
@login_required
@ensure_clients_initialized()
def handle_search_action():
    session['active_tab'] = 'search'
    retriever = get_retriever_client()
    if not retriever: # Should be caught by decorator, but as a safeguard
        flash("Search client not available. Please check folder settings.", "danger")
        return redirect(url_for('.main_app_page'))

    user_query_text = request.form.get('query') if request.form.get('query') else None
    image_file_from_form = request.files.get('search_image_file')
    
    form_search_option = request.form.get('search_option', 'Any')
    if form_search_option == "Any": search_for_param = "all"
    elif form_search_option == "Text": search_for_param = "text"
    elif form_search_option == "Media": search_for_param = "image"
    else: search_for_param = "all"

    limit_param = int(request.form.get('limit', 5))
    temp_image_path_for_search = None

    if image_file_from_form and image_file_from_form.filename != '' and allowed_file(image_file_from_form.filename, file_type='image'):
        filename = secure_filename(f"search_{session['username']}_{int(time.time())}_{image_file_from_form.filename}")
        temp_image_path_for_search = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        try: image_file_from_form.save(temp_image_path_for_search)
        except Exception as e: flash(f"Error saving uploaded image: {e}", "danger"); temp_image_path_for_search = None
    elif image_file_from_form and image_file_from_form.filename != '':
        flash(f"Uploaded image file type not allowed: {image_file_from_form.filename}", "warning")

    if not user_query_text and not temp_image_path_for_search:
        flash("Please provide a text query or an image for search.", "warning")
        session['search_results'] = None
        return redirect(url_for('.main_app_page'))

    current_app.logger.info(f"Search by {session['username']}: query='{user_query_text}', image='{temp_image_path_for_search}', option='{search_for_param}'")
    try:
        search_results_raw = retriever.search(
            text=user_query_text, image_path=temp_image_path_for_search,
            search_for=search_for_param, limit=limit_param
        )
        session['search_results'] = search_results_raw 
    except Exception as e:
        flash(f"An error occurred during search: {str(e)[:150]}", "danger")
        current_app.logger.error(f"Search error for {session['username']}: {e}", exc_info=True)
        session['search_results'] = None
    finally:
        if temp_image_path_for_search and os.path.exists(temp_image_path_for_search):
            try: os.remove(temp_image_path_for_search)
            except Exception as e_rem: current_app.logger.error(f"Error removing temp search image: {e_rem}")
    return redirect(url_for('.main_app_page'))


@bp.route('/app/chat', methods=['POST'])
@login_required
@ensure_clients_initialized()
def handle_chat_action():
    session['active_tab'] = 'chat'
    chat_service = get_chat_client()
    if not chat_service: # Should be caught by decorator, but as a safeguard
        flash("Chat client not available. Please check folder settings.", "danger")
        return redirect(url_for('.main_app_page'))


    user_message_text_from_form = request.form.get('user_message')
    user_query_for_chat = user_message_text_from_form if user_message_text_from_form else None 

    audio_file_from_form = request.files.get('chat_audio_file')
    image_file_from_form = request.files.get('chat_image_file')
    temp_audio_path_for_chat, temp_image_path_for_chat = None, None

    if audio_file_from_form and audio_file_from_form.filename != '' and allowed_file(audio_file_from_form.filename, file_type='audio'):
        filename = secure_filename(f"chat_audio_{session['username']}_{int(time.time())}_{audio_file_from_form.filename}")
        temp_audio_path_for_chat = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        try: audio_file_from_form.save(temp_audio_path_for_chat)
        except Exception as e: flash(f"Error saving audio: {e}", "danger"); temp_audio_path_for_chat = None
    elif audio_file_from_form and audio_file_from_form.filename != '':
         flash(f"Uploaded audio file type not allowed: {audio_file_from_form.filename}", "warning")

    if image_file_from_form and image_file_from_form.filename != '' and allowed_file(image_file_from_form.filename, file_type='image'):
        original_extension = image_file_from_form.filename.rsplit('.', 1)[-1] if '.' in image_file_from_form.filename else 'tmp'
        filename = secure_filename(f"chat_img_{session['username']}_{int(time.time())}.{original_extension}")
        temp_image_path_for_chat = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        try: image_file_from_form.save(temp_image_path_for_chat)
        except Exception as e: flash(f"Error saving image: {e}", "danger"); temp_image_path_for_chat = None
    elif image_file_from_form and image_file_from_form.filename != '':
        flash(f"Uploaded image file type not allowed: {image_file_from_form.filename}", "warning")
    
    if not user_query_for_chat and not temp_audio_path_for_chat and not temp_image_path_for_chat:
        flash("Please type a message or upload a file.", "warning")
        return redirect(url_for('.main_app_page'))

    display_user_query_in_history = user_query_for_chat or ""
    if temp_image_path_for_chat and image_file_from_form: # Check if temp_image_path_for_chat was successfully created
        display_user_query_in_history += f" [Image: {os.path.basename(image_file_from_form.filename)}]"
    if temp_audio_path_for_chat and audio_file_from_form: # Check if temp_audio_path_for_chat was successfully created
        display_user_query_in_history += f" [Audio: {os.path.basename(audio_file_from_form.filename)}]"
    
    current_chat_messages = session.get('chat_messages', [])
    current_chat_messages.append({"role": "user", "content": display_user_query_in_history.strip()})

    try:
        current_app.logger.info(f"Chat by {session['username']}: text='{user_query_for_chat}', image='{temp_image_path_for_chat}', audio='{temp_audio_path_for_chat}'")
        api_response = chat_service.get_assistant_response(
            user_text=user_query_for_chat,
            user_image_path=temp_image_path_for_chat, 
            user_audio_path=temp_audio_path_for_chat
        )
        
        assistant_reply_content = "Sorry, I could not generate a response at this time." # Default
        
        if api_response and isinstance(api_response, dict):
            if "message" in api_response and \
               isinstance(api_response["message"], dict) and \
               "content" in api_response["message"]:
                
                content_from_llm = api_response["message"]["content"]
                if content_from_llm is not None and str(content_from_llm).strip() != "":
                    assistant_reply_content = str(content_from_llm)
                else:
                    assistant_reply_content = "Assistant provided an empty response."
                    current_app.logger.warning(f"Chat for {session['username']} got empty/None content from LLM. Full response: {api_response}")
            elif "error" in api_response:
                error_from_llm = api_response["error"]
                assistant_reply_content = f"Chat service error: {error_from_llm}"
                current_app.logger.error(f"Ollama returned error for {session['username']}: {error_from_llm}. Full response: {api_response}")
            else:
                assistant_reply_content = "Received an unexpected response structure from the chat service."
                current_app.logger.error(f"Unexpected Ollama response structure for {session['username']}: {api_response}")
        elif api_response is None:
             assistant_reply_content = "Chat service returned no response (None)."
             current_app.logger.error(f"Ollama call returned None for {session['username']}.")
        
        current_chat_messages.append({"role": "assistant", "content": assistant_reply_content})
        session['chat_messages'] = current_chat_messages
    except AttributeError as ae: # Specifically catch if chat_service might be None (though decorator should prevent)
        current_app.logger.error(f"Chat service attribute error for {session['username']}: {ae}", exc_info=True)
        error_msg_for_user = "Chat service is not available. Please try again later."
        current_chat_messages.append({"role": "assistant", "content": error_msg_for_user})
        session['chat_messages'] = current_chat_messages
        flash(error_msg_for_user, "danger")
    except Exception as e:
        current_app.logger.error(f"Chat error for {session['username']}: {e}", exc_info=True)
        error_msg_for_user = f"Sorry, an unexpected error occurred in the chat service: {str(e)[:100]}..."
        current_chat_messages.append({"role": "assistant", "content": error_msg_for_user})
        session['chat_messages'] = current_chat_messages
        flash("An error occurred in the chat service.", "danger")
    finally:
        if temp_audio_path_for_chat and os.path.exists(temp_audio_path_for_chat):
            try: os.remove(temp_audio_path_for_chat)
            except Exception as e_rem: current_app.logger.error(f"Error removing temp chat audio: {e_rem}")
        if temp_image_path_for_chat and os.path.exists(temp_image_path_for_chat):
            try: os.remove(temp_image_path_for_chat)
            except Exception as e_rem: current_app.logger.error(f"Error removing temp chat image: {e_rem}")
                 
    return redirect(url_for('.main_app_page'))

@bp.route('/clear_chat_history')
@login_required
def clear_chat_history():
    session['chat_messages'] = []
    # Also clear the internal history of the cached Chat object if it exists
    chat_service = get_chat_client() 
    if chat_service and hasattr(chat_service, '_Chat__messages'): # Access private member carefully
        chat_service._Chat__messages.clear()
        current_app.logger.info(f"Cleared internal Ollama history for {session.get('username')}")
    
    flash("Chat history cleared.", "info")
    session['active_tab'] = 'chat'
    return redirect(url_for('.main_app_page'))

@bp.route('/media_item/<path:encoded_filepath>')
@login_required
def serve_media_file(encoded_filepath):
    try:
        decoded_filepath = base64.urlsafe_b64decode(encoded_filepath.encode('utf-8')).decode('utf-8')
    except Exception as e:
        current_app.logger.error(f"Error decoding media filepath '{encoded_filepath}': {e}")
        return abort(400, description="Invalid file path encoding.")
    user_folder_abs = os.path.abspath(session.get('folder_path', ''))
    requested_file_abs = os.path.abspath(decoded_filepath)
    is_safe_to_serve = False
    if user_folder_abs and requested_file_abs.startswith(user_folder_abs):
        is_safe_to_serve = True
    if not is_safe_to_serve:
        current_app.logger.warning(f"Access DENIED for media: '{decoded_filepath}' by {session['username']}.")
        return abort(403, description="Access to this file is forbidden.")
    if not os.path.exists(requested_file_abs) or not os.path.isfile(requested_file_abs):
        current_app.logger.error(f"Media file not found: {requested_file_abs}")
        return abort(404, description="File not found.")
    try:
        file_directory, file_name = os.path.split(requested_file_abs)
        return send_from_directory(file_directory, file_name, as_attachment=False)
    except Exception as e:
        current_app.logger.error(f"Error serving media file {requested_file_abs}: {e}", exc_info=True)
        return abort(500, description="Error serving file.")