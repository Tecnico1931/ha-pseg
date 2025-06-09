"""Support for PSEG sensors."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    CURRENCY_DOLLAR,
    ENERGY_KILO_WATT_HOUR,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import PSEGApi, PSEGError
from .const import (
    ATTR_CONSUMPTION,
    ATTR_COST,
    ATTR_LAST_READING,
    CONF_USERNAME,
    CONF_PASSWORD,
    DEFAULT_NAME,
    DOMAIN,
    ENERGY_KWH,
)

_LOGGER = logging.getLogger(__name__)

# Time between updating data from PSEG
SCAN_INTERVAL = timedelta(hours=1)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the PSEG sensor."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)

    coordinator = PSEGDataUpdateCoordinator(hass, username, password)
    await coordinator.async_config_entry_first_refresh()

    entities = [
        PSEGConsumptionSensor(coordinator, name),
        PSEGCostSensor(coordinator, name),
    ]

    async_add_entities(entities, True)


class PSEGDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching PSEG data."""

    def __init__(
        self, hass: HomeAssistant, username: str, password: str
    ) -> None:
        """Initialize the data updater."""
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL
        )
        self.api = PSEGApi(username, password)
        self.data: Dict[str, Any] = {}

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from PSEG."""
        try:
            # Fetch all data at once
            await self.hass.async_add_executor_job(self.api.fetch_data)
            
            # Extract the data we need
            energy_usage = await self.hass.async_add_executor_job(self.api.get_energy_usage)
            energy_cost = await self.hass.async_add_executor_job(self.api.get_energy_cost)
            read_date = await self.hass.async_add_executor_job(self.api.get_read_date)
            
            return {
                "consumption": energy_usage,
                "cost": energy_cost,
                "read_date": read_date,
            }
        except PSEGError as err:
            _LOGGER.error("Error retrieving PSEG data: %s", err)
            raise


class PSEGBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for PSEG sensors."""

    def __init__(
        self, coordinator: PSEGDataUpdateCoordinator, name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.api.username)},
            name=name,
            manufacturer="PSE&G",
        )


class PSEGConsumptionSensor(PSEGBaseSensor):
    """Representation of a PSEG consumption sensor."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(
        self, coordinator: PSEGDataUpdateCoordinator, name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, name)
        self._attr_name = f"{name} Energy Consumption"
        self._attr_unique_id = f"{coordinator.api.username}_consumption"
        self._attr_native_unit_of_measurement = ENERGY_KILO_WATT_HOUR

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return STATE_UNKNOWN
        
        consumption = self.coordinator.data.get("consumption")
        if consumption is None:
            return STATE_UNAVAILABLE
            
        return float(consumption)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes of the sensor."""
        if not self.coordinator.data:
            return {}
            
        return {
            "unit": ENERGY_KWH,
            "last_reading": self.coordinator.data.get("read_date"),
        }


class PSEGCostSensor(PSEGBaseSensor):
    """Representation of a PSEG cost sensor."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(
        self, coordinator: PSEGDataUpdateCoordinator, name: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, name)
        self._attr_name = f"{name} Energy Cost"
        self._attr_unique_id = f"{coordinator.api.username}_cost"
        self._attr_native_unit_of_measurement = CURRENCY_DOLLAR

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return STATE_UNKNOWN
            
        cost = self.coordinator.data.get("cost")
        if cost is None:
            return STATE_UNAVAILABLE
            
        return float(cost)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes of the sensor."""
        if not self.coordinator.data:
            return {}
            
        return {
            "last_reading": self.coordinator.data.get("read_date"),
        }
