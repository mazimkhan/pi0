from rpi_lcd import LCD
from time import sleep

# Initialize the LCD
# If your i2cdetect showed a different address (e.g., 0x3f), 
# use: lcd = LCD(address=0x3f)
lcd = LCD(address=0x27)

line1="STEM Learn with us.    "
line2="Electronics, robotics, remote control, Python, Internet of Things, Gadgets and more    "

try:
    while True:
        # Clear the screen
        lcd.clear()
        
        # Display text on specific lines
        lcd.text(line1, 1, "left")  # Line 1
        lcd.text(line2, 2, 'left')
        
        sleep(0.10)
        
        front = line1[0]
        line1 = line1[1:] + front
        front = line2[0]
        line2 = line2[2:] + front
except KeyboardInterrupt:
    # Clear the screen before exiting
    lcd.clear()

