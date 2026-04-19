import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import time

spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D5)
mcp = MCP.MCP3008(spi, cs)
chan = AnalogIn(mcp, MCP.P0) 

RL = 10.0 
VC = 5.0  
CLEAN_AIR_RATIO = 60.0 

print("Starting 30-minute Calibration in Empty Bag...")
rs_sum = 0
samples = 0

try:
    # Run for 1800 seconds
    for i in range(1800):
        v_out = chan.voltage
        if v_out > 0:
            rs = ((VC - v_out) / v_out) * RL
            rs_sum += rs
            samples += 1
        
        if i % 60 == 0:
            print(f"Minute {i//60} / 30...")
        time.sleep(1)

    average_rs = rs_sum / samples
    r0 = average_rs / CLEAN_AIR_RATIO
    
    print(f"R0 value: {round(r0, 4)}")

except KeyboardInterrupt:
    print("\nCalibration Aborted.")