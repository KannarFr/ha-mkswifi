"""DataUpdateCoordinator for MKS WIFI."""

from typing import override

from mkswifi import MksWifiClient, MksWifiError, PrinterStatus

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER, SCAN_INTERVAL

type MksWifiConfigEntry = ConfigEntry[MksWifiDataUpdateCoordinator]


class MksWifiDataUpdateCoordinator(DataUpdateCoordinator[PrinterStatus]):
    """Poll the printer status."""

    config_entry: MksWifiConfigEntry
    firmware: str | None = None

    def __init__(self, hass: HomeAssistant, entry: MksWifiConfigEntry) -> None:
        """Initialize the coordinator."""
        self.client = MksWifiClient(entry.data[CONF_HOST], entry.data[CONF_PORT])
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.data[CONF_HOST]}",
            update_interval=SCAN_INTERVAL,
        )

    @override
    async def _async_setup(self) -> None:
        """Read the firmware name once, for the device info."""
        try:
            self.firmware = await self.client.get_firmware()
        except MksWifiError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="communication_error",
            ) from err

    @override
    async def _async_update_data(self) -> PrinterStatus:
        """Fetch the printer status."""
        try:
            return await self.client.get_status()
        except MksWifiError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="communication_error",
            ) from err
