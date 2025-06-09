"""PSE&G Energy API using Selenium."""
import logging
from typing import Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

_LOGGER = logging.getLogger(__name__)

LOGIN_PAGE = "https://nj.myaccount.pseg.com/user/login"
LOGOUT_PAGE = "https://nj.myaccount.pseg.com/user/logout"
READING_DATE_XPATH = '//p[@class="f19-med-cnd next-meter-reading"]'
USERNAME_FIELD_ID = "username"
PASSWORD_FIELD_ID = "password"
SUBMIT_BUTTON_ID = "submit"

# Additional XPaths for energy data
ENERGY_USAGE_XPATH = '//div[@class="usage-box"]//span[@class="usage-value"]'
ENERGY_COST_XPATH = '//div[@class="cost-box"]//span[@class="cost-value"]'


class PSEGError(Exception):
    """Exception raised for errors in the PSEG API."""
    pass


class PSEGApi:
    """A PSE&G Energy account interface.

    Attributes:
        username: A string representing the user's PSE&G account username
        password: A string representing the user's PSE&G account password
    """

    def __init__(self, username: str, password: str):
        """Return a PSE&G API object with the given credentials"""
        self.username = username
        self.password = password
        self.driver = None
        self.reading_date = None
        self.energy_usage = None
        self.energy_cost = None

    def _initialize_driver(self):
        """Initialize the Chrome WebDriver"""
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception:
                pass
        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=chrome_options)

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

    def fetch_data(self):
        """Fetch all energy data"""
        try:
            if self.driver is None:
                self.login()
                
            # Get reading date
            self.reading_date = self.driver.find_element(By.XPATH, READING_DATE_XPATH).text
            _LOGGER.info("Scraped reading date: %s", self.reading_date)
            
            # Get energy usage
            try:
                usage_element = self.driver.find_element(By.XPATH, ENERGY_USAGE_XPATH)
                self.energy_usage = usage_element.text.strip()
                _LOGGER.info("Scraped energy usage: %s", self.energy_usage)
            except Exception as err:
                _LOGGER.error("Error retrieving energy usage: %s", err)
                self.energy_usage = None
                
            # Get energy cost
            try:
                cost_element = self.driver.find_element(By.XPATH, ENERGY_COST_XPATH)
                self.energy_cost = cost_element.text.strip().replace('$', '')
                _LOGGER.info("Scraped energy cost: %s", self.energy_cost)
            except Exception as err:
                _LOGGER.error("Error retrieving energy cost: %s", err)
                self.energy_cost = None
                
            return {
                "reading_date": self.reading_date,
                "energy_usage": self.energy_usage,
                "energy_cost": self.energy_cost
            }
        except Exception as err:
            _LOGGER.error("Error fetching data: %s", err)
            raise PSEGError(f"Error fetching data: {err}")
        finally:
            self.logout()

    def get_energy_usage(self) -> Optional[float]:
        """Return the energy usage"""
        try:
            if self.energy_usage is None:
                self.fetch_data()
            if self.energy_usage:
                # Remove any non-numeric characters except decimal point
                numeric_value = ''.join(c for c in self.energy_usage if c.isdigit() or c == '.')
                return float(numeric_value)
            return None
        except (PSEGError, ValueError) as err:
            _LOGGER.error("Error retrieving energy usage: %s", err)
            return None

    def get_energy_cost(self) -> Optional[float]:
        """Return the energy cost (in dollars)"""
        try:
            if self.energy_cost is None:
                self.fetch_data()
            if self.energy_cost:
                # Remove any non-numeric characters except decimal point
                numeric_value = ''.join(c for c in self.energy_cost if c.isdigit() or c == '.')
                return float(numeric_value)
            return None
        except (PSEGError, ValueError) as err:
            _LOGGER.error("Error retrieving energy cost: %s", err)
            return None
            
    def get_read_date(self) -> Optional[str]:
        """Return the date of the last energy reading"""
        try:
            if self.reading_date is None:
                self.fetch_data()
            return self.reading_date
        except PSEGError as err:
            _LOGGER.error("Error retrieving read date: %s", err)
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
