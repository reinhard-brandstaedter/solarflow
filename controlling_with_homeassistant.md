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

- DNS server/Forwarder in you local LAN where you can add custom records (e.g. pi-hole)
- Local MQTT broker (standalone or from Homeassistant/HA) - e.g. mosquitto MQTT
- Micro-inverter where you can set the input limit via API
- Homeassistant configured to use your MQTT broker
- Homeassistant or other automation tools/scripts
- Your current household consumption as a sensor in Homeassistant (optional)

### Basics

Solarflow reports device metrics such as firmware, serial numbers, states and also current power stats via MQTT to a service run by Zendure hosted
on AWS in Hongkong. The DNS name a SolarFlow tries to connect and send MQTT data to is mq.zen-iot.com.
Likely the SF-Hub uses a MQTT user/password to connect and post messages/telemetry there, which is then used by the App to display stats.
You can also register a [developer account](https://github.com/Zendure/developer-device-data-report) to get access to the MQTT broker.
The problem with that is that you cannot get full access to it and that I'm not a fan of sending data around the globe (with potential tracking) for
an IoT device that I just want to use locally.
So first step is to get SF-Hub to report to my MQTT broker

### Local MQTT broker
I do have a local MQTT Broker for my Homeassistant setup, so to get the SF-Hub to send it's messages there I just need to point mq.zen-iot.com to my
local broker. Since I can not configure that within SF-Hub (feature request!) I need to add a local DNS record to resolve Zendures MQTT host to my MQTT host.
I'm using pi-hole to filter adds in my LAN for all devices, so that is the place to create a custom DNS entry.

```
% nslookup mq.zen-iot.com
Server:		192.168.1.253
Address:	192.168.1.253#53

Name:	mq.zen-iot.com
Address: 192.168.1.245
```

Once that is in place SF will send it's messages to my MQTT server. Note that SF-Hub also uses the default mqtt port 1883 so your server needs to listen on that port also.
Additionally since the SF-Hub hopefully uses a user/password for MQTT, you will need to disable user/password authentication on your MQTT server (allow any).
Make sure your MQTT is protected in other forms. Maybe the SF-Hubs user/password can be sniffed and you could create the same user/credentials on your server.

Eventually you need to restart the SF-Hub to clear any DNS caches, and after some time you should see MQTT messages from your SF-Hub.
Using MQTT Explorer I could see the topics posted by my SF-Hub. The topic used contains the unique device IDs:

<img width="683" alt="image" src="https://github.com/reinhard-brandstaedter/solarflow/assets/10830223/9d576ca0-96de-4620-a887-aa5c6cfc776a">

### Getting Data into Homeassistant
To get the stats into Homeassistant we will need to create a couple of custom sensors in HA configuration.yaml file. For the beginning I was just browsing MQTT messages
to look for what seems to be interesting. I've added these sensors (not perfect but works as a PoC):

```
mqtt:
  sensor:
    - name: SolarFlow - solarInputPower                                                                                                                                                                                         
      unique_id: "solarInputPower"                                                                                                                                                                                              
      state_topic: /73bkTV/5ak8yGU7/properties/report                                                                                                                                                                           
      value_template: "{{ value_json.properties.solarInputPower }}"                                                                                                                                                             
      unit_of_measurement: "W"                                                                                                                                                                                                  
      device_class: power                                                                                                                                                                                                       
      state_class: measurement                                                                                                                                                                                                  
                                                                                                                                                                                                                                
    - name: SolarFlow - solarInputPowerCycle                                                                                                                                                                                    
      unique_id: "solarInputPowerCycle"                                                                                                                                                                                         
      state_topic: /73bkTV/5ak8yGU7/properties/report                                                                                                                                                                           
      value_template: "{{ value_json.properties.solarInputPowerCycle }}"                                                                                                                                                        
      unit_of_measurement: "W"                                                                                                                                                                                                  
      device_class: energy                                                                                                                                                                                                      
                                                                                                                                                                                                                                
    - name: SolarFlow - outputPackPower                                                                                                                                                                                         
      unique_id: "outputPackPower"                                                                                                                                                                                              
      state_topic: /73bkTV/5ak8yGU7/properties/report                                                                                                                                                                           
      value_template: "{{ value_json.properties.outputPackPower }}"                                                                                                                                                             
      unit_of_measurement: "W"                                                                                                                                                                                                  
      device_class: power                                                                                                                                                                                                       
      state_class: measurement                                                                                                                                                                                                  
                                                                                                                                                                                                                                
    - name: SolarFlow - packInputPower                                                                                                                                                                                          
      unique_id: "packInputPower"                                                                                                                                                                                               
      state_topic: /73bkTV/5ak8yGU7/properties/report                                                                                                                                                                           
      value_template: "{{ value_json.properties.packInputPower }}"                                                                                                                                                              
      unit_of_measurement: "W"                                                                                                                                                                                                  
      device_class: power                                                                                                                                                                                                       
      state_class: measurement                                                                                                                                                                                                  
                                                                                                                                                                                                                                
    - name: SolarFlow - outputHomePower                                                                                                                                                                                         
      unique_id: "outputHomePower"                                                                                                                                                                                              
      state_topic: /73bkTV/5ak8yGU7/properties/report                                                                                                                                                                           
      value_template: "{{ value_json.properties.outputHomePower }}"                                                                                                                                                             
      unit_of_measurement: "W"                                                                                                                                                                                                  
      device_class: power                                                                                                                                                                                                       
      state_class: measurement                                                                                                                                                                                                  
                                                                                                                                                                                                                                
    - name: SolarFlow - outputPackPowerCycle                                                                                                                                                                                    
      unique_id: "outputPackPowerCycle"                                                                                                                                                                                         
      state_topic: /73bkTV/5ak8yGU7/properties/report                                                                                                                                                                           
      value_template: "{{ value_json.properties.outputPackPowerCycle }}"                                                                                                                                                        
      unit_of_measurement: "W"                                                                                                                                                                                                  
                                                                                                                                                                                                                                
    - name: SolarFlow - battery socLevel                                                                                                                                                                                        
      unique_id: "socLevel"                                                                                                                                                                                                     
      state_topic: /73bkTV/5ak8yGU7/properties/report                                                                                                                                                                           
      value_template: "{{ value_json.packData[0].socLevel }}"                                                                                                                                                                   
      unit_of_measurement: "%"                                                                                                                                                                                                  
      device_class: battery                                                                                                                                                                                                     
      state_class: measurement                                                                                                                                                                                                  
                                                                                                                                                                                                                                
    - name: SolarFlow - battery maxTemp                                                                                                                                                                                         
      unique_id: "maxTemp"                                                                                                                                                                                                      
      state_topic: /73bkTV/5ak8yGU7/properties/report                                                                                                                                                                           
      value_template: "{{ value_json.packData[0].maxTemp | int / 100 | round(1) }}"                                                                                                                                             
      unit_of_measurement: "°C"
```

Note: you will eventually see some warnings in the Homeassistant logs as the MQTT messages not always contain all datapoints.

After some time you will see the first data coming into Homeassistant:

<img width="985" alt="image" src="https://github.com/reinhard-brandstaedter/solarflow/assets/10830223/1ac2d5af-8e7e-4ba5-8e63-5cc0790456f2">

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



