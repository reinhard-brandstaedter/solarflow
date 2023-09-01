import asyncio
from bleak import BleakClient, BleakScanner
from paho.mqtt import client as mqtt_client
import json
import logging
import sys
import os

FORMAT = '%(asctime)s:%(levelname)s: %(message)s'
logging.basicConfig(stream=sys.stdout, level="INFO", format=FORMAT)
log = logging.getLogger("")

'''
Very basic attempt to just report Solarflow Hub's stats to mqtt for local long-term tests
'''

address = "94:C9:60:3E:C8:E7"
MQTT_HOST = os.environ.get('MQTT_HOST',"192.168.1.245")
MQTT_PORT = os.environ.get('MQTT_PORT',1883)
local_broker = MQTT_HOST
local_port = MQTT_PORT
local_client: mqtt_client


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info("Connected to MQTT Broker!")
    else:
        log.error("Failed to connect, return code %d\n", rc)

async def local_mqtt_connect():
    global local_client
    global local_port
    local_client = mqtt_client.Client(client_id="solarflow-bt")
    local_client.connect(local_broker,local_port)
    local_client.on_connect = on_connect


def handle_rx(BleakGATTCharacteristic, data: bytearray):
    payload = json.loads(data.decode("utf8"))

    if "properties" in payload:
        log.info(payload["properties"])
        props = payload["properties"]

        for prop, val in props.items():
            local_client.publish(f'solarflow-statuspage/{prop}',val)

        # also report whole state to mqtt (nothing coming from cloud now :-)
        local_client.publish("SKC4SpSn/5ak8yGU7/state",json.dumps(payload["properties"]))
        '''
        if "outputHomePower" in payload["properties"]:
            local_client.publish("solarflow-statuspage/outputHomePower",payload["properties"]["outputHomePower"])
        if "solarInputPower" in payload["properties"]:
            local_client.publish("solarflow-statuspage/solarInputPower",payload["properties"]["solarInputPower"])
        if "outputPackPower" in payload["properties"]:
            local_client.publish("solarflow-statuspage/outputPackPower",payload["properties"]["outputPackPower"])
        if "packInputPower" in payload["properties"]:
            local_client.publish("solarflow-statuspage/packInputPower",payload["properties"]["packInputPower"])
        if "electricLevel" in payload["properties"]:
            local_client.publish("solarflow-statuspage/electricLevel",payload["properties"]["electricLevel"])
        '''

async def main(address):

    device = await BleakScanner.find_device_by_filter(
                lambda d, ad: d.name and d.name.lower().startswith("zen")
            )
    #device = await BleakScanner.find_device_by_address(address)

    log.info("Found device: " + str(device))

    async with BleakClient(device) as client:
        svcs = client.services
        print("Services:")
        for service in svcs:
            print(service)

        #Characteristic:  0000c30500001000800000805f9b34fb

        await local_mqtt_connect()

        while True:
            char = "0000c305-0000-1000-8000-00805f9b34fb"
            await client.start_notify(char,handle_rx)


asyncio.run(main(address))