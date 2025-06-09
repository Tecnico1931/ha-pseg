"""Constants for the PSEG integration."""

DOMAIN = "pseg"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

DEFAULT_NAME = "PSE&G Energy"

# Attribute keys
ATTR_CONSUMPTION = "consumption"
ATTR_COST = "cost"
ATTR_LAST_READING = "last_reading"

# Energy units
ENERGY_KWH = "kWh"  # Unit for electricity consumption
ENERGY_THERM = "therm"  # Unit for gas consumption

# Sensor types
SENSOR_TYPE_ELECTRIC = "electric"
SENSOR_TYPE_GAS = "gas"
