from datetime import datetime, timedelta
import re
from zoneinfo import ZoneInfo

import requests
import urllib3

from .base import BaseImageService

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CWAService(BaseImageService):
    source_name = "CWA"
    cwa_base_url = "https://www.cwa.gov.tw"
    satellite_source_url = "https://www.cwa.gov.tw/V8/C/W/OBS_Sat.html"
    satellite_image_prefix = "https://www.cwa.gov.tw/Data/satellite/LCC_IR1_CR_2750"
    satellite_image_pattern = "LCC_IR1_CR_2750-{timestamp}.jpg"
    radar_source_url = "https://www.cwa.gov.tw/V8/C/W/OBS_Radar.html"
    radar_data_url = "https://www.cwa.gov.tw/Data/js/obs_img/Observe_radar.js"
    radar_image_prefix = "https://www.cwa.gov.tw/Data/radar"
    radar_image_pattern = "CV1_3600_{timestamp}.png"
    radar_data_regex = re.compile(r"""0:\{"img":'(?P<filename>CV1_3600_(?P<timestamp>\d{12})\.png)',\s*'text':'(?P<text>\d{4}/\d{2}/\d{2} \d{2}:\d{2})'\}""")
    radar_image_regex = re.compile(r"(?:https://www\.cwa\.gov\.tw)?(/Data/radar/CV1_3600_(\d{12})\.png)")
    temperature_source_url = "https://www.cwa.gov.tw/V8/C/W/OBS_Temp.html"
    temperature_image_prefix = "https://www.cwa.gov.tw/Data/temperature"
    temperature_image_pattern = "{timestamp}.GTP8w.jpg"
    temperature_image_regex = re.compile(
        r"(?:https://www\.cwa\.gov\.tw)?(?P<path>/Data/temperature/(?P<timestamp>\d{4}-\d{2}-\d{2}_\d{4})\.GTP8w\.jpg)"
    )
    rainfall_source_url = "https://www.cwa.gov.tw/V8/C/P/Rainfall/Rainfall_QZJ.html"
    rainfall_image_prefix = "https://www.cwa.gov.tw/Data/rainfall"
    rainfall_image_pattern = "{timestamp}.QZJ8.jpg"
    rainfall_image_regex = re.compile(
        r"(?:https://www\.cwa\.gov\.tw)?(?P<path>/Data/rainfall/(?P<timestamp>\d{4}-\d{2}-\d{2}_\d{4})\.QZJ8\.jpg)"
    )
    weather_chart_source_url = "https://www.cwa.gov.tw/V8/C/W/analysis.html"
    weather_chart_image_url = "https://www.cwa.gov.tw/Data/fcst_img/FI04.png"
    weather_chart_image_regex = re.compile(
        r"(?:https://www\.cwa\.gov\.tw)?(?P<path>/Data/fcst_img/FI04\.png\?t=(?P<timestamp>\d{10}-\d+))"
    )
    tchp_data_url = "https://www.cwa.gov.tw/Data/js/TDD_TCHP.js"
    tchp_image_regex = re.compile(
        r"""var\s+TDD_TCHP\s*=\s*['"](?P<filename>(?P<date>\d{4}-\d{2}-\d{2})_TCHP_[^'"]+\.png)['"]"""
    )
    satellite_timezone = ZoneInfo("Asia/Taipei")
    satellite_publish_delay_minutes = 30
    radar_publish_delay_minutes = 20
    temperature_publish_delay_minutes = 20
    rainfall_publish_delay_minutes = 20

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
                timeout=5,
                stream=True,
                headers=self.no_cache_headers(),
                params={"_": datetime.now(self.satellite_timezone).timestamp()},
                verify=False,
            )
            exists = response.ok
            response.close()
            return exists
        except requests.RequestException:
            return False

    def resolve_latest_image(
        self,
        *,
        image_prefix: str,
        image_pattern: str,
        publish_delay_minutes: int,
    ) -> tuple[str, str] | None:
        now = datetime.now(self.satellite_timezone).replace(second=0, microsecond=0)
        delayed_now = now - timedelta(minutes=publish_delay_minutes)
        rounded_now = delayed_now - timedelta(minutes=delayed_now.minute % 10)

        for offset in range(0, 360, 10):
            candidate_time = rounded_now - timedelta(minutes=offset)
            timestamp = candidate_time.strftime("%Y%m%d%H%M")
            if image_pattern == self.satellite_image_pattern:
                timestamp = candidate_time.strftime("%Y-%m-%d-%H-%M")
            elif image_pattern in (self.temperature_image_pattern, self.rainfall_image_pattern):
                timestamp = candidate_time.strftime("%Y-%m-%d_%H%M")

            filename = image_pattern.format(timestamp=timestamp)
            image_url = f"{image_prefix}/{filename}"

            if self.image_exists(image_url):
                display_time = candidate_time.strftime("%Y-%m-%d %H:%M")
                return image_url, display_time

        return None

    def resolve_satellite_image_url(self) -> tuple[str, str] | None:
        return self.resolve_latest_image(
            image_prefix=self.satellite_image_prefix,
            image_pattern=self.satellite_image_pattern,
            publish_delay_minutes=self.satellite_publish_delay_minutes,
        )

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

    def resolve_radar_image_url(self) -> tuple[str, str] | None:
        try:
            response = requests.get(self.radar_data_url, timeout=10, verify=False)
            response.raise_for_status()
            match = self.radar_data_regex.search(response.text)
            if match:
                filename = match.group("filename")
                display_time = match.group("text").replace("/", "-")
                image_url = f"{self.radar_image_prefix}/{filename}"
                return image_url, display_time
        except requests.RequestException:
            pass

        try:
            response = requests.get(self.radar_source_url, timeout=10, verify=False)
            response.raise_for_status()
            match = self.radar_image_regex.search(response.text)
            if match:
                image_path = match.group(1)
                timestamp = match.group(2)
                image_url = f"{self.cwa_base_url}{image_path}"
                candidate_time = datetime.strptime(timestamp, "%Y%m%d%H%M").replace(tzinfo=self.satellite_timezone)
                display_time = candidate_time.strftime("%Y-%m-%d %H:%M")
                return image_url, display_time
        except requests.RequestException:
            pass

        return self.resolve_latest_image(
            image_prefix=self.radar_image_prefix,
            image_pattern=self.radar_image_pattern,
            publish_delay_minutes=self.radar_publish_delay_minutes,
        )

    def fetch_radar(self):
        resolved = self.resolve_radar_image_url()
        if resolved is None:
            return

        image_url, display_time = resolved
        yield self.build_payload(
            "radar",
            f"CWA Radar Echo {display_time}",
            image_url,
            self.radar_source_url,
        )

    def resolve_temperature_image_url(self) -> tuple[str, str] | None:
        try:
            response = requests.get(
                self.temperature_source_url,
                timeout=10,
                headers=self.no_cache_headers(),
                params={"_": datetime.now(self.satellite_timezone).timestamp()},
                verify=False,
            )
            response.raise_for_status()
            match = self.temperature_image_regex.search(response.text)
            if match:
                image_url = f"{self.cwa_base_url}{match.group('path')}"
                timestamp = datetime.strptime(match.group("timestamp"), "%Y-%m-%d_%H%M").replace(
                    tzinfo=self.satellite_timezone
                )
                display_time = timestamp.strftime("%Y-%m-%d %H:%M")
                return image_url, display_time
        except requests.RequestException:
            pass

        return self.resolve_latest_image(
            image_prefix=self.temperature_image_prefix,
            image_pattern=self.temperature_image_pattern,
            publish_delay_minutes=self.temperature_publish_delay_minutes,
        )

    def fetch_temperature(self):
        resolved = self.resolve_temperature_image_url()
        if resolved is None:
            return

        image_url, display_time = resolved
        yield self.build_payload(
            "temperature",
            f"CWA Temperature Distribution {display_time}",
            image_url,
            self.temperature_source_url,
        )

    def resolve_rainfall_image_url(self) -> tuple[str, str] | None:
        try:
            response = requests.get(
                self.rainfall_source_url,
                timeout=10,
                headers=self.no_cache_headers(),
                params={"_": datetime.now(self.satellite_timezone).timestamp()},
                verify=False,
            )
            response.raise_for_status()
            match = self.rainfall_image_regex.search(response.text)
            if match:
                image_url = f"{self.cwa_base_url}{match.group('path')}"
                timestamp = datetime.strptime(match.group("timestamp"), "%Y-%m-%d_%H%M").replace(
                    tzinfo=self.satellite_timezone
                )
                display_time = timestamp.strftime("%Y-%m-%d %H:%M")
                return image_url, display_time
        except requests.RequestException:
            pass

        return self.resolve_latest_image(
            image_prefix=self.rainfall_image_prefix,
            image_pattern=self.rainfall_image_pattern,
            publish_delay_minutes=self.rainfall_publish_delay_minutes,
        )

    def fetch_rainfall(self):
        resolved = self.resolve_rainfall_image_url()
        if resolved is None:
            return

        image_url, display_time = resolved
        yield self.build_payload(
            "rainfall",
            f"CWA Accumulated Rainfall {display_time}",
            image_url,
            self.rainfall_source_url,
        )

    def resolve_direct_weather_chart_image_url(self) -> tuple[str, str | None] | None:
        cache_bust = str(int(datetime.now(self.satellite_timezone).timestamp()))
        image_url = f"{self.weather_chart_image_url}?t={cache_bust}"

        if not self.image_exists(image_url):
            return None

        return image_url, None

    def resolve_weather_chart_image_url(self) -> tuple[str, str | None] | None:
        try:
            response = requests.get(
                self.weather_chart_source_url,
                timeout=10,
                headers=self.no_cache_headers(),
                params={"_": datetime.now(self.satellite_timezone).timestamp()},
                verify=False,
            )
            response.raise_for_status()
            match = self.weather_chart_image_regex.search(response.text)
            if match:
                image_url = f"{self.cwa_base_url}{match.group('path')}"
                timestamp = datetime.strptime(match.group("timestamp").split("-")[0], "%Y%m%d%H").replace(
                    tzinfo=self.satellite_timezone
                )
                display_time = timestamp.strftime("%Y-%m-%d %H:00")
                return image_url, display_time
        except requests.RequestException:
            pass

        return self.resolve_direct_weather_chart_image_url()

    def fetch_weather_chart(self):
        resolved = self.resolve_weather_chart_image_url()
        if resolved is None:
            return

        image_url, display_time = resolved
        title = "CWA Surface Weather Chart"
        if display_time:
            title = f"{title} {display_time}"

        yield self.build_payload(
            "weather_chart",
            title,
            image_url,
            self.weather_chart_source_url,
        )

    def resolve_tchp_image_url(self) -> tuple[str, str] | None:
        try:
            response = requests.get(
                self.tchp_data_url,
                timeout=10,
                headers=self.no_cache_headers(),
                params={"_": datetime.now(self.satellite_timezone).timestamp()},
                verify=False,
            )
            response.raise_for_status()
            match = self.tchp_image_regex.search(response.text)
            if match:
                cache_bust = str(int(datetime.now(self.satellite_timezone).timestamp()))
                image_url = f"{self.cwa_base_url}/Data/TCHP/{match.group('filename')}?T={cache_bust}"
                image_date = datetime.strptime(match.group("date"), "%Y-%m-%d").replace(tzinfo=self.satellite_timezone)
                display_time = image_date.strftime("%Y-%m-%d 00:00")
                return image_url, display_time
        except requests.RequestException:
            pass

        return None

    def fetch_tchp(self):
        resolved = self.resolve_tchp_image_url()
        if resolved is None:
            return

        image_url, display_time = resolved
        yield self.build_payload(
            "tchp",
            f"CWA TCHP {display_time}",
            image_url,
            self.weather_chart_source_url,
        )

    def fetch(self):
        yield from self.fetch_satellite()
        yield from self.fetch_radar()
        yield from self.fetch_temperature()
        yield from self.fetch_rainfall()
        yield from self.fetch_weather_chart()
        yield from self.fetch_tchp()
