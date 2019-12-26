
# https://github.com/websocket-client/websocket-client
#import websocket

import websocket

from threading import Thread
    
import time
from collections import deque

    
class _WebSocketApp_Dev():
    
    """context wrapper for websocket app device"""
    
    def __init__(self,passwd,timeout=3,debug=False,trace=False, debug_msg=False):
        self.debug = debug
        self.debug_msg = debug_msg
        self.trace = trace
        
        self.passwd = passwd
        self.timeout = timeout
        self.ws = None
        self.buf = deque()
        self.readbuf = bytearray()
        
        self.connected = None
        
    def print_d(self,*args):
        if self.debug:
            print("(debug)",*args)
            
    def print_t(self,*args):
        if self.trace:
            print("(trace)",*args)
    
    
    def __enter__(self):
        self.print_t("enter")
        return self
    
    def __exit__(self, exception_type, exception_value, traceback):
        self.print_t("exit")
        self.close()
       
       
    def close(self):
        self.print_t("close")
        self.ws.keep_running = False

    def clearbuf(self):
        self.readbuf.clear()
        self.buf.clear()
                
    def on_connect(self,status):
        self.print_t("on_connect", status)
        self.connected = status
        if status:
            self.clearbuf()

    def pull(self,size=-1):
        self.print_t("pull")
        
        try:
            while size==-1 or size>0:
                if size>0:
                    size-=1
                ch = self.buf.popleft()
                self.readbuf.append( ch )
                # peek ahead
                while ch in [0x00,0x01,0x02,0x03,0x04,0x05,ord("\r"),ord("\n")]:            
                    ch = self.buf.popleft()
                    if ch in  [0x00,0x01,0x02,0x03,0x04,0x05,ord("\r"),ord("\n")]:
                        self.readbuf.append( ch )
                    else:
                        self.buf.appendleft(ch)
                        return
                        
        except IndexError:
            pass

    def read(self,size=-1):
        self.print_t("read")
        
        self.pull(size)
        
        r = bytearray(self.readbuf)
        self.readbuf.clear()
        
        self.print_d("read", r )
        
        return r if len(r)>0 else None
    
    def write(self,buf):
        self.print_t("write")
        
        wb = self.ws.send(buf)
        return wb

    def flush(self):
        self.print_t("flush")
        
        pass

    # ws app plumbing
    
    def on_message(self, message):
        if self.debug_msg or self.trace:
            print("(incoming)","on_message", message.encode())    
        self.buf.extend(message.encode())
        
    def on_error(self, err):
        self.print_t("on_error",err)
        self.ws.keep_running = False

    def on_close(self):
        self.print_t("on_close")
        self.on_connect( ws, False )

    def on_open(self):
        self.print_t("on_open")
        
        def login(*args):
                    
            time.sleep(1)
            r = self.read()            
            self.print_d("open", r)
            
            self.write( self.passwd + "\n")            
            time.sleep(1)
            r = self.read()
            self.print_d("open", r)
            
            connected = False
            
            if r == b'\r\n':
                r = self.read()
                self.print_d("open", r)
                if r == b'WebREPL connected\r\n':
                    r = self.read(4)
                    self.print_d("open", r)
                    
                    connected = ( r == b'>>> ' )
                    
            self.on_connect( connected )
            
        # start logon task
        connectionThread = Thread( None, login, args=[] )
        connectionThread.start()
        return connectionThread


    def loop(self):
        
        def run_app(*args):
            r = self.ws.run_forever()
            self.print_d( "ws app finished with", r )
             
        loopThread = Thread( None, run_app, args=[] )
        loopThread.start()
        
        return loopThread


def pttywsappopen(url,passwd,timeout=3, debug=False, trace=False, debug_msg=False):
    
    wsapp = _WebSocketApp_Dev(passwd=passwd,debug=debug,trace=trace,debug_msg=debug_msg)
    wsapp.ws = websocket.WebSocketApp(url, 
                                on_message = wsapp.on_message,
                                on_error = wsapp.on_error,
                                on_close = wsapp.on_close,
                                on_open = wsapp.on_open,
                                )
    # start thread loop
    thrd = wsapp.loop()
    
    while wsapp.connected is None:
        if debug:
            print( "waiting for connection" )
        time.sleep( 0.5 )
    
    return wsapp


if __name__ == "__main__":
     
    url, passwd = "ws://192.168.178.21:8266","123456"
     
    with pttywsappopen( url, passwd, debug=True, trace=True, debug_msg=False ) as wsapp:    
        time.sleep(7)    
        print("request shutdown of all threads")
        
    