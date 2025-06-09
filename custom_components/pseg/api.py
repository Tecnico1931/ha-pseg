"""PSE&G Energy and Gas API using Selenium."""
import logging
from typing import Dict, Any, Optional
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

_LOGGER = logging.getLogger(__name__)

# URLs and login elements
LOGIN_PAGE = "https://nj.myaccount.pseg.com/user/login"
LOGOUT_PAGE = "https://nj.myaccount.pseg.com/user/logout"
DASHBOARD_PAGE = "https://nj.myaccount.pseg.com/dashboard"
GAS_DASHBOARD_PAGE = "https://nj.myaccount.pseg.com/gas"
ELECTRIC_DASHBOARD_PAGE = "https://nj.myaccount.pseg.com/electric"

USERNAME_FIELD_ID = "username"
PASSWORD_FIELD_ID = "password"
SUBMIT_BUTTON_ID = "submit"

# XPaths for reading dates
READING_DATE_XPATH = '//p[@class="f19-med-cnd next-meter-reading"]'
ELECTRIC_READING_DATE_XPATH = '//div[contains(@class, "electric-section")]//p[contains(@class, "next-meter-reading")]'
GAS_READING_DATE_XPATH = '//div[contains(@class, "gas-section")]//p[contains(@class, "next-meter-reading")]'

# XPaths for electricity data
ELECTRIC_USAGE_XPATH = '//div[contains(@class, "electric-section")]//div[@class="usage-box"]//span[@class="usage-value"]'
ELECTRIC_COST_XPATH = '//div[contains(@class, "electric-section")]//div[@class="cost-box"]//span[@class="cost-value"]'

# XPaths for gas data
GAS_USAGE_XPATH = '//div[contains(@class, "gas-section")]//div[@class="usage-box"]//span[@class="usage-value"]'
GAS_COST_XPATH = '//div[contains(@class, "gas-section")]//div[@class="cost-box"]//span[@class="cost-value"]'


class PSEGError(Exception):
    """Exception raised for errors in the PSEG API."""
    pass


class PSEGApi:
    """A PSE&G Energy and Gas account interface.

    Attributes:
        username: A string representing the user's PSE&G account username
        password: A string representing the user's PSE&G account password
    """

    def __init__(self, username: str, password: str):
        """Return a PSE&G API object with the given credentials"""
        self.username = username
        self.password = password
        self.driver = None
        
        # Electric data
        self.electric_reading_date = None
        self.electric_usage = None
        self.electric_cost = None
        
        # Gas data
        self.gas_reading_date = None
        self.gas_usage = None
        self.gas_cost = None

    def _initialize_driver(self):
        """Initialize the Chrome WebDriver with webdriver-manager"""
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception:
                pass
        
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.core.os_manager import ChromeType
            from selenium.webdriver.chrome.service import Service

            _LOGGER.debug("Initializing Chrome WebDriver with webdriver-manager")
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Try to use the ChromeDriverManager to get the driver
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                _LOGGER.debug("Successfully initialized Chrome WebDriver with ChromeDriverManager")
            except Exception as e:
                _LOGGER.warning(f"Failed to initialize with standard ChromeDriverManager: {e}")
                # Try with chromium driver as fallback
                try:
                    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    _LOGGER.debug("Successfully initialized Chrome WebDriver with Chromium driver")
                except Exception as e2:
                    _LOGGER.error(f"Failed to initialize with Chromium driver: {e2}")
                    raise
        except ImportError as e:
            _LOGGER.error(f"Failed to import webdriver-manager: {e}")
            raise PSEGError("webdriver-manager is required but not installed. Please make sure it's installed correctly.")

    def login(self):
        """Login to PSE&G account"""
        try:
            self._initialize_driver()
            _LOGGER.info("Navigating to login page")
            self.driver.get(LOGIN_PAGE)
            
            _LOGGER.info("Entering username")
            self.driver.find_element(By.ID, USERNAME_FIELD_ID).send_keys(self.username)
            
            _LOGGER.info("Entering password")
            self.driver.find_element(By.ID, PASSWORD_FIELD_ID).send_keys(self.password)
            
            _LOGGER.info("Clicking submit")
            self.driver.find_element(By.ID, SUBMIT_BUTTON_ID).click()
            
            # Wait for dashboard to load
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.XPATH, READING_DATE_XPATH))
            )
            _LOGGER.info("Login complete")
            return True
        except Exception as err:
            _LOGGER.error("Error during login: %s", err)
            if self.driver is not None:
                self.driver.quit()
                self.driver = None
            raise PSEGError(f"Error during login: {err}")

    def _extract_text(self, xpath, default=None):
        """Extract text from an element using XPath with error handling"""
        try:
            element = self.driver.find_element(By.XPATH, xpath)
            return element.text.strip()
        except (NoSuchElementException, TimeoutException) as err:
            _LOGGER.debug("Could not find element with xpath %s: %s", xpath, err)
            return default
        except Exception as err:
            _LOGGER.error("Error extracting text from xpath %s: %s", xpath, err)
            return default

    def _navigate_to_page(self, url):
        """Navigate to a specific page and wait for it to load"""
        try:
            self.driver.get(url)
            # Wait a moment for the page to load
            time.sleep(2)
            return True
        except Exception as err:
            _LOGGER.error("Error navigating to %s: %s", url, err)
            return False

    def fetch_data(self):
        """Fetch both electricity and gas data"""
        try:
            if self.driver is None:
                self.login()
            
            # First navigate to the main dashboard to get overview data
            self._navigate_to_page(DASHBOARD_PAGE)
            
            # Try to get data from the dashboard first
            self._fetch_dashboard_data()
            
            # If we're missing electric data, try the electric specific page
            if self.electric_usage is None or self.electric_cost is None:
                self._fetch_electric_data()
                
            # If we're missing gas data, try the gas specific page
            if self.gas_usage is None or self.gas_cost is None:
                self._fetch_gas_data()
                
            return {
                "electric_reading_date": self.electric_reading_date,
                "electric_usage": self.electric_usage,
                "electric_cost": self.electric_cost,
                "gas_reading_date": self.gas_reading_date,
                "gas_usage": self.gas_usage,
                "gas_cost": self.gas_cost
            }
        except Exception as err:
            _LOGGER.error("Error fetching data: %s", err)
            raise PSEGError(f"Error fetching data: {err}")
        finally:
            self.logout()

    def _fetch_dashboard_data(self):
        """Fetch data from the main dashboard"""
        # Get electric reading date
        self.electric_reading_date = self._extract_text(ELECTRIC_READING_DATE_XPATH)
        _LOGGER.info("Scraped electric reading date: %s", self.electric_reading_date)
        
        # Get gas reading date
        self.gas_reading_date = self._extract_text(GAS_READING_DATE_XPATH)
        _LOGGER.info("Scraped gas reading date: %s", self.gas_reading_date)
        
        # Get electric usage and cost
        self.electric_usage = self._extract_text(ELECTRIC_USAGE_XPATH)
        if self.electric_usage:
            _LOGGER.info("Scraped electric usage: %s", self.electric_usage)
        
        electric_cost_text = self._extract_text(ELECTRIC_COST_XPATH)
        if electric_cost_text:
            self.electric_cost = electric_cost_text.replace('$', '')
            _LOGGER.info("Scraped electric cost: %s", self.electric_cost)
        
        # Get gas usage and cost
        self.gas_usage = self._extract_text(GAS_USAGE_XPATH)
        if self.gas_usage:
            _LOGGER.info("Scraped gas usage: %s", self.gas_usage)
        
        gas_cost_text = self._extract_text(GAS_COST_XPATH)
        if gas_cost_text:
            self.gas_cost = gas_cost_text.replace('$', '')
            _LOGGER.info("Scraped gas cost: %s", self.gas_cost)

    def _fetch_electric_data(self):
        """Fetch data from the electric specific page"""
        if self._navigate_to_page(ELECTRIC_DASHBOARD_PAGE):
            # If we don't have a reading date yet, try to get it
            if not self.electric_reading_date:
                self.electric_reading_date = self._extract_text(READING_DATE_XPATH)
                _LOGGER.info("Scraped electric reading date from electric page: %s", self.electric_reading_date)
            
            # Get electric usage if we don't have it
            if not self.electric_usage:
                usage_xpath = '//div[@class="usage-box"]//span[@class="usage-value"]'
                self.electric_usage = self._extract_text(usage_xpath)
                if self.electric_usage:
                    _LOGGER.info("Scraped electric usage from electric page: %s", self.electric_usage)
            
            # Get electric cost if we don't have it
            if not self.electric_cost:
                cost_xpath = '//div[@class="cost-box"]//span[@class="cost-value"]'
                electric_cost_text = self._extract_text(cost_xpath)
                if electric_cost_text:
                    self.electric_cost = electric_cost_text.replace('$', '')
                    _LOGGER.info("Scraped electric cost from electric page: %s", self.electric_cost)

    def _fetch_gas_data(self):
        """Fetch data from the gas specific page"""
        if self._navigate_to_page(GAS_DASHBOARD_PAGE):
            # If we don't have a reading date yet, try to get it
            if not self.gas_reading_date:
                self.gas_reading_date = self._extract_text(READING_DATE_XPATH)
                _LOGGER.info("Scraped gas reading date from gas page: %s", self.gas_reading_date)
            
            # Get gas usage if we don't have it
            if not self.gas_usage:
                usage_xpath = '//div[@class="usage-box"]//span[@class="usage-value"]'
                self.gas_usage = self._extract_text(usage_xpath)
                if self.gas_usage:
                    _LOGGER.info("Scraped gas usage from gas page: %s", self.gas_usage)
            
            # Get gas cost if we don't have it
            if not self.gas_cost:
                cost_xpath = '//div[@class="cost-box"]//span[@class="cost-value"]'
                gas_cost_text = self._extract_text(cost_xpath)
                if gas_cost_text:
                    self.gas_cost = gas_cost_text.replace('$', '')
                    _LOGGER.info("Scraped gas cost from gas page: %s", self.gas_cost)

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
        if self.driver is not None:
            try:
                self.driver.get(LOGOUT_PAGE)
                _LOGGER.info("Logged out")
            except Exception as err:
                _LOGGER.error("Error during logout: %s", err)
            finally:
                self.quit()

    def quit(self):
        """Quit the WebDriver"""
        if self.driver is not None:
            try:
                _LOGGER.info("Quitting webdriver")
                self.driver.quit()
            except Exception as err:
                _LOGGER.error("Error quitting webdriver: %s", err)
            finally:
                self.driver = None
