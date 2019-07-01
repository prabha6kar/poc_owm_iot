import time, paho.mqtt.client as mqtt

# Define Variables
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "ha/_temperature1"
MQTT_MESSAGE = None

def on_log(client, userdata, level, buf):
    print("log: ",buf)
    
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker")
        global Connected                #Use global variable
        Connected = True                #Signal connection
    else:
        print("Connection failed")
        
def on_message(client, userdata, message):
    global MQTT_MESSAGE
    MQTT_MESSAGE = message
    print("message time: " + str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(MQTT_MESSAGE.timestamp))))
    print("message received: "  + str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)
    
Connected = False   #global variable for the state of the connection
client = mqtt.Client("Python1")                     #create new instance
client.on_log     = on_log
client.on_connect = on_connect                      #attach function to callback
client.on_message = on_message                      #attach function to callback
# client.connect(MQTT_BROKER,MQTT_PORT)               #connect to broker         

def get_temp_from_sensor():
    client.connect(MQTT_BROKER,MQTT_PORT)               #connect to broker         
    client.loop_start() #start loop to process received messages
    client.subscribe(MQTT_TOPIC)#subscribe
    time.sleep(1)
    client.disconnect()
    client.loop_stop() #stop loop
    return 0

if __name__ == '__main__':
    client.loop_start() #start loop to process received messages
    print("subscribing ")
    client.subscribe(MQTT_TOPIC)#subscribe
    time.sleep(6)
    client.loop_stop() #stop loop