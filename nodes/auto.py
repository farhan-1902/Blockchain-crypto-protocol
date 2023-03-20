import requests
import time

while(True):
    requests.get('http://172.20.10.5:5001/replace_chain')
    requests.get('http://172.20.10.13:5002/replace_chain')
    requests.get('http://172.20.10.11:5003/replace_chain')
    print('request sent')
    time.sleep(4)