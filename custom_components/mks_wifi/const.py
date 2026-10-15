"""Constants for the MKS WIFI integration."""

from datetime import timedelta
import logging

DOMAIN = "mks_wifi"
LOGGER = logging.getLogger(__package__)

DEFAULT_PORT = 8080
# The module only accepts a few TCP clients and a slicer may hold one: poll gently.
SCAN_INTERVAL = timedelta(seconds=30)
