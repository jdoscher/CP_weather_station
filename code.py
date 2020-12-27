import time
import board
from digitalio import DigitalInOut, Direction, Pull
import displayio
import terminalio
import busio

# internets
import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests

# battery guage
from adafruit_lc709203f import LC709023F

# adafruit bme680
import adafruit_bme680

# adafruit IO
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError

# Get Wi-Fi details and more from a secrets.py file
print("Importing secrets")
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Timeout between sending data to Adafruit IO, in seconds
IO_DELAY = 30

# Setup HTS221 Temp & Humidity Sensor
i2c = busio.I2C(board.SCL, board.SDA)

# set up bme680
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)

# change this to match the location's pressure (hPa) at sea level
bme680.sea_level_pressure = 1015.58

# battery sensor
sensor = LC709023F(i2c)

# Network / Wi-Fi Setup
while not wifi.radio.ap_info:
  try:
    wifi.radio.connect(secrets['ssid'], secrets['password'])
  except Exception as e:
    print("Could not connect to AP, retrying: ", e)
    continue
# Print Wi-Fi connection information
print(
  "Connected to Wi-Fi:\n\nSSID:\t\t{SSID}\nBSSID:\t\t{BSSID}\nChannel:\t{CHANNEL}\nIP:\t\t{IP}\nHOSTNAME:\t{HOSTNAME}".format(
    SSID = str(wifi.radio.ap_info.ssid, "utf-8"),
    BSSID = ':'.join('%02x' % (b) for b in wifi.radio.ap_info.bssid),
    CHANNEL = str(wifi.radio.ap_info.channel),
    IP = str(wifi.radio.ipv4_address),
    HOSTNAME = wifi.radio.hostname
  )
)

# Create an instance of the Adafruit IO HTTP client
aio_username = secrets["ADAFRUIT_IO_USERNAME"]
aio_key = secrets["ADAFRUIT_IO_KEY"]
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

# Initialize an Adafruit IO HTTP API object
io = IO_HTTP(aio_username, aio_key, requests)

# Main Loop
print("Here goes!")
while True:
    print("Intializing feeds")
    try:
        # Initialize Feeds
        bme680_temp_feed = io.get_feed("bme680-temp")
        bme680_pressure_feed = io.get_feed("bme680-pressure")
        bme680_gas_feed = io.get_feed("bme680-gas")
        bme680_humidity_feed = io.get_feed("bme680-humidity")
        battery_feed = io.get_feed("outdoor-battery")
    except AdafruitIO_RequestError as e:
        sys.print_exception(e)
    continue

    print ("Uploading data.")
    try:
        bme_temp_f =(((bme680.temperature/ 5)*9) +32)
        io.send_data(battery_feed["key"], sensor.cell_percent)
        io.send_data(bme680_temp_feed["key"], (((bme680.temperature/ 5)*9) +32))
        io.send_data(bme680_pressure_feed["key"], bme680.pressure)
        io.send_data(bme680_humidity_feed["key"], bme680.humidity)
        io.send_data(bme680_gas_feed["key"], bme680.gas)
    except RuntimeError:
        print("Could not POST to IO.  Retrying...")
    continue
    time.sleep(IO_DELAY)

