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

# Website URLs
BASE_URL = "https://nj.myaccount.pseg.com"
LOGIN_URL = f"{BASE_URL}/user/login"
DASHBOARD_URL = f"{BASE_URL}/dashboard"
ELECTRIC_URL = f"{BASE_URL}/electric"
GAS_URL = f"{BASE_URL}/gas"

# API endpoints for data extraction
API_BASE_URL = f"{BASE_URL}/api"
USAGE_API_URL = f"{API_BASE_URL}/usage"
BILL_API_URL = f"{API_BASE_URL}/billing"

# Form field names
USERNAME_FIELD = "username"
PASSWORD_FIELD = "password"
SUBMIT_FIELD = "login-submit"

# Request headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
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
        """Login to PSE&G account using form-based authentication"""
        try:
            _LOGGER.info("Attempting to login to PSE&G")
            
            # Reset session
            self.session = requests.Session()
            self.session.headers.update(DEFAULT_HEADERS)
            
            # Step 1: Get the login page to retrieve cookies and CSRF token if needed
            _LOGGER.debug("Getting login page to initialize session")
            login_page_response = self.session.get(LOGIN_URL, timeout=30)
            
            if login_page_response.status_code != 200:
                _LOGGER.error(f"Failed to load login page: {login_page_response.status_code}")
                raise PSEGError(f"Failed to load login page: {login_page_response.status_code}")
            
            # Step 2: Extract CSRF token if present
            csrf_token = None
            login_page_content = login_page_response.text
            
            # Look for CSRF token in the page content
            csrf_match = re.search(r'name="_csrf"\s+value="([^"]+)"', login_page_content)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                _LOGGER.debug(f"Found CSRF token: {csrf_token[:10]}...")
            
            # Step 3: Prepare login form data
            login_form_data = {
                USERNAME_FIELD: self.username,
                PASSWORD_FIELD: self.password
            }
            
            # Add CSRF token if found
            if csrf_token:
                login_form_data["_csrf"] = csrf_token
            
            # Step 4: Submit the login form
            _LOGGER.debug("Submitting login form")
            
            # Update headers for form submission
            form_headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": LOGIN_URL
            }
            self.session.headers.update(form_headers)
            
            login_response = self.session.post(
                LOGIN_URL,
                data=login_form_data,
                timeout=30,
                allow_redirects=True
            )
            
            # Step 5: Check if login was successful by looking for redirects
            _LOGGER.debug(f"Login response status code: {login_response.status_code}")
            _LOGGER.debug(f"Login response URL: {login_response.url}")
            
            # If we were redirected to the dashboard or another authenticated page
            if DASHBOARD_URL in login_response.url or "dashboard" in login_response.url:
                _LOGGER.info("Login successful - redirected to dashboard")
                self.authenticated = True
                return True
            
            # Check if we can access the dashboard directly
            _LOGGER.debug("Checking if we can access the dashboard")
            dashboard_response = self.session.get(DASHBOARD_URL, timeout=30)
            
            if dashboard_response.status_code == 200 and "login" not in dashboard_response.url.lower():
                _LOGGER.info("Login successful - can access dashboard")
                self.authenticated = True
                return True
            
            # Login failed
            self.authenticated = False
            
            # If we got here, login probably failed
            _LOGGER.error("Login failed - could not access dashboard")
            
            # Check for error messages in the login response
            error_match = re.search(r'class="error-message">([^<]+)<', login_response.text)
            if error_match:
                error_message = error_match.group(1).strip()
                _LOGGER.error(f"Login error message: {error_message}")
                raise PSEGError(f"Login failed: {error_message}")
            
            raise PSEGError("Login failed - authentication unsuccessful")
            
        except RequestException as err:
            _LOGGER.error("Network error during login: %s", err)
            raise PSEGError(f"Network error during login: {err}")
        except Exception as err:
            _LOGGER.error("Unexpected error during login: %s", err)
            raise PSEGError(f"Unexpected error during login: {err}")

    def fetch_data(self):
        """Fetch both electricity and gas data using web scraping"""
        try:
            if not self.authenticated:
                self.login()
            
            # Fetch dashboard data first
            self._fetch_dashboard_data()
            
            # If we're missing data, try the specific pages
            if not self.electric_usage or not self.electric_cost or not self.electric_reading_date:
                self._fetch_electric_data()
                
            if not self.gas_usage or not self.gas_cost or not self.gas_reading_date:
                self._fetch_gas_data()
            
            # Return the collected data
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
        finally:
            # Always call logout to clean up
            self.logout()

    def _update_utility_data(self, utility_type, usage, cost, reading_date):
        """Update utility data based on type"""
        if utility_type == "electric":
            if usage:
                self.electric_usage = usage
            if cost:
                self.electric_cost = cost
            if reading_date:
                self.electric_reading_date = reading_date
        elif utility_type == "gas":
            if usage:
                self.gas_usage = usage
            if cost:
                self.gas_cost = cost
            if reading_date:
                self.gas_reading_date = reading_date

    def _extract_and_process_section(self, html_content, section_class, utility_type):
        """Extract and process a section from the dashboard HTML"""
        try:
            # Look for the section in the dashboard
            section_pattern = f'<div[^>]*class=".*{section_class}.*"[^>]*>([\s\S]*?)</div>\s*</div>'
            section_match = re.search(section_pattern, html_content)
            if not section_match:
                return
                
            section_content = section_match.group(0)
            usage, cost, reading_date = self._extract_data_from_html(section_content, utility_type)
            
            # Update the appropriate attributes based on utility type
            self._update_utility_data(utility_type, usage, cost, reading_date)
        except Exception as err:
            _LOGGER.error(f"Error processing {utility_type} section: {err}")

    def _extract_data_from_html(self, html_content, utility_type):
        """Extract usage, cost and reading date from HTML content"""
        usage = None
        cost = None
        reading_date = None
        
        try:
            # Extract usage - look for usage value patterns
            usage_pattern = r'class="usage-value">(\d+[.,]?\d*)\s*([kK][Ww][Hh]|[Tt]herms?)<'
            usage_match = re.search(usage_pattern, html_content)
            if usage_match:
                usage_value = usage_match.group(1).replace(',', '')
                usage_unit = usage_match.group(2).lower()
                usage = usage_value
                _LOGGER.info(f"Found {utility_type} usage: {usage} {usage_unit}")
            
            # Extract cost - look for cost value patterns
            cost_pattern = r'class="cost-value">\$?(\d+[.,]?\d*)<'
            cost_match = re.search(cost_pattern, html_content)
            if cost_match:
                cost = cost_match.group(1).replace(',', '')
                _LOGGER.info(f"Found {utility_type} cost: ${cost}")
            
            # Extract reading date - look for next reading date patterns
            date_pattern = r'next-meter-reading[^>]*>([^<]+)<'
            date_match = re.search(date_pattern, html_content)
            if date_match:
                date_text = date_match.group(1).strip()
                reading_date = self._format_date(date_text)
                _LOGGER.info(f"Found {utility_type} reading date: {reading_date}")
        except Exception as err:
            _LOGGER.error(f"Error extracting {utility_type} data from HTML: {err}")
        
        return usage, cost, reading_date

    def _fetch_dashboard_data(self):
        """Fetch data from the main dashboard page"""
        try:
            _LOGGER.debug("Fetching dashboard data")
            response = self.session.get(DASHBOARD_URL, timeout=30)
            
            if response.status_code != 200:
                _LOGGER.warning(f"Failed to fetch dashboard: {response.status_code}")
                return
                
            html_content = response.text
            
            # Extract and process electric section data
            self._extract_and_process_section(html_content, "electric-section", "electric")
            
            # Extract and process gas section data
            self._extract_and_process_section(html_content, "gas-section", "gas")
                    
        except Exception as err:
            _LOGGER.error(f"Error fetching dashboard data: {err}")

    def _fetch_electric_data(self):
        """Fetch data from the electric specific page"""
        try:
            _LOGGER.debug("Fetching electric page data")
            response = self.session.get(ELECTRIC_URL, timeout=30)
            
            if response.status_code != 200:
                _LOGGER.warning(f"Failed to fetch electric page: {response.status_code}")
                return
                
            html_content = response.text
            usage, cost, reading_date = self._extract_data_from_html(html_content, "electric")
            
            # Only update if we got new data and don't have existing data
            if usage and not self.electric_usage:
                self.electric_usage = usage
                
            if cost and not self.electric_cost:
                self.electric_cost = cost
                
            if reading_date and not self.electric_reading_date:
                self.electric_reading_date = reading_date
                
        except Exception as err:
            _LOGGER.error(f"Error fetching electric data: {err}")

    def _fetch_gas_data(self):
        """Fetch data from the gas specific page"""
        try:
            _LOGGER.debug("Fetching gas page data")
            response = self.session.get(GAS_URL, timeout=30)
            
            if response.status_code != 200:
                _LOGGER.warning(f"Failed to fetch gas page: {response.status_code}")
                return
                
            html_content = response.text
            usage, cost, reading_date = self._extract_data_from_html(html_content, "gas")
            
            # Only update if we got new data and don't have existing data
            if usage and not self.gas_usage:
                self.gas_usage = usage
                
            if cost and not self.gas_cost:
                self.gas_cost = cost
                
            if reading_date and not self.gas_reading_date:
                self.gas_reading_date = reading_date
                
        except Exception as err:
            _LOGGER.error(f"Error fetching gas data: {err}")
            
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
