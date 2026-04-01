# Novo arquivo: mqtt_sender.py

import paho.mqtt.client as mqtt

BROKER = 'broker.hivemq.com'
PORT = 1883
TOPIC = 'TesteDoVitoEsp32226'

def send_message(message, topic: str = TOPIC):
    """Envia mensagem MQTT de forma confiável (QoS 1 + wait_for_publish)."""
    try:
        client = mqtt.Client()
        client.connect(BROKER, PORT, 60)
        info = client.publish(topic, message, qos=1, retain=False)
        # Aguarda confirmação de envio (PUBACK) por até 2s
        info.wait_for_publish(timeout=2.0)
        client.disconnect()
        print(f"MQTT OK: '{message}' -> '{topic}'")
    except Exception as e:
        print(f"MQTT ERRO: '{message}' -> '{topic}': {e}")