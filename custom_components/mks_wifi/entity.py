"""Base entity for the MKS WIFI integration."""

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MksWifiDataUpdateCoordinator


class MksWifiEntity(CoordinatorEntity[MksWifiDataUpdateCoordinator]):
    """Defines a MKS WIFI entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MksWifiDataUpdateCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize a MKS WIFI entity."""
        super().__init__(coordinator)
        self.entity_description = description
        entry = coordinator.config_entry
        # The protocol exposes no serial number or MAC address.
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Makerbase",
            model="MKS WIFI",
            name=entry.title,
            sw_version=coordinator.firmware,
            configuration_url=f"http://{entry.data[CONF_HOST]}/",
        )
