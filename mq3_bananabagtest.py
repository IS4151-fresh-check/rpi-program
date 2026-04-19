import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import time
import math

R0_VALUE = 0.076 # different for every node sensor

spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D5)
mcp = MCP.MCP3008(spi, cs)
chan = AnalogIn(mcp, MCP.P0)

A_MGL = 0.4       # Curve constant to get mg/L
B_MGL = -1.45     # Curve exponent
CONVERSION_FACTOR = 530

print(f"Starting Banana Test with R0: {R0_VALUE}")
def read_mq3():
    v_out = chan.voltage
    if v_out <= 0:
        return {"gas_voltage": 0, "lpg_ppm": 0}

    # VC=5.0V, RL=10kOhm
    rs = ((5.0 - v_out) / v_out) * 10.0
    ratio = rs / R0_VALUE

    mg_l = A_MGL * math.pow(ratio, B_MGL)

    ppm = mg_l * CONVERSION_FACTOR

    return {
        "gas_voltage": round(v_out, 3),
        "lpg_ppm": round(ppm, 2)
}