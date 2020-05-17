import json
import threading
import paramiko
from paramiko_expect import SSHClientInteraction
import paramiko_expect
import sys
from datetime import datetime
import queue

NewPlatpw = "Th#l@sT123!"  # Enter the New password/ You can set the new pw in the script or probably create JSON file for getting new pw
command = "set password user admin" #COmmand for Changing platform password

with open("Jsonfiles/password.json") as f: #JSON FIle for current/old passwords -- Dont forget to Update this is you changed the password ;)
    pwd = json.load(f)
for password in pwd['Passwords']:
    TestPwd = pwd['Passwords']['TestCluster']

# if all the nodes are already using one pw, it's easy to list all the IP's in one variable then push pw change thru threading
with open("Jsonfiles/inventory.json") as f:
    data = json.load(f)
for clusters in data['Clusters']:
    if 'Test' in clusters:     #take note this if statement is required to capture all the data inside the Json file // clusters is the variable representing the json file
        TestClusterNodes = clusters['Test']['nodes'] # set variable of Nodes
        TestClusterPub = clusters['Test']['Publisher'] # set variable of Publisher
        TestClusterUname = clusters['Test']['Username'] # set variable of Uname

## my function for changing platform password
def ChangePlatformPw(ip,username,password,NewPlatPw,command):
    sshsession = paramiko.SSHClient()
    sshsession.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    sshsession.connect(ip, username=username, password=password)
    # "display=True" is just to show you what script does in real time. While in production you can set it to False
    interact = SSHClientInteraction(sshsession, timeout=600, display=True)
    # program will wait till session is established and CUCM returns admin prompt
    # "display=True" is just to show you what script does in real time. While in production you can set it to False
    interact = SSHClientInteraction(sshsession, timeout=600, display=True)
    # program will wait till session is established and CUCM returns admin prompt
    interact.expect('admin:')
    interact.send(command)
    interact.expect('.*password:.*')
    interact.send(password)
    interact.expect('.*password:.*')
    interact.send(NewPlatPw)
    interact.expect('.*password.*')
    interact.send(NewPlatPw)
    interact.expect('admin:')
    output = interact.current_output
    with open("Logs/ChangeAppPw.txt", 'a') as outfile: # output for the threading will be push here
        outfile.write(output)
        outfile.write("{0} {1} -- Password Initiated changed to {2} {3}".format(ip, username, NewPlatPw,datetime.now()))
        outfile.close()
    sshsession.close()


# Threading function is in the main (take note that running this script password change will initiate to all the IP address provided)
def main():
    global data
    global pwd
    for ip in TestClusterNodes: #loop to all the IP in TestClusternodes var then initiate ChangePlatformPW function at the same time for all the ip :), data can be defined or get from excel, json(I used JSON)
        my_thread = threading.Thread(target=ChangePlatformPw, args=(ip, TestClusterUname, TestPwd, NewPlatpw, command))
        my_thread.start()
        # Wait for all threads to complete
    main_thread = threading.currentThread()
    for some_thread in threading.enumerate():
        if some_thread != main_thread:
            some_thread.join()

#when program starts run the main funtion
if __name__ == "__main__":
    main()

