#!/bin/python3

from sys import argv
import yaml
import psycopg2
import hashlib

db_config_path = '/etc/0tdns/db_connection_config.yml'

ovpn_config_path = argv[1]

with open(ovpn_config_path) as file:
    ovpn_config_text = file.read()

ovpn_config_raw = bytearray(ovpn_config_text, encoding='utf-8')

ovpn_config_hash = hashlib.sha256(ovpn_config_raw).hexdigest()

config = yaml.safe_load(open(db_config_path, 'r'))
connection = psycopg2.connect(user=config['user'], password=config['password'],
                              host=config['host'], port=config['port'],
                              database=config['database'])
cursor = connection.cursor()

cursor.execute('''
INSERT INTO vpn (location_id, ovpn_config, ovpn_config_sha256)
VALUES(%s, %s, %s)''', (11, ovpn_config_text, ovpn_config_hash))

connection.commit()
cursor.close()
connection.close()
