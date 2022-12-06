import paho.mqtt.client as mqtt
import json
import time
import ssl
import re

broker_host = "broker.qubitro.com"
broker_port = 8883
device_id = "af96df76-cec4-4203-9f73-ec3dca666e50"
device_token = "b$CgHxRWYgRprdlB14XMJbWy2QPiP$cIBemz2Cnb"
current_temp = 0
current_himid = 0

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.on_message = on_message
    else:
        print("Failed to connect, visit: https://docs.qubitro.com/client-guides/mqtt/client-libraries/python3.x\n return code:", rc)

def on_message(client, userdata, message):
    # print("received message =",str(message.payload.decode("utf-8")))
    temp_string = str(message.payload.decode("utf-8"))
    data = re.findall("\d+\.\d+", temp_string)
    global current_temp
    current_temp = data[0]
    global current_himid
    current_himid = data[1]
    

def get_temp():
    client.subscribe("148ee57d-2e50-4f1a-8cfb-1a562f188697", 0)
    # temp_ls = tuple(current_temp)
    
    return current_temp

def get_himid():
    client.subscribe("148ee57d-2e50-4f1a-8cfb-1a562f188697", 0)
    # temp_ls = tuple(current_temp)
    return current_himid

client = mqtt.Client(client_id=device_id)
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
client.tls_set_context(context)
client.username_pw_set(username=device_id, password=device_token)
client.connect(broker_host, broker_port, 60)
client.on_connect = on_connect
client.subscribe("148ee57d-2e50-4f1a-8cfb-1a562f188697", 0)
client.loop_start()




# while True:
#     if client.is_connected:
#         client.subscribe("ab1d5c45-bd04-4a4b-8506-305b17ed9ee8", 0)
#         print(current_temp)
#         print(current_himid)
#         time.sleep(1)