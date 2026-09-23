# -*- coding: utf-8 -*-
"""
ECE 437 - Lab 4 example
Sweep the DC power supply across the test diode circuit and record the
supplied voltage and current at each step.

If an instrument beeps and shows an error, it will ignore everything you send
afterwards. Clear it with:   power_supply.write("*CLS")
"""

import time
import numpy as np
import matplotlib.pyplot as plt
import pyvisa as visa

# %%
# Find every instrument on the USB bus and work out which is which.
#
# The match below looks for the MODEL NUMBER inside the *IDN? string rather
# than comparing the whole string. Full-string matching breaks the moment an
# instrument is swapped or its firmware is updated.

device_manager = visa.ResourceManager()
devices = device_manager.list_resources()
number_of_device = len(devices)

power_supply_id       = -1
waveform_generator_id = -1
digital_multimeter_id = -1
oscilloscope_id       = -1

for i in range(0, number_of_device):
    try:
        device_temp = device_manager.open_resource(devices[i])
        idn = device_temp.query("*IDN?")
        print("Instrument on USB port [" + str(i) + "] is " + idn.strip())

        if "E3631A" in idn:
            power_supply_id = i
        elif "33511B" in idn:
            waveform_generator_id = i
        elif "34461A" in idn:
            digital_multimeter_id = i
        elif "MSO-X 3024T" in idn:
            oscilloscope_id = i

        device_temp.close()
    except Exception:
        print("Instrument on USB port [" + str(i) + "] cannot be connected. "
              "It may be powered off, or it may not be an instrument.")

# %%
# Open the power supply. Never assume it is there.

if power_supply_id == -1:
    print("Power supply is not powered on or not connected to the PC.")
    raise SystemExit
else:
    print("Power supply is connected to the PC.")
    power_supply = device_manager.open_resource(devices[power_supply_id])

# %%
# Sweep the voltage and measure what the supply actually delivers.
#
# The applied and measured voltages agree only while the supply is in constant
# voltage mode. If the circuit demands more current than the limit allows, the
# supply drops into constant current mode and the measured voltage falls below
# the one you asked for. That is why we measure instead of assuming.

output_voltage    = np.arange(0,8.1,.1)
def err_check():
    print(power_supply.query("SYStem:ERRor?"))

measured_voltage  = np.array([])
measured_current  = np.array([])

power_supply.write("OUTPUT ON")
err_check()

for v in output_voltage:
    # APPLy <channel>, <volts>, <current limit in amps>
    power_supply.write("APPLy P25V, %0.2f, 0.03" % v)
    err_check()

    # Let the supply settle before reading. See post lab question 3.
    time.sleep(0.05)

    measured_voltage = np.append(
        measured_voltage, float(power_supply.query("MEASure:VOLTage:DC? P25V")))
    measured_current = np.append(
        measured_current, float(power_supply.query("MEASure:CURRent:DC? P25V")))

power_supply.write("OUTPUT OFF")
err_check()
power_supply.close()      # always close, or the next run cannot connect


# %%
plt.figure()
plt.plot(output_voltage, measured_current)
plt.title("Applied volts vs. measured supplied current")
plt.xlabel("Applied volts [V]")
plt.ylabel("Measured current [A]")
plt.grid(True)

plt.figure()
plt.plot(measured_voltage, measured_current)
plt.title("Measured voltage vs. measured supplied current")
plt.xlabel("Measured voltage [V]")
plt.ylabel("Measured current [A]")
plt.grid(True)

plt.show()
