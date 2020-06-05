import yaml
import psycopg2

db_config_path = '/etc/0tdns/db_connection_config.yml'

def start_db_connection():
    config = yaml.safe_load(open(db_config_path, 'r'))
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
    config = yaml.safe_load(open(db_config_path, 'r'))
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((config['database'], 80))
    hostaddr = s.getsockname()[0]
    s.close()
    return hostaddr
