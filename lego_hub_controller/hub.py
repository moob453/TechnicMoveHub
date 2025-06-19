
from typing import Optional, List, Dict
import asyncio
import logging
from .ble import HubBLE

logger = logging.getLogger(__name__)

class Motor:
    def __init__(self, hub: 'Hub', port: int):
        self._hub = hub
        self._port = port
    
    async def run_degrees(self, degrees: int, speed: int):
        '''Run motor for specified degrees at given speed'''
        command = self._create_motor_command(degrees, speed)
        await self._hub._ble.send_command(command)
    
    async def run_speed(self, speed: int):
        '''Run motor at constant speed'''
        command = self._create_speed_command(speed)
        await self._hub._ble.send_command(command)
    
    def _create_motor_command(self, degrees: int, speed: int) -> bytes:
        # Command format based on Control+ protocol analysis
        # Implementation pending complete protocol documentation
        return bytes([0x01, self._port, 0x02, degrees & 0xFF, (degrees >> 8) & 0xFF, speed & 0xFF])
    
    def _create_speed_command(self, speed: int) -> bytes:
        return bytes([0x01, self._port, 0x01, speed & 0xFF])

class Hub:
    def __init__(self):
        self._ble = HubBLE()
        self.motor_a = Motor(self, 0)
        self.motor_b = Motor(self, 1)
        self.motor_c = Motor(self, 2)
        self.motor_d = Motor(self, 3)
        self._tilt = (0, 0, 0)  # x, y, z
        self._button_pressed = False
        
    async def connect(self, address: Optional[str] = None) -> bool:
        '''Connect to the hub'''
        return await self._ble.connect(address)
    
    async def disconnect(self):
        '''Disconnect from the hub'''
        await self._ble.disconnect()
    
    async def get_tilt(self) -> tuple:
        '''Get current tilt values (x, y, z)'''
        return self._tilt
    
    async def is_button_pressed(self) -> bool:
        '''Check if the hub button is pressed'''
        return self._button_pressed
    
    async def set_led_color(self, r: int, g: int, b: int):
        '''Set the hub LED color'''
        command = bytes([0x02, r & 0xFF, g & 0xFF, b & 0xFF])
        await self._ble.send_command(command)
    
    def _update_tilt(self, x: int, y: int, z: int):
        '''Update tilt values from sensor data'''
        self._tilt = (x, y, z)
    
    def _update_button(self, pressed: bool):
        '''Update button state from sensor data'''
        self._button_pressed = pressed
    
    @property
    def is_connected(self) -> bool:
        return self._ble.is_connected
