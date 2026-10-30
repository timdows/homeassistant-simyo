"""The Simyo integration."""

from __future__ import annotations

from uuid import uuid4

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SimyoApiError, SimyoAuthError, SimyoClient, SimyoRateLimited
from .const import (
    CONF_DEVICE_ID,
    CONF_PHONE_NUMBER,
    CONF_SESSION_TOKEN,
    CONF_WEB_SESSION,
    DOMAIN,
)
from .coordinator import SimyoCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Simyo from a config entry."""
    session = async_get_clientsession(hass)
    if CONF_DEVICE_ID not in entry.data:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_DEVICE_ID: str(uuid4())}
        )
    client = SimyoClient(
        session,
        entry.data[CONF_PHONE_NUMBER],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_DEVICE_ID],
        entry.data.get(CONF_SESSION_TOKEN),
        entry.data.get(CONF_WEB_SESSION),
    )
    try:
        if not client.session_token:
            await client.login()
    except SimyoAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except SimyoApiError as err:
        raise ConfigEntryNotReady(str(err)) from err
    except SimyoRateLimited as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = SimyoCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
