"""Fixtures for the MKS WIFI integration tests."""

from collections.abc import Generator
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

from mkswifi import MksWifiClient, PrinterState, PrinterStatus, Temperature
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion

from custom_components.mks_wifi.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

HOST = "192.168.1.50"
PORT = 8080

# What a Wanhao D12 (firmware TFT24) reports mid-print: a phantom T1, a progress of 0.
STATUS = PrinterStatus(
    state=PrinterState.PRINTING,
    nozzles={0: Temperature(200.5, 210.0), 1: Temperature(24.8, 0.0)},
    bed=Temperature(59.7, 60.0),
    progress=0,
    file_name="stacked.gcode",
    file_size=2013404224,
    elapsed=timedelta(hours=1, minutes=2, seconds=3),
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations in all tests."""


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Home Assistant extension."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)


@pytest.fixture
def entity_registry_enabled_by_default() -> Generator[None]:
    """Enable all entities, including those disabled by default."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        new_callable=PropertyMock,
        return_value=True,
    ):
        yield


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "custom_components.mks_wifi.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"MKS WIFI {HOST}",
        data={CONF_HOST: HOST, CONF_PORT: PORT},
        entry_id="01JMKSWIFITESTENTRY000000",
    )


@pytest.fixture
def mock_mkswifi_client() -> Generator[MagicMock]:
    """Mock the MKS WIFI client, in the coordinator and the config flow."""
    with (
        patch(
            "custom_components.mks_wifi.coordinator.MksWifiClient",
            autospec=True,
        ) as client_mock,
        patch(
            "custom_components.mks_wifi.config_flow.MksWifiClient",
            new=client_mock,
        ),
    ):
        client: MagicMock = client_mock.return_value
        client.get_status.return_value = STATUS
        client.get_firmware.return_value = "TFT24"
        yield client


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_mkswifi_client: MksWifiClient,
) -> MockConfigEntry:
    """Set up the MKS WIFI integration for testing."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
