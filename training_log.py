#import paramiko #for establishing a ssh connection
import time
import RPi.GPIO as GPIO # import GPIO
from hx711 import HX711 # import the class HX711

#This is a script that reads the data of the hangboard, writes it in a file and sends the data to another
#machine if the data collection is finished.

#Fuctions
def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])

#Additional variables
time_start_training = 0
time_start_pause = time.time() 
time4print = time_start_pause
weight_old = 0
weight_treshold = 40000 #in grams 
#Ask the user which training he is doing, open a new file and write it to the header
selection = input("Please select which training you are doing. There are following options: \n Maximal Strength (1), Strength Endurance (2)\n")
if selection == '1':
    title = 'Maximum Strength'
else:
    title = 'Strength Endurance'

filename = 'testdata_' + time.strftime("%m_%d_%H_%M_%S", time.gmtime()) + '.txt'
file = open(filename,"w")
header = title + ' on ' + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + '\n\n'
file.write(header)
#file.write("Das ist ein Test \n")
#file.write("Und das ist ein zweiter Test")

try:                                                                                                                
    GPIO.setmode(GPIO.BCM)  # set GPIO pin mode to BCM numbering                                                    
    # Create an object hx which represents your real hx711 chip                                                     
    # Required input parameters are only 'dout_pin' and 'pd_sck_pin'                                                
    hx = HX711(dout_pin=5, pd_sck_pin=6)                                                                            
    # measure tare and save the value as offset for current channel                                                 
    # and gain selected. That means channel A and gain 128                                                          
    err = hx.zero()                                                                                                 
    # check if successful                                                                                           
    if err:                                                                                                         
        raise ValueError('Tare is unsuccessful.')                                                                   
                                                                                                                    
    reading = hx.get_raw_data_mean()                                                                                
    if reading:  # always check if you get correct value or only False                                              
        # now the value is close to 0                                                                               
        print('Data subtracted by offset but still not converted to units:',                                        
              reading)                                                                                              
    else:                                                                                                           
        print('invalid data', reading)                                                                              
                                                                                                                    
    # In order to calculate the conversion ratio to some units, in my case I want grams,                            
    # you must have known weight.                                                                                   
    input('Hold the crimp on the hangboard you wanna train on. Calibration is started in 10 seconds after you have pressed ENTER')
    countdown_ref = time.time()
    timeforprint = countdown_ref
    while (time.time() - countdown_ref) < 10:
        if(time.time() - timeforprint  >=1):
            print(str(10 - int(time.time()-countdown_ref)))
            timeforprint = time.time()
        #time.sleep(10)
    reading = hx.get_data_mean()                                                                                    
    if reading:                                                                                                     
        print('Mean value from HX711 subtracted by offset:', reading)                                               
        known_weight_grams = input(                                                                                 
            'Write the weigth you used for calibration (bodyweight) in gram  and press ENTER: ')
        try:
            value = float(known_weight_grams)
            print(value, 'grams')
        except ValueError:
            print('Expected integer or float and I have got:',
                  known_weight_grams)

        # set scale ratio for particular channel and gain which is
        # used to calculate the conversion to units. Required argument is only
        # scale ratio. Without arguments 'channel' and 'gain_A' it sets
        # the ratio for current channel and gain.
        ratio = reading / value  # calculate the ratio for channel A and gain 128
        hx.set_scale_ratio(ratio)  # set ratio for current channel
        print('Ratio is set.')
    else:
        raise ValueError('Cannot calculate mean value. Try debug mode. Variable reading:', reading)

    # Read data several times and return mean value
    # subtracted by offset and converted by scale ratio to
    # desired units. In my case in grams.
    print("Now, data will be read and written to the text file in an infinite loop. To exit press 'CTRL + C'")
    #input('Press Enter to start the session')
    print('Session starting...Hang on to continue. Be strong! ')
    while True:
        weight = hx.get_weight_mean(15)
        current_time = time.strftime("%H:%M:", time.gmtime())
        if(weight > weight_treshold and  weight_old < weight_treshold):
            time_start_training = time.time()
            print("TRAINING")

        if(weight > weight_treshold):
            print("Hang time:","%.2f" % float(time.time()-time_start_training), '\t','Weight: ', int(weight/1000), 'kg')

        if(weight < weight_treshold and weight_old > weight_treshold):
            time_start_pause = time.time()
            print("RECOVERY")

        if(weight < weight_treshold and time_start_training is not 0):
            seconds = time.time() - time_start_pause
            if(time.time() - time4print >= 1):
                print("Paused time: ",str(int(seconds/60)),':',str(int(seconds%60)))
                time4print = time.time()

        weight_old = weight

        seconds = time.time()%60
        milliseconds = seconds*1000
        # + str(int((time.time()%60)*1000)) +
        str_2_write = str(truncate(weight,2)) +  ' ' + current_time + str(int(seconds)) + '.'+ str(int(milliseconds%1000)) + '\n'
        file.write(str_2_write)

except (KeyboardInterrupt, SystemExit):
    print('Bye :)')

finally:
    GPIO.cleanup()



#All the data recording is done, now close the file and send it to the remote machine 
file.close()

#establish an ssh connection to remote machine
#ssh = paramiko.SSHClient()
#ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#ssh.connect('pc', username='joschua')
#sftp = ssh.open_sftp() 
#sftp.put('/home/pi/hangboard/my_code/testdata.txt','/home/joschua/from_hangboard/data.txt')

#sftp.close()
#ssh.close() 
#my_sftp_object = create_connection('pc', 'joschua','/home/joschua/from_hangboard')


