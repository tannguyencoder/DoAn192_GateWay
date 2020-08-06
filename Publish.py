import RPi.GPIO as GPIO 
import paho.mqtt.client as mqtt
import _thread, json
from datetime import datetime
import time
import serial
#====================================================
# MQTT Settings 
MQTT_Broker = "192.168.137.1"
MQTT_Port = 1883
Keep_Alive_Interval = 45
MQTT_Topic_SenSor = "Sensor"
MQTT_Topic_Control ="Control"
data=''
flagData=0
data_send=''
flagR=0
# GPIO setting
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(12, GPIO.OUT, initial=GPIO.LOW)
def Send_Enable():
	GPIO.output(12,GPIO.HIGH)
def Listen_Enable():
	GPIO.output(12,GPIO.LOW)
#====================================================
ser = serial.Serial (
	port		="/dev/ttyS0",
	baudrate	= 9600,
	parity		=serial.PARITY_NONE,
	stopbits	=serial.STOPBITS_ONE,
	bytesize	=serial.EIGHTBITS,
	timeout		=0.01)

def on_connect(client, userdata,flags, rc):
	if rc != 0:
		pass
		print ("Unable to connect to MQTT Broker...")
	else:
		print ("Connected with MQTT Broker: " + str(MQTT_Broker))

def on_publish(client, userdata, mid):
	pass

def on_disconnect(client, userdata, rc):
	if rc !=0:
		pass

def Data_Handler(msg):
	global data_send
	json_dict = json.loads(msg)
	NuA=json_dict['Control_Pump1']
	NuB=json_dict['Control_Pump2']
	Water_In=json_dict['Control_Water']
	data_send="w"+str(Water_In)+"ta"+str(NuA)+"tb"+str(NuB)+"t"
	global flagS
	flagS=1
	pass
def updateData(topic,msg):
	if topic == MQTT_Topic_Control:
		Data_Handler(msg)

def on_message(client, userdata, msg):
	print ("MQTT Data Received...")
	print ("MQTT Topic: " + msg.topic)
	print ("\n------------------------DATA SUBSCRIBE--------------------\n")
	print ("Data: ", msg.payload.decode("utf-8"))
	updateData(msg.topic,msg.payload.decode("utf-8"))



client = mqtt.Client()
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_publish = on_publish
client.on_message = on_message
client.connect(MQTT_Broker, int(MQTT_Port), int(Keep_Alive_Interval))
client.subscribe(MQTT_Topic_Control)
client.loop_start()

def publish_To_Topic(topic, message):
	client.publish(topic,message)
	print ("Published: " + str(message) + " " + "on MQTT Topic: " + str(topic))
#	print  ("-------------------END-----------------")

def Read_Uart_Publish():
	global flagR
	try:
		s = ser.readline()
		if(s):
			flagR=1
			flag=1
			data = s.decode()
		else:
			flagR=0
			flag=0
	except ValueError:
		flag=0
		flagR=0
		print("\nData err");
		pass
	if flag==1:
		data = data.rstrip()
		print(data)
		temp = data.split(",")
		if(data and len(temp)==9):
			print ("\n"+data)
			print("\n------------------------DATA RECEIVER--------------------------")
			print("Do am:       ",temp[1],"%")
			print("Nhiet Do:    ",temp[0],"°C")
			print("Anh sang:    ",temp[2],"Lux")
			print("Do PH:       ",temp[3],"pH")
			print("Do dan dien: ",temp[4],"mS/cm")
			print("Temp Water:  ",temp[5],"°C")
			print("Water In:    ",temp[6],"L")
			print("Nutrition A: ",temp[7],"L")
			print("Nutrition B: ",temp[8],"L")
			
			Sensor_data ={}
			Sensor_data['Date'] = (datetime.today()).strftime("%d-%b-%Y %H:%M:%S")
			Sensor_data['Humidity'] = temp[1]
			Sensor_data['Temperature'] = temp[0]
			Sensor_data['Light'] = temp[2]
			Sensor_data['PH'] = temp[3]
			Sensor_data['EC'] = temp[4]
			Sensor_data['WTemp'] =temp[5]
			Sensor_data['WIn'] = temp[6]
			Sensor_data['NuA'] = temp[7]
			Sensor_data['NuB'] = temp[8]
			
			print("\n------------------------DATA PUBLISH--------------------\n")
			Sensor_json_data = json.dumps(Sensor_data)
			publish_To_Topic(MQTT_Topic_SenSor, Sensor_json_data)
			flagR=0
		elif(data and not len(temp)==9):
			print("\nData err")
			flagR=0

def thread_Read_Publish():
	while True:
		Read_Uart_Publish();
		pass
try:
   _thread.start_new_thread( thread_Read_Publish,( ))
except:
   print ("Error: unable to start thread")

while 1:
	if(flagR==0 and data_send):
		Send_Enable();
		ser.write(str(data_send).encode("utf-8"))
		time.sleep(0.05);
		Listen_Enable()
		print("Data Send Uart:"+data_send+"\n")
		data_send=""
	pass

