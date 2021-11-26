from shutil import copy2, rmtree
from sys import exit
from subprocess import Popen
import time
GIT_URL = ""
GITHUB_PERSONAL_TOKEN = ""

lines=[]
with open("config.ini","r") as f:
    lines=f.readlines()
for line in lines:
    if line.startswith("GIT_URL"):
        GIT_URL=line.replace("GIT_URL=","").replace('"',"").replace("\n","")
    if line.startswith("GITHUB_PERSONAL_TOKEN"):
        GITHUB_PERSONAL_TOKEN=line.replace("GITHUB_PERSONAL_TOKEN=","").replace('"',"").replace("\n","")

Popen("curl -s https://"+GITHUB_PERSONAL_TOKEN+"@"+GIT_URL+'/master/main.py > main.py'+"", shell=True) # download last main.py
time.sleep(5)
Popen("python ./main.py", shell=True) # go back to your program

exit("restarting...")

