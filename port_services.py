import subprocess
import re
import sqlite3

## Begin DB ###################################################################
connection = sqlite3.connect('open_ports.db')
cursor = connection.cursor()

cursor.execute('''create table if not exists port_state_service(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             host VARCHAR(16) NOT NULL,
             port INTEGER NOT NULL,
             state VARCHAR(30) NOT NULL,
             service VARCHAR(100) NOT NULL,
             UNIQUE (host, port, state, service)
             );''')
connection.commit()
## End DB #####################################################################

network = '200.33.171'

print('Scanning hosts...\n')

p = subprocess.Popen(['/bin/bash', '-c', f'nmap -sP {network}.0/24'],
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE)
host_scan_output, host_scan_error = p.communicate()
host_scan_output = host_scan_output.decode('utf-8')
host_scan_error = host_scan_error.decode('utf-8')

if host_scan_error:
    print(f'\nThere was a problem with nmap host scanning execution:\n {host_scan_error}')
else:
    pattern = '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    hosts = re.findall(pattern, host_scan_output, re.MULTILINE)

    for host in hosts:
        print(f'The host ({host}) is active. Scanning ports...')

        p = subprocess.Popen(['/bin/bash', '-c', f'nmap -sT {host}'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        port_scan_output, port_scan_error = p.communicate()
        port_scan_output = port_scan_output.decode('utf-8')
        port_scan_error = port_scan_error.decode('utf-8')

        if port_scan_error:
            print(f'\nThere was a problem with nmap port scanning execution:\n {port_scan_error}')
        else:
            pattern = '^(\d+)\S+ +(\S+) +(\S+)$'
            result = re.findall(pattern, port_scan_output, re.MULTILINE)

            for port, state, service in result:
                print(f'Host: {host} | Port: {port} | State: {state} | Service: {service}')

                data = cursor.execute(f"""
                                    select * from port_state_service
                                     where host = '{host}'
                                     and port = {port}
                                     and state = '{state}'
                                     and service = '{service}'
                                     """)

                if not data.fetchone():
                    cursor.execute(f"""
                            insert into port_state_service
                            (host, port, state, service)
                            values('{host}',{port}, '{state}', '{service}')
                                   """)
                    connection.commit()

        print()
