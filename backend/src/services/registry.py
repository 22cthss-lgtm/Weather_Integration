from .aqi_service import AQIService
from .cwa_service import CWAService
from .kma_service import KMAService
from .meteologix_service import MeteologixService
from .ncdr_service import NCDRService
from .nsidc_service import NSIDCService
from .ocean_service import OceanService
from .reservoir_service import ReservoirService
from .ssec_service import SSECService


def get_services():
    return [
        CWAService(),
        AQIService(),
        KMAService(),
        OceanService(),
        NSIDCService(),
        NCDRService(),
        SSECService(),
        MeteologixService(),
        ReservoirService(),
    ]
