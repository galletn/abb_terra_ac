# ABB Terra AC Wallbox - Home Assistant Integration

Custom Home Assistant integration for ABB Terra AC W11 wallbox via Modbus TCP.

## Features

### Entities Created

**Sensors:**
- Charging Current (L1, L2, L3, Total)
- Voltage (L1, L2, L3)
- Active Power (W)
- Energy Delivered (Wh)
- Charging State (with IEC 61851-1 state names)
- Current Limit Setting
- Max Current
- Error Code
- Socket Lock State
- Communication Timeout
- Serial Number
- Firmware Version

**Controls:**
- **Number Slider** (0-16A) - Set charging current limit
  - Set to 0A to pause charging
  - Slide to desired amperage to charge at that rate

- **Start/Pause Switch** - Quick start/pause control
  - ON = Start charging at 6A (default)
  - OFF = Pause charging (0A)

- **Stop Button** - Emergency stop
  - Sends STOP command (register 16645 = 1)
  - Use for immediate charging termination

**Services:**
- `abb_terra_ac.set_current_limit` - Set current limit (0-16A)
- `abb_terra_ac.start_charging` - Start charging with optional current (default 6A)
- `abb_terra_ac.stop_charging` - Emergency stop

## Installation

### 1. Enable Local Controller Mode

On your ABB Terra AC wallbox:
1. Download and install the **Terra Config** app on your phone
2. Connect to the wallbox via Bluetooth
3. Navigate to settings
4. Enable **"Local Controller"** mode
5. Connect wallbox to your network via **Ethernet cable** (WiFi not supported for Modbus)

### 2. Install the Integration

Copy the `custom_components/abb_terra_ac` folder to your Home Assistant `custom_components` directory:

```
homeassistant/
  └── custom_components/
      └── abb_terra_ac/
          ├── __init__.py
          ├── button.py
          ├── config_flow.py
          ├── const.py
          ├── manifest.json
          ├── number.py
          ├── sensor.py
          ├── services.yaml
          └── switch.py
```

### 3. Restart Home Assistant

Restart Home Assistant to load the integration.

### 4. Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **"ABB Terra AC Wallbox"**
4. Enter configuration:
   - **Host**: IP address of your wallbox (e.g., `192.168.1.100`)
   - **Port**: `502` (default Modbus TCP port)
   - **Unit ID**: `1` (default)

## Usage

### Basic Control

**Using the Slider:**
- Drag slider to desired amperage (0-16A)
- Set to 0A to pause charging
- Wallbox will adjust charging rate in real-time

**Using the Switch:**
- Turn ON to start charging at 6A
- Turn OFF to pause (0A)

**Emergency Stop:**
- Press the "Stop Charging" button
- Sends immediate STOP command to wallbox

### Automation Examples

**Charge at Solar Surplus:**
```yaml
automation:
  - alias: "Charge EV with Solar Surplus"
    trigger:
      - platform: state
        entity_id: sensor.solar_surplus_power
    action:
      - service: abb_terra_ac.set_current_limit
        data:
          current: >
            {{ (states('sensor.solar_surplus_power') | float / 230 / 3) | round(0) | min(16) | max(0) }}
```

**Stop Charging at High Grid Price:**
```yaml
automation:
  - alias: "Stop EV Charging at Peak Price"
    trigger:
      - platform: numeric_state
        entity_id: sensor.electricity_price
        above: 0.30
    action:
      - service: abb_terra_ac.stop_charging
```

**Smart Charging Schedule:**
```yaml
automation:
  - alias: "Start EV Charging at Night"
    trigger:
      - platform: time
        at: "23:00:00"
    action:
      - service: abb_terra_ac.start_charging
        data:
          current: 16  # Full speed
```

## Technical Details

### Register Map

**Read Registers (0x4000 - 0x4020):**
- Serial Number, Firmware, Max Current
- Error Code, Socket Lock, Charging State
- Current Limit, Actual Current (L1/L2/L3)
- Voltage (L1/L2/L3)
- Active Power, Energy Delivered
- Communication Timeout

**Write Registers:**
- `0x4100` (16640): Set Current Limit (32-bit, mA)
- `0x4105` (16645): Start/Stop Command (0=START, 1=STOP)

### Charging States (IEC 61851-1)

- **0**: Idle (State A) - No vehicle connected
- **1**: EV Connected - Pending Auth (State B1)
- **2**: EV Connected - Ready (State B2)
- **3**: EV Ready - No PWM (State C1)
- **4**: **Charging** (State C2)
- **5**: Other

### Important Notes

- Only **ONE** Modbus connection allowed at a time
- Modbus only works over **Ethernet**, not WiFi
- Minimum charging current: 6A (per IEC 61851-1)
- Setting current below 6A pauses charging
- STOP button sends actual STOP command (different from pause)
- Default polling interval: 5 seconds

## Troubleshooting

**Integration won't connect:**
- Verify "Local Controller" mode is enabled in Terra Config app
- Check wallbox is connected via Ethernet (not WiFi)
- Ping wallbox IP address to verify network connectivity
- Ensure no other Modbus clients are connected

**Current limit not changing:**
- Check charging state sensor shows state 4 (charging)
- Car must be connected and authenticated (badge tap)
- Some cars may require manual authorization to start charging

**Car won't start charging:**
- Tap badge to authenticate on wallbox
- Check car is not set to scheduled charging
- Verify car's charge limit is not reached
- Try using STOP button, wait 5 seconds, then use Start/Pause switch

## Credits

Integration developed based on testing with ABB Terra AC W11 wallbox (firmware 1.8.34).

Register discovery and validation performed using Python scripts with pymodbus library.
