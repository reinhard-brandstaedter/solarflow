### getting MQTT Connect info from packet capture

sed --regexp-extended 's/(.++)([0-9]{4,5}:[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12})\.\.([aA-zZ]*)\.\.(.*)/client-id: \2\nuser: \3\npwd: \4/'


### List of properties one can set

Using the topic ```iot/<CLIENT>/<DEVICEID>/properties/write``` with payload
```{"properties": {propertyname: propertyvalue} }```
one can set:

- inverseMaxPower : the maximum output from the hub to the microinverter
- outputLimit : the limit output to home
- inputLimit : the solar input limit (??)


### get current property values

One can trigger a property pull by posting a topic to ```iot/<CLIENT>/<DEVICEID>/properties/read``` with payload
{"properties": [<propertyname>]}
And then the reply with values can be found in ```iot/<CLIENT>/<DEVICEID>/properties/read/reply```
