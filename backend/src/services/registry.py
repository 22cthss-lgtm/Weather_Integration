from .cwa_service import CWAService
from .kma_service import KMAService
from .meteologix_service import MeteologixService
from .ncdr_service import NCDRService
from .nsidc_service import NSIDCService
from .ocean_service import OceanService
from .ssec_service import SSECService


def get_services():
    return [
        CWAService(),
        KMAService(),
        OceanService(),
        NSIDCService(),
        NCDRService(),
        SSECService(),
        MeteologixService(),
    ]
