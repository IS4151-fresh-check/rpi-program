import time
import math
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn

# --- CONFIGURATION ---
RL_VALUE = 1      # Load resistance in kilo-ohms (standard for MQ2 modules)
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

def calibrate_mq2():
    """Run this once in clean air at startup."""
    global ro
    print("MQ2 Calibrating... please wait (10s).")
    total_rs = 0
    for _ in range(10):
        total_rs += get_rs(channel.voltage)
        time.sleep(1)
    ro = (total_rs / 10) / RO_CLEAN_AIR_FACTOR
    print(f"MQ2 Calibration done! R0 = {ro:.2f} kOhm")
    return ro

def read_mq2():
    """Returns the gas levels and voltage as a dictionary."""
    v = channel.voltage
    rs = get_rs(v)
    ppm = get_ppm(rs, ro, LPG_CURVE)
    
    return {
        "gas_voltage": round(v, 3),
        "lpg_ppm": round(ppm, 2)
    }

# 3. Main Loop
if __name__ == "__main__":
    calibrate_mq2()
    try:
        while True:
            data = read_mq2()
            print(f"Voltage: {data['gas_voltage']}V | LPG: {data['lpg_ppm']} PPM")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped.")