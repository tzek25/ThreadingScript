from concurrent.futures import ThreadPoolExecutor
from genie.conf import Genie
from rugm_genie_database import *
from genie.metaparser.util.exceptions import InvalidCommandError, SchemaEmptyParserError
from unicon.core.errors import SubCommandFailure
import json

with open('credentials.json', mode='r') as f:
    creds = json.load(f)

Username = creds['Username']
Password = creds['Password']

inventory = lookup('inventory.txt').lookup_dict()  # CREATE DICTIONARY INVENTORY
testbed_yaml = dict_to_yaml(inventory, 'testbeds/inventory', Username, Password)  # GENERATE DICTIONARY TO YAML TESTBED

start_time = datetime.now() 	# WILL BE USED TO RECORD COMPLETION TIME
print('{} START SCRIPT {}'.format('#-' * 20, '-#' * 20)) 	# START SCRIPT
testbed = Genie.init(testbed_yaml) 		# INITIALIZE/LOAD TESTBED
devices = [] 	# PUT ALL TESTBED OBJECTS INSIDE THIS LIST FOR THREADING
device_failed = {}		# PUT ALL FAILED DEVICES HERE


for device in testbed.devices:
    devices.append(device)


def to_do(hostname):		# TASK TO DO
    tb = testbed.devices[hostname]
    try:
        tb.connect(log_stdout=False)

        if tb.type == 'IOSXE':
            command_file = 'ios.txt'
        else:
            command_file = 'nxos.txt'

        output_text = {}
        with open(f'Predefined_commands/{command_file}', 'r') as f:
            show_commands = f.read().splitlines()

        for command in show_commands:
            try:
                val = tb.execute(command)
                output_text[command] = val
            except SubCommandFailure:
                val = 'InvalidCommandError'
                output_text[command] = val

        filename = f'{tb.alias}.txt'
        with open(f'script_outputs/{filename}', 'w') as txtfile:
            for k, val in output_text.items():
                txtfile.write('# ' * 20 + k + ' #' * 20 + '\n')
                txtfile.write(f'{val}\n\n')

        print(f'{hostname} :: COMPLETE')
        tb.disconnect()

    except Exception as g:
        device_failed[hostname] = g
        print(f'{hostname} :: FAILED')
        tb.disconnect()


with ThreadPoolExecutor(max_workers=100) as executor:  # ACTUAL THREADING BY BATCH OF 100
    executor.map(to_do, devices)


print('\n{} FAILED DEVICES {}'.format('#-' * 20, '-#' * 21)) 	# FAILED DEVICES BANNER
if device_failed != {}:
    for k, val in device_failed.items():		# DISPLAY DEVICES WHICH ENCOUNTERED ERROR
        print(f'{k} :: {val}')
else:
    print(f'NO. FAILED DEVICES == {str(len(device_failed))}')
print('\n{} END SCRIPT {}'.format('#-' * 20, '-#' * 20)) 	# END SCRIPT
print("Elapsed time: {} seconds\n".format(str(datetime.now() - start_time)))  # SCRIPT COMPLETION TIME
