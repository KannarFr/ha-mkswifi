"""Support for MKS WIFI sensors."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from mkswifi import PrinterState, PrinterStatus

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import MksWifiConfigEntry
from .entity import MksWifiEntity

# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class MksWifiSensorEntityDescription(SensorEntityDescription):
    """Class describing MKS WIFI sensor entities."""

    value_fn: Callable[[PrinterStatus], StateType]


def _temperature(
    key: str, translation_key: str, value_fn: Callable[[PrinterStatus], StateType]
) -> MksWifiSensorEntityDescription:
    return MksWifiSensorEntityDescription(
        key=key,
        translation_key=translation_key,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=value_fn,
    )


SENSORS: tuple[MksWifiSensorEntityDescription, ...] = (
    MksWifiSensorEntityDescription(
        key="state",
        translation_key="state",
        device_class=SensorDeviceClass.ENUM,
        options=[
            state.value
            for state in (PrinterState.IDLE, PrinterState.PRINTING, PrinterState.PAUSED)
        ],
        # An unrecognised state is reported as Home Assistant's own unknown state.
        value_fn=lambda status: (
            None if status.state is PrinterState.UNKNOWN else status.state.value
        ),
    ),
    _temperature(
        "nozzle_temperature",
        "nozzle_temperature",
        lambda status: status.nozzle.current if status.nozzle else None,
    ),
    _temperature(
        "nozzle_target_temperature",
        "nozzle_target_temperature",
        lambda status: status.nozzle.target if status.nozzle else None,
    ),
    _temperature(
        "bed_temperature",
        "bed_temperature",
        lambda status: status.bed.current if status.bed else None,
    ),
    _temperature(
        "bed_target_temperature",
        "bed_target_temperature",
        lambda status: status.bed.target if status.bed else None,
    ),
    MksWifiSensorEntityDescription(
        key="progress",
        translation_key="progress",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        # Many firmwares (the TFT24 on a Wanhao D12, for one) always report 0.
        entity_registry_enabled_default=False,
        value_fn=lambda status: status.progress,
    ),
    MksWifiSensorEntityDescription(
        key="file_name",
        translation_key="file_name",
        value_fn=lambda status: status.file_name,
    ),
    MksWifiSensorEntityDescription(
        key="elapsed",
        translation_key="elapsed",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        value_fn=lambda status: (
            int(status.elapsed.total_seconds()) if status.elapsed else None
        ),
    ),
)


def _extra_nozzle_sensors(index: int) -> tuple[MksWifiSensorEntityDescription, ...]:
    """Sensors for nozzle T<index>, index >= 1.

    Disabled by default: some single-nozzle firmwares report a phantom T1.
    """
    placeholders = {"nozzle": str(index + 1)}
    return (
        MksWifiSensorEntityDescription(
            key=f"nozzle_{index}_temperature",
            translation_key="extra_nozzle_temperature",
            translation_placeholders=placeholders,
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            entity_registry_enabled_default=False,
            value_fn=lambda status: (
                nozzle.current if (nozzle := status.nozzles.get(index)) else None
            ),
        ),
        MksWifiSensorEntityDescription(
            key=f"nozzle_{index}_target_temperature",
            translation_key="extra_nozzle_target_temperature",
            translation_placeholders=placeholders,
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            entity_registry_enabled_default=False,
            value_fn=lambda status: (
                nozzle.target if (nozzle := status.nozzles.get(index)) else None
            ),
        ),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MksWifiConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up MKS WIFI sensors based on a config entry."""
    coordinator = entry.runtime_data
    descriptions = list(SENSORS)
    for index in coordinator.data.nozzles:
        if index >= 1:
            descriptions.extend(_extra_nozzle_sensors(index))
    async_add_entities(
        MksWifiSensorEntity(coordinator, description) for description in descriptions
    )


class MksWifiSensorEntity(MksWifiEntity, SensorEntity):
    """Defines a MKS WIFI sensor."""

    entity_description: MksWifiSensorEntityDescription

    @property
    @override
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
