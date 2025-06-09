# PSE&G Energy Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/tecnico1931/ha-pseg.svg?style=flat-square)](https://github.com/tecnico1931/ha-pseg/releases)
[![License](https://img.shields.io/github/license/tecnico1931/ha-pseg.svg?style=flat-square)](LICENSE)

This integration allows you to monitor your PSE&G electricity and gas usage and cost data in Home Assistant and integrate it with the Energy Dashboard.

## Features

- Electric consumption sensor (in kWh)
- Electric cost sensor (in USD)
- Gas consumption sensor (in kWh for Energy Dashboard compatibility)
- Gas cost sensor (in USD)
- Integration with Home Assistant Energy Dashboard
- Hourly data updates
- Secure authentication with your PSE&G account credentials

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

- **Username**: Your PSE&G account username/email
- **Password**: Your PSE&G account password

The integration uses Selenium to securely log in to your PSE&G account and scrape the data from the dashboard. Your credentials are stored securely in Home Assistant and are only used to authenticate with the PSE&G website.

## Energy Dashboard Integration

To add your PSE&G electricity data to the Energy Dashboard:

1. Go to **Settings** > **Dashboards** > **Energy**
2. Under "Electricity grid", click "Add Consumption"
3. Select your "PSE&G Electric Consumption" sensor
4. Under "Electricity cost", click "Add Cost"
5. Select your "PSE&G Electric Cost" sensor

To add your PSE&G gas data to the Energy Dashboard:

1. Go to **Settings** > **Dashboards** > **Energy**
2. Under "Gas Consumption", click "Add Consumption"
3. Select your "PSE&G Gas Consumption" sensor
4. Under "Gas Cost", click "Add Cost"
5. Select your "PSE&G Gas Cost" sensor

## Notes

- Data is updated hourly
- Gas consumption is converted from therms to kWh for Energy Dashboard compatibility (1 therm = 29.3001 kWh)
- Original therm values are available in the gas sensor attributes
- The integration uses a lightweight requests-based implementation with no external dependencies
- Works reliably in all Home Assistant environments including containers and restricted environments
- No browser or ChromeDriver installation required

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
