import yaml
import psycopg2
import os
import fcntl
from time import gmtime, strftime

db_config_path = '/etc/0tdns/db_connection_config.yml'
logfile = '/var/log/0tdns.log'

def get_ztdns_config():
    return yaml.safe_load(open(db_config_path, 'r'))

def start_db_connection(config):
    connection = psycopg2.connect(user=config['user'], password=config['password'],
                                  host=config['host'], port=config['port'],
                                  database=config['database'])
    # we might later decide that each user of start_db_connection()
    # should set it themselves - but for now, set it here
    connection.autocommit = True
    return connection

# we'll use it for setting SNAT
# https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
def get_default_host_address(remote_address):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((remote_address, 80))
    hostaddr = s.getsockname()[0]
    s.close()
    return hostaddr

loghour = None

def set_loghour(hour):
    global loghour
    loghour = hour

def log(msg):
    msg = '[{}] {}'.format(strftime('%H:%M', gmtime()), msg)
    if loghour:
        msg = '[{}]{}'.format(loghour, msg)
    msg = bytearray(msg + '\n', "UTF-8")
    fd = os.open(logfile, os.O_APPEND | os.O_WRONLY | os.O_CREAT)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.write(fd, msg)
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
