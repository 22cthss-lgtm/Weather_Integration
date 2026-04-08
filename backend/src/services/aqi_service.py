from .base import BaseImageService


class AQIService(BaseImageService):
    source_name = "EPA AQI"

    def fetch(self):
        image_url = "https://placehold.co/900x600?text=AQI+Map"
        source_url = "https://airtw.moenv.gov.tw/"
        self.request_placeholder(image_url)
        yield self.build_payload("aqi", "Air Quality AQI Map", image_url, source_url)
