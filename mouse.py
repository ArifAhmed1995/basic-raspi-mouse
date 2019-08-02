import time
from threading import Thread 
 
import pyautogui 
 
import RPi.GPIO as GPIO 
 
pyautogui.FAILSAFE = False 
 
GPIO.setmode(GPIO.BCM) 
 
# Pins for charge and discharge of the capacitor 
x_a_pin = 17 
x_b_pin = 23 
 
y_a_pin = 24 
y_b_pin = 25 
 
# Pins to listen for left and right click 
left_click_pin = 21 
right_click_pin = 20 
 
# Important to set the set the pull down resistor otherwise infinite clicks happen 
GPIO.setup(left_click_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
GPIO.setup(right_click_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) 
 
# Subclass of Thread to return the charge time taken by the capacitor 
class ChargeTimeThread(Thread): 
    def __init__(self, group=None, target=None, name=None, 
                 args=(), kwargs={}, verbose=None): 
        Thread.__init__(self, group, target, name, args, kwargs) 
        self._return = None 
 
    def run(self): 
        if self._target is not None: 
            self._return = self._target(*self._args, **self._kwargs) 
     
    def join(self, *args): 
        # Once thread finishes then return the value 
        Thread.join(self, *args) 
        return self._return 
 
# Switch the pins and give time for capacitors to discharge. 
def discharge(): 
    # Two capacitors. One for X-axis and other for Y. 
    GPIO.setup(x_a_pin, GPIO.IN) 
    GPIO.setup(x_b_pin, GPIO.OUT) 
    GPIO.output(x_b_pin, False) 
 
    GPIO.setup(y_a_pin, GPIO.IN) 
    GPIO.setup(y_b_pin, GPIO.OUT) 
    GPIO.output(y_b_pin, False) 
 
    # For a 100 microFarad capacitor this was enough time to discharge. 
    time.sleep(0.001) 

# create time function for capturing analog count value
def x_charge_time():
    # Switch the pins and measure time taken for capacitor to charge up.
    GPIO.setup(x_b_pin, GPIO.IN)
    GPIO.setup(x_a_pin, GPIO.OUT)
    
    x_charge_t = 0
    
    GPIO.output(x_a_pin, True)
    while not GPIO.input(x_b_pin):
        x_charge_t += 1
    return x_charge_t

def y_charge_time():
    GPIO.setup(y_b_pin, GPIO.IN)
    GPIO.setup(y_a_pin, GPIO.OUT)
    
    y_charge_t = 0
    
    GPIO.output(y_a_pin, True)
    while not GPIO.input(y_b_pin):
        y_charge_t += 1
    return y_charge_t

# Some corrections to be done after getting counts from the charge time functions.
def xy_correction(x, y):
    x_max = 170
    x_min = 0
    x -= 50
    y -= 50
    y_max = 170

    if x > x_max:
        x = x_max
    if y > y_max:
        y = y_max

    x /= x_max

    if y_max == 0:
        y = 0
    else:
        y /= y_max

    return x, y

def get_coords():
    discharge()
    # Disharge and run separate threads for measuring charge times.
    # This has to be done on separate threads because charging of both capacitors
    # are independent and start immediately. Hence, we cannot measure one after another.
    rx = ChargeTimeThread(target=x_charge_time)
    ry = ChargeTimeThread(target=y_charge_time)
    rx.start()
    ry.start()

if __name__ == "__main__":
    prev_x = 0
    prev_y = 0
    screen_x, screen_y = pyautogui.size()
    screen_x = screen_x * 2
    screen_y = screen_y * 2
    try:
        while True:
            # Mouse movement
            x, y = get_coords()
            x, y = xy_correction(x, y)
            x = screen_x * x
            y = screen_y * y
            if abs(x - prev_x) < 5 and abs(y - prev_y) < 5:
                pyautogui.moveTo(x, y)
            prev_x = x
            prev_y = y

            # Mouse click
            if GPIO.input(left_click_pin):
                pyautogui.click(button='left')

            if GPIO.input(right_click_pin):
                pyautogui.click(button='right')
    except KeyboardInterrupt:
        GPIO.cleanup()
