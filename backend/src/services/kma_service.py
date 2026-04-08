from .base import BaseImageService


class KMAService(BaseImageService):
    source_name = "KMA"

    def fetch(self):
        image_url = "https://placehold.co/900x600?text=KMA+850hPa"
        source_url = "https://www.weather.go.kr/"
        self.request_placeholder(image_url)
        yield self.build_payload("850hpa", "KMA 850hPa", image_url, source_url)
