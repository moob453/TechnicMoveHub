#defines commands to technic hub

#imports
import os, sys
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import asyncio
from bleak import BleakScanner, BleakClient
import time


#hub class
class TechnicMoveHub:
    #sets initial values
    def __init__(self, device_name):
        self.device_name = device_name
        self.service_uuid = "00001623-1212-EFDE-1623-785FEABCD123"
        self.char_uuid = "00001624-1212-EFDE-1623-785FEABCD123"
        self.client = None
        
        self.LIGHTS_OFF_OFF =    0b100
        self.LIGHTS_OFF_ON =     0b101
        self.LIGHTS_ON_ON =      0b000

    #discovers hub
    def run_discover(self):
        try:
            devices = BleakScanner.discover(timeout=20)
            return devices
        except Exception as e:
            print(f"Discovery failed with error: {e}")
            return None

    #scans and connects    
    async def scan_and_connect(self):
        scanner = BleakScanner()
        print(f"searching for Technic Move Hub...")
        devices = await scanner.discover(timeout =5)

        for device in devices:
            if device.name is not None and self.device_name in device.name:
                print(f"Found device: {device.name} with address: {device.address}")
                self.client = BleakClient(device)

                
                await self.client.connect()
                if self.client.is_connected:
                    print(f"Connected to {self.device_name}")
                    
                    paired = await self.client.pair(protection_level = 2) # this is crucial!!!
                    if not paired:
                        print(f"could not pair")
                    return True
                else:
                    print(f"Failed to connect to {self.device_name}")
        print(f"Device {self.device_name} not found.")
        return False
    
    #sends data
    async def send_data(self, data):
        global start_time
        if self.client is None:
            print("No BLE client connected.")
            return

        try:
            # Write the data to the characteristic
            await self.client.write_gatt_char(self.char_uuid, data)
            #print(f"Data written to characteristic {self.char_uuid}: {data}")
       
            elapsed_time_ms = (time.time() - start_time) * 1000
            #print(f"Timestamp: {elapsed_time_ms:.2f} ms", end=" ")
            #print(' '.join(f'{byte:02x}' for byte in data))

        except Exception as e:
            print(f"Failed to write data: {e}")

    #disconects hub
    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("Disconnected from the device")
    
    #hub Leds?
    LED_MODE_COLOR = 0x00
    LED_MODE_RGB = 0x01        

    #hub color
    async def change_led_color(self, colorID):
        if self.client and self.client.is_connected:
            await self.send_data(bytearray([0x08, 0x00, 0x81, self.ID_LED, self.IO_TYPE_RGB_LED, 0x51, self.LED_MODE_COLOR, colorID]))
    
    #set motor power
    async def motor_start_power(self, motor, power):
        if self.client and self.client.is_connected:
            await self.send_data(bytearray([0x08, 0x00, 0x81, motor&0xFF, self.SC_BUFFER_NO_FEEDBACK, 0x51, self.MOTOR_MODE_POWER, 0xFF&power]))

    #stops motor
    async def motor_stop(self, motor, brake=True):
        # motor can be 0x32, 0x33, 0x34
        if self.client and self.client.is_connected:
            await self.send_data(bytearray([0x08, 0x00, 0x81, motor&0xFF, self.SC_BUFFER_NO_FEEDBACK, 0x51, self.MOTOR_MODE_POWER, self.END_STATE_BRAKE if brake else 0x00]))  
    
    #calibrates steering
    async def calibrate_steering(self):
        await self.send_data(bytes.fromhex("0d008136115100030000001000"))
        #await asyncio.sleep(0.1)
        await self.send_data(bytes.fromhex("0d008136115100030000000800"))
        #await asyncio.sleep(0.1)

    #some form of driving
    async def drive(self, speed=0, angle=0, lights = 0x00):
        await self.send_data(bytearray([0x0d,0x00,0x81,0x36,0x11,0x51,0x00,0x03,0x00, speed&0xFF, angle&0xFF, lights&0xFF,0x00]))
        #await asyncio.sleep(0.1)

