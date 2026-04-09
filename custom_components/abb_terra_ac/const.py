"""Constants for the ABB Terra AC integration."""

DOMAIN = "abb_terra_ac"

CONF_UNIT_ID = "unit_id"
DEFAULT_SCAN_INTERVAL = 5  # seconds

# Charging states
# Standard IEC 61851-1 states (0-5) and ABB custom states (128+)
CHARGING_STATES = {
    # IEC 61851-1 standard states
    0: "Idle (State A)",
    1: "EV Connected - Pending Auth (State B1)",
    2: "EV Connected - Ready (State B2)",
    3: "EV Ready - No PWM (State C1)",
    4: "Charging (State C2)",
    5: "Other",
    # ABB custom states (firmware-dependent)
    128: "No Car Connected",
    129: "Ready",
    130: "Charging Complete",
    132: "Charging",
    133: "Paused",
}

# State codes that indicate the EV is plugged in
PLUGGED_IN_STATES = {1, 2, 3, 4, 129, 130, 132, 133}

# State codes that indicate active charging
CHARGING_ACTIVE_STATES = {4, 132}
