# Changelog

## 0.2.1

### Bug Fixes

- Added webdriver-manager to automatically download and manage ChromeDriver
- Fixed issue with ChromeDriver not being found in Home Assistant container environments
- Added better error handling and logging for driver initialization
- Added fallback to Chromium driver if Chrome driver fails

## 0.2.0

### Features

- Updated to use Selenium for web scraping instead of direct API calls
- Added support for collecting both electricity and gas data
- Created separate sensors for electricity and gas consumption and cost
- Improved error handling and data extraction methods
- Added proper unit conversion for gas (therms to kWh) for Energy Dashboard compatibility

### Breaking Changes

- Configuration now requires username and password instead of energize_id and session_id
- Existing sensors will need to be reconfigured

## 0.1.0

### New Features

- Initial release
- Support for PSE&G gas meter data
