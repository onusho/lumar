from database import DatabaseClient

class RetrieverClient:
    
    def __init__(self, folder_path):
        self.__database = DatabaseClient(folder_path)

    def __retrieve(self, text=None, image_path=None):
        if image_path == None and text == None:
            return []
        elif image_path != None and text != None:
            return self.__database.search_with_image(image_path) + self.database.search_with_text(text)
        elif text == None:
            return self.__database.search_with_image(image_path)
        elif image_path == None:
            return self.__database.search_with_text(text)
    
    def __organize_by_media_type(self, properties):
        response =  {
            'text': [],
            'image': []
        }
        for property in properties:
            if property["media_type"] == "text" and property not in response['text']:
                response['text'].append(property)
            if property["media_type"] == "image" and property not in response['image']:
                response.append(property)
        return response
    
    def search(self, text=None, image_path=None):
        return self.__organize_by_media_type(self.__retrieve(text, image_path))
    
    def close_database_connection(self):
        self.__database.close_connection()
        