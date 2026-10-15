"""Tests for the MKS WIFI sensors."""

from dataclasses import replace
from unittest.mock import MagicMock

from freezegun.api import FrozenDateTimeFactory
from mkswifi import MksWifiConnectionError, PrinterState
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion

from custom_components.mks_wifi.const import SCAN_INTERVAL
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import STATUS


@pytest.mark.usefixtures("entity_registry_enabled_by_default", "init_integration")
async def test_sensors(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the sensor entities and their states."""
    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


@pytest.mark.usefixtures("init_integration")
@pytest.mark.parametrize(
    "entity_id",
    [
        "sensor.mks_wifi_192_168_1_50_progress",
        "sensor.mks_wifi_192_168_1_50_nozzle_2_temperature",
        "sensor.mks_wifi_192_168_1_50_nozzle_2_target_temperature",
    ],
)
async def test_disabled_by_default(
    entity_registry: er.EntityRegistry, entity_id: str
) -> None:
    """Test the progress and extra nozzle sensors are disabled by default."""
    entry = entity_registry.async_get(entity_id)
    assert entry is not None
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_no_extra_nozzle(
    hass: HomeAssistant,
    mock_mkswifi_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test no extra nozzle sensors are created for a single-nozzle printer."""
    mock_mkswifi_client.get_status.return_value = replace(
        STATUS, nozzles={0: STATUS.nozzles[0]}
    )
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert entity_registry.async_get("sensor.mks_wifi_192_168_1_50_nozzle_temperature")
    assert not entity_registry.async_get(
        "sensor.mks_wifi_192_168_1_50_nozzle_2_temperature"
    )


@pytest.mark.usefixtures("entity_registry_enabled_by_default", "init_integration")
async def test_missing_values(
    hass: HomeAssistant,
    mock_mkswifi_client: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test sensors are unknown when the printer leaves a value out."""
    mock_mkswifi_client.get_status.return_value = replace(
        STATUS,
        state=PrinterState.UNKNOWN,
        nozzles={},
        bed=None,
        progress=None,
        file_name=None,
        elapsed=None,
    )
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    for state in hass.states.async_all("sensor"):
        assert state.state == STATE_UNKNOWN, state.entity_id


@pytest.mark.usefixtures("init_integration")
async def test_unavailable(
    hass: HomeAssistant,
    mock_mkswifi_client: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test sensors go unavailable when the printer stops answering, then recover."""
    entity_id = "sensor.mks_wifi_192_168_1_50_state"
    assert hass.states.get(entity_id).state == "printing"

    mock_mkswifi_client.get_status.side_effect = MksWifiConnectionError
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    mock_mkswifi_client.get_status.side_effect = None
    mock_mkswifi_client.get_status.return_value = replace(
        STATUS, state=PrinterState.PAUSED
    )
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "paused"
