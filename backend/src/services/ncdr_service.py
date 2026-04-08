from .base import BaseImageService


class NCDRService(BaseImageService):
    source_name = "NCDR"

    def fetch(self):
        image_url = "https://placehold.co/900x600?text=NCDR+Wind"
        source_url = "https://www.ncdr.nat.gov.tw/"
        self.request_placeholder(image_url)
        yield self.build_payload("wind", "NCDR Wind Map", image_url, source_url)
