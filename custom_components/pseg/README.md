# PSE&G Energy Integration for Home Assistant

This integration allows you to monitor your PSE&G gas usage and cost data in Home Assistant and integrate it with the Energy Dashboard.

## Features

- Gas consumption sensor (in kWh for Energy Dashboard compatibility)
- Gas cost sensor (in USD)
- Integration with Home Assistant Energy Dashboard
- Hourly data updates

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
