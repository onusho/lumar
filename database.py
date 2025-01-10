import weaviate
from weaviate.classes.config import Configure, Multi2VecField
from weaviate.classes.query import Filter
from loader import DataLoader
import base64
from hashlib import md5

class DatabaseClient:
    
    def __init__(self, folder_path):
        self.__folder_path = folder_path
        self.__create_client()
        if self.__generate_collection():
            self.loader = DataLoader(folder_path, chunk_size=300, chunk_overlap=50)
            self.__data_ingestion()
   
    def __create_client(self):
        self.client = weaviate.connect_to_local()
    
    def __get_hashed_path(self):
        return self.__folder_path.split("\\")[-1]  + ''.join(filter(str.isalpha, md5(self.__folder_path.encode()).hexdigest()))

    def __generate_collection(self):
        collection_name = self.__get_hashed_path()
        if self.client.collections.exists(collection_name):
            # self.collection = self.client.collections.get(self.__get_hashed_path())
            # return False
            self.client.collections.delete(collection_name)

        # self.collection = self.client.collections.create(
        #     name = self.__get_hashed_path(),
        #     vectorizer_config=Configure.Vectorizer.multi2vec_clip(
        #             image_fields=[
        #                 Multi2VecField(
        #                     name="image"
        #                 )
        #             ],
        #             text_fields=[
        #                 Multi2VecField(
        #                     name="text"
        #                 ),
        #                 Multi2VecField(
        #                     name="path"
        #                 )
        #             ]
        #     )
        # )
        self.collection = self.client.collections.create(
            name=collection_name,
            vectorizer_config=Configure.Vectorizer.text2vec_ollama(
                api_endpoint="http://host.docker.internal:11434",
                model='nomic-embed-text'
            )
        )
        return True
    
    def __data_ingestion(self):
        object_list = self.loader.load_data()
        with self.collection.batch.dynamic() as batch:
            for object in object_list:
                batch.add_object(
                    properties=object
                )
    
    def search_with_text(self, query : str, search_for="all"):
        if search_for == "all":
            response =  self.collection.query.near_text(
                query=query,
                limit=5
            )
        elif search_for == "image":
            response =  self.collection.query.near_text(
                query=query,
                filters=Filter.by_property("media_type").equal("image"),
                limit=5
            )
        elif search_for == "text":
            response =  self.collection.query.near_text(
                query=query,
                filters=Filter.by_property("media_type").equal("text"),
                limit=5
            )

        return [object.properties for object in response.objects]
        
    def search_with_image(self, image_path, search_for = 'all'):
        def to_base64(path):
            with open(path, 'rb') as file:
                return base64.b64encode(file.read()).decode('utf-8')
        if search_for == "all":
            response = self.collection.query.near_image(
                near_image=to_base64(image_path),
                limit=5
            )
        elif search_for == "image":
            response = self.collection.query.near_image(
                near_image=to_base64(image_path),
                filters=Filter.by_property("media_type").equal("image"),
                limit=5
                )
        elif search_for == "text":
            response = self.collection.query.near_image(
                near_image=to_base64(image_path),
                filters=Filter.by_property("media_type").equal("text"),
                limit=5
            )
        return [object.properties for object in response.objects]
    
    def close_connection(self):
        self.client.close()
            
    def __repr__(self):
        return f"""Folder: {self.__folder_path}"""

