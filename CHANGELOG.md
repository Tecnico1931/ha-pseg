# Changelog

## 0.3.1

### HTML Scraping Implementation

- Fixed JSON parsing error by implementing HTML scraping approach
- Improved login process with form-based authentication
- Added more robust data extraction from HTML content
- Enhanced error handling and logging
- Fixed issues with API endpoints

## 0.3.0

### Major Changes

- Completely replaced Selenium-based implementation with a pure requests-based implementation
- Eliminated all dependencies on ChromeDriver and browser automation
- Significantly improved reliability in restricted environments like Home Assistant
- Reduced resource usage and simplified installation requirements
- Improved error handling and data extraction
- Refactored code for better maintainability and reduced complexity

## 0.2.2

### Bug Fixes

- Implemented a more robust approach to initialize Chrome WebDriver in Home Assistant environments
- Added multiple fallback methods to find and use Chrome/Chromium in different locations
- Improved error handling and debugging information
- Fixed issues with ChromeDriver not being found in containerized environments

## 0.2.1

### Initial ChromeDriver Fixes

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
