"""Constants for the ABB Terra AC integration."""

DOMAIN = "abb_terra_ac"

CONF_UNIT_ID = "unit_id"
DEFAULT_SCAN_INTERVAL = 5  # seconds

# Charging states (IEC 61851-1)
CHARGING_STATES = {
    0: "Idle (State A)",
    1: "EV Connected - Pending Auth (State B1)",
    2: "EV Connected - Ready (State B2)",
    3: "EV Ready - No PWM (State C1)",
    4: "Charging (State C2)",
    5: "Other",
}
