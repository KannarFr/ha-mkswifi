"""Config flow for the MKS WIFI integration."""

from typing import Any, override

from mkswifi import MksWifiClient, MksWifiError
import probatio

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers import selector

from .const import DEFAULT_PORT, DOMAIN, LOGGER

_PORT_SELECTOR = probatio.All(
    selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=1, max=65535, mode=selector.NumberSelectorMode.BOX
        ),
    ),
    probatio.Coerce(int),
)


_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_HOST): selector.TextSelector(),
        probatio.Required(CONF_PORT, default=DEFAULT_PORT): _PORT_SELECTOR,
    }
)


async def _async_validate(user_input: dict[str, Any]) -> dict[str, str]:
    """Check the printer answers; return the form errors."""
    client = MksWifiClient(user_input[CONF_HOST], user_input[CONF_PORT])
    try:
        await client.get_status()
    except MksWifiError:
        return {"base": "cannot_connect"}
    except Exception:  # noqa: BLE001
        LOGGER.exception("Unexpected exception")
        return {"base": "unknown"}
    return {}


class MksWifiConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MKS WIFI.

    The protocol exposes no serial number or MAC address, so entries are not
    given a unique ID: a printer is recognised by its host and port.
    """

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._async_abort_entries_match(
                {CONF_HOST: user_input[CONF_HOST], CONF_PORT: user_input[CONF_PORT]}
            )
            if not (errors := await _async_validate(user_input)):
                return self.async_create_entry(
                    title=f"MKS WIFI {user_input[CONF_HOST]}", data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a change of host or port, e.g. after the printer got a new IP."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            for other in self._async_current_entries(include_ignore=False):
                if (
                    other.entry_id != entry.entry_id
                    and other.data[CONF_HOST] == user_input[CONF_HOST]
                    and other.data[CONF_PORT] == user_input[CONF_PORT]
                ):
                    return self.async_abort(reason="already_configured")
            if not (errors := await _async_validate(user_input)):
                return self.async_update_reload_and_abort(
                    entry, data_updates=user_input
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _SCHEMA, user_input or entry.data
            ),
            errors=errors,
        )
