"""The MKS WIFI integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import MksWifiConfigEntry, MksWifiDataUpdateCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: MksWifiConfigEntry) -> bool:
    """Set up MKS WIFI from a config entry."""
    coordinator = MksWifiDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: MksWifiConfigEntry) -> bool:
    """Unload a MKS WIFI config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
