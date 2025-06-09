"""PSE&G Energy and Gas API using requests."""
import logging
from typing import Dict, Any, Optional
import time
import json
import re
from datetime import datetime

import requests
from requests.exceptions import RequestException

_LOGGER = logging.getLogger(__name__)

# API URLs
BASE_URL = "https://nj.myaccount.pseg.com"
LOGIN_URL = f"{BASE_URL}/api/v1/user/login"
DASHBOARD_API_URL = f"{BASE_URL}/api/v1/dashboard"
ELECTRIC_API_URL = f"{BASE_URL}/api/v1/electric/usage"
GAS_API_URL = f"{BASE_URL}/api/v1/gas/usage"

# Request headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/dashboard"
}


class PSEGError(Exception):
    """Exception raised for errors in the PSEG API."""
    pass


class PSEGApi:
    """A PSE&G Energy and Gas account interface using requests.

    Attributes:
        username: A string representing the user's PSE&G account username
        password: A string representing the user's PSE&G account password
    """

    def __init__(self, username: str, password: str):
        """Return a PSE&G API object with the given credentials"""
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.authenticated = False
        
        # Electric data
        self.electric_reading_date = None
        self.electric_usage = None
        self.electric_cost = None
        
        # Gas data
        self.gas_reading_date = None
        self.gas_usage = None
        self.gas_cost = None
        
        # Token data
        self.auth_token = None

    def login(self):
        """Login to PSE&G account using requests"""
        try:
            _LOGGER.info("Attempting to login to PSE&G")
            
            # Reset session
            self.session = requests.Session()
            self.session.headers.update(DEFAULT_HEADERS)
            
            # Prepare login data
            login_data = {
                "username": self.username,
                "password": self.password
            }
            
            # Make login request
            response = self.session.post(
                LOGIN_URL,
                json=login_data,
                timeout=30
            )
            
            # Check if login was successful
            if response.status_code == 200:
                response_data = response.json()
                
                # Check if we have an auth token
                if "token" in response_data:
                    self.auth_token = response_data["token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.authenticated = True
                    _LOGGER.info("Login successful")
                    return True
                else:
                    _LOGGER.error("Login response did not contain auth token")
                    raise PSEGError("Login response did not contain auth token")
            else:
                _LOGGER.error(f"Login failed with status code {response.status_code}: {response.text}")
                raise PSEGError(f"Login failed with status code {response.status_code}: {response.text}")
                
        except RequestException as err:
            _LOGGER.error("Network error during login: %s", err)
            raise PSEGError(f"Network error during login: {err}")
        except Exception as err:
            _LOGGER.error("Unexpected error during login: %s", err)
            raise PSEGError(f"Unexpected error during login: {err}")

    def fetch_data(self):
        """Fetch both electricity and gas data using API requests"""
        try:
            if not self.authenticated:
                self.login()
            
            # Fetch dashboard data first for reading dates
            self._fetch_dashboard_data()
            
            # Fetch electric and gas data
            self._fetch_electric_data()
            self._fetch_gas_data()
            
            return {
                "electric_reading_date": self.electric_reading_date,
                "electric_usage": self.electric_usage,
                "electric_cost": self.electric_cost,
                "gas_reading_date": self.gas_reading_date,
                "gas_usage": self.gas_usage,
                "gas_cost": self.gas_cost
            }
        except RequestException as err:
            _LOGGER.error("Network error fetching data: %s", err)
            self.authenticated = False
            raise PSEGError(f"Network error fetching data: {err}")
        except Exception as err:
            _LOGGER.error("Error fetching data: %s", err)
            raise PSEGError(f"Error fetching data: {err}")

    def _extract_reading_date(self, data):
        """Extract reading date from API response"""
        if "nextReadingDate" in data:
            reading_date = data["nextReadingDate"]
            formatted_date = self._format_date(reading_date)
            _LOGGER.info(f"Got reading date: {formatted_date}")
            return formatted_date
        return None
        
    def _extract_usage_cost(self, summary_data, type_label):
        """Extract usage and cost from summary data"""
        usage = None
        cost = None
        
        if "usage" in summary_data:
            usage = str(summary_data["usage"])
            _LOGGER.info(f"Got {type_label} usage: {usage}")
            
        if "cost" in summary_data:
            cost = str(summary_data["cost"])
            _LOGGER.info(f"Got {type_label} cost: {cost}")
            
        return usage, cost

    def _fetch_dashboard_data(self):
        """Fetch data from the main dashboard API"""
        try:
            _LOGGER.debug("Fetching dashboard data")
            response = self.session.get(DASHBOARD_API_URL, timeout=30)
            
            if response.status_code != 200:
                _LOGGER.warning(f"Failed to fetch dashboard data: {response.status_code} - {response.text}")
                return
                
            data = response.json()
            
            # Extract reading dates
            reading_date = self._extract_reading_date(data)
            if reading_date:
                self.electric_reading_date = reading_date
                self.gas_reading_date = reading_date
            
            # Extract electric data
            if "electricSummary" in data:
                usage, cost = self._extract_usage_cost(data["electricSummary"], "electric")
                if usage:
                    self.electric_usage = usage
                if cost:
                    self.electric_cost = cost
            
            # Extract gas data
            if "gasSummary" in data:
                usage, cost = self._extract_usage_cost(data["gasSummary"], "gas")
                if usage:
                    self.gas_usage = usage
                if cost:
                    self.gas_cost = cost
                    
        except Exception as err:
            _LOGGER.error(f"Error fetching dashboard data: {err}")

    def _extract_bill_data(self, data, utility_type):
        """Extract bill data from API response"""
        usage = None
        cost = None
        reading_date = None
        
        # Extract usage and cost from current bill
        if "currentBill" in data:
            bill = data["currentBill"]
            if "usage" in bill:
                usage = str(bill["usage"])
                _LOGGER.info(f"Got {utility_type} usage: {usage}")
                
            if "cost" in bill:
                # Remove $ if present
                cost = str(bill["cost"]).replace('$', '')
                _LOGGER.info(f"Got {utility_type} cost: {cost}")
        
        # Extract reading date
        if "nextReadingDate" in data:
            date_str = data["nextReadingDate"]
            reading_date = self._format_date(date_str)
            _LOGGER.info(f"Got {utility_type} reading date: {reading_date}")
            
        return usage, cost, reading_date

    def _fetch_utility_data(self, url, utility_type):
        """Generic method to fetch utility data"""
        try:
            _LOGGER.debug(f"Fetching {utility_type} data")
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                _LOGGER.warning(f"Failed to fetch {utility_type} data: {response.status_code} - {response.text}")
                return None, None, None
                
            return self._extract_bill_data(response.json(), utility_type)
            
        except Exception as err:
            _LOGGER.error(f"Error fetching {utility_type} data: {err}")
            return None, None, None

    def _fetch_electric_data(self):
        """Fetch data from the electric specific API"""
        usage, cost, reading_date = self._fetch_utility_data(ELECTRIC_API_URL, "electric")
        
        # Only update if we got new data and don't have existing data
        if usage and self.electric_usage is None:
            self.electric_usage = usage
            
        if cost and self.electric_cost is None:
            self.electric_cost = cost
            
        if reading_date and self.electric_reading_date is None:
            self.electric_reading_date = reading_date

    def _fetch_gas_data(self):
        """Fetch data from the gas specific API"""
        usage, cost, reading_date = self._fetch_utility_data(GAS_API_URL, "gas")
        
        # Only update if we got new data and don't have existing data
        if usage and self.gas_usage is None:
            self.gas_usage = usage
            
        if cost and self.gas_cost is None:
            self.gas_cost = cost
            
        if reading_date and self.gas_reading_date is None:
            self.gas_reading_date = reading_date
            
    def _format_date(self, date_str):
        """Format date string to a consistent format"""
        try:
            # Try to parse the date string and format it consistently
            # This handles different date formats that might come from the API
            if not date_str:
                return None
                
            # Remove any time component if present
            date_part = date_str.split('T')[0] if 'T' in date_str else date_str
            
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%b %d, %Y']:
                try:
                    parsed_date = datetime.strptime(date_part, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # If we couldn't parse it, return as is
            return date_str
        except Exception:
            return date_str

    def get_electric_usage(self) -> Optional[float]:
        """Return the electric usage"""
        try:
            if self.electric_usage is None:
                self.fetch_data()
            if self.electric_usage:
                # Remove any non-numeric characters except decimal point
                numeric_value = ''.join(c for c in self.electric_usage if c.isdigit() or c == '.')
                return float(numeric_value)
            return None
        except (PSEGError, ValueError) as err:
            _LOGGER.error("Error retrieving electric usage: %s", err)
            return None

    def get_electric_cost(self) -> Optional[float]:
        """Return the electric cost (in dollars)"""
        try:
            if self.electric_cost is None:
                self.fetch_data()
            if self.electric_cost:
                # Remove any non-numeric characters except decimal point
                numeric_value = ''.join(c for c in self.electric_cost if c.isdigit() or c == '.')
                return float(numeric_value)
            return None
        except (PSEGError, ValueError) as err:
            _LOGGER.error("Error retrieving electric cost: %s", err)
            return None

    def get_gas_usage(self) -> Optional[float]:
        """Return the gas usage"""
        try:
            if self.gas_usage is None:
                self.fetch_data()
            if self.gas_usage:
                # Remove any non-numeric characters except decimal point
                numeric_value = ''.join(c for c in self.gas_usage if c.isdigit() or c == '.')
                return float(numeric_value)
            return None
        except (PSEGError, ValueError) as err:
            _LOGGER.error("Error retrieving gas usage: %s", err)
            return None

    def get_gas_cost(self) -> Optional[float]:
        """Return the gas cost (in dollars)"""
        try:
            if self.gas_cost is None:
                self.fetch_data()
            if self.gas_cost:
                # Remove any non-numeric characters except decimal point
                numeric_value = ''.join(c for c in self.gas_cost if c.isdigit() or c == '.')
                return float(numeric_value)
            return None
        except (PSEGError, ValueError) as err:
            _LOGGER.error("Error retrieving gas cost: %s", err)
            return None
            
    def get_electric_read_date(self) -> Optional[str]:
        """Return the date of the last electric reading"""
        try:
            if self.electric_reading_date is None:
                self.fetch_data()
            return self.electric_reading_date
        except PSEGError as err:
            _LOGGER.error("Error retrieving electric read date: %s", err)
            return None
            
    def get_gas_read_date(self) -> Optional[str]:
        """Return the date of the last gas reading"""
        try:
            if self.gas_reading_date is None:
                self.fetch_data()
            return self.gas_reading_date
        except PSEGError as err:
            _LOGGER.error("Error retrieving gas read date: %s", err)
            return None

    def logout(self):
        """Logout from PSE&G account"""
        try:
            # Clear session and reset authentication state
            self.session.cookies.clear()
            self.authenticated = False
            self.auth_token = None
            _LOGGER.info("Logged out successfully")
        except Exception as err:
            _LOGGER.error("Error during logout: %s", err)

    def quit(self):
        """Clean up resources"""
        try:
            # Close the session
            self.session.close()
            _LOGGER.info("Session closed successfully")
        except Exception as err:
            _LOGGER.error("Error closing session: %s", err)
