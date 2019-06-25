import time
import numpy as np
import matplotlib.pyplot as plt
import seabreeze.spectrometers as sb
from multiprocessing import Process, Lock
import serial
import sys
try:
    bb.shutdown()
except:
    pass
class beamBlock:
    def __init__(self,comport='COM1'):
        """
        Initialized hardware with a closed shutter
        """
        self.ser = serial.Serial(comport,9600,timeout=1,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS)
        self.ser.write('mode=0\r'.encode())
        self.ser.read(20)
        if self.qopenShutter():
            self.toggleShutter()
        
    def toggleShutter(self):
        """
        toggles the state of the shutter
        """
        jump = self.ser.write('ens\r'.encode())
        self.ser.read(size=jump+2)
        
    def qopenShutter(self):
        """
        Checks if shutter is open
        """
        jump = self.ser.write('ens?\r'.encode())
        #print(jump)
        self.ser.read(size=jump)
        res = self.ser.read()
        self.ser.read(size=3)
        #print(res)
        if  res == b'1':
            return True
        elif res == b'0':
            return False
        else:
            print('Something\'s amiss, killing it...')
            self.shutdown()
            #self.__init__()
    
    def qcloseShutter(self):
        """
        checks if shutter is closed
        """
        return not self.qopenShutter()
    
    def openShutter(self):
        """
        opens shutter, if closed
        """
        if not self.qopenShutter():
            self.toggleShutter()
    
    def closeShutter(self):
        """
        closes shutter if closed
        """
        if self.qopenShutter():
            self.toggleShutter()
        
    def shutdown(self):
        """
        closes the serial connection. MUST EXICUTE BEFORE CALLING ANOTHER 
        INSTANCE OF THIS CLASS, otherwise you need restart your kernel.
        """
        self.ser.close()
#%%
def specDump(it,file,l,ls):
#    it = 20#ms
    try:
        s = sb.Spectrometer(sb.list_devices()[0])
    except:
        print("Something's off with spectrometer...")
    s.integration_time_micros(it*1000)
    f = open(file,"w")
    f.write(",".join([str(time.time())]+[str(x) for x in s.wavelengths()])+'\n')
    j = 0
    ls.release()
    while j<100000 and not l.acquire(False):
        t = time.time()
        f.write(",".join([str(t)]+[str(int(x)) for x in s.intensities()])+'\n')
        j += 1
    f.close()
def timePull(file="test.txt"):
    f = open(file)
    t = [float(l.split(",")[0]) for l in f]
    f.close()
    return np.array(t)
def timebbPull(file="test.txt"):
    f = open(file)
    l = f.readline()
    t = np.array([float(i) for i in l.split(",")])
    f.close()
    return np.array(t)
def specPull(file="test.txt"):
    f = open(file)
    t = [[float(ii) for ii in l.strip('\n').split(",")[1:]] for l in f]
    f.close()
    return np.transpose(t)
#%
if __name__ == "__main__":
    try:
        file = sys.argv[1]
    except IndexError:
        file = "temp"
    #-----------------
    # Edit Here
    #-----------------
    it = 50#ms
    bleachTime=30#sec
    recoveryTime=100#sec
    sampleNum = 20
    lamStart = 540#nm
    #------------------
    # \Edit Here
    #------------------
    onTime=4*it/1000#sec
    offTime=(recoveryTime/sampleNum)-onTime#sec
    
    f = open('temp.log',"w")
    bb = beamBlock()
    bb.closeShutter()
    l = Lock()
    ls = Lock()
    l.acquire(False)
    ls.acquire(False)
    p = Process(target=specDump, args=(it,"temp.dat",l,ls))
    print("Running...")
    p.start()
    #What for file writting to begin
    ls.acquire()
    #Mark Start
    f.write(str(time.time()))
    #wait
    time.sleep(1)
    #Bleach
    bb.openShutter()
    f.write(","+str(time.time()))
    time.sleep(bleachTime)
    #Recovery
    for i in range(sampleNum):
        #Close Shutter
        f.write(","+str(time.time()))
        bb.closeShutter()
        time.sleep(offTime)
        #Open Shutter
        bb.openShutter()
        f.write(","+str(time.time()))
        time.sleep(onTime)
    #Stop measurement
    f.write(","+str(time.time()))
    bb.closeShutter()
    time.sleep(2*it/1000)
    #Stop acquisition
    l.release()
    f.close()
    p.join()
    print("Done")
    t = timePull("temp.dat")
    tbb = timebbPull("temp.log")
    tbbO = tbb[1::2]
    tbbC = tbb[1+1::2]
    spec = specPull("temp.dat")
    fig = plt.figure(figsize=(15,5))
    ax = fig.add_subplot(111)
    for ii in range(len(tbbO)):
        mask = np.array([tt>tbbO[ii]+it/1000 and tt<tbbC[ii] for tt in t[1:]])
        maskl = np.array([lam>lamStart for lam in spec[:,0]])
        plt.plot((t[1:]-t[0])[mask],np.sum(spec[maskl,1:][:,mask],axis=0)-np.sum(spec[maskl,1]),".")
#    ax.set_ylim(bottom=0)
    ylim = ax.get_ylim()
    #plt.vlines(tbb-t[0],*ylim)
    ax.set_ylim(ylim)
    plt.xlabel("Time (sec)")
    plt.ylabel("Integrate Counts")
    plt.yscale("log")
    plt.show()
    print(len(t))
    print("IT_th  = {0:.1f} ms".format(it))
    print("IT_exp = {0:.1f}+-{1:.1f} ms".format(np.mean(np.diff(t[1:])*1000),np.std(np.diff(t[1:])*1000)))
    print("BBTimes:",tbb[1:]-tbb[0])
    f = open(file+".csv","w")
    f.write("Integration Time={:.0f} ms\n".format(it))
    f.write("Bleaching Time={:.0f} s\n".format(bleachTime))
    f.write("Total Recovery Time={:.0f} s\n".format(recoveryTime))
    f.write("Bright Time={:.3f} s\n".format(onTime))
    f.write("Dark Time={:.3f} s\n".format(offTime))
    f.write("Recovery Samples={:.0f}\n".format(sampleNum))
    f.write("#Beam Block opening times\n")
    f.write(",".join(["{:.4f}".format(tt-t[0]) for tt in tbbO])+"\n")
    f.write("#Beam Block closing times\n")
    f.write(",".join(["{:.4f}".format(tt-t[0]) for tt in tbbC])+"\n")
    f.write("#Measurements: time, wavelegnth1,  wavelegnth2, ... \n")
    mask = np.full(len(spec[0,:])-1,True)
    s2 = np.transpose(spec)
    l = "{:.4f},".format(t[0]-t[0])
    l += ",".join(["{:.3f}".format(jj) for jj in s2[0]])
    l += "\n"
    f.write(l)
    for ii in range(1,len(s2)):
        e = False
        for iii in range(len(tbbO)):
            e = e or (t[ii]>tbbO[iii]+it/1000 and t[ii]<tbbC[iii])
        e = e or t[ii]<tbbO[0]-it/1000
        if e:
            l = "{:.4f},".format(t[ii]-t[0])
            l += ",".join(["{:.0f}".format(jj) for jj in s2[ii]])
            l += "\n"
            f.write(l)
    f.close
