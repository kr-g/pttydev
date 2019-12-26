
# PTTYDev - Pseudo TTY Device

PTTYDev provides a common interface and enhanced timeout and automatic reconnection handling.
Using a pptydev enables your code to read input from a serial device or via websocket.

## Platform

Tested on ESP32, pyserial and MicroPython WebRepl

## Development status

Alpha state, 
The websocket device is __experimental__ and will fail when sending longer strings to micropython 

## Code

some code for opening micropython raw-repl


    from pttydev import *

    try:
        from dev_serial import *
        from dev_ws import *
        from dev_wsapp import *

    except:
        pass

    # open wrappers

    # a open function is required to reconnect properly the device in case of an error

    def get_pttyopen():

        port = '/dev/ttyUSB0' 
        baudrate = 115200
        bytesize = 8
        parity = 'N'
        stopbits = 1
        timeout = 0.25

        return pttyopen(port=port, baudrate=baudrate,
                        bytesize=bytesize, parity=parity, stopbits=stopbits,
                        timeout=timeout)

    def get_pttywsopen():
        return pttywsopen("ws://your-ip:8266","your-password")

    def get_pttywsappopen():    
        return pttywsappopen("ws://your-ip:8266","your-password")

    # the sample code

    def send_cntrl_c(ptty,timeout=1):
        ptty.reset_input_buffer()
        ptty.write([0x03,0x03])
        buf = []
        while True:
            r = ptty.readline(timeout=timeout)
            if r is None: # timeout
                break
            buf.append(r)
            if r.startswith(b'>>>'):
                break
        return buf
            
    def enter_raw_repl(ptty,timeout=1):
        ptty.write([0x01])
        r = ptty.readline(timeout=timeout)
        if r.startswith(b'raw REPL;'):
            r = ptty.read(1)
            if r == b'>':
                return True
        raise Exception("could not eneter raw-repl")

    def skipOK(ptty,timeout=1):
        print("skipOK")
        r = ptty.read(2,timeout=timeout)
        print("skipOK", r )
        if r!=b'OK':
            raise Exception("")
        return r

    def skip0x04(ptty,timeout=1):
        print("skip0x04")
        buf = bytearray()
        while True:
            ch = ptty.read(1,timeout=timeout) # this performs slow!
            if ch == b'\x04':
                break
            buf.extend(ch)
        return buf

    def send_cmd(ptty,cmd,handshake=True,echocmd=False,timeout=3):
        print("send_cmd")
        import textwrap
        cmd = textwrap.dedent( cmd )
        if echocmd:
            print(cmd)
        ptty.write(cmd.encode())
        ptty.write([0x04])
        if handshake:
            skipOK(ptty,timeout=timeout)
            data = skip0x04(ptty,timeout=timeout)
            err = skip0x04(ptty,timeout=timeout)
            r = ptty.read(1,timeout=timeout)
            if r != b'>':
                raise Exception("no prompt",data,err)
            return data,err


    def sample():
        
        """this sample code opens the ptty, performs some commands and follows the output"""
        
        tty = PseudoTTY(
                        # uncomment the part you want to test
                        #get_pttyopen,
                        get_pttywsopen,                    
                        #get_pttywsappopen,
                        
                        #thrd_reader=_the_thread_reader,
                        
                        timeout=0.35,
                        block_size=512,
                        reconnect_delay=1,
                        
                        debug=True,
                        #trace_on=True,                    
                        #thrd_debug=True,
                        thrd_trace_on=True
                        )

        with tty.open() as ptty:
            
            ptty.waitready() # raises PseudoTTYOpenException 
            
            print("ptty", ptty )
            
            try:
                
                send_cntrl_c(ptty)
                enter_raw_repl(ptty)
                
                r = send_cmd(ptty,"""
                        print('hello world!')
                    """)
                print( r )
     
                r = send_cmd(ptty,"""
                        import uos
                        print('12345')
                        print(uos.listdir())
                    """)
                print( r )

                r = send_cmd(ptty,"""
                        import uos
                        print('12345')
                        print(uos.listdir())
                    """,echocmd=True)
                print( r )

                r = send_cmd(ptty,"""
                        import uos
                        _m=False
                        _r=False
                        try:
                            uos.mkdir("test_dir")
                            _m=True
                        except:
                            pass
                        try:
                            uos.rmdir("test_dir")
                            _r=True
                        except:
                            pass
                        print(_m,_r)
                    """)
                print( r )

                r = send_cmd(ptty,"""
                        import json, machine, sys, network, ubinascii
                        _ids = { 'dummy': True }
                        _ids["unique_id"] = ubinascii.hexlify( machine.unique_id() )
                        _ids["platform"] = sys.platform
                        _ids["version"] = sys.version
                        print( json.dumps( _ids ) )
                    """,echocmd=True)
                print( r )

                try:
                    r = send_cmd(ptty, """
                            #
                            # long running task
                            #
                            for i in range(1,1000):
                                print(i)
                            #
                            """ , echocmd=True)                    
                    print( r )
                except Exception as e:
                    print("runtime error", ex )
                    print(type(ex))
                    print(ex.args)

                print("reset micropython")
                ptty.write([0x03,0x04]) # cntrl c and cntrl d 

                while True:                
                    # get the current size of available chars in the internal buffer
                    # if no crlf is in the buffer readline will not return content (or if timed out)
                    available = len(ptty) 
                    if available>0:
                        try:
                            r = ptty.readline(timeout=3)
                            print("main",r)
                        except PseudoTTYTimeoutException:
                            print("timeout")                       

            except KeyboardInterrupt as intr:
                print("user stop request", intr )        
            except Exception as ex:
                print("runtime error", ex )
                print(type(ex))
                print(ex.args)
                import traceback
                traceback.print_last()
            finally:
                print("close device")
            
        return
    

    if __name__=='__main__':
        print( "running", __name__ )
        sample()
        
    


