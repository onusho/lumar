import weaviate
from weaviate.classes.config import Configure, Multi2VecField
from weaviate.classes.query import Filter
from loader import DataLoader
import base64

class DatabaseClient:
    
    def __init__(self, folder_path):
        self.create_client()
        if self.generate_collection():
            self.data_ingestion(folder_path)
   
    def create_client(self):
        self.client = weaviate.connect_to_local()

    def generate_collection(self):
        if self.client.collections.exists('ClipCollection'):
            self.collection = self.client.collections.get('ClipCollection')
            return False
            # self.client.collections.delete('ClipCollection')

        self.collection = self.client.collections.create(
            name="ClipCollection",
            vectorizer_config=Configure.Vectorizer.multi2vec_clip(
                    image_fields=[
                        Multi2VecField(
                                name="image"
                        )
                    ],
                    text_fields=[
                        Multi2VecField(
                                name="text"
                        )
                    ]
            )
        )
        return True
    
    def data_ingestion(self, folder_path):
        loader = DataLoader(folder_path)
        object_list = loader.load_data()
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