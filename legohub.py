#Made by moob453
#The new legomovehubv2 libary

# Imports
import asyncio
import logging
import threading
from concurrent.futures import Future
import time # For simulating delays
import sys # Import sys for program exit

from bleak import BleakScanner, BleakClient

# Configure logging for more visibility into what Bleak and asyncio are doing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# Optionally, increase Bleak's logging verbosity for deeper debugging
#logging.getLogger("bleak").setLevel(logging.DEBUG)


class movehub2:
    # Class-level constants for connection
    DEVICE_NAME = "Technic Move"
    CHAR_UUID = "00001624-1212-EFDE-1623-785FEABCD123"

    # Define the mapping of color names to their corresponding hex IDs
    COLORS = dict(
        off=0x00,
        white=0x0a,
        pink=0x01,
        purple=0x02,
        blue=0x03,
        cyan=0x04,
        light_green=0x05,
        green=0x06,
        yellow=0x07,
        orange=0x08,
        red=0x09,
    )
    MOTOR_NAMES = dict(
        motor_a=0x32, # Changed to lowercase to match processing
        motor_b=0x33,
        motor_c=0x34,
    )
    MOTOR_TYPE = dict(
        power=0x00,
        speed=0x00,
    )
    def __init__(self):
        self._client: BleakClient = None
        self._loop: asyncio.AbstractEventLoop = None
        self._loop_thread: threading.Thread = None
        self._loop_ready_event = threading.Event() # To signal when the loop is ready
        logger.info("movehub2 instance created.")

    def _run_event_loop(self):
        """Method to run the asyncio event loop in a separate thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop_ready_event.set() # Signal that the loop is ready
        self._loop.run_forever()
        # Clean up the loop after it stops
        self._loop.close()

    def _start_loop_thread(self):
        """Starts the asyncio event loop in a new, daemon thread if not already running."""
        if self._loop_thread is None or not self._loop_thread.is_alive():
            self._loop_ready_event.clear() # Reset the event before starting
            self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self._loop_thread.start()
            self._loop_ready_event.wait(timeout=5) # Wait for the loop to signal it's ready
            if not self._loop_ready_event.is_set():
                logger.error("Failed to start event loop thread within timeout.")
                raise RuntimeError("Failed to start asyncio event loop in background.")

    def _stop_loop_thread(self):
        """Stops the asyncio event loop gracefully in its separate thread."""
        if self._loop and self._loop.is_running():
            logger.info("Stopping background event loop...")
            # Schedule a stop on the event loop from the main thread
            self._loop.call_soon_threadsafe(self._loop.stop)
            # Give the loop a moment to process the stop, then join the thread
            self._loop_thread.join(timeout=5) # Wait for the thread to finish
            if self._loop_thread.is_alive():
                logger.warning("Background event loop thread did not terminate gracefully.")
            self._loop = None
            self._loop_thread = None
            logger.info("Background event loop thread stopped.")

    def _run_async_in_thread(self, coro):
        """
        Runs an async coroutine on the background event loop and blocks
        the calling thread until the coroutine completes.
        """
        if self._loop is None:
            logger.error("Event loop reference is None. This should not happen after connect.")
            # We don't exit here immediately as _start_loop_thread will be called by connect
            # and may resolve this.
            raise RuntimeError("Event loop not initialized. Call connect() first.")
        if not self._loop.is_running():
            logger.error("Event loop is not running. It might have stopped unexpectedly or not started correctly.")
            raise RuntimeError("Event loop not running. Call connect() first or check loop health.")
        
        logger.debug(f"Submitting coroutine {coro.__name__ if hasattr(coro, '__name__') else 'unknown'} to event loop.")
        future: Future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            result = future.result() # Blocks until the coroutine completes
            logger.debug(f"Coroutine {coro.__name__ if hasattr(coro, '__name__') else 'unknown'} completed.")
            return result
        except Exception as e:
            logger.error(f"Error in background async operation: {e}", exc_info=True)
            # When an exception is caught here from the async operation,
            # we need to decide if it means immediate exit or propagation.
            # For "Hub not connected" we exit in _async_send_raw_command.
            # Other errors will still propagate as exceptions.
            raise # Re-raise the exception to the calling (synchronous) thread

    # --- Synchronous-looking Public API ---

    def connect(self, timeout: float = 10.0, device_name: str = DEVICE_NAME):
        """
        Connects to the Technic Move Hub.
        This method is synchronous for the user.
        """
        logger.info(f"Attempting to connect to '{device_name}' (timeout: {timeout}s)")
        self._start_loop_thread() # Ensure the background loop is running

        async def _connect_async_internal():
            if self._client and self._client.is_connected:
                logger.info("Already connected.")
                return self

            devices = await BleakScanner.discover(timeout=timeout)
            target_device = None
            for device in devices:
                if device.name and device_name in device.name:
                    target_device = device
                    logger.info(f"Found device: {device.name} at {device.address}")
                    break
            
            if not target_device:
                logger.warning(f"No device named '{device_name}' found within timeout.")
                return None # Return None if device not found
            
            self._client = BleakClient(target_device)
            try:
                await self._client.connect()
                if self._client.is_connected:
                    logger.info(f"Successfully connected to {target_device.name} ({target_device.address})")
                    return self
                else:
                    logger.error(f"Failed to connect to {target_device.name}, client not connected.")
                    self._client = None
                    return None
            except Exception as e:
                logger.error(f"Exception during connection to {target_device.name}: {e}", exc_info=True)
                self._client = None
                return None
        
        # Run the async connection logic on the background thread
        return self._run_async_in_thread(_connect_async_internal())

    def disconnect(self):
        """
        Disconnects the hub. This method is synchronous for the user.
        """
        
        if self._client is None and (self._loop is None or not self._loop.is_running()):
            logger.info("No BLE client connected and event loop is not running. Nothing to disconnect.")
            return
        logger.info("Ended program")

        async def _disconnect_async_internal():
            if self._client and self._client.is_connected:
                await self._client.disconnect()
                logger.info("Disconnected from hub.")
            else:
                logger.info("No active connection to disconnect.")
            self._client = None # Clear the client reference
        
        try:
            # Only try to run disconnect if the loop is active
            if self._loop and self._loop.is_running():
                self._run_async_in_thread(_disconnect_async_internal())
            else:
                logger.info("Event loop not running, cannot perform async disconnect.")
        except Exception as e:
            logger.error(f"Error during disconnection: {e}")
        finally:
            self._stop_loop_thread() # Always try to stop the loop when disconnecting

    # New internal async method for sending raw commands
    async def _async_send_raw_command(self, *args: int) -> bool:
        """
        Internal asynchronous method to send a raw command to the hub.
        This can be awaited directly by other async methods within the class.
        Prints an error and exits if not connected.
        """
        logger.debug("Executing _async_send_raw_command.")
        if not self._client or not self._client.is_connected:
            logger.fatal("Hub is not connected.") # User requested specific output
            self.disconnect() # Attempt to clean up resources
            sys.exit(1) # Terminate the program cleanly
        try:
            data = bytearray(args)
            await self._client.write_gatt_char(self.CHAR_UUID, data)
            logger.info(f"Sent: {' '.join(f'{byte:02x}' for byte in data)}")
            return True
        except Exception as e:
            logger.error(f"Failed to send command: {e}", exc_info=True)
            return False

    def send_raw_command(self, *args: int) -> bool:
        """
        Sends a raw command to the hub by converting a sequence of integers into a bytearray.
        Example: hub.send_raw_command(0x08, 0x00, 0x81, 0x32, 0x11, 0x51, 0x00, 0x03)
        This method is synchronous for the user.
        Prints an error and exits if the hub is not connected.
        """
        logger.info("Synchronous send_raw_command called.")
        # This public method now just calls the async internal one via _run_async_in_thread.
        # _async_send_raw_command handles the error message and exit.
        return self._run_async_in_thread(self._async_send_raw_command(*args))

    def led(self, color_name: str):
        """
        Sets the LED color of the hub using a predefined dictionary of colors.
        Args:
            color_name (str): The name of the color (e.g., "blue", "red", "off").
                              Must be a key in the 'COLORS' dictionary.
        This method is synchronous for the user.
        Prints an error and exits if the hub is not connected.
        """
        async def _set_led_color_async_internal():
            logger.debug("Executing _set_led_color_async_internal.")
            # _async_send_raw_command handles the connection check and exits if not connected.
            
            color_id = self.COLORS.get(color_name.lower())

            if color_id is None:
                logger.error(f"Error: Color '{color_name}' not found in the color dictionary.")
                logger.info(f"Available colors are: {', '.join(self.COLORS.keys())}")
                return # Do not exit, as this is an invalid color, not a connection error

            # Directly await the internal async send command.
            # This call will print an error and sys.exit(1) if the hub is not connected.
            success = await self._async_send_raw_command(0x08, 0x00, 0x81, 0x3f, 0x11, 0x51, 0x00, color_id)

            if success:
                logger.info(f"Attempted to set LED color to '{color_name}' (ID: 0x{color_id:02x})")
            else:
                logger.error(f"Failed to set LED color to '{color_name}'.")

        # _run_async_in_thread will execute _set_led_color_async_internal.
        # If _async_send_raw_command is called within it and finds no connection,
        # it will print the message and exit the program.
        self._run_async_in_thread(_set_led_color_async_internal())


 #funtion for motor control
    def motor(self, motor_name: str, type: str, value: int):
        """
        Sets the motor controlled and its value.
        Args:
            motor_name (str): name can be "motor A", "motor B" or "motor C".
            The type can be either power or speed. Both control continuous motor power.
            The value can be between -100 (full reverse) and 100 (full forward), 0 to stop.
        """

        async def _motor_async_internal():
            # Standardize motor_name to match dictionary keys (e.g., "motor A" -> "motor_a")
            processed_motor_name = motor_name.lower().replace(" ", "_")
            motor_port = self.MOTOR_NAMES.get(processed_motor_name)
            
            # Validate if the motor name is valid
            if motor_port is None:
                logger.error(f"Error: Invalid motor name '{motor_name}'. Available names: {', '.join(self.MOTOR_NAMES.keys())}")
                return # Exit the async function if motor name is invalid

            # Validate type and get its corresponding byte value (0x00 for both 'power' and 'speed' in your setup)
            processed_type = type.lower()
            motor_control_mode_byte = self.MOTOR_TYPE.get(processed_type)
            
            if motor_control_mode_byte is None:
                logger.error(f"Error: Invalid motor control type '{type}'. Must be 'power' or 'speed'.")
                return # Exit if type is invalid
            
            # Validate and convert value to integer, handling potential errors
            try:
                motor_value = int(value)
            except ValueError:
                logger.error(f"Error: Motor value '{value}' is not a valid integer.")
                return # Exit if value is not an integer

            # Validate motor value range (-100 to 100)
            if not (-100 <= motor_value <= 100):
                logger.error(f"Error: Motor value {motor_value} is out of range. Must be between -100 and 100.")
                return # Exit if value is out of range

            # --- NEW LOGIC FOR INVERTING MOTOR_A SPEED ---
            if processed_motor_name == "motor_a":
                logger.debug(f"Inverting speed for motor_A: {motor_value} -> {-motor_value}")
                motor_value = -motor_value
            # --- END NEW LOGIC ---

            # --- Convert motor_value to unsigned 8-bit byte before sending ---
            # This ensures negative values are correctly represented as two's complement (0-255)
            # which bytearray can handle, and the BLE hub will interpret as signed.
            motor_value_byte = motor_value & 0xFF
            # --- END LOGIC ---

            # Send the raw command to set motor power/speed.
            success = await self._async_send_raw_command(
                0x08, 0x00, 0x81, motor_port, 0x11, 0x51, motor_control_mode_byte, motor_value_byte # Use motor_value_byte here
            )

            if success:
                logger.info(f"Successfully set {processed_type} for {motor_name} to {value} (sent as {motor_value_byte})")
            else:
                logger.error(f"Failed to set {processed_type} for {motor_name}. Check logs for details.")
            
        # Run the asynchronous motor control logic in the background thread.
        self._run_async_in_thread(_motor_async_internal())