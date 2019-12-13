from collections.abc import Sized
from threading import Thread
import time

from atomic import *


def peekone(buf,matching):
    pos = -1
    for m in matching:
        match = buf.find( m )
        if pos==-1 and match>=0:
            pos=len(buf)
        pos = min( pos, match )
    return pos

def peekone_r(buf,matching):
    pos = -1
    for m in matching:
        match = buf.rfind( m )
        pos = max( pos, match )
    return pos


class PseudoTTYException(Exception):
    def __init__(self,*args ):
        super().__init__(*args)
        
class PseudoTTYBufferException(Exception):
    pass

class PseudoTTYOpenException(Exception):
    pass

class PseudoTTYTimeoutException(Exception):
    pass


def _the_thread_reader( ptty ):
    
    ptty._print_d("thread startup")
    ptty.thrd_stat = 0 # thread starting
    
    while True:
        try:
            ptty._print_d("thread connecting")
            with ptty.pttyopen() as ptty_dev:
                
                ptty._print_d("thread connected", type(ptty_dev))
                ptty.dev = ptty_dev
                
                ptty.thrd_stat = 1 # device is open
                buf = bytearray()
                
                while True:
                    if ptty.status < 0:
                        ptty._print_d("thread shutdown")
                        ptty.thrd_stat = None
                        return
                    
                    stoptime = time.time()+0.1
                    readmax=1
                    while readmax>0 and time.time() < stoptime:
                        readmax-=1
                        cb = ptty_dev.read(ptty.block_size)
                        if cb is None:
                            #raise PseudoTTYTimeoutException("device timeout")
                            break # timeout
                        if len(cb)>0:
                            ptty._print_d("thread received serial", cb, debug=ptty._thrd_debug)
                            buf.extend(cb)
                        else:
                            break
                    
                    try:
                        ptty.addtoibuf( buf )
                        buf.clear()
                    except AtomicOwnerException:
                        ptty._print_d("skip serial read",debug=ptty._thrd_debug)
                                            
        except Exception as ex:
            ptty.dev = None
            ptty.dev_reconnect_count += 1
            ptty._print_d("reconnect", ex )
            import traceback
            traceback.print_exception(None, ex, ex.__traceback__)
            ptty.thrd_stat = 2 # device is reconnecting
            ptty._print_t("thread sleep between reconnect", trace=ptty._thrd_trace_on)
            time.sleep(ptty.reconnect_delay)
     
          
class _Open_Context():

    """context wrapper for ptty device"""

    def __init__(self,ptty):
        self.ptty = ptty

    def __enter__(self):
        self.ptty._open()
        return self.ptty

    def __exit__(self, exception_type, exception_value, traceback):
        self.ptty._close()
        

class PseudoTTY(Atomic,Sized):
    
    DEFAULT_READLINE_DELIMITER = [0x00,0x01,0x02,0x03,0x04,0x05,ord("\r"),ord("\n")]

    def __init__(self,pttyopen,
                 thrd_reader=_the_thread_reader,
                 timeout=0.1,
                 block_size=512,
                 reconnect_delay=1,
                 trace_on=False,debug=False,
                 thrd_trace_on=False,thrd_debug=False
                 ):
        
        super().__init__(trace_on=not True)
        
        self._ibuf = bytearray()
        
        self.timeout = timeout
        self.block_size = block_size
        self.pttyopen = pttyopen
        self.dev = None
        self.dev_reconnect_count = 0
        self.dev_reconnect_time = None
        
        self.status = 0
        self.reconnect_delay = reconnect_delay
        
        self.thrd_reader = thrd_reader #if thrd_reader != None else _the_thread_reader
        self.thrd = None
        self.thrd_stat = None
        self.thrd_timeout = self.timeout / 100
        
        self._main_trace_on = trace_on
        self._main_debug = debug
        self._thrd_trace_on = thrd_trace_on
        self._thrd_debug = thrd_debug

    #
    
    def _print_t( self, *args, trace=None ):
        if trace is None and self._main_trace_on:
            trace = True
        if trace:
             print("(trace)", *args )

    def _print_d( self, *args, debug=None ):
        if debug is None and self._main_debug:
            debug = True
        if debug:
             print("(debug)", *args )

    #
    
    def open(self):
        return _Open_Context(self)
    
    def _open(self):
        if self.thrd:
            raise( PseudoTTYOpenException("the device is already open") )
        self.thrd = Thread( None, _the_thread_reader, args=[self] )
        self.thrd_stat = None
        self.thrd.start()
    
    def _close(self):
        """close ptty thread down by setting status to -1"""
        if self.thrd is None:
            raise( PseudoTTYOpenException("the device is not open") )
        self.status = -1
        self.thrd.join()
        self.thrd = None
        
    def close(self):
        return self._close()
        
    # basic buffer functions
    
    @Atomic.LockFunc
    def reset_input_buffer(self):
        """clear the intenal buffer"""
        self._print_d("clr buffer",self._ibuf)
        self._ibuf.clear()
    
    @Atomic.LockFunc
    def addtoibuf(self,data):
        """add data to internal buffer"""
        self._ibuf.extend(data)

    @Atomic.LockFunc
    def getbufcopy(self):
        """get a copy of the internal buffer"""
        return bytearray(self._ibuf)
    
    @Atomic.LockFunc
    def available(self):
        """get amount of available chars to read from internal buffer"""
        return len(self._ibuf)

    def len(self):
        return self.available()
    
    def __len__(self):
        return self.len()

    # stream functions
    
    @Atomic.LockFunc
    def getch(self):
        """get one char from the stream"""
        try:
            return self._ibuf.pop(0)
        except IndexError:
            return None
        
    @Atomic.LockFunc
    def ungetch(self,ch):
        """unget/pushback one char to the stream"""
        self._ibuf.insert(0,ch)
    
    #

    def peek(self,s):
        """get the position of s within the internal buffer, or -1 if not found"""
        return self.getbufcopy().find(s)

    def peekone(self,matching):
        """find the first occurance of the matching set within the internal buffer, or -1 if not found"""
        return peekone(self._ibuf,matching)

    def peekone_r(self,matching):
        """find the first occurance of the matching set with the internal buffer (searching from the right), or -1 if not found"""
        return peekone_r(self._ibuf,matching)

    #
    
    def waitready(self,timeout=5):
        stop = time.time()+timeout 
        while time.time() < stop:
            if self.dev != None:
                return
            time.sleep(0.1)
        raise PseudoTTYOpenException("device not open")        
    
    #
    
    def write(self,buf):
        if self.dev is None:
            raise PseudoTTYOpenException("device not open")

        self._print_d("ptty write", buf )
        # we assume that the device sends the complete buffer
        wb = self.dev.write(buf)
        # wb might be different from len(buf)
        # eg. websocket will add frame to payload -> wb > len(buf)
        return wb

    def flush(self):
        if self.dev is None:
            raise PseudoTTYOpenException("device not open")
        self.dev.flush()

    @Atomic.LockFunc
    def _readibuf(self,size=1):
        """get chars from the internal buffer"""
        if len(self._ibuf) <= 0:
            r = self._ibuf
            self._ibuf.clear()
            return r
        
        r = self._ibuf[:size]
        self._ibuf = self._ibuf[size:]
        return r

    #             

    MAX_READ_DELAY=0.01

    def read(self,size=1,timeout=0):
        """read a defined length buffer from the internal buffer"""
        delta = max( self.timeout, timeout )
        stop = time.time() + delta
        delay = max(delta / 10, self.MAX_READ_DELAY)
        r = None
        while True:
            try:
                if size<=0:
                    r = self._readibuf(-1)
                elif len(self._ibuf)>=size:
                    r = self._readibuf(size)
                    self._print_d( "read", r )
                    return r 
            except AtomicOwnerException:
                self._print_t("skip read this loop, buffer locked by thread reader")
             
            if time.time() > stop :
                break
            
            self._print_t("delay read for", delay)
            time.sleep(delay)
            
        return r
            
    def readline(self,timeout=0,delimiter=DEFAULT_READLINE_DELIMITER,combine_crlf=True):
        """read one line from the internal buffer"""
        delta = max( self.timeout, timeout )
        stop = time.time() + delta
        delay = max(delta / 10, self.MAX_READ_DELAY)
        r = None
        while True:
            #print( self._ibuf )
            try:
                pos = self.peekone( delimiter )
                if pos >= 0:
                    r = self._readibuf(pos+1)
                    if r != None and len(r)>0:
                        if combine_crlf:
                            if r[-1:][0] == ord("\r"):
                                ch = self.getch()
                                if ch == ord("\n"):
                                    # add look-a-head
                                    r.append(ch)
                                else:
                                    # push back look-a-head
                                    self.ungetch(ch)                        
                    break
            except AtomicOwnerException:
                self._print_t("skip readline this loop, buffer locked by thread reader")                
            if time.time() < stop:
                self._print_t("delay readline for", delay)
                time.sleep(delay)
            else:
                break
                #raise PseudoTTYTimeoutException()
        if r!=None and len(r)>0:
            self._print_d( "readline", r )
        return r     
 
    def readlines(self,timeout=0,delimiter=DEFAULT_READLINE_DELIMITER,combine_crlf=True):
        delta = max( self.timeout, timeout )
        stop = time.time() + delta
        delay = max(delta / 10, self.MAX_READ_DELAY)
        buf = []
        while True:
            b = self.readline(timeout=timeout,delimiter=delimiter,combine_crlf=combine_crlf)
            if b is None:
                break
            buf.append(b)
            if time.time() < stop:
                self._print_t("delay readlines for", delay)
                time.sleep(delay)
            else:
                break
        return buf