"""Constants for the ABB Terra AC integration."""

DOMAIN = "abb_terra_ac"

CONF_UNIT_ID = "unit_id"
DEFAULT_SCAN_INTERVAL = 5  # seconds

# Charging states
# The firmware emits both IEC 61851-1 codes (0-5) and ABB extended codes
# (128-133) — sometimes flipping between an IEC and ABB code that mean the
# same physical state. Synonyms below share a display string so the sensor
# does not pingpong between equivalent names. The raw numeric code is still
# exposed via the `state_code` attribute for debugging.
CHARGING_STATES = {
    # Idle / no car
    0: "Idle",
    128: "Idle",
    # Connected, awaiting authorization
    1: "Connected (auth pending)",
    # Connected and ready
    2: "Connected",
    129: "Connected",
    # Ready but no PWM signal
    3: "Connected (no PWM)",
    # Actively charging
    4: "Charging",
    132: "Charging",
    # Charging complete
    130: "Charging Complete",
    # Soft-paused (current limit at 0, session still authorized)
    133: "Paused",
    # Catch-all
    5: "Other",
}

# State codes that indicate the EV is plugged in
PLUGGED_IN_STATES = {1, 2, 3, 4, 129, 130, 132, 133}

# State codes that indicate active charging
CHARGING_ACTIVE_STATES = {4, 132}
