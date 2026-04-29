"""The Simyo integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SimyoApiError, SimyoAuthError, SimyoClient
from .const import CONF_PHONE_NUMBER, DOMAIN
from .coordinator import SimyoCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Simyo from a config entry."""
    session = async_get_clientsession(hass)
    client = SimyoClient(
        session,
        entry.data[CONF_PHONE_NUMBER],
        entry.data[CONF_PASSWORD],
    )
    try:
        await client.login()
    except SimyoAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except SimyoApiError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = SimyoCoordinator(hass, client)
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
