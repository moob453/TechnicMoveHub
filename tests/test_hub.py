
import unittest
import asyncio
from lego_hub_controller import Hub

class TestHubController(unittest.TestCase):
    def setUp(self):
        self.hub = Hub()
        
    async def async_test_connection(self):
        # Test connection (will fail if no hub is present)
        connected = await self.hub.connect()
        self.assertTrue(connected)
        self.assertTrue(self.hub.is_connected)
        
        # Test LED control
        await self.hub.set_led_color(255, 0, 0)  # Red
        
        # Test motor control
        await self.hub.motor_a.run_degrees(45, 50)
        await asyncio.sleep(1)
        
        # Test sensor reading
        tilt = await self.hub.get_tilt()
        self.assertEqual(len(tilt), 3)  # Should return x,y,z values
        
        # Test disconnection
        await self.hub.disconnect()
        self.assertFalse(self.hub.is_connected)
    
    def test_connection(self):
        asyncio.run(self.async_test_connection())

if __name__ == '__main__':
    unittest.main()
