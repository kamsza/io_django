#!/bin/python3

from sys import argv
from threading import Thread
from time import sleep
import unbound
import psycopg2

# our own module used by several scripts in the project
from ztdns_db_connectivity import start_db_connection, get_ztdns_config

class dns_queries:
    def __init__(self, dns_IP, dns_id, services):
        self.dns_IP = dns_IP
        self.dns_id = dns_id
        self.services = services

class single_query:
    def __init__(self, hour, cursor, vpn_id, dns_id, service_id):
        self.hour = hour
        self.cursor = cursor
        self.vpn_id = vpn_id
        self.dns_id = dns_id
        self.service_id = service_id

def query_planned_queries(cursor, hour, vpn_id):
    # return [
    #     #           dns server IP   | dns server id | service_id | service_name
    #     dns_queries("195.98.79.117",  23,           [[89,          "devuan.org"],
    #                                                  [44,          "gry.pl"],
    #                                                  [112,         "invidio.us"]]),
    #     dns_queries("192.71.245.208", 33,           [[77,          "debian.org"],
    #                                                  [22,          "nie.ma.takiej.domeny"],
    #                                                  [100,         "onet.pl"]])
    # ]
    cursor.execute('''
    SELECT DISTINCT d."IP", d.id
    FROM user_side_queries AS q JOIN user_side_dns AS d
    ON d.id = q.dns_id
    WHERE q.vpn_id = %s
    ''', (vpn_id,))
    dnss = cursor.fetchall()

    dnss_to_query = []
    
    for dns_IP, dns_id in dnss:
        cursor.execute('''
        SELECT s.id, s.name
        FROM user_side_service AS s JOIN user_side_queries AS q
        ON s.id = q.service_id
        WHERE q.vpn_id = %s AND q.dns_id = %s
        ''', (vpn_id, dns_id))
        
        queries = dns_queries(dns_IP, dns_id, cursor.fetchall())
        
        dnss_to_query.append(queries)

    return dnss_to_query

def resolve_call_back(mydata, status, result):
    query = mydata
    # debugging
    print("callback called for {}".format(result.qname))
    if status==0 and result.havedata:
        result_info = 'successful'
        print("Result:",result.data.address_list)
    else:
        result_info = 'not found'
    # write to database
    try:
        query.cursor.execute('''
        INSERT INTO user_side_responses
            (date, result, dns_id, service_id, vpn_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        ''', (query.hour, result_info, query.dns_id,
              query.service_id, query.vpn_id))

        responses_id = query.cursor.fetchone()[0]

        if status==0 and result.havedata:
            for address in result.data.address_list:
                query.cursor.execute('''
                INSERT INTO user_side_response (returned_ip, responses_id)
                VALUES(%s, %s)
                ''', (address, responses_id))
    except psycopg2.IntegrityError:
        # Unique constraint is stopping us from adding duplicates;
        # This is most likey because back-end has been run multiple times
        # during the same hour (bad configuration or admin running manually
        # after cron)
        pass
    # no committing, since auto-commit mode is set on the connection

hour = argv[1]
vpn_id = argv[2]
config = get_ztdns_config()

def query_dns(dns_queries):
    connection = start_db_connection(config)
    cursor = connection.cursor()
    ctx = unbound.ub_ctx()
    ctx.set_fwd(dns_queries.dns_IP)
    
    first = True
    for service_id, service_name in dns_queries.services:
        if first:
            first = False
        else:
            sleep(0.4) # throttle between queries

        print("starting resolution of {} through {}".format(service_name,
                                                            dns_queries.dns_IP))
        query = single_query(hour, cursor, vpn_id,
                             dns_queries.dns_id, service_id)

        ctx.resolve_async(service_name, query, resolve_call_back,
                          unbound.RR_TYPE_A, unbound.RR_CLASS_IN)

    ctx.wait()
    cursor.close()
    connection.close()

connection = start_db_connection(config)
cursor = connection.cursor()
planned_queries = query_planned_queries(cursor, hour, vpn_id)
# each thread will make its own connection
cursor.close()
connection.close()
    
threads = []
for dns_queries in planned_queries:
    thread = Thread(target = query_dns, args = (dns_queries,))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()

cursor.close()
connection.close()
