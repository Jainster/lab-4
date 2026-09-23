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
    except Exception as e:
        print("Instrument on USB port [" + str(i) + "] cannot be connected. "
              "It may be powered off, or it may not be an instrument.")
        print("Error:", e)

# %%
# Open the power supply. Never assume it is there.

if power_supply_id == -1:
    print("Power supply is not powered on or not connected to the PC.")
    raise SystemExit

if oscilloscope_id == -1:
    print("Oscilloscope is not powered on or not connected to the PC.")
    raise SystemExit

if digital_multimeter_id == -1:
    print("Digital multimeter is not powered on or not connected to the PC.")
    raise SystemExit

print("Power supply is connected to the PC.")
print("Oscilloscope is connected to the PC.")
print("Digital multimeter is connected to the PC.")

power_supply = device_manager.open_resource(devices[power_supply_id])
oscilloscope = device_manager.open_resource(devices[oscilloscope_id])
digital_multimeter = device_manager.open_resource(devices[digital_multimeter_id])

# %%
# Sweep the voltage and measure what the supply actually delivers.
#
# The applied and measured voltages agree only while the supply is in constant
# voltage mode. If the circuit demands more current than the limit allows, the
# supply drops into constant current mode and the measured voltage falls below
# the one you asked for. That is why we measure instead of assuming.

output_voltage = np.arange(0, 8.1, .1)

def power_err_check():
    error = power_supply.query("SYStem:ERRor?").strip()
    if not error.startswith("+0") and not error.startswith("0"):
        print("Power supply error:", error)
    return error

def oscilloscope_err_check():
    error = oscilloscope.query("SYStem:ERRor?").strip()
    if not error.startswith("+0") and not error.startswith("0"):
        print("Oscilloscope error:", error)
    return error

def multimeter_err_check():
    error = digital_multimeter.query("SYStem:ERRor?").strip()
    if not error.startswith("+0") and not error.startswith("0"):
        print("Multimeter error:", error)
    return error


measured_current = np.array([])
diode_voltage = np.array([])

power_supply.write("OUTPUT ON")
power_err_check()

digital_multimeter.write("CONF:CURR:DC .1")
multimeter_err_check()

print()
print("Starting sweep...")
print()

for v in output_voltage:
    power_supply.write("APPLy P25V, %0.2f, 0.03" % v)
    power_err_check()

    time.sleep(0.05)

    a = float(oscilloscope.query(
        "MEASure:VAVerage? DISPlay,CHANnel1"))
    oscilloscope_err_check()

    b = float(oscilloscope.query(
        "MEASure:VAVerage? DISPlay,CHANnel2"))
    oscilloscope_err_check()

    ab = a - b

    current = float(digital_multimeter.query("READ?"))
    multimeter_err_check()

    diode_voltage = np.append(
        diode_voltage, ab)

    measured_current = np.append(
        measured_current, current)

    print("Applied: %0.2f V | CH1: %0.5f V | CH2: %0.5f V | "
          "Diode: %0.5f V | Current: %0.6f A"
          % (v, a, b, ab, current))

print()
print("Sweep complete.")

power_supply.write("OUTPUT OFF")
power_err_check()

power_supply.close()
oscilloscope.close()
digital_multimeter.close()

print("Power supply output OFF.")
print("All instruments closed.")

# %%
plt.figure()
plt.plot(diode_voltage, measured_current)
plt.title("Diode I-V Characteristic")
plt.xlabel("Diode Voltage [V]")
plt.ylabel("Measured current [A]")
plt.grid(True)

plt.show()