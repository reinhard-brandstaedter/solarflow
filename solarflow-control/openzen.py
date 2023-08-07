from zenapi import ZendureAPI as zapp
import logging
import os
import sys

loglevel = os.environ.get("LOG_LEVEL", "info").upper()
FORMAT = '%(asctime)s:%(levelname)s: %(message)s'
logging.basicConfig(stream=sys.stdout, level=loglevel, format=FORMAT)
log = logging.getLogger(__name__)

ZEN_USER = os.environ.get('ZEN_USER',None)
ZEN_PASSWD = os.environ.get('ZEN_PASSWD',None)

if ZEN_USER is None or ZEN_PASSWD is None:
    log.error("No username and password environment variable set!")
    sys.exit(0)

with zapp.ZendureAPI() as api:
    token = api.authenticate(ZEN_USER,ZEN_PASSWD)
    log.info(f'Token: {token}')
    devices = api.get_device_ids()
    for dev_id in devices:
        api.get_device_details(dev_id)