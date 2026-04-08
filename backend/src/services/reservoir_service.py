from .base import BaseImageService


class ReservoirService(BaseImageService):
    source_name = "Reservoir"

    def fetch(self):
        image_url = "https://placehold.co/900x600?text=Reservoir+Map"
        source_url = "https://fhy.wra.gov.tw/"
        self.request_placeholder(image_url)
        yield self.build_payload("reservoir", "Reservoir Water Condition Map", image_url, source_url)
