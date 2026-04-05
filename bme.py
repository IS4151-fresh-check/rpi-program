import board
import busio
import adafruit_bme280

# Create I2C object
i2c = busio.I2C(board.SCL, board.SDA)

# Create BME280 object
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

def read_bme280():
    return{
        "temperature": round(bme280.temperature, 2),
        "humidity": round(bme280.humidity, 2),
    }