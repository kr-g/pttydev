
# https://github.com/websocket-client/websocket-client
#import websocket

from websocket import *
import socket
import time

    
class _WebSocket_Dev():
    
    """context wrapper for websocket device"""
    
    def __init__(self,ws,write_delay):
        self.ws = ws
        self.write_delay = write_delay
        
    def __enter__(self):
        return self
    
    def __exit__(self, exception_type, exception_value, traceback):
        import traceback
        print( exception_type, exception_value, traceback )
        self.ws.close()
        
    def read(self,size=1):
        r = None
        try:
            r = self.ws.recv()
        except WebSocketTimeoutException:
            pass
            #print("dev timeout")
        if r is None:
            return r
        try:
            return r.encode()
        except:
            return r
        
    def write(self,buf):
        #print("dev write", buf )
        
        wbtotal = 0
        
        for i in range(0, len(buf), 255):
            bslice = buf[i:min(i + 255, len(buf))]
            wb = self.ws.send(bslice)
            wbtotal += wb
            print("dev write slice", wb, len(bslice) )
            time.sleep(self.write_delay)
        
        print("dev write total", wbtotal, len(buf) )
        return wbtotal
    
    def flush(self):
        import os
        fd = self.ws.sock.fileno()
        #print("dev flush fd", self.ws.sock, fd)
              
   


def pttywsopen(url,password,timeout=3,write_delay=0.5):
    
    # a open function is required to reconnect properly the device in case of error
    #websocket.enableTrace(False)
   
    ws = create_connection(url,timeout=timeout,
                           sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 0),)
                                   )        
    r =  ws.recv()
    print("dev got", r )
    if r.find("Password:")>=0:
        ws.send(password+"\n")
    r = ws.recv()
    print("dev got", r )
    if r.find("WebREPL connected")>=0:
        ptty = _WebSocket_Dev(ws,write_delay)
        return ptty
    
    raise Exception( "wrong password, additional information", r)

