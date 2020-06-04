#!/bin/python3

from sys import argv
import subprocess
import os.path
import yaml
import psycopg2

wrapper = '/var/lib/0tdns/vpn_wrapper.sh'
perform_queries = '/var/lib/0tdns/perform_queries.py'
db_config_path = '/etc/0tdns/db_connection_config.yml'

def sync_ovpn_config(cursor, vpn_id, config_path, config_hash):
    cursor.execute('''
    select ovpn_config
    from user_side_vpn
    where id = %s and ovpn_config_sha256 = %s
    ''', (vpn_id, config_hash))
    
    (config_contents,) = cursor.fetchone()
    
    with open(config_path, "w") as config_file:
        config_file.write(config_contents)

def get_vpn_connections(cursor, hour):
    # return (
    #     # vpn_id | config_path
    #     (14,       "./vpngate_178.254.251.12_udp_1195.ovpn"),
    #     (13,       "./vpngate_public-vpn-229.opengw.net_tcp_443.ovpn")
    # )
    cursor.execute('''
    select v.id, v.ovpn_config_sha256
    from user_side_queries as q join user_side_vpn as v
    on v.id = q.vpn_id;
    ''')
    return cursor.fetchall()

config = yaml.safe_load(open(db_config_path, 'r'))
connection = psycopg2.connect(user=config['user'], password=config['password'],
                              host=config['host'], port=config['port'],
                              database=config['database'])
cursor = connection.cursor()

hour = argv[1]
vpns = get_vpn_connections(cursor, hour)

for vpn_id, config_hash in vpns:
    config_path = "/var/lib/0tdns/{}.ovpn".format(config_hash)
    if not os.path.isfile(config_path):
        sync_ovpn_config(cursor, vpn_id, config_path, config_hash)

cursor.close()
connection.close()

for vpn_id, config_hash in vpns:
    config_path = "/var/lib/0tdns/{}.ovpn".format(config_hash)
    subprocess.run([wrapper, config_path, perform_queries, hour, vpn_id])
