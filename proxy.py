from socket import *
from datetime import datetime
from threading import *
import webbrowser

# Host and Port
HOST = ''
PORT = 8000

class RequestConfig:
    def __init__(self, methods, whitelist, start_time, end_time, cache_types, cache_time):
        self.methods = methods
        self.whitelist = whitelist
        self.start_time = start_time
        self.end_time = end_time
        self.cache_types = cache_types
        self.cache_time = cache_time

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
    if "-" in time_range:
        time_parts = [part.strip() for part in time_range.split('-')]
        if len(time_parts) == 2:
            start_time, end_time = time_parts
    cache_types = [cache.strip() for cache in config_data.get("Cache_type", "").split(',')]
    cache_time = config_data.get("Cache_time", "")

    # Create and return a RequestConfig instance
    return RequestConfig(methods, whitelist, start_time, end_time, cache_types, cache_time)


def Validate(request, config, message):
    # Empty request
    if not request:
        message[0] = 'Empty request'
        print(1)
        return False

    # Method
    method = request.decode().split()[0]
    if method not in config.methods:
        message[0] = 'Invalid method'
        print(2, end='\n')
        print(method, end='\n')
        return False

    # Whitelist
    hostn = request.decode().split()[4].replace('www.', '')
    if hostn not in config.whitelist:
        message[0] = 'You are not allowed to access this page'
        print(3, end='\n')
        print(hostn, end='\n')
        return False

    # Time
    now = datetime.now().time().strftime("%H:%M")
    if now < config.start_time or now > config.end_time:
        message[0] = 'You are not allowed to access this page at this moment'
        print(4, end='\n')
        print(now, config.start_time, config.end_time)
        print(end='\n')
        return False
    print(5)
    # Accept
    return True

# Path to the input file
file_path = "config.txt"

# Parse the configuration and create a RequestConfig instance
request_config = parse_request_config(file_path)

# Simulating a request
request = b"POS /path HTTP/1.1\r\nHost: example.com\r\n\r\n"

# Placeholder for the error message
error_message = [None]

# Validate the request using the configuration
# is_valid = Validate(request, request_config, error_message)

def ProcessProxy(client ,address):
    req = client.recv(4096)
    message = ['']
    print(req.decode())
    if (Validate(req, request_config, message)):
        print(message)
    # else:
    #     print("Validation failed:", error_message[0])
    #     webbrowser.open_new_tab('error.html') # open 403 when meets the invalid time, link: https://www.guru99.com/accessing-internet-data-with-python.html
    return

#create a server
socServer = socket(AF_INET, SOCK_STREAM)

try:
    socServer.bind((HOST, PORT))
except:
    print("Binded Failed")

print("Socket binding operation completed")

socServer.listen()
print("Listening ...")

while True:
    clientSocket, address = socServer.accept()
    Thread(target = ProcessProxy, args = [clientSocket, address]).start()
    
'''
GET http://example.com/ HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: keep-alive
Upgrade-Insecure-Requests: 1
'''