# PSE&G Energy Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/bvlaicu/ha-pseg.svg?style=flat-square)](https://github.com/bvlaicu/ha-pseg/releases)
[![License](https://img.shields.io/github/license/bvlaicu/ha-pseg.svg?style=flat-square)](LICENSE)

This integration allows you to monitor your PSE&G gas usage and cost data in Home Assistant and integrate it with the Energy Dashboard.

## Features

- Gas consumption sensor (in kWh for Energy Dashboard compatibility)
- Gas cost sensor (in USD)
- Integration with Home Assistant Energy Dashboard
- Hourly data updates

## Installation

### HACS Installation (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed in your Home Assistant instance.
2. Click on HACS in the sidebar.
3. Click on "Integrations".
4. Click the three dots in the top right corner and select "Custom repositories".
5. Enter the URL of this repository and select "Integration" as the category.
6. Click "Add".
7. Search for "PSE&G Energy" in the HACS store and install it.
8. Restart Home Assistant.
9. Go to **Settings** > **Devices & Services** > **Add Integration** and search for "PSE&G Energy".

### Manual Installation

1. Copy the `custom_components/pseg` folder to your Home Assistant's `custom_components` directory.
2. Restart Home Assistant.
3. Go to **Settings** > **Devices & Services** > **Add Integration** and search for "PSE&G Energy".

## Configuration

You will need to provide:

- **Energize ID**: Your PSE&G energize session ID
- **Session ID**: Your PSE&G session ID

These values can be found by:

1. Log in to your PSE&G MyEnergy account at [https://myenergy.pseg.com/](https://myenergy.pseg.com/)
2. Open your browser's developer tools (F12 in most browsers)
3. Go to the "Application" tab (Chrome) or "Storage" tab (Firefox)
4. Look for Cookies and find the `_energize_session` and `EMSSESSIONID` values

## Energy Dashboard Integration

To add your PSE&G gas data to the Energy Dashboard:

1. Go to **Settings** > **Dashboards** > **Energy**
2. Under "Gas Consumption", click "Add Consumption"
3. Select your "PSEG Gas Consumption" sensor
4. Under "Gas Cost", click "Add Cost"
5. Select your "PSEG Gas Cost" sensor

## Notes

- Data is updated hourly
- Gas consumption is converted from therms to kWh for Energy Dashboard compatibility (1 therm = 29.3001 kWh)
- Original therm values are available in the sensor attributes

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
