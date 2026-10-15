"""Tests for the MKS WIFI integration setup."""

from unittest.mock import MagicMock

from mkswifi import MksWifiConnectionError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mks_wifi.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .conftest import HOST


async def test_load_unload_entry(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test loading and unloading the config entry."""
    assert init_integration.state is ConfigEntryState.LOADED

    device = device_registry.async_get_device_by_identifier(
        (DOMAIN, init_integration.entry_id), init_integration.entry_id
    )
    assert device is not None
    assert device.manufacturer == "Makerbase"
    assert device.model == "MKS WIFI"
    assert device.name == f"MKS WIFI {HOST}"
    assert device.sw_version == "TFT24"
    assert device.configuration_url == f"http://{HOST}/"

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    assert init_integration.state is ConfigEntryState.NOT_LOADED


@pytest.mark.parametrize("method", ["get_status", "get_firmware"])
async def test_setup_retry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_mkswifi_client: MagicMock,
    method: str,
) -> None:
    """Test the entry is retried when the printer cannot be reached."""
    getattr(mock_mkswifi_client, method).side_effect = MksWifiConnectionError
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY
