from database import DatabaseClient
from ollama import chat, generate

class ChatClient:

    def __init__(self, folder_path,  chat_model = 'llava', transform_model = 'phi3'):
        self.messages = []
        self.chat_model = chat_model
        self.transform_model = transform_model
        self.database = DatabaseClient(folder_path)
        
    
    def retriever(self, query = None, image_path = None):
        if image_path != None and query != None:
            return self.database.search_with_image(image_path) + self.database.search_with_text(query)  
        elif query == None:
            return self.database.search_with_image(image_path)
        elif image_path == None:
            return self.database.search_with_text(query)
        
    def transform_query(self, user_content):
        content = f"""Extract exactly 3-5 keywords from the following query, and return them in a comma-separated list with no additional text.
        Query: "{user_content}"
        Keywords: """
        return generate(self.transform_model, prompt=content, options={'temperature':0})['response']

    def handle_properties(self, properties):
        context = ""
        image_paths = []
        for property in properties:
            if property['media_type'] == 'text' and property['text'] not in context:
                context += "\n" + property['text']
            if property['media_type'] == 'image' and property['path'] not in image_paths:
                image_paths.append(property['path'])
        return context, image_paths

    def user_message(self, content, image_paths):
        return {
            'role' : 'user',
            'content' : content,
            'images' : image_paths
        }

    def input_text(self, user_content):
        transfomed_query = self.transform_query(user_content)
        context, image_paths = self.handle_properties(self.retriever(query=transfomed_query))
        return self.user_message(
            content=f"""Given context : {context}.
                        The user says :  {user_content}""", 
            image_paths=image_paths
            )

    def input_image(self, image_path):
        context, image_paths = self.handle_properties(self.retriever(image_path=image_path))
        if image_path not in image_paths:
            image_paths.append(image_path)
        return self.user_message(
            content=f"""Explain with help of images. 
                        Context : {context}.""", 
            image_paths=image_paths
            )
    
    def input_text_image(self, user_content, image_path):
        transfomed_query = self.transform_query(user_content)
        context, image_paths = self.handle_properties(self.retriever(query=transfomed_query, image_path=image_path))
        if image_path not in image_paths:
            image_paths.append(image_path)
        return self.user_message(
            content=f"""Given context : {context} and images.
                        User says : {user_content}.""",
            image_paths=image_paths
        )
    
    def interact(self):
        print("Type /exit to end.")
        while True:
            user_content = input("User Content: ")
            if user_content == "/exit":
                self.database.close_connection()
                break
            user_image_path = input("User Image Path: ")
            
            if user_content != '' and user_image_path != '':
                self.messages.append(self.input_text_image(
                    user_content=user_content,
                    image_path=user_image_path
                ))
            elif user_image_path == '':
                self.messages.append(self.input_text(user_content))
            elif user_content == '':
                self.messages.append(self.input_image(user_image_path))
            else:
                continue
            
            assistant_content = ''
            for chunk in chat(self.chat_model, stream=True, messages=self.messages, options={'temperature':0}):
                assistant_content += chunk['message']['content']
                print(chunk['message']['content'], end='', flush=True)
            
            print()
            print('-'*50)
            self.messages.append({
                    'role' : 'assistant',
                    'content' : assistant_content
                })


