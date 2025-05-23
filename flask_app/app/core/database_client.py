from .data_loader import DataLoader

import weaviate
from weaviate.classes.config import Configure, Multi2VecField
from weaviate.classes.query import Filter
import base64
import os
import re
from hashlib import md5

class DatabaseClient:
    
    def __init__(self, folder_path):
        self.__folder_path = folder_path
        self.__create_client()
        if self.__generate_collection():
            self.loader = DataLoader(folder_path, chunk_size=300, chunk_overlap=50)
            self.__data_ingestion(folder_path)
   
    def __create_client(self):
        self.client = weaviate.connect_to_local(port=8081)
        # self.client = weaviate.Client(
        #         url="http://localhost:8081"  # host port, not container port
        #     )
    
    # def __get_hashed_path(self):
    #     return self.__folder_path.split("\\")[-1]  + ''.join(filter(str.isalpha, md5(self.__folder_path.encode()).hexdigest()))

    def __get_hashed_path(self):
        folder_name = os.path.basename(self.__folder_path)
        sanitized_name = re.sub(r'[^A-Za-z0-9_]', '', folder_name)
        if not sanitized_name or not sanitized_name[0].isalpha() or not sanitized_name[0].isupper():
            sanitized_name = "Doc" + sanitized_name.capitalize()
        hash_suffix = ''.join(filter(str.isalnum, md5(self.__folder_path.encode()).hexdigest()))[:6]
        class_name = f"{sanitized_name}_{hash_suffix}"
        return class_name


    def __generate_collection(self):
        collection_name = self.__get_hashed_path()
        if self.client.collections.exists(collection_name):
            self.collection = self.client.collections.get(self.__get_hashed_path())
            return False
            # self.client.collections.delete(collection_name)

        self.collection = self.client.collections.create(
            name = self.__get_hashed_path(),
            vectorizer_config=Configure.Vectorizer.multi2vec_clip(
                    image_fields=[
                        Multi2VecField(
                            name="image"
                        )
                    ],
                    text_fields=[
                        Multi2VecField(
                            name="text"
                        ),
                        Multi2VecField(
                            name="path"
                        )
                    ]
            )
        )
        return True
    
    def __data_ingestion(self, folder_path):
        object_list = self.loader.load_data()
        with self.collection.batch.dynamic() as batch:
            for object in object_list:
                batch.add_object(
                    properties=object
                )
    
    def search_with_text(self, query : str, search_for="all", limit=5):
        if search_for == "all":
            response =  self.collection.query.near_text(
                query=query,
                limit=limit
            )
        else:
            response = self.collection.query.near_text(
                query=query,
                filters=Filter.by_property("media_type").equal(search_for),
                limit=limit
            )
        return [object.properties for object in response.objects]
    
    def __to_base64(self, path):
            with open(path, 'rb') as file:
                return base64.b64encode(file.read()).decode('utf-8')
            
    def search_with_image(self, image_path, search_for = 'all', limit=5):
        if search_for == "all":
            response = self.collection.query.near_image(
                near_image=self.__to_base64(image_path),
                limit=limit
            )
        else:
            response = self.collection.query.near_image(
                near_image=self.__to_base64(image_path),
                filters=Filter.by_property("media_type").equal(search_for),
                limit=limit
                )
        return [object.properties for object in response.objects]

    def list_collections(self):
        return self.client.collections.list_all()
    
    def delete_collections(self, name):
        return self.client.collections.delete(name)
    
    def close_connection(self):
        self.client.close()
            
    def __repr__(self):
        return f"""Folder: {self.__folder_path}"""
