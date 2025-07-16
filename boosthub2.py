import os, sys
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import pygame
import asyncio
from bleak import BleakScanner, BleakClient
import time