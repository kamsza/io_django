#!/bin/python3

from sys import argv
import subprocess
from os import path, waitpid, unlink
from time import gmtime, strftime, sleep

# our own module used by several scripts in the project
from ztdnslib import start_db_connection, \
    get_default_host_address, get_ztdns_config

wrapper = '/var/lib/0tdns/vpn_wrapper.sh'
perform_queries = '/var/lib/0tdns/perform_queries.py'
lockfile = '/var/lib/0tdns/lockfile'

def sync_ovpn_config(cursor, vpn_id, config_path, config_hash):
    cursor.execute('''
    select ovpn_config
    from user_side_vpn
    where id = %s and ovpn_config_sha256 = %s
    ''', (vpn_id, config_hash))

    (config_contents,) = cursor.fetchone()

    with open(config_path, "wb") as config_file:
        config_file.write(config_contents.tobytes())

def get_vpn_connections(cursor, hour):
    # return (
    #     # vpn_id | config_path
    #     (14,       "./vpngate_178.254.251.12_udp_1195.ovpn"),
    #     (13,       "./vpngate_public-vpn-229.opengw.net_tcp_443.ovpn")
    # )
    cursor.execute('''
    SELECT DISTINCT v.id, v.ovpn_config_sha256
    FROM user_side_queries AS q JOIN user_side_vpn AS v
    ON v.id = q.vpn_id;
    ''')
    return cursor.fetchall()

# return True on success and False if lock exists
def lock_on_file():
    try:
        with open(lockfile, 'x'):
            return True
    except FileExistsError:
        return False

# return True on success and False if lock got removed in the meantime
def unlock_on_file():
    try:
        unlink(lockfile)
        return True
    except FileNotFoundError:
        return False

def do_hourly_work(hour, logfile):
    ztdns_config = get_ztdns_config()
    if ztdns_config['enabled'] != 'yes':
        logfile.write("0tdns not enabled in the config - exiting\n")
        exit()

    connection = start_db_connection(ztdns_config)
    cursor = connection.cursor()

    vpns = get_vpn_connections(cursor, hour)

    handled_vpns = ztdns_config.get('handled_vpns')
    if handled_vpns:
        logfile.write("Only handling vpns of ids {}\n".format(handled_vpns))
        vpns = [vpn for vpn in vpns if vpn[0] in handled_vpns]
    else:
        # if not specfied in the config, all vpns are handled
        hadled_vpns = [vpn[0] for vpn in vpns]

    for vpn_id, config_hash in vpns:
        config_path = "/var/lib/0tdns/{}.ovpn".format(config_hash)
        if not path.isfile(config_path):
            logfile.write("Syncing config for vpn {} with hash {}\n"\
                          .format(vpn_id, config_hash))
            sync_ovpn_config(cursor, vpn_id, config_path, config_hash)

    parallel_vpns = ztdns_config['parallel_vpns']
    pids_vpns = {} # map each wrapper pid to id of the vpn it connects to

    def wait_for_wrapper_process():
        while True:
            pid, exit_status = waitpid(0, 0)
            # make sure 
            if pids_vpns.get(pid) is not None:
                break
        if exit_status == 2:
            # this means our perform_queries.py crashed... not good
            logfile.write('performing queries through vpn {} failed\n'\
                          .format(pids_vpns[pid]))
        elif exit_status != 0:
            # vpn server is probably not responding
            logfile.write('connection to vpn {} failed\n'\
                          .format(pids_vpns[pid]))
        pids_vpns.pop(pid)

    for vpn_id, config_hash in vpns:
        if len(pids_vpns) == parallel_vpns:
            wait_for_wrapper_process()

        config_path = "/var/lib/0tdns/{}.ovpn".format(config_hash)
        physical_ip = get_default_host_address(ztdns_config['host'])
        route_through_veth = ztdns_config['host'] + "/32"
        command_in_namespace = [perform_queries, hour, str(vpn_id)]
        logfile.write("Running connection for vpn {}\n".format(vpn_id))
        
        p = subprocess.Popen([wrapper, config_path, physical_ip,
                              route_through_veth] + command_in_namespace)

        pids_vpns[p.pid] = vpn_id

    while len(pids_vpns) > 0:
        wait_for_wrapper_process()

    cursor.execute('''
    INSERT INTO user_side_responses(date, result, dns_id, service_id, vpn_id)
    (SELECT TIMESTAMP WITH TIME ZONE %s,
            'internal failure: vpn_connection_failure',
            q.dns_id, q.service_id, q.vpn_id
     FROM user_side_responses AS r RIGHT JOIN user_side_queries AS q
          ON q.service_id = r.service_id AND
             q.dns_id = r.dns_id AND
             q.vpn_id = r.vpn_id AND
             date = %s
     WHERE r.id IS NULL AND q.vpn_id = ANY(%s));
    ''', (hour, hour, handled_vpns))

    cursor.close()
    connection.close()


with open("/var/log/0tdns.log", "a") as logfile:
    # round down to an hour - this datetime format is one
    # of the formats accepted by postgres
    hour = strftime('%Y-%m-%d %H:00%z', gmtime())
    if not lock_on_file():
        logfile.write("Failed trying to run for {}; {} exists\n"\
                      .format(hour, lockfile))
    else:
        try:
            logfile.write("Running for {}\n".format(hour))
            do_hourly_work(hour, logfile)
        finally:
            if not unlock_on_file():
                logfile.write("Can't remove lock - {} already deleted!\n"\
                              .format(lockfile))
                        
