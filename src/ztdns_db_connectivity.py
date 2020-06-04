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
