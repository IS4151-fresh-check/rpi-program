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
LPG_CURVE = [2.3, 0.45, -0.35] 

# 1. Setup SPI and MCP3008
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D5)
mcp = MCP.MCP3008(spi, cs)
channel = AnalogIn(mcp, MCP.P0)

def get_rs(voltage):
    """Calculate sensor resistance Rs from voltage."""
    if voltage < 0.1: return 100.0
    if voltage > 4.9: return 0.01
    
    # NEW FORMULA: RS = RL * (Vcc - Vout) / Vout
    # This ensures that as Voltage RISES, RS DROPS, and PPM INCREASES.
    return ((5.0 - voltage) / voltage) * RL_VALUE

def get_ppm(rs, ro, curve):
    ratio = rs / ro
    if ratio <= 0: ratio = 0.001
    ppm_log = ((math.log10(ratio) - curve[1]) / curve[2]) + curve[0]
    return math.pow(10, ppm_log)

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