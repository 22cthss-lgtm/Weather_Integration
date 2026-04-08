from .base import BaseImageService


class MeteologixService(BaseImageService):
    source_name = "Meteologix"

    def fetch(self):
        image_url = "https://placehold.co/900x600?text=Meteologix+Rain"
        source_url = "https://meteologix.com/"
        self.request_placeholder(image_url)
        yield self.build_payload("model_rainfall", "Meteologix Model Rainfall", image_url, source_url)
