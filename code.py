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

# adafruit pm25 particle sensor
reset_pin = None
from adafruit_pm25.i2c import PM25_I2C


# Get wifi details and more from a secrets.py file
print("Importing secrets")
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
print("WiFi Connect")
wifi.radio.connect(secrets["ssid"], secrets["password"])

# Create an instance of the Adafruit IO HTTP client
aio_username = secrets["ADAFRUIT_IO_USERNAME"]
aio_key = secrets["ADAFRUIT_IO_KEY"]
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

# Initialize an Adafruit IO HTTP API object
io = IO_HTTP(aio_username, aio_key, requests)

# Create library object, use 'slow' 100KHz frequency!
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)

# set up bme680
bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c, debug=False)

# change this to match the location's pressure (hPa) at sea level
bme680.sea_level_pressure = 1015.58

# adafruit pm25 particle sensor
pm25 = PM25_I2C(i2c, reset_pin)

# battery sensor
sensor = LC709023F(i2c)
time.sleep(5)

print("Starting Loop")
while True:
    #print(".")
    try:
        # Get the 'temperature' feed from Adafruit IO
        bme680_temp_feed = io.get_feed("bme680-temp")
        bme680_pressure_feed = io.get_feed("bme680-pressure")
        bme680_gas_feed = io.get_feed("bme680-gas")
        bme680_humidity_feed = io.get_feed("bme680-humidity")
        battery_feed = io.get_feed("outdoor-battery")
        pm25_03um_feed = io.get_feed("particles-03um")
        pm25_05um_feed = io.get_feed("particles-05um")
        pm25_10um_feed = io.get_feed("particles-10um")
        pm25_25um_feed = io.get_feed("particles-25um")
        pm25_50um_feed = io.get_feed("particles-50um")
        pm25_100um_feed = io.get_feed("particles-100um")

    #except AdafruitIO_RequestError:
    #    # If no 'temperature' feed exists, create one
    #    print("Could not get feeds")
    #    sys.print_exception(e)
    #    continue

    except AdafruitIO_RequestError as e:
        sys.print_exception(e)
        continue

    try:
        aqdata = pm25.read()
       # print(aqdata)
    except RuntimeError:
        aqdata = 0
        print("Unable to read from sensor, retrying...")
        continue

    bme_temp_f =(((bme680.temperature/ 5)*9) +32)

    print("Uploading to Adafruit IO")
    try:
        io.send_data(battery_feed["key"], sensor.cell_percent)
        io.send_data(bme680_temp_feed["key"], (((bme680.temperature/ 5)*9) +32))
        io.send_data(bme680_pressure_feed["key"], bme680.pressure)
        io.send_data(bme680_humidity_feed["key"], bme680.humidity)
        io.send_data(bme680_gas_feed["key"], bme680.gas)
        io.send_data(pm25_03um_feed["key"], aqdata["particles 03um"])
        io.send_data(pm25_05um_feed["key"], aqdata["particles 05um"])
        io.send_data(pm25_10um_feed["key"], aqdata["particles 10um"])
        io.send_data(pm25_25um_feed["key"], aqdata["particles 25um"])
        io.send_data(pm25_50um_feed["key"], aqdata["particles 50um"])
        io.send_data(pm25_100um_feed["key"], aqdata["particles 100um"])
        print("Done.")
    except RuntimeError:
        print("Unable to post to IO, retrying...")
        continue
    inc_count = inc_count + 1
    print(inc_count)
    time.sleep(30)
