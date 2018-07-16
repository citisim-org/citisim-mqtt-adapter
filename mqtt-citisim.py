import paho.mqtt.client as mqtt
from libcitisim import Broker

class TemperaturePublisher:
    def run(self, args):
        broker = Broker('citisim.config')
        publisher = broker.get_publisher(
            topic_name = "Temperature",
            source = "TestSensor")

    def publish_citisim_temperature(value):
          publisher.publish(value)
          print("Published Temperature event: {}. C".format(value))



# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("meshliumf958/#")

# The callback for when a PUBLISH message is received from the server.
def on_message_temperature(client, userdata, msg):
    TemperaturePublisher().run(sys.argv)
    print(msg.topic+" "+str(msg.payload))
    ## extract the temperature from MQTT message
    TemperaturePublisher().publish_citisim_temperature(10.0)

if __name__ == "__main__":
    mqtt_broker_addr= "mqtt.beia-telemetrie.ro"
    client = mqtt.Client("CitisimUCLM")
    client.on_connect =  on_connect
    client.on_message =  on_message_temperature
    client.connect(mqtt_broker_addr)
    client.loop_forever()
