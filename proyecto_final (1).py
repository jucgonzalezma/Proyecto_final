#!/bin/python3
import os
import time
import sys
import random
import threading
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.register_read_message import ReadHoldingRegistersResponse
from Adafruit_IO import RequestError, Client, Feed, MQTTClient, MQTTError, errors
import Mykey
import requests
import os

Voltage=[]
Current=[]
Power=[]
Frequency=[]

ADAFRUIT_IO_USERNAME = Mykey.user()
ADAFRUIT_IO_KEY = Mykey.llave()
IO_FEED = 'corriente'
IO_FEED_2 = 'voltaje'
IO_FEED_3 = 'frecuencia'

def variables():
  while True:
    client = ModbusClient(method='rtu', port='/dev/ttyUSB0', stopbits=1, bytesize=8, parity='N', baudrate=9600, timeout=1)
    connection=client.connect()
    i_register = client.read_holding_registers(3,2, unit=0x01)
    i_decoder = BinaryPayloadDecoder.fromRegisters(i_register.registers, Endian.Big, wordorder=Endian.Little)
    i_float = int(i_decoder.decode_32bit_int())*0.001
    Current.append(i_float)
    v_register = client.read_holding_registers(2,1, unit=0x01)
    v_float=int(v_register.registers[0])*0.01
    Voltage.append(v_float)
#    print (Voltage)
    f_register = client.read_holding_registers(11,1, unit=0x01)
    f_float=int(f_register.registers[0])*0.01
    Frequency.append(f_float)
#    print (Frequency)
#    n = random.uniform(0.5,1)  ##Generación de numero random para pruebas
#    print (n)
#    Current.append(n)
#    m = random.randint(10,20)
#    print (m)
#    Power.append(m)
#    o = random.uniform(115,120)
#    print (o)
#    Voltage.append(o)
#    p = random.uniform(59.9,60.1)
#    print (p)
#    Frequency.append(p)
    time.sleep(1)

def publish():
  N = 10
  prom_current=[]
  prom_voltage=[]
  prom_frequency=[]

  while True:
    if (len(Current)>0):
      prom_current.append(Current.pop(0))
    if (len(Voltage)>0):
      prom_voltage.append(Voltage.pop(0))
    if (len(Frequency)>0):
      prom_frequency.append(Frequency.pop(0))
    if (len(prom_current) >= N):
      mean_current=sum(prom_current)/len(prom_current)
      print ('Publicando {0} en {1}.'.format(mean_current, IO_FEED))
      client.publish(IO_FEED, mean_current)
      prom_current.clear()
      Current.clear()
    if (len(prom_voltage) >= N):
      mean_voltage=sum(prom_voltage)/len(prom_voltage)
      print ('Publicando {0} en {1}.'.format(mean_voltage, IO_FEED_2))
      client.publish(IO_FEED_2, mean_voltage)
      prom_voltage.clear()
      Voltage.clear()
    if (len(prom_frequency) >= N):
      mean_frequency=sum(prom_frequency)/len(prom_frequency)
      print ('Publicando {0} en {1}.'.format(mean_frequency, IO_FEED_3))
      client.publish(IO_FEED_3, mean_frequency)
      prom_frequency.clear()
      Frequency.clear()

def connected(client):
    print ('Conectado a Adafruit IO! Publicando a {0}, {1} y {2}...'.format(IO_FEED, IO_FEED_2, IO_FEED_3))
    client.subscribe(IO_FEED)
    client.subscribe(IO_FEED_2)
    client.subscribe(IO_FEED_3)

def disconnected(client):
    print ('Desconectado de Adafruit IO!')
    sys.exit(1)

def message(client, feed_id, payload):
    print ('Feed {0} recibió un nuevo valor: {1}'.format(feed_id, payload))

def monitoring():
     url = "http://io.adafruit.com"
     timeout = 60
     time.sleep(180)
     while True:
        try:
              request = requests.get(url, timeout=timeout)
#              print ('Hay internet')
              time.sleep(60)
        except (requests.ConnectionError, requests.Timeout) as exception:
#          print ("No hay internet")
          time.sleep(50)
          os._exit(1)

client = MQTTClient(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

client.on_connect = connected
client.on_disconnect = disconnected
client.on_message = message

client.connect()
client.loop_background()

print ('Publicando un nuevo mensaje cada minuto (presiona Ctrl+C para salir)...')

tt=threading.Thread(target=variables)
tt2=threading.Thread(target=publish)
tt3=threading.Thread(target=monitoring)
tt.start()
tt2.start()
tt3.start()
