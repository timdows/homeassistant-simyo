"""Constants for the Simyo integration."""

from datetime import timedelta

DOMAIN = "simyo"

CONF_PHONE_NUMBER = "phone_number"

DEFAULT_SCAN_INTERVAL = timedelta(hours=5)

API_BASE = "https://appapi.simyo.nl/simyoapi/api/v1"

CLIENT_PLATFORM = "ios"
CLIENT_VERSION = "4.23.5"
USER_AGENT = f"MijnSimyoFT/{CLIENT_VERSION} (iOS 26.3; iPhone16,1)"
