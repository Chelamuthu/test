import spidev
import RPi.GPIO as GPIO
import time
import serial
import pynmea2

# GPIO Pin Definitions for SX1262
PIN_CS = 8     # CE0
PIN_BUSY = 23
PIN_RST = 25
PIN_DIO1 = 24

# LoRa Constants
LORA_FREQ = 868000000  # Hz

# GNSS UART Port
GNSS_PORT = "/dev/ttyAMA0"
GNSS_BAUD = 9600

# Setup GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_CS, GPIO.OUT)
GPIO.setup(PIN_BUSY, GPIO.IN)
GPIO.setup(PIN_RST, GPIO.OUT)
GPIO.setup(PIN_DIO1, GPIO.IN)

# Setup SPI
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

# Reset SX1262
def reset():
    GPIO.output(PIN_RST, GPIO.LOW)
    time.sleep(0.01)
    GPIO.output(PIN_RST, GPIO.HIGH)
    time.sleep(0.01)

# Wait until SX1262 not busy
def wait_busy():
    while GPIO.input(PIN_BUSY) == 1:
        time.sleep(0.001)

# Write command
def write_cmd(cmd, data=[]):
    wait_busy()
    GPIO.output(PIN_CS, GPIO.LOW)
    spi.writebytes([cmd] + data)
    GPIO.output(PIN_CS, GPIO.HIGH)
    wait_busy()

# Transmit simple payload (manually)
def send_lora(payload):
    reset()
    write_cmd(0x80, list(payload.encode()))  # Write buffer
    write_cmd(0x83, [0x00, len(payload)])     # Set payload length
    write_cmd(0x8E, [0x00, 0x00, 0x00])       # Set TX timeout
    write_cmd(0x03, [])                       # Start TX

# GNSS setup
gps = serial.Serial(GNSS_PORT, GNSS_BAUD, timeout=1)

print("✅ GNSS + SX1262 LoRa Ready")

while True:
    try:
        line = gps.readline().decode("utf-8", errors="ignore").strip()
        if line.startswith("$GNRMC") or line.startswith("$GPRMC"):
            msg = pynmea2.parse(line)
            if msg.status == "A":
                lat = f"{msg.latitude:.6f}{msg.lat_dir}"
                lon = f"{msg.longitude:.6f}{msg.lon_dir}"
                msg_str = f"Lat:{lat}, Lon:{lon}"
                print("📤 Sending:", msg_str)
                send_lora(msg_str)
                time.sleep(5)
    except Exception as e:
        print("⚠️ Error:", e)
