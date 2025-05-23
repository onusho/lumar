from database import DatabaseClient

class RetrieverClient:
    
    def __init__(self, folder_path):
        self.__database = DatabaseClient(folder_path)

    def __retrieve(self, text=None, image_path=None, search_for="all", limit=5):
        if image_path == None and text == None:
            return []
        elif image_path != None and text != None:
            return self.__database.search_with_image(image_path, search_for=search_for, limit=limit) + self.__database.search_with_text(text, search_for=search_for, limit=limit)
        elif text == None:
            return self.__database.search_with_image(image_path, search_for=search_for, limit=limit)
        elif image_path == None:
            return self.__database.search_with_text(text, search_for=search_for, limit=limit)
    
    def __organize_by_media_type(self, properties):
        response =  {
            'text': [],
            'image': []
        }
        for property in properties:
            if property["media_type"] == "text" and property not in response['text']:
                response['text'].append(property)
            if property["media_type"] == "image" and property not in response['image']:
                response["image"].append(property)
        return response
    
    def search(self, text=None, image_path=None, search_for="all", limit=5):
        """
            Inputs: text and/or images
            Options: search_for [all, text, image (name it media in frontend)], 
                    limit
            Output: {"text":[],
                    "image":[]}   
                it's a dictionary with "text" and "images" fields which are lists
        """
        return self.__organize_by_media_type(self.__retrieve(text, image_path, search_for=search_for, limit=limit))
        
    def close_database_connection(self):
        self.__database.close_connection()
        