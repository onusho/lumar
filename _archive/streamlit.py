# import os
# import json
# import hashlib
# import streamlit as st

# if 'folder_path' not in st.session_state:
#     st.session_state['folder_path'] = None
# if 'indexing_done' not in st.session_state:
#     st.session_state['indexing_done'] = False
# if 'mode' not in st.session_state:
#     st.session_state['mode'] = 'Chat'
# if 'chat_messages' not in st.session_state:
#     st.session_state['chat_messages'] = []
# if 'search_messages' not in st.session_state:
#     st.session_state['search_messages'] = []
# if 'logged_in' not in st.session_state:
#     st.session_state['logged_in'] = False
# if 'change_folder_mode' not in st.session_state:
#     st.session_state['change_folder_mode'] = False

# CREDENTIALS_FILE = "user_credentials.json"

# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# def load_credentials():
#     if os.path.exists(CREDENTIALS_FILE):
#         with open(CREDENTIALS_FILE, 'r') as file:
#             try:
#                 return json.load(file)
#             except json.JSONDecodeError:
#                 return {}
#     return {}

# def save_credentials(credentials):
#     with open(CREDENTIALS_FILE, 'w') as file:
#         json.dump(credentials, file)

# def login(username, password):
#     credentials = load_credentials()
#     hashed_password = hash_password(password)
#     if username in credentials and credentials[username]['password'] == hashed_password:
#         st.session_state['logged_in'] = True
#         st.session_state['username'] = username
#         st.session_state['folder_path'] = credentials[username]['folder_path']
#         return True
#     return False

# def signup(username, password, folder_path):
#     credentials = load_credentials()
#     if username not in credentials:
#         hashed_password = hash_password(password)
#         credentials[username] = {'password': hashed_password, 'folder_path': folder_path}
#         save_credentials(credentials)
#         st.session_state['logged_in'] = True
#         st.session_state['username'] = username
#         st.session_state['folder_path'] = folder_path
#         return True
#     return False

# def logout():
#     st.session_state.clear()
#     st.session_state['logged_in'] = False
#     st.session_state['folder_path'] = None
#     st.session_state['indexing_done'] = False
#     st.session_state['mode'] = 'Chat'
#     st.session_state['chat_messages'] = []
#     st.session_state['search_messages'] = []

# def login_signup_interface():
#     st.title("Login / Signup")
#     login_tab, signup_tab = st.tabs(["Login", "Signup"])
#     with login_tab:
#         username = st.text_input("Username", key="login_username")
#         password = st.text_input("Password", type="password", key="login_password")
#         if st.button("Login"):
#             if login(username, password):
#                 st.success("Logged in successfully!")
#                 st.rerun()
#             else:
#                 st.error("Invalid username or password.")
#     with signup_tab:
#         username = st.text_input("New Username", key="signup_username")
#         password = st.text_input("New Password", type="password", key="signup_password")
#         folder_path = st.text_input("Initial Folder Path", key="signup_folder_path")
#         if st.button("Signup"):
#             if signup(username, password, folder_path):
#                 st.success("Signed up and logged in successfully!")
#                 st.session_state['indexing_done'] = False
#                 st.rerun()
#             else:
#                 st.error("Username already exists.")

# def set_folder_path():
#     st.header("Change Folder Path")
#     with st.container():
#         folder_path = st.text_input("Enter the folder path to index:", key="folder_path_input")
#         if folder_path:
#             if os.path.exists(folder_path) and os.path.isdir(folder_path):
#                 st.session_state['folder_path'] = folder_path
#                 st.write(f"Selected folder: {folder_path}")
#                 files = os.listdir(folder_path)
#                 st.write("Folder contents:", files)
#                 if st.button("Index Folder"):
#                     update_folder_path(st.session_state['username'], folder_path)
#                     generate_embeddings(folder_path)
#                     st.session_state['indexing_done'] = True
#                     st.session_state['change_folder_mode'] = False
#                     st.rerun()
#             else:
#                 st.error("Invalid folder path. Please enter a valid path.")
#         if st.button("Back"):
#             st.session_state['change_folder_mode'] = False
#             st.rerun()

# def update_folder_path(username, folder_path):
#     credentials = load_credentials()
#     if username in credentials:
#         credentials[username]['folder_path'] = folder_path
#         save_credentials(credentials)

# def generate_embeddings(folder_path):
#     st.write(f"Generating embeddings for files in {folder_path}...")

# def add_file():
#     uploaded_file = st.file_uploader("Choose a file", key="file_uploader_add")
#     if uploaded_file is not None:
#         st.write(f"Processing file: {uploaded_file.name}")

# def handle_chat():
#     user_message = st.text_input("Type your message here:", key="chat_input")
#     if st.button("Send", key="chat_send"):
#         if user_message:
#             st.session_state['chat_messages'].append({"role": "user", "content": user_message})
#             st.session_state['chat_messages'].append({"role": "bot", "content": "This is a chat mode response."})
#             st.rerun()

# def display_chat():
#     chat_container = st.container()
#     with chat_container:
#         messages = st.session_state['chat_messages'] if st.session_state['mode'] == 'Chat' else st.session_state['search_messages']
#         for message in messages:
#             if message['role'] == 'user':
#                 st.write(f"You: {message['content']}")
#             else:
#                 st.write(f"Bot: {message['content']}")

# def handle_search():
#     user_query = st.text_input("Type your search query here:", key="search_input")
#     if st.button("Search", key="search_send"):
#         if user_query:
#             st.session_state['search_messages'].append({"role": "user", "content": user_query})
#             st.session_state['search_messages'].append({"role": "bot", "content": "This is a search mode response."})
#             st.rerun()

# def main_interface():
#     st.sidebar.title("Options")
#     st.sidebar.button("Change Folder Path", on_click=lambda: st.session_state.update({'change_folder_mode': True}))
#     st.sidebar.button("Logout", on_click=logout)
#     st.session_state['mode'] = st.sidebar.radio("Select Mode", options=["Search", "Chat"])
#     if st.session_state['mode'] == 'Search':
#         st.header("Search Mode")
#         display_chat()
#         handle_search()
#     else:
#         st.header("Chat Mode")
#         display_chat()
#         handle_chat()
#     if st.sidebar.button("Online Mode"):
#         st.write("Triggering video inferencing function...")
#         video_inferencing()

# def video_inferencing():
#     st.write("Video Inferencing trigger")

# if not st.session_state['logged_in']:
#     login_signup_interface()
# elif st.session_state['change_folder_mode']:
#     set_folder_path()
# else:
#     main_interface()




