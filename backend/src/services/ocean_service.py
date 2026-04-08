from .base import BaseImageService


class OceanService(BaseImageService):
    source_name = "Ocean"

    def fetch(self):
        items = [
            (
                "sst",
                "Sea Surface Temperature",
                "https://placehold.co/900x600?text=SST",
                "https://www.ospo.noaa.gov/",
            ),
            (
                "ohc",
                "Ocean Heat Content",
                "https://placehold.co/900x600?text=OHC",
                "https://www.ospo.noaa.gov/",
            ),
        ]
        for image_type, title, image_url, source_url in items:
            self.request_placeholder(image_url)
            yield self.build_payload(image_type, title, image_url, source_url)
