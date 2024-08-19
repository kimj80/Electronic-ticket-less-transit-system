
import RPi.GPIO as GPIO
import time

# RED LED PIN
RED_LED_PIN = 26
# GREEN LED PIN
GREEN_LED_PIN = 12

def setup_LEDs():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RED_LED_PIN,GPIO.OUT)
    GPIO.setup(GREEN_LED_PIN,GPIO.OUT)


def flash_led(colour):

    flash_count = 8 # Number to times to flash LED's
    delay = 0.15

    if(colour == "G" or colour == "g" or colour == "green"):
        PIN = GREEN_LED_PIN
    else: PIN = RED_LED_PIN

    # GPIO.setup(PIN,GPIO.OUT)

    for x in range(flash_count):
        # LED ON
        GPIO.output(PIN,GPIO.LOW)
        time.sleep(delay)
        # LED OFF
        GPIO.output(PIN,GPIO.HIGH)
        time.sleep(delay*0.8)

if __name__ == "__main__":

    setup_LEDs()

    flash_led("red")
    flash_led("green")

