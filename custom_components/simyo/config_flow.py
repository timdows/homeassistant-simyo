"""Config flow for Simyo."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SimyoApiError, SimyoAuthError, SimyoClient
from .const import CONF_PHONE_NUMBER, DOMAIN

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PHONE_NUMBER): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class SimyoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Simyo config flow."""

    VERSION = 1

    async def _validate(self, phone_number: str, password: str) -> None:
        session = async_get_clientsession(self.hass)
        client = SimyoClient(session, phone_number, password)
        await client.login()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            phone_number = user_input[CONF_PHONE_NUMBER]
            await self.async_set_unique_id(phone_number)
            self._abort_if_unique_id_configured()
            try:
                await self._validate(phone_number, user_input[CONF_PASSWORD])
            except SimyoAuthError:
                errors["base"] = "invalid_auth"
            except SimyoApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Simyo {phone_number}", data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]  # noqa: ARG002
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        phone_number = entry.data[CONF_PHONE_NUMBER]
        if user_input is not None:
            try:
                await self._validate(phone_number, user_input[CONF_PASSWORD])
            except SimyoAuthError:
                errors["base"] = "invalid_auth"
            except SimyoApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry, data={**entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={"phone_number": phone_number},
            errors=errors,
        )
