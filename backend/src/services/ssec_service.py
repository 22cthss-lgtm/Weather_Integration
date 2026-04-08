from .base import BaseImageService


class SSECService(BaseImageService):
    source_name = "SSEC"

    def fetch(self):
        image_url = "https://placehold.co/900x600?text=SSEC+Wind+Shear"
        source_url = "https://www.ssec.wisc.edu/"
        self.request_placeholder(image_url)
        yield self.build_payload("wind_shear", "SSEC Wind Shear", image_url, source_url)
