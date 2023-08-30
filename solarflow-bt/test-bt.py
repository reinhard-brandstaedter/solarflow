import asyncio
from bleak import BleakClient, BleakScanner
import json


address = "94:C9:60:3E:C8:E7"


def handle_rx(BleakGATTCharacteristic, data: bytearray):
    print(f'{data.decode("utf8")}')

async def main(address):

    device = await BleakScanner.find_device_by_filter(
                lambda d, ad: d.name and d.name.lower().startswith("zen")
            )
    #device = await BleakScanner.find_device_by_address(address)
    
    print("Found the device: " + str(device))

    async with BleakClient(device) as client:
        svcs = client.services
        print("Services:")
        for service in svcs:
            print(service)

        #Report Characteristic:  0000c305-0000-1000-8000-00805f9b34fb
        report_char = "0000c305-0000-1000-8000-00805f9b34fb"
        while True:
            await client.start_notify(report_char,handle_rx)

        #Write Characteristic 0000c304-0000-1000-8000-00805f9b34fb
        write_char = "0000c304-0000-1000-8000-00805f9b34fb"


asyncio.run(main(address))