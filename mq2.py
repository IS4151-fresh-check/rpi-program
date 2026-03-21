import time
import math
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# --- CONFIGURATION ---
RL_VALUE = 5      # Load resistance in kilo-ohms (standard for MQ2 modules)
RO_CLEAN_AIR_FACTOR = 9.83  # RS/R0 ratio in clean air (from datasheet)

# LPG curve constants: [log(x), log(y), slope]
# Derived from datasheet: log(y) = m * log(x) + b
LPG_CURVE = [2.3, 0.45, -0.47] 

# 1. Setup SPI and MCP3008
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D5)
mcp = MCP.MCP3008(spi, cs)
channel = AnalogIn(mcp, MCP.P0)

def get_rs(voltage):
    """Calculate sensor resistance Rs from voltage."""
    if voltage == 0: return 0
    return ((3.3 - voltage) / voltage) * RL_VALUE

def get_ppm(rs, ro, curve):
    """Calculate PPM using the log-log curve formula."""
    return math.pow(10, (((math.log10(rs/ro) - curve[1]) / curve[2]) + curve[0]))

# 2. Calibration (Run this in CLEAN AIR)
print("Calibrating... please wait.")
total_rs = 0
for _ in range(50):
    total_rs += get_rs(channel.voltage)
    time.sleep(1)
ro = (total_rs / 50) / RO_CLEAN_AIR_FACTOR
print(f"Calibration done! R0 = {ro:.2f} kOhm")

# 3. Main Loop
try:
    while True:
        rs = get_rs(channel.voltage)
        ppm = get_ppm(rs, ro, LPG_CURVE)
        
        print(f"Voltage: {channel.voltage:.2f}V | LPG: {ppm:.2f} PPM")
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopped.")