# Imports 
import os
import json
import hashlib
import base64
import time
import streamlit as st
from chat import Chat
from retriever import RetrieverClient 

# Session State Initializations
if 'folder_path' not in st.session_state:
    st.session_state['folder_path'] = None
if 'indexing_done' not in st.session_state:
    st.session_state['indexing_done'] = False
if 'main_mode' not in st.session_state:
    st.session_state['main_mode'] = 'Chat'
if 'chat_mode' not in st.session_state:
    st.session_state['chat_mode'] = 'offline'
if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []
if 'search_messages' not in st.session_state:
    st.session_state['search_messages'] = []
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'change_folder_mode' not in st.session_state:
    st.session_state['change_folder_mode'] = False
if 'retriever' not in st.session_state:
    st.session_state['retriever'] = None
if 'chat' not in st.session_state:
    st.session_state['chat'] = None

CREDENTIALS_FILE = "user_credentials.json"

# Password Hash Function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Parse Json File to load credentials
def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

# Save Provided credentials back into the Json file
def save_credentials(credentials):
    with open(CREDENTIALS_FILE, 'w') as file:
        json.dump(credentials, file)

# Login Function
def login(username, password):
    credentials = load_credentials()
    hashed_password = hash_password(password)
    if username in credentials and credentials[username]['password'] == hashed_password:
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.session_state['folder_path'] = credentials[username]['folder_path']
        initialize_clients(st.session_state['folder_path'])
        return True
    return False

# Signup Function
def signup(username, password, folder_path):
    credentials = load_credentials()
    if username not in credentials:
        hashed_password = hash_password(password)
        credentials[username] = {'password': hashed_password, 'folder_path': folder_path}
        save_credentials(credentials)
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.session_state['folder_path'] = folder_path
        initialize_clients(folder_path)
        return True
    return False

# Logout Function
def logout():
    st.session_state.clear()
    st.session_state['logged_in'] = False

# UI for Login/Signup
def login_signup_interface():
    st.title("LocalInsight - Document Search and Chat")
    st.write("Welcome to LocalInsight, your personal document assistant!")  
    login_tab, signup_tab = st.tabs(["Login", "Signup"])   
    with login_tab:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_button"):
            if login(username, password):
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
    with signup_tab:
        new_username = st.text_input("New Username", key="signup_username")
        new_password = st.text_input("New Password", type="password", key="signup_password")
        folder_path = st.text_input("Initial Folder Path", key="signup_folder_path")
        if st.button("Signup", key="signup_button"):
            if signup(new_username, new_password, folder_path):
                st.success("Signed up and logged in successfully!")
                st.session_state['indexing_done'] = False
                st.rerun()
            else:
                st.error("Username already exists.")

# Lets user change document directory
def set_folder_path():
    st.header("Change Folder Path")
    folder_path = st.text_input("Enter the folder path to index:", key="folder_path_input")
    if folder_path:
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            st.session_state['folder_path'] = folder_path
            update_folder_path(st.session_state['username'], folder_path)
            initialize_clients(folder_path)
            st.session_state['indexing_done'] = True
            st.session_state['change_folder_mode'] = False
            st.success("Folder path updated successfully!")
            st.rerun()
        else:
            st.error("Invalid folder path. Please enter a valid path.")
    if st.button("Back"):
        st.session_state['change_folder_mode'] = False
        st.rerun()

# Overwrite changed folder path content into the json file
def update_folder_path(username, folder_path):
    credentials = load_credentials()
    if username in credentials:
        credentials[username]['folder_path'] = folder_path
        save_credentials(credentials)

# Initialize Retriever & Chat Clients
def initialize_clients(folder_path):
    st.session_state['retriever'] = RetrieverClient(folder_path)
    st.session_state['chat'] = Chat()


def handle_chat():
    # # Display past chat messages
    # for message in st.session_state['chat_messages']:
    #     if message['role'] == 'user':
    #         with st.chat_message("user"):
    #             st.write(message['content'])
    #     else:
    #         with st.chat_message("assistant"):
    #             st.write(message['content'])

    # Input fields for user message, audio, and image
    user_message = st.chat_input("Type your message here:")
    user_audio = st.file_uploader("Or upload an audio file:", type=["wav", "mp3"], key="audio_uploader")
    # user_audio = None
    user_image = st.file_uploader("Or upload an image:", type=["png", "jpg", "jpeg"], key="image_uploader")

    # When a message or file is uploaded
    if user_message or user_audio or user_image:
        user_query = user_message if user_message else None

        user_audio_path = None
        user_image_path = None

        # Save uploaded image or audio to temporary path
        if user_image:
            user_image_path = f"temp_uploaded_image.{user_image.name.split('.')[-1]}"
            with open(user_image_path, "wb") as f:
                f.write(user_image.getbuffer())

        if user_audio:
            user_audio_path = f"temp_uploaded_audio.{user_audio.name.split('.')[-1]}"
            with open(user_audio_path, "wb") as f:
                f.write(user_audio.getbuffer())

        chat_client = st.session_state['chat']

        # Get response from assistant and append user message to chat history
        response = chat_client.get_assistant_response(
            user_text=user_query,
            user_image_path=user_image_path,
            user_audio_path=user_audio_path
        )

        # Extract assistant's response content
        assistant_response = response.message.content

        # Append user and assistant messages to chat history
        st.session_state['chat_messages'].append({"role": "user", "content": user_query or ""})
        st.session_state['chat_messages'].append({"role": "assistant", "content": assistant_response})

        # Display assistant's response
        with st.chat_message("assistant"):
            st.write(assistant_response)

        # Clean up temporary files if uploaded
        if user_image_path and os.path.exists(user_image_path):
            os.remove(user_image_path)
        if user_audio_path and os.path.exists(user_audio_path):
            os.remove(user_audio_path)

    # Button to view chat history
    if st.button("View Chat History"):
        st.write("### Chat History:")
        for message in st.session_state['chat_messages']:
            role = "User" if message['role'] == "user" else "Assistant"
            st.write(f"**{role}:** {message['content']}")


# File Open Function
def open_file(path):
    try:
        if not os.path.exists(path):
            st.error(f"File not found: {path}")
            return
        # Open File in different applications
        if os.name == 'nt':  # For Windows
            os.startfile(path)
        elif os.name == 'posix':  # For macOS and Linux
            os.system(f'open "{path}"' if 'darwin' in os.uname().sysname.lower() else f'xdg-open "{path}"')
        else:
            st.warning("Your operating system may not support this operation.")
    except Exception as e:
        st.error(f"Failed to open the file: {e}")

# Search Interaction Handler Function
import os
import streamlit as st

def handle_search():
    # Search input fields
    user_query = st.text_input("Type your search query here:", key="search_input")
    uploaded_image = st.file_uploader("Upload an image:", type=["png", "jpg", "jpeg"], key="image_uploader")
    search_option = st.radio("Choose a search type:", ("Any","Text", "Media"))
    limit = st.slider("Number of Results", min_value=1, max_value=20, value=5, key="limit_slider")

    # Perform search when the search button is clicked
    if st.button("Search", key="search_send"):
        with st.spinner("Searching..."):
            if user_query or uploaded_image:
                image_path = None
                
                if uploaded_image:
                    image_path = f"temp_uploaded_image.{uploaded_image.name.split('.')[-1]}"
                    with open(image_path, "wb") as f:
                        f.write(uploaded_image.getbuffer())
                        
                if search_option == "Any": search_for = "all"
                elif search_option == "Text": search_for = "text"
                elif search_option == "Media": search_for = "image"

                search_results = st.session_state['retriever'].search(
                    text=user_query, 
                    image_path=image_path, 
                    search_for=search_for, 
                    limit=limit
                )

                st.session_state['search_results'] = search_results

                # Clean up temporary image
                if uploaded_image and os.path.exists(image_path):
                    os.remove(image_path)

    # Display search results
    if 'search_results' in st.session_state:
        search_results = st.session_state['search_results']
        st.subheader("Search Results:")
        file_paths = []
        image_paths = []
        video_paths = []

        # Organize results
        for result in search_results['text']:
            if result['path'] not in file_paths:
                file_paths.append(result['path'])
        for result in search_results['image']:
            if result['file_type'] == 'image' and result['path'] not in image_paths:
                image_paths.append(result['path'])
            if result['file_type'] == 'video_frame' and result['path'] not in video_paths:
                video_paths.append(result['path'])

        # Display text files
        for path in file_paths:
            st.write(f"**Found:** {os.path.basename(path)}")
            if st.button(f"Open: {os.path.basename(path)}", key=f"open_{path}"):
                open_file(path)

        # Display images
        for image_path in image_paths:
            st.image(image_path, caption=os.path.basename(image_path), use_column_width=True)

        # Display videos
        for video_path in video_paths:
            st.video(video_path)

def front_page():
    st.markdown("<h1 style='text-align: center;'>Welcome to LocalInsight!</h1>", unsafe_allow_html=True)

    # Path for the local video
    local_video_path = "LOCALINSIGHT (2).mp4"
    
    # Check if the video file exists
    if os.path.exists(local_video_path):
        with open(local_video_path, "rb") as file:
            video_bytes = file.read()
        
        # Video styling (fixed size, centered, and no overflow)
        video_html = f"""
        <style>
        .video-container {{
            width: 70%;
            height: 400px;  /* Fixed height for the video */
            margin: 20px auto;
            padding: 10px;
            background-color: #000;
            border-radius: 10px;
            box-shadow: 0px 4px 20px rgba(0, 0, 0, 0.3);
            text-align: center;
        }}
        .video-container:hover {{
            transform: scale(1.05);
            box-shadow: 0px 8px 40px rgba(0, 0, 0, 0.6);
        }}
        
        video {{
            width: 100%;
            height: 100%;  /* Ensure the video takes up all available space */
            object-fit: cover;
            border-radius: 10px;
        }}

        .stButton > button {{
            display: block;
            margin: 20px auto;
            padding: 12px 30px;
            border-radius: 10px;
            border: none;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }}

        .stButton > button:hover {{
            background-color: #FFA500;
        }}
        </style>

        <div class="video-container">
            <video autoplay muted loop playsinline>
                <source src="data:video/mp4;base64,{base64.b64encode(video_bytes).decode()}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
        """
        
        # Display the video HTML
        st.markdown(video_html, unsafe_allow_html=True)
    else:
        st.error("Video file not found. Please check the path.")
    
    # Handle session timing
    if 'start_time' not in st.session_state:
        st.session_state['start_time'] = time.time()
    elapsed_time = time.time() - st.session_state['start_time']
    
    if elapsed_time > 5:  
        st.session_state['viewed_front_page'] = True
        st.rerun()

    # Button placed directly below the video (Centered)
    col1, col2, col3 = st.columns([1, 2, 1])  # Center the button
    with col2:
        if st.button("Proceed to Login/Signup"):
            st.session_state['viewed_front_page'] = True
            st.rerun()


# UI for main page
def main_interface():
    st.sidebar.title("Options")
    st.sidebar.button("Change Folder Path", on_click=lambda: st.session_state.update({'change_folder_mode': True}))
    st.sidebar.button("Logout", on_click=logout)
    st.session_state['main_mode'] = st.sidebar.radio("Select Mode", options=["Search", "Chat"])
    st.title("LocalInsight")
    st.write(f"Current Folder: {st.session_state['folder_path']}")
    if st.session_state['main_mode'] == 'Search':
        st.header("Search Mode")
        handle_search()
    else:
        st.header("Chat Mode")
        handle_chat()

def main():
    st.set_page_config(page_title="LocalInsight", page_icon="🔍", layout="wide")
    if 'viewed_front_page' not in st.session_state:
        st.session_state['viewed_front_page'] = False
    if not st.session_state['viewed_front_page']:
        front_page()
    elif not st.session_state['logged_in']:
        login_signup_interface()
    elif st.session_state['change_folder_mode']:
        set_folder_path()
    else:
        main_interface()

# Running the app
if __name__ == "__main__":
    main()
