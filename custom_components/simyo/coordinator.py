"""DataUpdateCoordinator for the Simyo integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import SimyoApiError, SimyoAuthError, SimyoClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SimyoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinates polling of the Simyo API."""

    def __init__(self, hass: HomeAssistant, client: SimyoClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{client.phone_number}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.fetch_all()
        except SimyoAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except SimyoApiError as err:
            raise UpdateFailed(str(err)) from err
