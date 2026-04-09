from datetime import datetime, timezone
import re

import requests

from .base import BaseImageService


class OceanService(BaseImageService):
    source_name = "JMA"
    sst_source_url = "https://www.data.jma.go.jp/goos/data/rrtdb/jma-pro/him_sst_pac_D.html"
    sst_date_script_url = "https://www.data.jma.go.jp/goos/data/rrtdb/jma-pro/js/date_day_him.js"
    sst_image_base_url = "https://www.data.jma.go.jp/goos/data/pub/JMA-product/IMAGE/him_sst_pac_D"
    latest_date_regex = re.compile(
        r"var yye = (?P<year>\d{4}); var mme = (?P<month>\d{2}); var dde = (?P<day>\d{2});"
    )

    def resolve_latest_sst_image(self) -> tuple[str, str] | None:
        session = requests.Session()
        session.headers.update(
            {
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
        )

        try:
            date_script = session.get(self.sst_date_script_url, timeout=15)
            date_script.raise_for_status()
        except requests.RequestException:
            return None

        match = self.latest_date_regex.search(date_script.text)
        if match is None:
            return None

        display_date = f"{match.group('year')}-{match.group('month')}-{match.group('day')}"
        date_string = display_date.replace("-", "")
        image_url = f"{self.sst_image_base_url}/{match.group('year')}/him_sst_pac_D{date_string}.gif"

        try:
            response = session.get(image_url, timeout=15, stream=True)
            exists = response.ok and response.headers.get("Content-Type", "").startswith("image/")
            response.close()
            if exists:
                return image_url, display_date
        except requests.RequestException:
            return None

        return None

    def fetch_sst(self):
        resolved = self.resolve_latest_sst_image()
        if resolved is None:
            return

        image_url, display_date = resolved
        fetched_marker = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        cache_busted_url = f"{image_url}?fetched={fetched_marker}"
        yield self.build_payload(
            "sst",
            f"JMA Sea Surface Temperature Western North Pacific {display_date}",
            cache_busted_url,
            self.sst_source_url,
        )

    def fetch(self):
        yield from self.fetch_sst()
