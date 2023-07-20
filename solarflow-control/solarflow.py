import random, json, time, logging, sys, requests, os
from datetime import datetime
from functools import reduce
from paho.mqtt import client as mqtt_client


# our MQTT broker where we subscribe to all the telemetry data we need to steer
# could also be an external one, e.g. fetching SolarFlow data directly from their dv-server
broker = '192.168.1.245'
port = 1883
topic_house = "tele/E220/SENSOR"
topic_acinput = "inverter/HM-600/ch0/P_AC"
topic_solarflow = "SKC4SpSn/5ak8yGU7/state"
topic_ahoylimit = "inverter/ctrl/limit/0"
client_id = f'subscribe-{random.randint(0, 100)}'

# sliding average windows for telemetry data, to remove spikes and drops
sf_window = 5
solarflow_values = [0]*sf_window
sm_window = 10
smartmeter_values = [0]*sm_window
inv_window = 5
inverter_values = [0]*inv_window


battery = -1
charging = 0
MIN_CHARGE_LEVEL = 125          # The amount of power that should be always reserved for charging, if available. Nothing will be fed to the house if less is produced
MAX_DISCHARGE_LEVEL = 145       # The maximum discharge level of the battery. Even if there is more demand it will not go beyond that
OVERAGE_LIMIT = 10              # if we produce more than what we need we can feed that much to the grid
last_limit = -1                 # just record the last limit to avoid too many calls to inverter API
last_solar_input_update = datetime.now()


FORMAT = '%(asctime)s:%(levelname)s: %(message)s'
logging.basicConfig(stream=sys.stdout, level="INFO", format=FORMAT)
log = logging.getLogger("")
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

def on_solarflow_update(msg):
    global battery, charging
    global last_solar_input_update

    now = datetime.now()
    diff = now - last_solar_input_update
    seconds = diff.total_seconds()
    #if we haven't received any update on solarInputPower we assume it's not producing
    #log.info(f'No solarInputPower measurement received for {seconds}s')
    if seconds > 120:
        solarflow_values.pop(0)
        solarflow_values.append(0)

    payload = json.loads(msg)
    if "solarInputPower" in payload:
        if len(solarflow_values) > sf_window:
            solarflow_values.pop(0)
        solarflow_values.append(payload["solarInputPower"])
        last_solar_input_update = now
    if "electricLevel" in payload:
        battery = int(payload["electricLevel"])
    if "outputPackPower" in payload:
        charging = int((payload["outputPackPower"]))

def on_inverter_update(msg):
    if len(inverter_values) > inv_window:
        inverter_values.pop(0)
    inverter_values.append(float(msg))

def on_smartmeter_update(msg):
    payload = json.loads(msg)
    if len(smartmeter_values) > sm_window:
        smartmeter_values.pop(0)
    smartmeter_values.append(int(payload["Power"]["Power_curr"]))

def on_message(client, userdata, msg):
    if msg.topic == topic_acinput:
        on_inverter_update(msg.payload.decode())
    if msg.topic == topic_solarflow:
        on_solarflow_update(msg.payload.decode())
    if msg.topic == topic_house:
        on_smartmeter_update(msg.payload.decode())

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

def connect_mqtt() -> mqtt_client:
    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def subscribe(client: mqtt_client):
    client.subscribe(topic_house)
    client.subscribe(topic_acinput)
    client.subscribe(topic_solarflow)
    client.on_message = on_message

def steerInverter(client: mqtt_client):
    # ensure we have data to work on
    if len(smartmeter_values) == 0:
        log.warning(f'Waiting for smartmeter data to make decisions...')
        return
    if len(solarflow_values) == 0:
        log.warning(f'Waiting for solarflow input data to make decisions...')
        return
    if len(inverter_values) == 0:
        log.warning(f'Waiting for inverter data to make decisions...')
        return
    if battery < 0:
        log.warning(f'Waiting for battery state to make decisions...')
        return
        
    smartmeter = reduce(lambda a,b: a+b, smartmeter_values)/len(smartmeter_values)
    solarinput = int(round(reduce(lambda a,b: a+b, solarflow_values)/len(solarflow_values)))
    inverterinput = round(reduce(lambda a,b: a+b, inverter_values)/len(inverter_values),1)
    demand = int(round((smartmeter + inverterinput)))
    limit = 0

    #now all the logic when/how to set limit
    if battery >= 98:
        if solarinput > 0:                                      # to avoid SF from limiting the input we start feeding everythong to the house, just do not get 100% charged
            limit = solarinput
        if solarinput <= 0 and demand <= MAX_DISCHARGE_LEVEL:    # not producing and demand is less than discharge limit => discharge with demand
            limit = demand
        if solarinput <= 0 and demand > MAX_DISCHARGE_LEVEL:
            limit = MAX_DISCHARGE_LEVEL
    elif battery > 95:
        if solarinput > 0 and solarinput > demand:              # producing more than what is needed => only take what is needed and charge, giving a bit extra to demand
            limit = demand + OVERAGE_LIMIT
        if solarinput > 0 and solarinput < demand:              # producing less than what is needed => take what we can
            limit = solarinput
        if solarinput <= 0 and demand <= MAX_DISCHARGE_LEVEL:    # not producing and demand is less than discharge limit => discharge with demand
            limit = demand
        if solarinput <= 0 and demand > MAX_DISCHARGE_LEVEL:
            limit = MAX_DISCHARGE_LEVEL
    else:
        if solarinput > 0 and solarinput > MIN_CHARGE_LEVEL:
            if demand < solarinput - MIN_CHARGE_LEVEL:          # producing more than what is needed => charge more!
                limit = int(round(demand))
            if demand > solarinput - MIN_CHARGE_LEVEL:          # producing less than what is needed => make sure battery is charged with MIN_CHARGE_LEVEL
                limit = solarinput - MIN_CHARGE_LEVEL
        if solarinput > 0 and solarinput <= MIN_CHARGE_LEVEL:   # producing less than the minimum charge level => everything goes to the battery
            limit = 0
        if solarinput <= 0 and demand <= MAX_DISCHARGE_LEVEL:   # not producing and the battery is not full => discharge with MAX_DISCHARGE_LEVEL
            limit = int(round(demand))
        if solarinput <= 0 and demand > MAX_DISCHARGE_LEVEL:
            limit = MAX_DISCHARGE_LEVEL

    log.info(f'Demand: {demand}W, Solar: {solarinput}W, Inverter: {inverterinput}W, Battery: {battery}% charging: {charging}W => Limit: {limit}W')
    client.publish(topic_ahoylimit,f'{limit}W')

def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_start()

    while True:
        time.sleep(20)
        steerInverter(client)

if __name__ == '__main__':
    run()
