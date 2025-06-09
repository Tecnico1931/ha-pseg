"""PSE&G Gas Meter API."""
import logging
import requests
from typing import Dict, Any, Optional

_LOGGER = logging.getLogger(__name__)


class PSEGError(Exception):
    """Exception raised for errors in the PSEG API."""
    pass


class PSEGApi:
    """A gas meter of PSE&G.

    Attributes:
        energize_id: A string representing the meter's energize id
        session_id: A string representing the meter's session id
    """

    def __init__(self, energize_id: str, session_id: str):
        """Return a meter object whose energize id is *energize_id*"""
        self.energize_id = energize_id
        self.session_id = session_id

    def last_gas_read(self) -> Dict[str, Any]:
        """Return the last gas meter read"""
        try:
            url = 'https://myenergy.pseg.com/api/meter_for_year'
            _LOGGER.debug("url = %s", url)

            headers = {"Cookie": f"_energize_session={self.energize_id}; EMSSESSIONID={self.session_id};"}
            _LOGGER.debug("headers = %s", headers)

            response = requests.get(url, headers=headers)
            _LOGGER.debug("response = %s", response)

            json_response = response.json()
            _LOGGER.debug("json_response = %s", json_response)

            if 'errors' in json_response:
                raise PSEGError(f"Error in getting the meter data: {json_response['errors']}")

            # parse the return reads and extract the most recent one
            # (i.e. last one in list)
            last_read = None
            for read in json_response['samples']['GAS']['GAS']:
                last_read = read
            _LOGGER.debug("last_read = %s", last_read)

            return last_read
        except requests.exceptions.RequestException as err:
            raise PSEGError(f"Error retrieving meter data: {err}")

    def last_gas_read_consumption(self) -> Optional[float]:
        """Return the consumption from the last gas meter read (in therms)"""
        try:
            last_read = self.last_gas_read()
            val = last_read['consumption']
            _LOGGER.debug("consumption = %s", val)
            return float(val)
        except (PSEGError, KeyError, ValueError) as err:
            _LOGGER.error("Error retrieving consumption data: %s", err)
            return None

    def last_gas_read_cost(self) -> Optional[float]:
        """Return the cost from the last gas meter read (in dollars)"""
        try:
            last_read = self.last_gas_read()
            val = last_read['dollars']
            _LOGGER.debug("cost = %s", val)
            return float(val)
        except (PSEGError, KeyError, ValueError) as err:
            _LOGGER.error("Error retrieving cost data: %s", err)
            return None
            
    def get_read_date(self) -> Optional[str]:
        """Return the date of the last gas meter read"""
        try:
            last_read = self.last_gas_read()
            val = last_read['read_date']
            _LOGGER.debug("read_date = %s", val)
            return val
        except (PSEGError, KeyError) as err:
            _LOGGER.error("Error retrieving read date: %s", err)
            return None
