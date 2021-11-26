import requests
from subprocess import Popen, PIPE

GIT_URL="raw.githubusercontent.com/DiegoPortoghese/BTCPAX_BLOCKCHAIN_BOT"
GITHUB_PERSONAL_TOKEN="b9b89e08c4f59e10136c6b56fc4a3cf724bf8216"
"""
full_url='https://'+GITHUB_PERSONAL_TOKEN+'@'+GIT_URL+'/master/version_controller.txt'
print(full_url)
response = requests.get(full_url)
print(response)
"""

VERSION = "1.0"
pipe = Popen("curl -s https://"+GITHUB_PERSONAL_TOKEN+"@"+GIT_URL+'/master/version_controller.txt'+"", shell=True,stdout=PIPE) # curl call 
version_buff = pipe.communicate()[0].decode("utf-8")
print(str(version_buff))

if version_buff != VERSION:
    print("New version available")
else:
    print("Now new version available")


