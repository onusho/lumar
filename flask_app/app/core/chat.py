import ollama
import speech_recognition as sr

class Chat:
    
    def __init__(self, model="gemma3:latest"):
        self.__messages = []
        self.__model = model
    
    def __process_audio_file(self, file_path):
        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(file_path) as source:
                audio_data = recognizer.record(source)
                return recognizer.recognize_google(audio_data)

        except Exception as e:
            print(f"Error processing audio file {file_path}: {e}")
            return None
        
    def __append_user_message(self, user_query, user_image_path, user_audio_path):
        audio_content = ""
        image_paths = []
        if user_query is None:
            user_query = "Describe."
        if user_image_path:
            image_paths.append(user_image_path)
        if user_audio_path:
            audio_content = self.__process_audio_file(user_audio_path)
   
        query_with_context = f"""Given Context: {audio_content}
                                 Query: {user_query}"""
        self.__messages.append({"role": "user", "content": query_with_context, "images": image_paths})

    def append_assistant_message(self, content):
        self.__messages.append({"role": "assistant", "content" : content})  
    
    def get_assistant_response(self, user_text=None, user_image_path=None, user_audio_path=None):
        self.__append_user_message(user_text, user_image_path, user_audio_path)
        return ollama.chat(self.__model, self.__messages, options={"temperature":0})
    
    def get_history(self):
        return self.__messages
