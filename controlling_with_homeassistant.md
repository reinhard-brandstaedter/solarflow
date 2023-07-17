*UPDATE:* my initial attempt to just getting stats into Homeassistant vie DNS forging, turned out to be not as practical. After 24hrs this setup stopped working properly. I have now a more "official" way to get data into HA.

## SolarFlow's Limitation

Unfortunately Zendure's Solarflow is rather limited when it comes to controlling various aspects of the system.
Apart from some missing features and a rather suboptimal user experience when using the App (no webinterface!),
there are lots of limitations what can be controlled and how fine settings can be controlled.
E.g:

- setting the Output to Home limit in more fine granular steps or via API
- use of a local MQTT broker for integration with homeautomation systems
- missing bypass for generated energy when the batteries are full
- ...

## Complete Control

In an attempt to workaround some of the limitations above I came up with a solution that involves some "hacking and stitching together".
My solution might not be perfect and I'm still testing the practical aspects of it.
What you will need:

- A Zendure developer account, [please see here how to create one](https://github.com/Zendure/developer-device-data-report)
- Local MQTT broker (standalone or from Homeassistant/HA) - e.g. mosquitto MQTT
- Micro-inverter where you can set the input limit via API
- Homeassistant configured to use your MQTT broker
- Homeassistant or other automation tools/scripts
- Your current household consumption as a sensor in Homeassistant (optional)

### Basics

Solarflow reports device metrics such as firmware, serial numbers, states and also current power stats via MQTT to a service run by Zendure hosted
on AWS in Hongkong. This MQTT service is used to exchange data between your device and Zendure, it is also used for timesync, update checking, etc.
With a Zendure developer account you can subscribe to a MQTT service to get your SolarFlow's metrics (not control it) into your own local MQTT broker.
This is called a bridge setup. Basically you subscribe your broker to the Zendure broker and listen to topics which you will then publish locally.

To do so you will need a Zendure Developer Account (see above), which grant you login and access to your data.

### Local MQTT broker
I'm using [mosquitto MQTT](https://mosquitto.org/) so first thing after getting the developer account is to subscribe to the remote broker and brindge my topics locally. To do so ypou will need to add these lines to your ```mosquitto.conf```:

```
...
connection external-bridge
address mqtt.zen-iot.com:1883
remote_username <Your Zendure Developer AppKey>
remote_password <Your Zendure Developer Secret>
clientid <AppKey>
topic <AppKey>/<device ID>/# in 0
topic # in 0 homeassistant/sensor/<AppKey>/ <AppKey>/sensor/device/
...
```

To get your ```device ID``` you will first need to connect to the Zendure MQTT broker, you will see it as part of the topic of your SolarFlow.
In the above configuration we are doing two things:

- login with your account so you only see your device
- mapping of sensor config topic into the right place so that homeassistant can automatically create the sensors (no manual config needed anymore) via MQTT

Once you have restarted your MQTT broker you should be seeing topics coming in from Zendure for your SolarFlow:

<img width="1231" alt="Screenshot 2023-07-16 at 14 57 45" src="https://github.com/reinhard-brandstaedter/solarflow/assets/10830223/bfc24b57-e226-415d-84c0-53ec75f448e4">

Note that the sensor configuration topics are mapped correctly into the ```homassistant/sensor``` topic. This allows HA to automatically create those sensors for you.

### Getting Data into Homeassistant
After some time you will see the first data coming into Homeassistant:

<img width="501" alt="image" src="https://github.com/reinhard-brandstaedter/solarflow/assets/10830223/71822f52-598f-485c-b1bf-b9def96be86a">


### Using the Data for Automation
The last part is to use the now available data for some smart automation in Homeassistant. Here comes the API access to the micro-inverter into play.
We will not directly control the SF-Hub but rather steer the limit of the inverter so that it only draws what is needed or what you want it to.
For that to work I've set the SF-Hub into Time mode with a constant max output to my home/inverter (in my case 600W). Since we are limiting the inverter
we will never draw that in an uncontrolled fashion.
Instead we will use the current household consumption, the current state of charge of the batteries, the current solar production and sunrise/sunset times
to make decisions on how to set the inverter limit with an automation.

For that to work we need three things:

- the inverter API available in Homeassistant e.g. via a REST command
- a helper input in homeassistant for the limit
- an automation that is triggered on a regular basis

#### Inverter API
I'm using Ahoy-DTU with my Hoymiles inverter. This has a simple API to POST the inverter limit. In Homeassistant you can add this command in your configuration.yaml:

```
rest_command:                    
  set_inverter_power_limit:
    url: 'http://<IP of AhoyDTU/api/ctrl'
    method: post
    content_type: "application/json"
    payload: '{"id":0,"cmd":"limit_nonpersistent_absolute","val": "{{ limit }}" }'
```

Now this is available as a service you can call in automations.

#### Helper input for Inverter Limit
I'm storing the current inverter limit in a helper of type input number.

#### Automation for Limiting Inverter
Finally we'll use an automation that is triggered every 15s that adapts the inverter limit, based on the data we get from the SF-Hub. This could look like the one below.

What I'm trying to do here (still has to be fully verified at time of writing):

- during the day (after sunrise, before sunset), if the battery is full I'm setting the inverter limit to exactly what is generated by the solar panels
- during the day, if the battery is not full, set the limit to a bit less than what is needed in the house, but only if we produce more than that on the panels.
  This should give us room for charging the battery (likely needs tuning)
- during the night (after sunset, before sunrise), adjust the limit to a bit less than what is needed in the house, to keep the household consumption close to zero (as long as the battery lasts)

```
alias: Adapt SF Control
description: ""
trigger:
  - platform: time_pattern
    seconds: /15
condition: null
action:
  - if:
      - condition: and
        conditions:
          - condition: sun
            after: sunrise
          - condition: sun
            before: sunset
          - condition: numeric_state
            entity_id: sensor.solarflow_soclevel
            above: 99
    then:
      - service: input_number.set_value
        data:
          value: "{{ states('sensor.solarflow_solarinputpower') | int(0) }}"
        target:
          entity_id: input_number.inverter_power_limit
    else:
      - choose:
          - conditions:
              - condition: sun
                after: sunset
                before: sunrise
            sequence:
              - service: input_number.set_value
                data:
                  value: >-
                    {{ (states('sensor.e220_power_power_curr') | int +
                    states('input_number.inverter_power_limit') | int - 10 ) |
                    int }}
                target:
                  entity_id: input_number.inverter_power_limit
          - conditions:
              - condition: sun
                after: sunrise
                before: sunset
            sequence:
              - if:
                  - condition: numeric_state
                    entity_id: sensor.e220_power_power_curr
                    below: sensor.solarflow_solarinputpower
                then:
                  - service: input_number.set_value
                    data:
                      value: >-
                        {{ (states('sensor.e220_power_power_curr') | int +
                        states('input_number.inverter_power_limit') | int - 10 )
                        | int }}
                    target:
                      entity_id: input_number.inverter_power_limit
                else:
                  - service: input_number.set_value
                    data:
                      value: >-
                        {{ states('sensor.solarflow_solarinputpower') | int(0)
                        }}
                    target:
                      entity_id: input_number.inverter_power_limit
  - service: rest_command.set_inverter_power_limit
    data:
      limit: "{{ states('input_number.inverter_power_limit') | int }}"
mode: single
```

### Impressions
After a day letting the automation do it's work this looks like this (Dashboards are in Grafana as I export timeseries data from Homeassistant):
<img width="1534" alt="image" src="https://github.com/reinhard-brandstaedter/solarflow/assets/10830223/c64938d7-9103-46e8-a56e-238b36226839">

<img width="1343" alt="image" src="https://github.com/reinhard-brandstaedter/solarflow/assets/10830223/5f88e690-25f0-4238-98d8-c15273f2d3f9">

The power consumption measured on my house' smartmeter is a rather flat line, slightly above 0, where possible. Only during midday (kitchen on!) I'm daring from the grid,
although the automation increased the limit to the max to leverage the sun as much as possible. Note that at this time it's also drawing from the battery, which gave me
an idea to also factor that in an eventually limit how much it is allowed to drain from the battery during the day (e.g. allow a max of 75W added from the battery - see [#1](/../../issues/1)) 



