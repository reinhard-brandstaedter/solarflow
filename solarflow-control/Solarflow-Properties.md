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
