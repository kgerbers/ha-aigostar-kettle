"""Constants for the AigoSmart integration."""

DOMAIN = "aigostar"

# Alibaba Cloud IoT EU endpoint
ALIBABA_IOT_HOST = "eu-central-1.api-iot.aliyuncs.com"
ALIBABA_IOT_BASE = f"https://{ALIBABA_IOT_HOST}"
ENDPOINT_GET     = "/thing/properties/get"
ENDPOINT_SET     = "/thing/properties/set"

# API credentials extracted from the AigoSmart Android APK (public, not user secrets)
APP_KEY    = "28770785"
APP_SECRET = "41fd4a1eb18fa7ace5e2abbbe3867f93"

# Config entry keys
CONF_EMAIL       = "email"
CONF_PASSWORD    = "password"

# Kettle property names vary slightly by product firmware.  The diagnostic
# sensor exposes the complete property map first; these aliases are used by
# the first kettle entity implementation once a matching TSL is observed.
KETTLE_TEMPERATURE_KEYS = (
    "CurrentTemperature", "CurrentTemp", "Temperature", "WaterTemperature",
)
KETTLE_TARGET_KEYS = (
    "TargetTemperature", "TargetTemp", "TemperatureSet", "SetTemperature",
)
KETTLE_HEATING_KEYS = (
    "Heating", "HeatingStatus", "WorkState", "Status", "Switch",
)

KETTLE_TEMPERATURE = "temperature"
KETTLE_TARGET_TEMPERATURE = "Target_temperature"
KETTLE_HEATING_SWITCH = "HeatingSwitch"
KETTLE_KEEP_WARM_SWITCH = "heatpreservation"
KETTLE_MODE = "Mode"
KETTLE_KEEP_WARM_TIME = "Time"

SCAN_INTERVAL_SECONDS = 30
