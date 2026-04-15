from datetime import datetime, timedelta, timezone
import re

import requests

from .base import BaseImageService


class KMAService(BaseImageService):
    source_name = "KMA"
    analysis_chart_url = "https://www.kma.go.kr/nchn/image/chart/analysis-chart.do"
    weather_base_url = "https://www.weather.go.kr"
    image_prefix = f"{weather_base_url}/w/repositary/image/cht/img"
    image_pattern = "kim_up85_anlmod_pa4_{timestamp}.gif"
    image_regex = re.compile(
        r"(?P<url>(?:https://www\.weather\.go\.kr)?/w/repositary/image/cht/img/"
        r"kim_up85_anlmod_pa4_(?P<timestamp>\d{10})\.gif)"
    )

    @staticmethod
    def no_cache_headers() -> dict[str, str]:
        return {
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
        }

    def image_exists(self, image_url: str) -> bool:
        try:
            response = requests.get(
                image_url,
                timeout=10,
                stream=True,
                headers=self.no_cache_headers(),
                params={"_": datetime.now(timezone.utc).timestamp()},
            )
            exists = response.ok
            response.close()
            return exists
        except requests.RequestException:
            return False

    def resolve_latest_850hpa_image_by_probe(self) -> tuple[str, str] | None:
        now_utc = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        rounded_hour = now_utc.hour - (now_utc.hour % 12)
        candidate = now_utc.replace(hour=rounded_hour)

        for offset in range(0, 15):
            candidate_time = candidate - timedelta(hours=offset * 12)
            timestamp = candidate_time.strftime("%Y%m%d%H")
            image_url = f"{self.image_prefix}/{self.image_pattern.format(timestamp=timestamp)}"
            if self.image_exists(image_url):
                return image_url, candidate_time.strftime("%Y-%m-%d %H:00")

        return None

    def resolve_850hpa_image_url(self) -> tuple[str, str] | None:
        try:
            response = requests.get(
                self.analysis_chart_url,
                timeout=10,
                headers=self.no_cache_headers(),
                params={"_": datetime.now(timezone.utc).timestamp()},
            )
            response.raise_for_status()
            match = self.image_regex.search(response.text)
            if match:
                image_url = match.group("url")
                if image_url.startswith("/"):
                    image_url = f"{self.weather_base_url}{image_url}"
                image_time = datetime.strptime(match.group("timestamp"), "%Y%m%d%H").strftime("%Y-%m-%d %H:00")
                return image_url, image_time
        except requests.RequestException:
            pass

        return self.resolve_latest_850hpa_image_by_probe()

    def fetch_850hpa(self):
        resolved = self.resolve_850hpa_image_url()
        if resolved is None:
            return

        image_url, display_time = resolved
        yield self.build_payload(
            "850hpa",
            f"KMA 850hPa Analysis {display_time}",
            image_url,
            self.analysis_chart_url,
        )

    def fetch(self):
        yield from self.fetch_850hpa()
