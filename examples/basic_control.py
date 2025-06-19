
import asyncio
from lego_hub_controller import Hub

async def main():
    # Create hub instance
    hub = Hub()
    
    try:
        # Connect to hub
        print("Connecting to hub...")
        connected = await hub.connect()
        if not connected:
            print("Failed to connect to hub")
            return
        
        print("Connected to hub!")
        
        # Set LED color to blue
        print("Setting LED color to blue...")
        await hub.set_led_color(0, 0, 255)
        
        # Run motor A for 90 degrees at 50% speed
        print("Running motor A...")
        await hub.motor_a.run_degrees(90, 50)
        await asyncio.sleep(2)  # Wait for motor to complete
        
        # Get tilt values
        tilt = await hub.get_tilt()
        print(f"Hub tilt (x,y,z): {tilt}")
        
        # Check button state
        button = await hub.is_button_pressed()
        print(f"Button pressed: {button}")
        
    finally:
        # Always disconnect properly
        if hub.is_connected:
            print("Disconnecting...")
            await hub.disconnect()
            print("Disconnected")

if __name__ == "__main__":
    asyncio.run(main())
