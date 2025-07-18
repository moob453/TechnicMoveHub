#example made by moob453

from legohub import movehub2
from time import sleep

def main():
     
     hub = movehub2()
     hub.connect(4)
     hub.led("red")
     hub.motor('motor_A', 'speed', 100)
     hub.motor('motor_b', 'speed', -100)
     sleep(4)

if __name__ == "__main__":
    main()


