import random
import serial
import scope
import TRS_TraceSet
# Si Gao 2017.12.5
# This is a Python script send/receive data through COM port
# It keeps sending until interrupted by keyboard
# Use the "single" triggering mod of the oscilloscope to capture one trace
# Figure out the trace you want and keeps the setup parameters for the actual acquisition


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

    #Intiliazed random generator
    random.seed()
    #Open serial port
    ser=serial.Serial(port)

    i=0;
    # Start sending
    while(True):
        # Generate random plaintext
        plaintext = bytearray([random.getrandbits(8) for j in range (0,plain_len)])

        # Send plaintext to the device
        ser.write(plaintext)
        # Read out ciphertext.
        ciphertext = bytearray(ser.read(cipher_len))
        # Print data
        if i%100==0:
            print("i="+str(i))
            print("plain=")
            PrintHexData(plaintext)
            print("cipher=")
            PrintHexData(ciphertext)
        else:
            pass
        i=i+1;
    # Close the serial port
    ser.close()
    return


if __name__ == '__main__':
    main()