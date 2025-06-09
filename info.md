# PSE&G Energy Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

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

These values can be found in your browser cookies after logging into your PSE&G account.

## Energy Dashboard Integration

This integration is fully compatible with the Home Assistant Energy Dashboard for tracking gas consumption and cost.
