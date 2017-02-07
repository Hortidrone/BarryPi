import serial
import time
import pynmea2
import bluetooth as BT
import os
import picamera 
import sys


def Bluetooth_Initial():

    BTsoc = BT.BluetoothSocket(BT.RFCOMM)
    BTPort = 1
    
    #print '=== Bluetooth: binding...'
    BTsoc.bind(("",BTPort))
    #print '=== Bluetooth: Binding done, Listenin...'
    BTsoc.listen(BTPort)
    BTconn, BTconnAddr = BTsoc.accept()
    #print "=== Bluetooth: Conn accepted from"+str(BTconnAddr)

    return (BTconn, BTsoc)

def Bluetooth_Receive(BTconn):
    try:
        BTconn.settimeout(0.05)
        BTrecvData = BTconn.recv(1024)
        BTconn.settimeout(0.0)
    except:
        BTrecvData = None
    return (BTrecvData)

def Bluetooth_Send(BTconn, message):
    #print "sending: "+str(message)
    BTconn.send(str(message))
    #print "done sending"

def Bluetooth_Close(BTconn, BTsoc):
    try:
        BTconn.close()
        BTsoc.close()
        succes = True
    except:
        succes = False

    return (succes)

def GPS_Initial():
    GPSser = serial.Serial("/dev/ttyACM1", 9600, timeout=3.0)
    return (GPSser)
    
def GPS_Read(GPSser,message):
    try:
        GPSser.flushInput()
    except:
        print " failed to flush memory"
    #GPSrecvData = GPSser.readline()
    try:
        GPSrecvData = GPSser.readline()
    except:
        GPSrecvData = None
        print " failed to read GPS stuff"
    print GPSrecvData
    try:
        GPSrecvData = pynmea2.parse(GPSrecvData)
        Lat = round(GPSrecvData.latitude, 8)
        Lon = round(GPSrecvData.longitude, 8)
        message += " GPS = T"
    except:
        Lat = float(0)
        Lon = float(0)
        message += " GPS = F"
    return (Lat, Lon, message)

def Eco_Initial():
    Ecoser = serial.Serial("/dev/ttyACM0", 115200, timeout=3.0)
    return (Ecoser)

def Eco_Read(Ecoser, message):
    Ecoser.flushInput()
    #EcorecvData = Ecoser.readline()
    EcorecvData = Ecoser.readline()
    print EcorecvData
    try:
        EcorecvData = EcorecvData.split(",")
        tem_Sensor = float(EcorecvData[0])
        hum_Sensor = float(EcorecvData[1])
        lum_Sensor = float(EcorecvData[2])
        co2_Sensor = float(EcorecvData[3])
        message += " Eco = T"
    except:
        tem_Sensor = float(0)
        hum_Sensor = float(0)
        lum_Sensor = float(0)
        co2_Sensor = float(0)
        message += " Eco = F"
    return(tem_Sensor, hum_Sensor, lum_Sensor, co2_Sensor, message)

def Camera_Initial():
    cam = picamera.PiCamera(resolution=(2592, 1944))
    cam.led = False
    cam.start_preview()
    time.sleep(2)
    cam.stop_preview()
    picNr = 1
    camFolder = CreateFolder()
    return (camFolder, picNr, cam)
    
    
def CreateFolder ():
    FolderString = "/media/usbdatastuff/Data/"+time.strftime("%d-%m-%Y_%H.%M.%S")
    i = 0
    FolderMade=False
    while FolderMade == False:
        if not os.path.exists(FolderString):
            os.makedirs(FolderString)
            FolderMade=True
        elif os.path.exists(FolderString):
            FolderString=FolderString+"-"+str(i)
            i+=1

    return (FolderString)

def Camera_run(camFolder, picNr, message, cam):
    try:
        picName = camFolder+("/picture_%04d" % picNr)+".jpg"
        cam.capture(str(picName))
        message += ' Pic = T'
        picNr += 1
    except:
        message += ' Pic = F'
        
    return (picName, picNr, message)

def Camera_Close(cam):
    cam.close()
    

def Create_File(camFolder):
    FolderString = camFolder
    if not os.path.exists(FolderString):
        FolderString = "/media/usbdatastuff/SensorDataFolderFail/"+time.strftime("%d-%m-%Y_%H.%M.%S")
        os.makedirs(FolderString)
    FileString = '/Sensor_Data.txt'
    return (str(FolderString)+str(FileString))

def Write_File(Lat, Lon, tem_Sensor, hum_Sensor, lum_Sensor, co2_Sensor, picName, FilePath, message):
    try:
        File = open(str(FilePath), "a")
        string = (str(Lat)+","+
                   str(Lon)+","+
                   str(tem_Sensor)+","+
                   str(hum_Sensor)+","+
                   str(lum_Sensor)+","+
                   str(co2_Sensor)+","+
                   str(picName)+"\n")
        File.write(string)
	File.close()
        message += " File = T"
	string_cons = "\n"+string
	sys.stdout.write(string_cons)
	sys.stdout.flush()
    except:
        message += " File = F"
    return (message)
    



#==== main ====#


BTconn, BTsoc = Bluetooth_Initial()
running = False

try:
    
    while 1:
        BTrecvData = Bluetooth_Receive(BTconn)
        if BTrecvData != None:
            if (BTrecvData == "start" and running != True):
                running = True
                GPSser = GPS_Initial()
                Ecoser = Eco_Initial()
                camFolder, picNr, cam = Camera_Initial()
                FilePath = Create_File(camFolder) 
            elif BTrecvData == "test":
                Camera_Close(cam)
                running = False
            elif BTrecvData == "close":
                os.system('sudo shutdown -P +1')
                break
            else:
                pass
                
        if running == True:
            message = "STATUS== "
            #print '0'
            Lat, Lon, message = GPS_Read(GPSser,message)
            #print '1'
            tem_Sensor, hum_Sensor, lum_Sensor, co2_Sensor, message = Eco_Read(Ecoser, message)
            #print '2'
            picName, picNr, message = Camera_run(camFolder, picNr, message, cam)
            #print '3'
            message = Write_File(Lat, Lon, tem_Sensor, hum_Sensor, lum_Sensor, co2_Sensor, picName, FilePath, message)
            #print '4'
            #Bluetooth_Send(BTconn, message)
            #print '5'

finally:
    succes = Bluetooth_Close(BTconn, BTsoc)
    if succes == True:
    	print "YEAAHHH!!!!"


