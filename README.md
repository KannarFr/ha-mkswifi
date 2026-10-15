# MKS WIFI for Home Assistant

A Home Assistant integration for 3D printers fitted with a Makerbase **MKS WIFI**
module, the ESP8266 add-on found on MKS Robin boards. It reads the printer's
state, temperatures and current job over the local network, with no cloud and
no account.

It is read-only: it does not pause, resume or stop prints.

## Supported hardware

Printers using an MKS Robin board with the MKS WIFI module, for example:

- Wanhao D12 (firmware "TFT24"), the printer it was developed on
- Two Trees printers (Sapphire, Bluer...)
- Flying Bear printers (Ghost, Reborn...)

Other printers that use the MKS WIFI module probably work too. If yours does,
or does not, please open an issue.

## Installation

### HACS

1. In HACS, open the menu in the top right corner and choose **Custom repositories**.
2. Add `https://github.com/KannarFr/ha-mkswifi` with the type **Integration**.
3. Search for **MKS WIFI** in HACS and download it.
4. Restart Home Assistant.

### Manually

Copy `custom_components/mks_wifi` into the `custom_components` folder of your
Home Assistant configuration, then restart Home Assistant.

Home Assistant 2026.9 or later is required.

## Configuration

Go to **Settings > Devices & services > Add integration** and pick **MKS WIFI**.

| Field | Description |
| ----- | ----------- |
| Host  | The hostname or IP address of the MKS WIFI module. Give it a fixed IP address (DHCP reservation) in your router. |
| Port  | The TCP port of the module, `8080` unless you changed it. |

The integration checks it can reach the printer before saving.

If the printer gets a new IP address, open the integration and choose
**Reconfigure** to change the host or port without losing your entities.

## Entities

| Entity | Description | Enabled by default |
| ------ | ----------- | ------------------ |
| State | `Idle`, `Printing` or `Paused` | Yes |
| Nozzle temperature | Current nozzle temperature, °C | Yes |
| Nozzle target temperature | Target nozzle temperature, °C | Yes |
| Bed temperature | Current bed temperature, °C | Yes |
| Bed target temperature | Target bed temperature, °C | Yes |
| Current file | Name of the file being printed | Yes |
| Print time | Time spent on the current print | Yes |
| Progress | Print progress, % | No |
| Nozzle 2 temperature, Nozzle 2 target temperature | Only created if the printer reports a second nozzle | No |

The printer device shows the firmware name and links to the module's web page.

## Data updates

The printer is polled every 30 seconds. The module accepts very few connections
at a time, and a slicer may already hold one, so each poll opens a connection,
asks for the status and closes it straight away.

When the printer cannot be reached (turned off, out of connections...), its
entities become unavailable until it answers again.

## Known limitations

- **Progress**: many firmwares, including the TFT24 on the Wanhao D12, always
  report 0 %. This is why the sensor is disabled by default.
- **Second nozzle**: some single-nozzle firmwares report a second nozzle (`T1`)
  with a target of 0. Its sensors are created disabled; enable them only if your
  printer really has two nozzles.
- **File size**: some firmwares report a meaningless file size, so it is not exposed.
- **No discovery**: the module only advertises a generic `ESP_XXXXXX` hostname,
  so it has to be added by hand.
- **Unknown state**: if the printer reports a state the integration does not
  recognise, the State sensor shows `Unknown`.
- **Read-only**: pausing, resuming and stopping prints is not supported.

## Removal

Go to **Settings > Devices & services**, open **MKS WIFI**, and delete the
entry. If you installed through HACS, also remove the repository from HACS.

## License

MIT, see [LICENSE](LICENSE).
