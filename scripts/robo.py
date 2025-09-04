import network
import time
from machine import Pin
from umqtt.simple import MQTTClient

direita = Pin(23, Pin.OUT)
esquerda = Pin(22, Pin.OUT)

# ——— Configurações MQTT + Wi-Fi ———
SSID        = 'E-colab'
PASSWORD    = 'E-colab117'
BROKER      = 'broker.hivemq.com'
PORT        = 1883
TOPIC       = b'TesteDoVitoEsp32226'

# variável global para armazenar a última mensagem recebida
msg = None

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Conectando à rede', SSID, '...')
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print('Wi-Fi conectado, IP:', wlan.ifconfig()[0])

def mqtt_callback(topic, payload):
    global msg
    try:
        texto = payload.decode('utf-8')
    except:
        texto = str(payload)
    print('Mensagem recebida em', topic.decode(), ':', texto)
    msg = texto
    
    if int(texto) == 1:
        print("anda para frente")
        esquerda.value(1)
        direita.value(1)
        time.sleep(1)
        esquerda.value(0)
        direita.value(0)
        
    elif int(texto) == 2:
        print("anda para trás")
        esquerda.value(1)
        direita.value(0)
        time.sleep(1)
        esquerda.value(0)
        
    elif int(texto) == 3:
        print("anda para direita")
        esquerda.value(0)
        direita.value(1)
        time.sleep(1)
        
        direita.value(0)
    elif int(texto) == 4:
        print("anda para esquerda")
        esquerda.value(1)
        direita.value(1)
        time.sleep(5)
        esquerda.value(0)
        direita.value(0)

def main():
    global msg

    # 1) Conecta ao Wi-Fi
    connect_wifi()

    # 2) Cria cliente MQTT e define callback
    client = MQTTClient(client_id='esp32', server=BROKER, port=PORT)
    client.set_callback(mqtt_callback)
    client.connect()
    print('Conectado ao broker MQTT em', BROKER)

    # 3) Inscreve-se no tópico para receber mensagens
    client.subscribe(TOPIC)
    print('Inscrito no tópico', TOPIC.decode())

    # 4) Espera por mensagens
    try:
        print('Aguardando mensagens...')
        while True:
            # bloqueia até chegar uma mensagem e chama mqtt_callback
            client.wait_msg()
            # após cada mensagem msg contém o último payload recebido
    finally:
        client.disconnect()
        print('Desconectado do broker')

if __name__ == '__main__':
    main()


