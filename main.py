#example made by moob453

from legohub import movehub2
from time import sleep

def main():
     
     hub = movehub2()
     hub.connect(2)
     hub.set_led_color("red")
     sleep(1)
     hub.set_led_color("green")
     sleep(1)
     hub.set_led_color("blue")
     sleep(2)
     hub.disconnect()

if __name__ == "__main__":
    main()


