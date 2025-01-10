import ollama

class OfflineChat:
    
    def __init__(self, model="phi3-rag"):
        self.__messages = []
        self.__model = model
    
    def __append_user_message(self, user_query, search_result):
        content = ""
        image_paths = []
        for text_properties in search_result['text']:
            content += text_properties['text'] + "\n"
        for image_properties in search_result['image']:
            image_paths.append(image_properties['path'])
        query_with_context = f"""Given Context: {content}
                                 Query: {user_query}"""
        self.__messages.append({"role": "user", "content": query_with_context, "images": image_paths})
    
    def append_assistant_message(self, content):
        self.__messages.append({"role": "assistant", "content" : content})  
         
    def get_assistant_response(self, user_text, search_result):
        """
        Usage:
            for chunk in get_assistant_response(...):
                assistant_response += chunk["message"]["content"]
                print(chunk["message"]["content"], end="", flush=True)
            offline_chat.append_assistant_message(assistant_response)
        """
        self.__append_user_message(user_text, search_result)
        return ollama.chat(self.__model, self.__messages, stream=True, options={"temperature":0})
    
    def get_history(self):
        return self.__messages

import google.generativeai as genai
from IPython.display import Image

class OnlineChat:
    
    def __init__(self, api_key):
        self.__chat = self.__initiate_chat(api_key=api_key)
         
    def __initiate_chat(self, api_key, model_name="gemini-1.5-flash-001"):
        system_instructions = "You are a RAG Chatbot and you will only respond using the information given to you and nothing else."
        safey_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE",
            },
        ]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_name, 
                                      system_instruction=system_instructions, 
                                      safety_settings=safey_settings)
        return model.start_chat()
    
    def __create_user_message(self, user_text, search_result):
        content = ""
        images = []
        for text_properties in search_result['text']:
            content += text_properties['text'] + "\n"
        for image_properties in search_result['image']:
            images.append(Image(image_properties['path']))
        query_with_context = [f"Given Context: {content} \nQuery: {user_text}"] + images
        return query_with_context
    
    def get_assistant_response(self, user_text, search_result):
        """
        Usage:
            chat = OnlineChat(...)
            for chunk in chat.get_assistant_response(user_text, user_image_path):
                print(chunk.text, end="", flush=True)
        """
        return self.__chat.send_message(content=self.__create_user_message(user_text, search_result), stream=True)    
    
    def get_history(self):
        return self.__chat.history