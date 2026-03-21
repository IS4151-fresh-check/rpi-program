import board
import busio
import adafruit_bme280

# Create I2C object
i2c = busio.I2C(board.SCL, board.SDA)

# Create BME280 object
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

# Print values
print(f"Temperature: {bme280.temperature:.2f} C")
print(f"Humidity: {bme280.humidity:.2f} %")
print(f"Pressure: {bme280.pressure:.2f} hPa")