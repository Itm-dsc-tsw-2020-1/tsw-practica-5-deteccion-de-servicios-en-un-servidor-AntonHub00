import subprocess
import re
import sqlite3
import sys, getopt


def initialize_db():
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

    print('Done\n')
    return connection


def get_hosts(network, mask):
    print('Scanning hosts...')

    p = subprocess.Popen(['/bin/bash', '-c', f'nmap -sP {network}/{mask}'],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    output, error = p.communicate()
    output = output.decode('utf-8')
    error = error.decode('utf-8')

    if error:
        print(f'\nThere was a problem with nmap host scanning execution:\n {error}')
        sys.exit(2)
    else:
        pattern = '(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        hosts = re.findall(pattern, output, re.MULTILINE)
        print('Done\n')
        return hosts


def get_ports_info(hosts):
    final_result = []

    for host in hosts:
        print(f'Host {host} is active. Scanning ports...')

        p = subprocess.Popen(['/bin/bash', '-c', f'nmap -sT {host}'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        output, error = p.communicate()
        output = output.decode('utf-8')
        error = error.decode('utf-8')
        result =[]

        if error:
            print(f'\nThere was a problem with nmap port scanning execution:\n {error}')
        else:
            pattern = '^(\d+)\S+ +(\S+) +(\S+)$'
            result = re.findall(pattern, output, re.MULTILINE)
            final_result.append([host] + [result])

        print('Done\n')

    return final_result


def store_data(hosts_info, connection):
    print('Storing data...')

    cursor = connection.cursor()

    for host_ports_info in hosts_info:
        host, ports_info = host_ports_info
        for port, state, service in ports_info:
            # print(f'Host: {host} | Port: {port} | State: {state} | Service: {service}')

            data = cursor.execute(f"""
                                select * from ports_info
                                 where host = '{host}'
                                 and port = {port}
                                 and state = '{state}'
                                 and service = '{service}'
                                 """)

            if not data.fetchone():
                cursor.execute(f"""
                        insert into ports_info
                        (host, port, state, service)
                        values('{host}',{port}, '{state}', '{service}')
                               """)
                connection.commit()

    print('Done\n\n')



def main(network, mask):

    connection = initialize_db()
    hosts = get_hosts(network, mask)
    hosts_info = get_ports_info(hosts)
    store_data(hosts_info, connection)


if __name__ == '__main__':
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

    main(network, mask)
