import spidev
import RPi.GPIO as GPIO
import time

# --- SPI setup ---
spi = spidev.SpiDev()
spi.open(0, 0)   # Bus 0, Device 0 (CE0)
spi.max_speed_hz = 5000000

# --- GPIO setup ---
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# SX1262 pins (check your board’s docs)
RESET_PIN = 17
BUSY_PIN = 18
DIO1_PIN = 4   # IRQ pin connected to DIO1

GPIO.setup(RESET_PIN, GPIO.OUT)
GPIO.setup(BUSY_PIN, GPIO.IN)
GPIO.setup(DIO1_PIN, GPIO.IN)

# --- Reset LoRa module ---
def reset_lora():
    GPIO.output(RESET_PIN, GPIO.LOW)
    time.sleep(0.05)
    GPIO.output(RESET_PIN, GPIO.HIGH)
    time.sleep(0.05)
    print("LoRa module reset done")

# --- IRQ handler ---
def checkReceiveDone(channel):
    print("IRQ received on DIO1! Packet available.")

def enable_irq():
    # Remove any old detection first
    GPIO.remove_event_detect(DIO1_PIN)

    # Attach new edge detection
    GPIO.add_event_detect(DIO1_PIN, GPIO.RISING, 
                          callback=checkReceiveDone, 
                          bouncetime=100)
    print("IRQ interrupt enabled")

# --- Main ---
reset_lora()
enable_irq()

print("Waiting for LoRa packets... Press CTRL+C to stop.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
    spi.close()
    print("Exiting...")
