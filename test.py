import asyncio
from bleak import BleakClient, BleakScanner

# Define the UUIDs for the LEGO Wireless Protocol service and characteristic
# These are standard for LEGO hubs like the Technic Move Hub.
LEGO_SERVICE_UUID = "00001623-1212-efde-1623-785feabcd123"
LEGO_CHARACTERISTIC_UUID = "00001624-1212-efde-1623-785feabcd123"

# The name of your LEGO Technic Move Hub
# Using a partial name for more robust discovery, as the advertised name
# might include additional characters.
DEVICE_NAME = "Technic Move"

def notification_handler(sender, data):
    """
    Simple notification handler for BLE data.
    This function will be called whenever the hub sends data to the characteristic.
    """
    print(f"Received from hub (handle {sender}): {data.hex()}")

async def send_raw_lego_command():
    """
    Scans for the LEGO Technic Move Hub, connects to it,
    starts listening for notifications, and allows the user to send raw hexadecimal commands.
    """
    print(f"Searching for LEGO device: {DEVICE_NAME}...")
    device = None
    # Scan for devices with the specified name
    devices = await BleakScanner.discover(timeout=10)
    for d in devices:
        # Changed from '==' to 'in' for more robust device name matching
        if d.name and DEVICE_NAME in d.name:
            device = d
            print(f"Found device: {device.name} ({device.address})")
            break

    if not device:
        print(f"Could not find device: {DEVICE_NAME}. Make sure it's on and in range.")
        return

    async with BleakClient(device.address) as client:
        if client.is_connected:
            print(f"Connected to {device.name} ({device.address})")

            try:
                # Start listening for notifications from the characteristic
                print(f"Starting notifications on characteristic: {LEGO_CHARACTERISTIC_UUID}")
                await client.start_notify(LEGO_CHARACTERISTIC_UUID, notification_handler)
                print("Listening for incoming data from the hub...")

                while True:
                    # Prompt the user for the raw hexadecimal command
                    hex_command_str = input(
                        "Enter raw hex command (e.g., 0800813211510020) or 'quit' to exit: "
                    ).strip()

                    if hex_command_str.lower() == 'quit':
                        print("Exiting.")
                        break

                    if not hex_command_str:
                        print("No command entered. Please try again.")
                        continue

                    try:
                        # Convert the hexadecimal string to bytes
                        command_bytes = bytes.fromhex(hex_command_str)
                        print(f"Sending command: {hex_command_str} (bytes: {command_bytes.hex()})")

                        # Write the bytes to the LEGO characteristic
                        await client.write_gatt_char(LEGO_CHARACTERISTIC_UUID, command_bytes, response=True)
                        print("Command sent successfully!")
                    except ValueError:
                        print("Invalid hex string. Please enter a valid hexadecimal sequence.")
                    except Exception as e:
                        print(f"An error occurred while sending the command: {e}")
            except KeyboardInterrupt:
                print("\nOperation interrupted by user.")
            except Exception as e:
                print(f"An error occurred during communication: {e}")
            finally:
                # Stop notifications before disconnecting
                print("Stopping notifications.")
                await client.stop_notify(LEGO_CHARACTERISTIC_UUID)
                print("Disconnecting from the hub.")
        else:
            print(f"Failed to connect to {device.name}.")

if __name__ == "__main__":
    # Run the asynchronous function
    asyncio.run(send_raw_lego_command())
