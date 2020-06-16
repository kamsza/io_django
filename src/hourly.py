#!/bin/python3

from sys import argv
import subprocess
from os import path, waitpid, unlink
from time import gmtime, strftime, sleep
import re

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

address_range_regex = re.compile(r'''
([\d]+\.[\d]+\.[\d]+\.[\d]+) # first IPv4 address in the range

[\s]*-[\s]*                  # dash (with optional whitespace around)

([\d]+\.[\d]+\.[\d]+\.[\d]+) # last IPv4 address in the range
''', re.VERBOSE)

address_regex = re.compile(r'([\d]+)\.([\d]+)\.([\d]+)\.([\d]+)')

def ip_address_to_number(address):
    match = address_regex.match(address)
    if not match:
        return None
    number = 0
    for byte in match.groups():
        byteval = int(byte)
        if byteval > 256:
            return None
        number = number * 256 + byteval
    return number

def number_to_ip_address(number):
    byte1 = number % 256
    number = number // 256
    byte2 = number % 256
    number = number // 256
    byte3 = number % 256
    number = number // 256
    byte4 = number % 256
    return "{}.{}.{}.{}".format(byte4, byte3, byte2, byte1)

# this functions accepts list of IPv4 address ranges like:
#     ['10.25.25.0 - 10.25.25.59', '10.25.25.120 - 10.25.25.135']
# and returns a set of /30 subnetworks; each subnetwork is represented
# by a tuple of 2 usable addresses within that subnetwork.
# E.g. for subnetwork 10.25.25.16/30 it would be ('10.25.25.17', '10.25.25.18');
# Addressess ending with .16 (subnet address)
# and .19 (broadcast in the subnet) are considered unusable in this case.
# The returned set will contain up to count elements.
def get_available_subnetworks(count, address_ranges, logfile):
    available_subnetworks = set()

    for address_range in address_ranges:
        match = address_range_regex.match(address_range)
        ok_flag = True

        if not match:
            ok_flag = False

        if ok_flag:
            start_addr_number = ip_address_to_number(match.groups()[0])
            end_addr_number = ip_address_to_number(match.groups()[1])
            if not start_addr_number or not end_addr_number:
                ok_flag = False

        if ok_flag:
            # round so that start_addr is first ip address in a /30 network
            # and end_addr is last ip address in a /30 network
            while start_addr_number % 4 != 0:
                start_addr_number += 1
            while end_addr_number % 4 != 3:
                end_addr_number -= 1

            if start_addr_number >= end_addr_number:
                logfile.write("address range '{}' doesn't contain any"
                              " /30 subnetworks\n".format(address_range))
            else:
                while len(available_subnetworks) < count and \
                      start_addr_number < end_addr_number:
                    usable_addr1 = number_to_ip_address(start_addr_number + 1)
                    usable_addr2 = number_to_ip_address(start_addr_number + 2)
                    available_subnetworks.add((usable_addr1, usable_addr2))
                    start_addr_number += 4
        else:
            logfile.write("'{}' is not a valid address range\n"\
                          .format(address_range))

    return available_subnetworks

def do_hourly_work(hour, logfile):
    ztdns_config = get_ztdns_config()
    if ztdns_config['enabled'] != 'yes':
        logfile.write("0tdns not enabled in the config - exiting\n")
        return

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

    parallel_vpns = ztdns_config['parallel_vpns'] # we need this many subnets
    subnets = get_available_subnetworks(parallel_vpns,
                                        ztdns_config['private_addresses'],
                                        logfile)

    if not subnets:
        logfile.write("couldn't get ANY /30 subnet of private addresses from"
                      " the 0tdns config file - exiting\n");
        return # TODO close cursor and connection here

    if len(subnets) < parallel_vpns:
        logfile.write("configuration allows running {0} parallel vpn"
                      " connections, but provided private ip addresses give"
                      " only {1} /30 subnets, which limits parallel connections"
                      " to {1}\n".format(parallel_vpns, len(subnets)))
        parallel_vpns = len(subnets)
    
    for vpn_id, config_hash in vpns:
        config_path = "/var/lib/0tdns/{}.ovpn".format(config_hash)
        if not path.isfile(config_path):
            logfile.write("Syncing config for vpn {} with hash {}\n"\
                          .format(vpn_id, config_hash))
            sync_ovpn_config(cursor, vpn_id, config_path, config_hash)

    # map of each wrapper pid to tuple containing id of the vpn it connects to
    # and subnet (represented as tuple of addresses) it uses for veth device
    pids_wrappers = {}

    def wait_for_wrapper_process():
        while True:
            pid, exit_status = waitpid(0, 0)
            # make sure it's one of our wrapper processes
            vpn_id, subnet, _ = pids_wrappers.get(pid, (None, None, None))
            if subnet:
                break

        if exit_status == 2:
            # this means our perform_queries.py crashed... not good
            logfile.write('performing queries through vpn {} failed\n'\
                          .format(vpn_id))
        elif exit_status != 0:
            # vpn server is probably not responding
            logfile.write('connection to vpn {} failed\n'\
                          .format(vpn_id))
        pids_wrappers.pop(pid)
        subnets.add(subnet)

    for vpn_id, config_hash in vpns:
        if len(pids_wrappers) == parallel_vpns:
            wait_for_wrapper_process()

        config_path = "/var/lib/0tdns/{}.ovpn".format(config_hash)
        physical_ip = get_default_host_address(ztdns_config['host'])
        subnet = subnets.pop()
        veth_addr1, veth_addr2 = subnet
        route_through_veth = ztdns_config['host'] + "/32"
        command_in_namespace = [perform_queries, hour, str(vpn_id)]
        logfile.write("Running connection for vpn {}\n".format(vpn_id))

        p = subprocess.Popen([wrapper, config_path, physical_ip, veth_addr1,
                              veth_addr2, route_through_veth] +
                             command_in_namespace)

        pids_wrappers[p.pid] = (vpn_id, subnet, p)

    while len(pids_wrappers) > 0:
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
                        
