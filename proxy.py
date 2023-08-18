from socket import *
from datetime import datetime, timedelta
from threading import *
import time
import os

# Struct in config file
class RequestConfig:
    def __init__(self, methods, whitelist, start_time, end_time, cache_types, cache_time):
        self.methods = methods  # Methods
        self.whitelist = whitelist # whitelist
        self.start_time = start_time # Start Time
        self.end_time = end_time    # End Time
        self.cache_types = cache_types # Types of caches
        self.cache_time = cache_time # Time to reload caches
        
# Function to read config file
def parse_request_config(file_path):
    config_data = {}
    with open(file_path, "r") as file:
        for line in file:
            key, value = map(str.strip, line.strip().split(":", 1))
            config_data[key] = value

    # Parse methods, whitelist, time, cache types, and cache time
    methods = [method.strip() for method in config_data.get("Method", "").split(',')]
    whitelist = [domain.strip() for domain in config_data.get("Whitelist", "").split(',')]
    time_range = config_data.get("Time", "").strip()
    start_time = ""
    end_time = ""
    
    # Read time
    if "-" in time_range:
        time_parts = [part.strip() for part in time_range.split('-')]
        if len(time_parts) == 2:
            start_time, end_time = time_parts
    # Read cache types
    cache_types = [cache.strip() for cache in config_data.get("Cache_type", "").split(',')]
    #Read caches time
    cache_time = config_data.get("Cache_time", "")

    # Create and return a RequestConfig instance
    return RequestConfig(methods, whitelist, start_time, end_time, cache_types, cache_time)

# Fuction to delete caches 
def releaseCache(caches):
    while True:
        current_time = datetime.now()
        for cache in caches:
            if current_time > cache['time']:
                os.remove('pycache/' + cache['name'])
        time.sleep(30)

# Function to validate request
def Validate(request, config, message):
    # Empty request
    if not request:
        message[0] = 'Empty request'
        return False

    strRequest = request.decode()
    # ["GET", "/path", "HTTP/1.1", "Host:", "example.com"]
    
    # Method
    method = strRequest.split()[0]
    if method not in config.methods:
        message[0] = 'Invalid method'
        return False

    # Whitelist
    hostn = strRequest.split()[4]
    if 'www.' in hostn:
        hostn = hostn.replace('www.', '')

    if hostn not in config.whitelist:
        message[0] = 'You are not allowed to access this page !!!'
        return False

    # Time
    now = str(datetime.now().time())
    hour_now = now.split(":")[0]
    mins_now = now.split(":")[1]
    now = hour_now + ":" + mins_now
    if now < config.start_time or now > config.end_time:
        message[0] = 'You are not allowed to access this page at this moment !!!'
        return False
    # Accept
    return True

# Path to the input file
file_path = "config.txt"

# Parse the configuration and create a RequestConfig instance
request_config = parse_request_config(file_path)

# Function to send 403 error
def handleForbidden():
    with open("error.html", 'r') as file:
        error = file.read()
    errorRes = f"HTTP/1.1 403 Forbidden\r\n\r\n{error}"
    return errorRes.encode()

# Connect
def ProcessProxy(client, caches):
    # Get request from client
    req = client.recv(2 ** 20)
    #Validate
    message = ['']
    if (Validate(req, request_config, message)):
        if (req.decode().split()[0] != "CONNECT"):
            print('Sending Request for', req.decode().split()[1])

            # example.com
            pathName = req.decode().split()[1]
            cacheName = pathName.replace('http://', '').replace('/', '')
            
            try:
                fileCache = open('pycache/' + cacheName, 'rb')
                print('Founded ', pathName, 'in cache')
                
                responseBrowser = fileCache.read()
                
                client.send(responseBrowser)
                
            except IOError:
                # print('Path: ', req.decode().split()[4], end='\n')

                addr = req.decode().split()[4]
                if not addr.startswith('www.'):
                    addr = 'www.' + addr
                # print(addr, end='\n')
                s = socket(AF_INET,SOCK_STREAM)
                s.connect((addr, 80))
                # Send request to client
                s.send(req)
                
                # Read type caches
                typeCache = pathName.split('.')[-1]
                if typeCache in request_config.cache_types:
                    cache = open('pycache/' + cacheName, 'wb')
                    caches.append({
                        'name': cacheName,
                        'time': datetime.now() + timedelta(minutes = int(request_config.cache_time))                        
                    })
                # Receive response
                while True:
                    responseBrowser = s.recv(2 ** 20)
                    if not responseBrowser:
                        print('Not Response !!!')
                        break
                    print('Received Response for: ', req.decode().split()[1])
                    if typeCache in request_config.cache_types:
                        header, body = responseBrowser.split(b'\r\n\r\n', 1)
                        cache.write(body)
                        
                    client.send(responseBrowser)
                    
                s.close()
    else:
        
        reply = handleForbidden()
        client.send(reply)

    # Close connect from browser
    client.close()
    
#MAIN

#create a server
socServer = socket(AF_INET, SOCK_STREAM)

for file in os.listdir('pycache'):
    os.remove('pycache/' + file)

caches = []
cacheThread = Thread(target = releaseCache, args = [caches])
cacheThread.start()

try:
    socServer.bind(('', 8000))
except:
    print("Binded Failed")

print("Socket binding operation completed")

socServer.listen()
print("Listening ...")

while True:
    clientSocket, address = socServer.accept()
    Thread(target = ProcessProxy, args = [clientSocket, caches]).start()