import random
import serial
import scope
import TRS_TraceSet
# Si Gao 2017.11.21
# This is a general acquisition Python script: talk to the people in the hardcore lab if you need something more
# Please run the setup progamme and find out the appropriate parameters (trigger delay, sampling rate etc.)
# Noted the float acquisition MIGHT be more accurate, but is much slower than the short acquisition


# Print Hex Data
def PrintHexData(data):
    pdata = bytearray(data)
    rwdstr = pdata.hex().upper()
    # Insert spaces for between each 16-bits.
    dstr = ''
    i = 0
    while i in range(len(rwdstr)):
        dstr += rwdstr[i:i + 4] + ' '
        i += 4
    print(dstr)
    return


def main():
    # Serial port communication: look this up in 'device manager'
    port='COM4'                                                 # Serial port

    # Basic info about the target cipher
    #As the key is hard-coded in the encryption device, no need to take care of the key
    plain_len=16                                                # byte length of the plaintext
    cipher_len=16                                               # byte length of the ciphertext

    # Acquisition setup: find this setting through the capturing traces from the setup program
    num_of_traces=1000                                          # number of traces
    num_of_samples=50000                                        # number of samples
    sample_rate=250E6                                           # Sample Rate
    isshort=True                                                # Type of the samples: short or float
    vdiv=1.8E-2                                                 # Vertical resolution: V/div
    trg_delay = "-311.2US"                                      # Trigger delay: negative means post trigger (S)
    trg_level = "1V"                                            # Trigger level: start capture when trigger passes it
    isenc = True                                                # Perform encryption/decryption
    voffset="-11.4 mV"                                          # Vertical Offset

    # File name for the trace set file
    # For convenience, please add necessary information to the file name
    filename = 'SCALE_1000T_50000S_250MHz_AES_Int16.trs'        # Name of the TRS trace set file

    # In most common cases, you do not have to change anything below this line
    # Compute the setup parameters from above
    xscale=1/sample_rate                                        # sampling interval (s)
    duration=xscale*num_of_samples                              # sample duration (s)
    # For short type of acquisition, the captured trace is scaled in order to store in a 16 bit integer
    # yscale saves the scale value, in case you need to reconstruct the real traces
    # For float type of acquisition, the samples are exactly the real samples on the trace, so yscale=1
    if(isshort):
       yscale=vdiv/(65536/10.0)
    else:
        yscale=1
    timebase=str(xscale*num_of_samples/10)+"S"                  # timebase: s/div

    #Intiliazed random generator
    random.seed()
    #Open serial port
    ser=serial.Serial(port)
    #Open scope
    oscope    = scope.Scope()
    # setup the scope
    oscope.setup(str(vdiv)+"V",timebase,str(sample_rate/1E6)+"MS/s",str(duration)+"S",voffset)
    # set trigger
    oscope.set_trigger(trg_delay,trg_level)

    #Open Trace Set
    trs = TRS_TraceSet.TRS_TraceSet(filename)
    trs.write_header(num_of_traces,num_of_samples,isshort,plain_len+cipher_len,xscale,yscale)

    # Start acquisition
    for i in range(0,num_of_traces):
        # Generate random plaintext 
        plaintext = bytearray([random.getrandbits(8) for j in range (0,plain_len)])
        # start trigger
        if (oscope.start_trigger()==False):
            print("Triggering Error!")
            return
        # Send plaintext to the device
        ser.write(plaintext)
        # Read out ciphertext.
        ciphertext = bytearray(ser.read(cipher_len))
        # Get trace: if Lecroy has not stopped yet, discard this trace
        if(oscope.wait_for_trigger()==False):
            i=i-1;
            continue;
        trc=oscope.get_channel(num_of_samples,isshort,'C1')
        # Storing plaintext/ciphertext/trace
        trs.write_trace(plaintext,ciphertext,trc,isenc)
        # Print data
        if i%100==0:
            print("i="+str(i))
            print("plain=")
            PrintHexData(plaintext)
            print("cipher=")
            PrintHexData(ciphertext)
        else:
            pass
    # Close the serial port
    ser.close()
    # Close TRS file
    trs.close()
    return


if __name__ == '__main__':
    main()
