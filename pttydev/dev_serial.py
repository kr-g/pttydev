
import serial # its pyserial


def pttyopen(**kwargs):
    
    # a open function is required to reconnect properly the device in case of error
    
    ser = serial.Serial(**kwargs)
    
    return ser

