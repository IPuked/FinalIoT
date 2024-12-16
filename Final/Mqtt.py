import sys
import paho.mqtt.client as paho


def message_handling(client, userdata, msg):
    print(f"{msg.topic}: {msg.payload.decode()}")
    

def ConnectMqtt():
    client = paho.Client()
    client.on_message = message_handling
    if client.connect("RPI", 1883, 60) != 0:
        print("could not connect to mqtt broker")
        sys.exit(1)

    client.subscribe("temp")
    #client.disconnect
    try:
        print("Press CTRL+C exit..")
        client.loop_forever()
    except Exception:
        print("caugh exception, something went wrong..")
    finally:
        print("disconnecting from MQTT")
        client.disconnect()
        
ConnectMqtt()