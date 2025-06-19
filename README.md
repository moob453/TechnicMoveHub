
# LEGO Hub Controller and Firmware Analysis

This repository contains two main components:

1. Python Library for LEGO Hub Control
2. Firmware and Bootloader Analysis

## Python Library

The `lego_hub_controller` library provides a high-level interface for controlling LEGO Technic Smart Hubs via Bluetooth LE. See the [library documentation](lego_hub_controller/README.md) for usage details.

## Firmware Analysis

Based on the Control+ app analysis, we've discovered:

### Bootloader Information
- The hub uses a secure bootloader for firmware updates
- Bootloader mode can be activated through specific BLE commands
- Firmware updates are delivered through the Control+ app

### Firmware Update Process
1. The app sends a command to enter bootloader mode
2. The hub switches to DFU (Device Firmware Update) mode
3. Firmware is transferred in chunks via BLE
4. The hub verifies and applies the update

### Firmware Location
The Control+ app contains references to firmware in:
- Asset packs (downloaded during app updates)
- Cached firmware files in app storage

### Security Notes
- The bootloader appears to be locked and secure
- Firmware updates are signed
- The hub implements secure boot

### Next Steps for Firmware Investigation
1. Monitor BLE traffic during firmware updates
2. Analyze firmware update packets
3. Document the DFU protocol
4. Investigate firmware extraction from app assets

## Installation

```bash
pip install lego-hub-controller
```

## Usage Example

```python
import asyncio
from lego_hub_controller import Hub

async def main():
    hub = Hub()
    await hub.connect()
    await hub.motor_a.run_degrees(90, 50)
    await hub.disconnect()

asyncio.run(main())
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.
