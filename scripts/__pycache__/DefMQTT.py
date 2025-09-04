# Novo arquivo: mqtt_sender.py

import paho.mqtt.client as mqtt

BROKER = 'broker.hivemq.com'
PORT = 1883
TOPIC = 'TesteDoVitoEsp32226'

def send_message(message):
    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)
    client.publish(TOPIC, message)
    client.disconnect()
    print(f"Mensagem '{message}' enviada para o tópico '{TOPIC}'.")

if __name__ == '__main__':
    msg = input("Digite a mensagem para enviar via MQTT: ")
    send_message(msg)