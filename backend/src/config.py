from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "weather.db"

DEFAULT_IMAGE_TTL_MINUTES = 24 * 60
IMAGE_TYPE_TTL_MINUTES = {
    "radar": 10,
    "satellite": 10,
    "temperature": 60,
    "rainfall": 30,
    "weather_chart": 12 * 60,
    "850hpa": 12 * 60,
    "cimss_wind_analysis": 3 * 60,
    "cimss_wind_shear": 3 * 60,
    "cimss_850mb_vorticity": 3 * 60,
    "cimss_steering_flow": 3 * 60,
    "cimss_steering_flow_700_850mb": 3 * 60,
    "cimss_steering_flow_500_850mb": 3 * 60,
    "cimss_steering_flow_400_850mb": 3 * 60,
    "cimss_steering_flow_300_850mb": 3 * 60,
    "cimss_steering_flow_250_850mb": 3 * 60,
    "cimss_steering_flow_200_700mb": 3 * 60,
}
