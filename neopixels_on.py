import serial, time
arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(5)
arduino.write("white")