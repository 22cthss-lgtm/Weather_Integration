from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import re

import requests

from .base import BaseImageService


class NSIDCService(BaseImageService):
    source_name = "NSIDC"
    sea_ice_today_url = "https://nsidc.org/sea-ice-today"
    extent_image_url = "https://nsidc.org/data/seaice_index/images/daily_images/N_daily_extent_hires.png"
    concentration_image_url = "https://nsidc.org/data/seaice_index/images/daily_images/N_daily_concentration_hires.png"
    timeseries_image_url = "https://nsidc.org/data/seaice_index/images/daily_images/N_iqr_timeseries.png"
    month_names_regex = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    image_date_regex = re.compile(
        rf"(?:Sea Ice Extent|Sea Ice Concentration|Arctic Sea Ice Extent(?: Time Series)?).*?(\d{{2}} {month_names_regex} \d{{4}})"
    )

    @staticmethod
    def no_cache_headers() -> dict[str, str]:
        return {
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
        }

    def fetch_page_html(self) -> str | None:
        try:
            response = requests.get(
                self.sea_ice_today_url,
                timeout=20,
                headers=self.no_cache_headers(),
                params={"_": int(datetime.now(timezone.utc).timestamp())},
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            return None

    def fetch_image_response(self, image_url: str) -> requests.Response | None:
        try:
            response = requests.get(
                image_url,
                timeout=20,
                headers=self.no_cache_headers(),
                params={"_": int(datetime.now(timezone.utc).timestamp())},
            )
            response.raise_for_status()
            return response
        except requests.RequestException:
            return None

    def fetch_image_bytes(self, image_url: str) -> bytes:
        response = self.fetch_image_response(image_url)
        if response is None:
            return b""
        try:
            return response.content
        finally:
            response.close()

    def extract_image_time_from_bytes(self, image_bytes: bytes) -> str | None:
        if not image_bytes:
            return None

        text = image_bytes.decode("latin1", errors="ignore")
        match = self.image_date_regex.search(text)
        if match is None:
            return None

        parsed_date = datetime.strptime(match.group(1), "%d %b %Y")
        return parsed_date.strftime("%Y-%m-%d 00:00")

    def extract_image_time_from_headers(self, response: requests.Response) -> str | None:
        last_modified = response.headers.get("Last-Modified")
        if not last_modified:
            return None

        parsed_date = parsedate_to_datetime(last_modified)
        return parsed_date.strftime("%Y-%m-%d 00:00")

    def resolve_image_time(self, image_url: str) -> str | None:
        response = self.fetch_image_response(image_url)
        if response is None:
            return None

        try:
            image_time = self.extract_image_time_from_bytes(response.content)
            if image_time:
                return image_time
            return self.extract_image_time_from_headers(response)
        finally:
            response.close()

    def resolve_latest_sea_ice_images(self) -> dict[str, dict[str, str]] | None:
        page_html = self.fetch_page_html()
        if page_html is None:
            return None

        required_urls = {
            "seaice_extent": self.extent_image_url,
            "seaice_concentration": self.concentration_image_url,
            "seaice_timeseries": self.timeseries_image_url,
        }
        if not all(image_url in page_html for image_url in required_urls.values()):
            return None

        resolved_images: dict[str, dict[str, str]] = {}
        for image_type, image_url in required_urls.items():
            image_time = self.extract_image_time_from_bytes(self.fetch_image_bytes(image_url))
            if image_time is None:
                image_time = self.resolve_image_time(image_url)
            if image_time is None:
                return None
            resolved_images[image_type] = {
                "image_url": image_url,
                "image_time": image_time,
            }

        return resolved_images

    def fetch(self):
        resolved_images = self.resolve_latest_sea_ice_images()
        if resolved_images is None:
            return

        titles = {
            "seaice_extent": "NSIDC Sea Ice Extent",
            "seaice_concentration": "NSIDC Sea Ice Concentration",
            "seaice_timeseries": "NSIDC Arctic Sea Ice Extent Time Series",
        }

        for image_type in ("seaice_extent", "seaice_concentration", "seaice_timeseries"):
            resolved = resolved_images[image_type]
            yield self.build_payload(
                image_type,
                f"{titles[image_type]} {resolved['image_time']}",
                f"{resolved['image_url']}?ts={int(datetime.now(timezone.utc).timestamp())}",
                self.sea_ice_today_url,
            )
