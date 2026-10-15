"""Tests for the MKS WIFI config flow."""

from unittest.mock import AsyncMock, MagicMock

from mkswifi import MksWifiConnectionError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mks_wifi.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import HOST, PORT

pytestmark = pytest.mark.usefixtures("mock_setup_entry")


@pytest.mark.usefixtures("mock_mkswifi_client")
async def test_user_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test the full user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: 8081}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"MKS WIFI {HOST}"
    assert result["data"] == {CONF_HOST: HOST, CONF_PORT: 8081}
    assert result["result"].unique_id is None
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (MksWifiConnectionError, "cannot_connect"),
        (RuntimeError, "unknown"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    mock_mkswifi_client: MagicMock,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test the user flow shows an error, then recovers."""
    mock_mkswifi_client.get_status.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error}

    mock_mkswifi_client.get_status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: HOST, CONF_PORT: PORT}


async def test_user_flow_already_configured(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_mkswifi_client: MagicMock,
) -> None:
    """Test the user flow aborts when the printer is already configured."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    mock_mkswifi_client.get_status.assert_not_called()


@pytest.mark.usefixtures("mock_mkswifi_client")
@pytest.mark.parametrize(
    "new_data",
    [
        {CONF_HOST: "192.168.1.51", CONF_PORT: PORT},
        {CONF_HOST: HOST, CONF_PORT: 8081},
    ],
)
async def test_reconfigure_flow(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    new_data: dict[str, str | int],
) -> None:
    """Test changing the host or the port."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], new_data)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == new_data


@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (MksWifiConnectionError, "cannot_connect"),
        (RuntimeError, "unknown"),
    ],
)
async def test_reconfigure_flow_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_mkswifi_client: MagicMock,
    side_effect: type[Exception],
    error: str,
) -> None:
    """Test the reconfigure flow shows an error, then recovers."""
    mock_config_entry.add_to_hass(hass)
    mock_mkswifi_client.get_status.side_effect = side_effect
    result = await mock_config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.51", CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": error}

    mock_mkswifi_client.get_status.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.51", CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == {CONF_HOST: "192.168.1.51", CONF_PORT: PORT}


async def test_reconfigure_flow_already_configured(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_mkswifi_client: MagicMock,
) -> None:
    """Test the reconfigure flow aborts when another entry has that host and port."""
    mock_config_entry.add_to_hass(hass)
    MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "192.168.1.51", CONF_PORT: PORT}
    ).add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "192.168.1.51", CONF_PORT: PORT}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert mock_config_entry.data == {CONF_HOST: HOST, CONF_PORT: PORT}
    mock_mkswifi_client.get_status.assert_not_called()
