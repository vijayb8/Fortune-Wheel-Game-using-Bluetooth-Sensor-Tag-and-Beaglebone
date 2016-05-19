#!/usr/bin/env python
# Michael Saunby. April 2013
#
# Notes.
# pexpect uses regular expression so characters that have special meaning
# in regular expressions, e.g. [ and ] must be escaped with a backslash.
#
#   Copyright 2013 Michael Saunby
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import pexpect
import sys
import time
from sensor_calcs import *
import json
import select
from PyQt4 import QtGui , QtCore
from PyQt4.Qt import QTextEdit
from PyQt4.Qt import pyqtSignal
import sys , time
from PyQt4.QtCore import pyqtSlot,SIGNAL,SLOT
from PyQt4.QtGui import QDialog, QApplication, QPushButton, QLineEdit, QFormLayout, QStatusBar, QMessageBox
from array import *

def twos_comp(val, bits):
        #"""compute the 2's compliment of int value val"""
        if( (val&(1<<(bits-1))) != 0 ):
            val = val - (1<<bits)
        return val

def floatfromhex(h):
    t = float.fromhex(h)
    if t > float.fromhex('7FFF'):
        t = -(float.fromhex('FFFF') - t)
        pass
    return t
#def operation(x) : 
#  print "hello from call before assignment" 
#  decel = decel + x 
#  print "hello from call after assignment" 
#  print decel 
#  return
class SensorTag:

    def __init__( self, bluetooth_adr ):
        self.n = 0
        self.con = pexpect.spawn('gatttool -b ' + bluetooth_adr + ' --interactive')
        self.con.expect('\[LE\]>', timeout=600)
        print "Preparing to connect. You might need to press the side button..."
        self.con.sendline('connect')
        # test for success of connect
	self.con.expect('Connection successful.*\[LE\]>')
        # Earlier versions of gatttool returned a different message.  Use this pattern -
        #self.con.expect('\[CON\].*>')
        self.cb = {}
        return
        
        self.con.expect('\[CON\].*>')
        self.cb = {}
        return

    def char_write_cmd( self, handle, value ):
        # The 0%x for value is VERY naughty!  Fix this!
        cmd = 'char-write-cmd 0x%02x 0%x' % (handle, value)
        print cmd
        self.con.sendline( cmd )
        return

    def char_read_hnd( self, handle ):
        self.con.sendline('char-read-hnd 0x%02x' % handle)
        self.con.expect('descriptor: .*? \r')
        after = self.con.after
        rval = after.split()[1:]
        return [long(float.fromhex(n)) for n in rval]

    def register_cb( self, handle, fn ):
        self.cb[handle]=fn;
        return

    # Notification handle = 0x0025 value: 9b ff 54 07
    def notification_loop( self ):
        #while True:
            #self.n = self.n +1
	    try:
              pnum = self.con.expect('Notification handle = .*? \r', timeout=10)
            except pexpect.TIMEOUT:
              print "TIMEOUT exception!"
              #break
	    if pnum==0:
                after = self.con.after
	        hxstr = after.split()[3:]
                handle = long(float.fromhex(hxstr[0]))
            	#try:
	        if True:
                  self.cb[handle]([long(float.fromhex(n)) for n in hxstr[2:]])
            	#except:
                #  print "Error in callback for %x" % handle
                #  print sys.argv[1]
                pass
            else:
               print "TIMEOUT!!"
        #pass

barometer = None
datalog = sys.stdout
acceleration = 0.0
angleEstimate = 0
timeRem = 0
flag = False

class notificationLoop(QtCore.QThread):

    angleSignal = pyqtSignal(int)
    timeSignal = pyqtSignal(int)
    speedSignal = pyqtSignal(str)
    recordSignal = pyqtSignal(int)
	
    def __init__(self):
    	super(notificationLoop,self).__init__()
    	print "init completed"
	self.angle=0.0
	self.count=0
    def __del__(self):
    	self.wait()

    def run(self):
    	global datalog
    	global barometer
	global flag


    	bluetooth_adr = sys.argv[1]
    	#data['addr'] = bluetooth_adr
    	if len(sys.argv) > 2:
        	datalog = open(sys.argv[2], 'w+')

    	while True:
     		try:   
      			print "[re]starting.."

      			tag = SensorTag(bluetooth_adr)
      			cbs = SensorCallbacks(bluetooth_adr)

      			# enable TMP006 sensor
      			#tag.register_cb(0x25,cbs.tmp006)
      			#tag.char_write_cmd(0x29,0x01)
      			#tag.char_write_cmd(0x26,0x0100)

      			# enable accelerometer
      			tag.register_cb(0x2d,cbs.accel)
      			tag.char_write_cmd(0x31,0x01)
      			tag.char_write_cmd(0x2e,0x0100)

      			# enable humidity
      			#tag.register_cb(0x38, cbs.humidity)
      			#tag.char_write_cmd(0x3c,0x01)
      			#tag.char_write_cmd(0x39,0x0100)

      			# enable magnetometer
      			#tag.register_cb(0x40,cbs.magnet)
      			#tag.char_write_cmd(0x44,0x01)
      			#tag.char_write_cmd(0x41,0x0100)

      			# enable gyroscope
      			tag.register_cb(0x57,cbs.gyro)
      			tag.char_write_cmd(0x5b,0x01)
      			tag.char_write_cmd(0x58,0x0100)

      			# fetch barometer calibration
      			#tag.char_write_cmd(0x4f,0x02)
      			#rawcal = tag.char_read_hnd(0x52)
      			#barometer = Barometer( rawcal )
      			# enable barometer
      			#tag.register_cb(0x4b,cbs.baro)
      			#tag.char_write_cmd(0x4f,0x01)
      			#tag.char_write_cmd(0x4c,0x0100)

			#self.angleSignal.emit(100)
			#self.timeSignal.emit(36)
			#self.speedSignal.emit('10')


      			while True:
				if(flag):
					self.count+=1
					tag.notification_loop()
					self.angle += angleEstimate 
					self.angleSignal.emit(self.angle)
					self.timeSignal.emit(timeRem)
					self.speedSignal.emit(str(abs(acceleration)))
					if(angleEstimate <= 5 and self.count>75):
						flag=False
						self.recordSignal.emit(self.angle)
						self.angle=0
						self.count=0
							

      			print "hello"
      			tag.con.sendline('disconnect')
      			tag.con.sendline('exit')
     		except:
      			pass
	

class SensorCallbacks:

    data = {}

    def __init__(self,addr):
        self.data['addr'] = addr
        self.decelerate = 0
        self.decel = 0
        self.stoptime = 0 
        self.index = 0
        self.filter = [0,0,0,0,0,0,0,0,0,0]
        self.filtersum = 0 
        self.filterdecel = 0
    def tmp006(self,v):
        objT = (v[1]<<8)+v[0]
        ambT = (v[3]<<8)+v[2]
        targetT = calcTmpTarget(objT, ambT)
        self.data['t006'] = targetT
        print "T006 %.1f" % targetT

    def accel(self,v):
	global acceleration
	global timeRem
        (xyz,mag) = calcAccel(v[0],v[1],v[2])
        self.data['accl'] = xyz
        self.decelerate = (xyz[1] + 0.15625 - self.decel)*9.8
        self.decel = xyz[1] + 0.15625 
        if self.gyro > 10 :
          if self.decelerate != 0:
            self.stoptime = (abs(self.decel)*9.8) / 0.926 #abs(self.decelerate)
            self.remDistance = ((self.decel)*9.8)**2 / 0.926 #(2 * abs(self.decelerate))
            self.remRotations = self.remDistance / (2 *3.14*0.19)
          print "estimated stop time",self.stoptime
          print "estimated distance left",self.remDistance 
          print "estimated rotations left",self.remRotations
	  timeRem = int(self.stoptime)
           
        elif self.gyro <= 10:
          self.stoptime = 0
          self.remDistance = 0 
          self.remRotations = 0 
          self.decel = 0 
          self.decelerate = 0 
          print "Please rotate the wheel for estimations" 
        print "ACCL", (xyz[1]+.15625)*9.8
	acceleration = (xyz[1]+.15625)*9.8

    def humidity(self, v):
        rawT = (v[1]<<8)+v[0]
        rawH = (v[3]<<8)+v[2]
        (t, rh) = calcHum(rawT, rawH)
        self.data['humd'] = [t, rh]
        print "HUMD %.1f" % rh

    def baro(self,v):
        global barometer
        global datalog
        rawT = (v[1]<<8)+v[0]
        rawP = (v[3]<<8)+v[2]
        (temp, pres) =  self.data['baro'] = barometer.calc(rawT, rawP)
        print "BARO", temp, pres
        self.data['time'] = long(time.time() * 300);
        # The socket or output file might not be writeable
        # check with select so we don't block.
        (re,wr,ex) = select.select([],[datalog],[],0)
        if len(wr) > 0:
            datalog.write(json.dumps(self.data) + "\n")
            datalog.flush()
            pass

    def magnet(self,v):
        x = (v[1]<<8)+v[0]
        y = (v[3]<<8)+v[2]
        z = (v[5]<<8)+v[4]
        xyz = calcMagn(x, y, z)
        self.data['magn'] = xyz
        print "MAGN", xyz

    def gyro(self,v):
	global angleEstimate
	dx = (((  (v[1]<<8) | v[0] ) /(65536.0/ 1000.0)) - 2.0)*4.35
        self.gyro = dx - 4.0
        print self.gyro
	angleEstimate = self.gyro


class Example(QtGui.QWidget):

	
	def __init__(self):
    		super(Example,self).__init__()
		self.maxSpeed=0
    		self.UI()
    	def UI(self):
		self.name_array = []
		self.speed_array = []
		self.fortune_array = []
		self.ctdown=5
    		self.setWindowTitle('Revolving Circle')
    		self.setGeometry(700,700,600,600)
    		layout=QtGui.QGridLayout(self)
    		self.button=QtGui.QPushButton('Start')
		self.button2=QtGui.QPushButton('show')
		self.button3=QtGui.QPushButton('Reset')
		self.button4=QtGui.QPushButton('Init')
		self.timer=QtGui.QLCDNumber()
		self.timer.display('0')
		layout.addWidget(self.timer,0,0)

		title = QtGui.QLabel('Name')
        	Speed = QtGui.QLabel('Speed')
        	Fortune = QtGui.QLabel('Fortune')

		self.speedDisplay = QtGui.QLabel(self)
		self.fortuneDisplay = QtGui.QLabel(self)
		self.speedDisplay.setText('0')				
		self.titleEdit = QtGui.QLineEdit()

        	layout.addWidget(title, 1, 0)
        	layout.addWidget(self.titleEdit, 1, 1)

        	layout.addWidget(Speed, 2, 0)
		layout.addWidget(self.speedDisplay, 2, 1)

        	layout.addWidget(Fortune, 3, 0)
        	layout.addWidget(self.fortuneDisplay, 3, 1)
		self.fortuneDisplay.setText("Wait for it")
        
    		view=QtGui.QGraphicsView()
    		self.scene=QtGui.QGraphicsScene()
    		view.setScene(self.scene)
    		layout.addWidget(view,0,1)
    		layout.addWidget(self.button,4,1)
    		layout.addWidget(self.button2,4,2)
    		layout.addWidget(self.button3,4,0)
		layout.addWidget(self.button4,3,2)
    		self.show()
		self.connect(self.button2, SIGNAL("clicked()"),self.button_click_show)
		self.connect(self.button3, SIGNAL("clicked()"),self.button_click_reset)
    		self.button.clicked.connect(self.startNew)
		self.button4.clicked.connect(self.initProcess)
		
    		circle=QtGui.QGraphicsEllipseItem(150,250,200,200)
    		self.scene.addItem(circle)

		self.linH=QtCore.QLineF(QtCore.QPointF(350,350),QtCore.QPointF(150,350))
    		self.lineH=QtGui.QGraphicsLineItem()
    		self.lineH.setLine(self.linH)
    		self.scene.addItem(self.lineH)

		self.linV=QtCore.QLineF(QtCore.QPointF(250,250),QtCore.QPointF(250,450))
    		self.lineV=QtGui.QGraphicsLineItem()
    		self.lineV.setLine(self.linV)
    		self.scene.addItem(self.lineV)

    		self.lin=QtCore.QLineF(QtCore.QPointF(250,350),QtCore.QPointF(150,350))
    		self.line1=QtGui.QGraphicsLineItem()
    		self.line1.setLine(self.lin)
    		self.scene.addItem(self.line1)
    		self.threadpool=[]
    		self.thread=notificationLoop()
	def initProcess(self):
		self.thread.start()
		self.thread.angleSignal.connect(self.changeAngle)
		self.thread.timeSignal.connect(self.changeTime)
		self.thread.speedSignal.connect(self.changeSpeed)
		self.thread.recordSignal.connect(self.recordData)  	
    	def startNew(self):
		global flag
		flag = True
		self.maxSpeed=0
		self.titleEdit.setEnabled(False)
		self.fortuneDisplay.setText("Wait for it...")
		self.lin.setAngle(0)
    		self.line1.setLine(self.lin)
    		#self.connect(self.thread,QtCore.SIGNAL('update(QString)'),self.changeAngle)		    			
    	def changeAngle(self,theta):
    		self.lin.setAngle(int(theta))
    		self.line1.setLine(self.lin)
    		print "degree: ",theta
    		self.scene.update()
	def changeTime(self,timeRem):			
		self.timer.display(timeRem)
	def changeSpeed(self,speed):
		if(float(str(speed)) > self.maxSpeed):			
			self.maxSpeed = float(str(speed))
			self.speedDisplay.setText(speed)
		print "Hello at change speed"
	def recordData(self,totAngle):
		print totAngle
		self.fDis=""
		if(totAngle%360 <= 90):
			self.fDis = "You will be hungry again in one hour"
		elif(totAngle%360 > 90 and totAngle%360 <= 180):
			self.fDis = "Love is on the horizon"
		elif(totAngle%360 > 180 and totAngle%360 <= 270):
			self.fDis = "Beaglebone has chosen you as the Beer sponsor!"
		elif(totAngle%360 > 270 and totAngle%360 <= 360):
			self.fDis = "Eat your vegetables and you will grow strong like Popeye!"
		else:
			self.fDis = "Invalid"
		self.fortuneDisplay.setText(self.fDis)
		self.shost = self.titleEdit.text()
		self.name_array.append(str(self.shost))
		print self.shost
		self.speed_array.append(self.maxSpeed)
		print self.speed_array
		self.hostFortune = self.fortuneDisplay.text()
		print self.hostFortune
		self.fortune_array.append(str(self.hostFortune))
		time.sleep(2)
		self.titleEdit.setText("")
		self.speedDisplay.setText('0')
		#self.fortuneDisplay.setText("Wait for it...")
		self.titleEdit.setEnabled(True)
		
		#self.thread.angleSignal.disconnect()
		#self.thread.timeSignal.disconnect()
		#self.thread.speedSignal.disconnect()
		#self.thread.angleSignal.connect(self.changeAngle)
		#self.thread.timeSignal.connect(self.changeTime)
		#self.thread.speedSignal.connect(self.changeSpeed)				
		#print self.speed_array
	def button_click_show(self):
		print self.speed_array
		print self.name_array
		maxVal=max(self.speed_array)
		indexMaxVal=self.speed_array.index(maxVal)
		print indexMaxVal
		winner=self.name_array[indexMaxVal]
		QMessageBox.about(self, "Winner!!", winner)
	def button_click_reset(self):
		self.shost=""
		self.titleEdit.setText("")
		self.speedDisplay.setText('0')
		del self.name_array[:]
		del self.speed_array[:]
		QMessageBox.about(self, "Thank you", "Reset successful,Close this window for next game")
		self.fortuneDisplay.setText("Wait for it...")

   	

def main():
	app = QtGui.QApplication(sys.argv)
	demo=Example()  
	# It's exec_ because exec is a reserved word in Python
	sys.exit(app.exec_())
    

if __name__ == "__main__":
    main()

