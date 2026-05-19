from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request

from ..config import RAINFALL_OBSERVATION_TTL_MINUTES
from ..models.rainfall_observation_repository import (
    METRIC_COLUMNS,
    get_latest_rainfall_fetched_at,
    get_top_rainfall_observations,
)
from ..services.rainfall_observation_service import (
    CWA_API_KEY_MISSING_MESSAGE,
    RainfallObservationService,
)

rainfall_bp = Blueprint("rainfall", __name__)


def parse_fetched_at(fetched_at: str | None) -> datetime | None:
    if not fetched_at:
        return None
    try:
        parsed = datetime.fromisoformat(fetched_at)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def should_refresh_rainfall_observations() -> bool:
    fetched_at = parse_fetched_at(get_latest_rainfall_fetched_at())
    if fetched_at is None:
        return True
    ttl = timedelta(minutes=RAINFALL_OBSERVATION_TTL_MINUTES)
    return datetime.now(timezone.utc) - fetched_at > ttl


@rainfall_bp.get("/top")
def top_rainfall_observations():
    metric = request.args.get("metric", "10min").strip()
    if metric not in METRIC_COLUMNS:
        return jsonify({"error": f"Unsupported rainfall metric: {metric}"}), 400

    if should_refresh_rainfall_observations():
        try:
            RainfallObservationService().refresh_observations()
        except RuntimeError as exc:
            status_code = 503 if str(exc) == CWA_API_KEY_MISSING_MESSAGE else 502
            return jsonify({"error": str(exc)}), status_code

    rows = get_top_rainfall_observations(metric, limit=10)
    return jsonify(
        {
            "metric": metric,
            "unit": "mm",
            "fetched_at": get_latest_rainfall_fetched_at(),
            "items": [
                {
                    **row,
                    "rank": index + 1,
                }
                for index, row in enumerate(rows)
            ],
        }
    )
