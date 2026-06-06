# pi0
Raspberry Pi Zero 2 Experiments

## Installation
### Write image to SD card
Install Raspberry Pi OS lite using the [Raspberry Pi Imager App](https://www.raspberrypi.com/software/). Follow these instructions:
 - Select Device Raspberry Pi Zero
 - Select Raspberry Pi OS (other) and then select Raspberry Pi OS Lite (32-bit)
 - Insert the SD card in the laptop socket and it should appear in imager UI. Select it and press next
 - Type host name, for example `mypizero0`
 - Enter localization info, for example time zone and keyboard layout
 - Enter user and password. Tip: use a simple and memorizable user/password. For example: pi/raspberry. Do not use too short password otherwise installation will fail
 - Skip wifi setup
 - Enable SSH and enable password authentication
 - Skip/uncheck Raspberry Pi Connect
 - Click Write
 - Once finished, take out and insert again
 - Open bootfs in explorer or Mac Finder

### Enable serial console
 - Open `<root>/bootfs/cmdline.txt` and add `modules-load=dwc2,g_serial` after `rootwait` attribute in the kernel command line
 - Open `<root>/bootfs/config.txt` and at the bottom under section `[all]` add line `dtoverlay=dwc2`
 - Edit `<root>/bootfs/user-data` to add following lines to the end
```
runcmd:
  - systemctl enable --now getty@ttyGS0.service

```
and update password line to (encrypted text for "raspberry")
```
  passwd: "$y$jB5$r.XJiF3K5ZaP9doJYNaOi/$37FKecXQB00JAdZaT.PZ3vgnZyfvhOfn1eTBWqee6/0"
```
 - Unmount the SD card and take it out.
 - Insert the SD card in the raspberry pi, connect a micro USB in the port that is not marked as power(PWR) and connect other end of the USB cable to a laptop.
 - Wait for the serial port (for example `COM4`) to appear in the device manager
 - On first boot the serial port may go and come back couple of times and may not respond in the serial app like putty. Please have patience

## Setting up the WiFi
Run `sudo nmtui` and follow textual UI for selecting the network and entring password. Test connection by pinging `ping www.google.com`.

## Blinky/LED/Output test
Connect a LED with 220ohm resistor to PIN 3 and to ground. Create a Python file with following code
```Python
import time
from gpiozero import OutputDevice

led = OutputDevice(3)  # GPIO Pin 3

while True:
    led.on()
    time.sleep(1)
    led.off()
    time.sleep(1)

```
Copy file on pi and run with following command
```
python3 blinky.py
```
This should turn the LED On and Off at 1 second interval.

## Button/Input test
Reading button input

```py
import time
from gpiozero import InputDevice

inp = InputDevice(14)

while True:
    if inp.value:
        print("Button Pressed")
    else:
        print("Button Off")
    time.sleep(0.25)
```

## Button/Input test
Following command demonstrates interfacing an input for example a button

```py
import time
from gpiozero import OutputDevice, InputDevice

out = OutputDevice(3)
inp = InputDevice(14)

while True:
    if inp.value:
        out.on()
    else:
        out.off()
    time.sleep(0.25)
```
