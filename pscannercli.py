import subprocess
import re
import sqlite3
import sys, getopt


def initialize_db():
    '''Creates a sqlite DB (if doesn't exist) and return the DB connection'''

    print('Initializing db...')

    connection = sqlite3.connect('port_scanning.db')
    cursor = connection.cursor()

    cursor.execute('''
                create table if not exists ports_info(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host VARCHAR(16) NOT NULL,
                port INTEGER NOT NULL,
                state VARCHAR(30) NOT NULL,
                service VARCHAR(100) NOT NULL,
                UNIQUE (host, port, state, service)
                );''')
    connection.commit()

    print('Done!\n')
    return connection


def get_hosts(network, mask):
    '''Recieves a network and its mask, scans the active hosts (IPs) and return
    them as a list'''

    print('Scanning hosts...')

    p = subprocess.Popen(['/bin/bash', '-c', f'nmap -sP {network}/{mask}'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    output, error = p.communicate()
    output = output.decode('utf-8') # Contains the terminal output
    error = error.decode('utf-8') # Contains the error if there is one

    if error:
        print(f'\nThere was a problem with nmap host scanning execution:\n {error}')
        sys.exit(2)
    else:
        # Finds the available hosts (IPs) as a list
        pattern = '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        hosts = re.findall(pattern, output, re.MULTILINE)
        print(f'{len(hosts)} hosts found')
        print('Done!\n')
        return hosts


def get_ports_info(hosts):
    '''Recieves a list of hosts (IPs) and gets the ports, its states and and
    the services running in each port. Returns a list with 2 values: hosts and
    a list of tuples with the ports info:
    ['host', [(port1, state1, service1), (port2, state2, service2), ...]]'''

    final_result = []

    for host in hosts:
        print(f'Host {host} is active. Scanning ports...')

        p = subprocess.Popen(['/bin/bash', '-c', f'nmap -sT {host}'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        output, error = p.communicate()
        output = output.decode('utf-8') # Contains the terminal output
        error = error.decode('utf-8') # Contains the error if there is one
        result =[]

        if error:
            print(f'\nThere was a problem with nmap port scanning execution:\n {error}')
        else:
            # Find the pattern and append the host and a list of tuples with
            # the ports, states and services
            pattern = '^(\d+)\S+ +(\S+) +(\S+)$'
            result = re.findall(pattern, output, re.MULTILINE)
            final_result.append([host] + [result])


            # Prints the current host info
            if result:
                for port, state, service in result:
                    print(f'Port: {port} | State: {state} | Service: {service}')
            else:
                print('No ports available')

        print('Done!\n')

    return final_result


def store_data(hosts_info, connection):
    '''Recieves the hosts_info (host, ports, states, services), the DB
    connection and stores that data in the DB'''

    print('Storing data...')

    cursor = connection.cursor()

    for host_ports_info in hosts_info:

        # Splits the host and the list of tuples with the ports, states and
        # services
        host, ports_info = host_ports_info

        # If "ports_info" is empty (empty list) the for loop won't be executed
        # So no problem with "NOT NULL" fields in the DB
        for port, state, service in ports_info:
            data = cursor.execute(f"""
                                select * from ports_info
                                 where host = '{host}'
                                 and port = {port}
                                 and state = '{state}'
                                 and service = '{service}'
                                 """)

            # If the row exists don't do anything, else insert a row with the
            # values
            if not data.fetchone():
                cursor.execute(f"""
                        insert into ports_info
                        (host, port, state, service)
                        values('{host}',{port}, '{state}', '{service}')
                               """)
                connection.commit()

    print('Done!\n\n')


def parse_command_line_arguments():
    '''Parse the argument given in the command line and returns the network and
    mask to be processed'''
    try:
        options_arguments, _ = getopt.getopt(sys.argv[1:], 'hn:m:',
                                       ['help', 'network=', 'mask='])
    except getopt.error as err:
        print ('(-h | --help)')
        print ('(-n | --network=) <network> (-m | --mask=) <mask>')
        sys.exit(2)

    network = ''
    mask = ''

    for option, argument in options_arguments:
        if option in ['-h', '--help']:
            print ('(-h | --help)')
            print ('(-n | --network=) <network> (-m | --mask=) <mask>')
        elif option in ['-n', '--network']:
            network = argument
        elif option in ['-m', '--mask']:
            mask = argument
        else:
            print ('(-h | --help)')
            print ('(-n | --network=) <network> (-m | --mask=) <mask>')

    return network, mask


if __name__ == '__main__':
    network, mask =parse_command_line_arguments()
    connection = initialize_db()
    hosts = get_hosts(network, mask)
    hosts_info = get_ports_info(hosts)
    store_data(hosts_info, connection)
