from .cwa_service import CWAService
from .kma_service import KMAService
from .nsidc_service import NSIDCService
from .ocean_service import OceanService


def get_services():
    return [
        CWAService(),
        KMAService(),
        OceanService(),
        NSIDCService(),
    ]
