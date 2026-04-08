from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from .base import BaseImageService


class CWAService(BaseImageService):
    source_name = "CWA"
    satellite_source_url = "https://www.cwa.gov.tw/V8/C/W/OBS_Sat.html"
    satellite_image_prefix = "https://www.cwa.gov.tw/Data/satellite/LCC_IR1_CR_2750"
    satellite_image_pattern = "LCC_IR1_CR_2750-{timestamp}.jpg"
    satellite_timezone = ZoneInfo("Asia/Taipei")
    satellite_publish_delay_minutes = 30

    def satellite_image_exists(self, image_url: str) -> bool:
        try:
            response = requests.get(image_url, timeout=5, stream=True)
            exists = response.ok
            response.close()
            return exists
        except requests.RequestException:
            return False

    def resolve_satellite_image_url(self) -> tuple[str, str] | None:
        now = datetime.now(self.satellite_timezone).replace(second=0, microsecond=0)
        delayed_now = now - timedelta(minutes=self.satellite_publish_delay_minutes)
        rounded_now = delayed_now - timedelta(minutes=delayed_now.minute % 10)

        for offset in range(0, 360, 10):
            candidate_time = rounded_now - timedelta(minutes=offset)
            timestamp = candidate_time.strftime("%Y-%m-%d-%H-%M")
            filename = self.satellite_image_pattern.format(timestamp=timestamp)
            image_url = f"{self.satellite_image_prefix}/{filename}"

            if self.satellite_image_exists(image_url):
                display_time = candidate_time.strftime("%Y-%m-%d %H:%M")
                return image_url, display_time

        return None

    def fetch_satellite(self):
        resolved = self.resolve_satellite_image_url()
        if resolved is None:
            return

        image_url, display_time = resolved
        yield self.build_payload(
            "satellite",
            f"CWA Color Satellite Cloud {display_time}",
            image_url,
            self.satellite_source_url,
        )

    def fetch(self):
        yield from self.fetch_satellite()

        items = [
            (
                "radar",
                "CWA Radar Echo",
                "https://placehold.co/900x600?text=CWA+Radar",
                "https://www.cwa.gov.tw/",
            ),
            (
                "weather_chart",
                "CWA Weather Chart",
                "https://placehold.co/900x600?text=CWA+Weather+Chart",
                "https://www.cwa.gov.tw/",
            ),
            (
                "rainfall",
                "CWA Accumulated Rainfall",
                "https://placehold.co/900x600?text=CWA+Rainfall",
                "https://www.cwa.gov.tw/",
            ),
        ]
        for image_type, title, image_url, source_url in items:
            self.request_placeholder(image_url)
            yield self.build_payload(image_type, title, image_url, source_url)
