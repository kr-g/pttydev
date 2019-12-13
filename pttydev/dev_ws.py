
# https://github.com/websocket-client/websocket-client
#import websocket

from websocket import *
import socket

    
class _WebSocket_Dev():
    
    """context wrapper for websocket device"""
    
    def __init__(self,ws):
        self.ws = ws
        
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
        wb = self.ws.send(buf)
        #print("dev write", wb, len(buf) )
        return wb
    
    def flush(self):
        import os
        fd = self.ws.sock.fileno()
        #print("dev flush fd", self.ws.sock, fd)
              
   


def pttywsopen(url,password,timeout=3):
    
    # a open function is required to reconnect properly the device in case of error
    #websocket.enableTrace(False)
   
    ws = create_connection(url,timeout=timeout,
                           #sockopt=((socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),)
                                   )        
    r =  ws.recv()
    print("dev got", r )
    if r.find("Password:")>=0:
        ws.send(password+"\n")
    r = ws.recv()
    print("dev got", r )
    if r.find("WebREPL connected")>=0:
        ptty = _WebSocket_Dev(ws)
        return ptty
    
    raise Exception( "wrong password, additional information", r)

