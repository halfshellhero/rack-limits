#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, pyrax, argparse, json, requests, getpass, math
from prettytable import PrettyTable
from rackspace_monitoring.providers import get_driver
from rackspace_monitoring.types import Provider


# Handy functions
def get_compute_limits(region):
    """ Returns a dictionary containing the absolute limits in desired region """
    cs = eval("%s" % 'ctx.' + region + '.compute.client')
    limits_tmp = cs.limits.get()
    absolute_dict = limits_tmp.to_dict()
    return absolute_dict

def get_cbs_limits(region):
    """ Returns a dictionary containing the absolute limits in desired region """
    cbs = eval("%s" % 'ctx.' + region + '.volume.client')
    limits_dict = cbs.get_limits()
    return limits_dict

def get_cbs_usage(region):
    """ Returns the total usage for CBS in desired region """
    cbs = eval("%s" % 'ctx.' + region + '.volume.client')
    all_cbs = cbs.list()
    total_disk = 0
    total_volumes = len(all_cbs)
    x = 0
    while (x < len(all_cbs)):
        total_disk = total_disk + all_cbs[x].size
        x = x + 1
    return total_disk,total_volumes

def get_clb_usage(region):
    """ Returns the total usage for LBaaS in desired region """
    clb = eval("%s" % 'ctx.' + region + '.load_balancer.client')
    all_clbs = clb.list()
    return len(all_clbs)

def get_clb_limits(region):
    """ Returns a dictionary containing the absolute limits in desired region """
    headers = {'Content-Type': 'application/json'}
    token = ctx.auth_token
    url = 'https://' + region.lower() + '.loadbalancers.api.rackspacecloud.com/v1.0/' + args.account + '/loadbalancers/absolutelimits'
    limit_req = requests.get(url, headers={'X-Auth-Token': token })
    return limit_req.json()

def get_mon_alarm_usage(username, key):
    """ Returns the number (integer) of alarms for the account """
    Cls = get_driver(Provider.RACKSPACE)
    driver = Cls(username, key)
    overview = driver.ex_views_overview()
    total_alarms = 0
    x = 0
    while x < len(overview):
        total_alarms = total_alarms + len(overview[x]['alarms'])
        x = x + 1
    return total_alarms


def get_mon_check_usage(username, key):
    """ Returns the number (integer) of checks for the account """
    Cls = get_driver(Provider.RACKSPACE)
    driver = Cls(username, key)
    overview = driver.ex_views_overview()
    total_checks = 0
    x = 0
    while x < len(overview):
        total_checks = total_checks + len(overview[x]['checks'])
        x = x + 1
    return total_checks

def get_mon_limits(username, key):
    """ Obtains absolute limits for alarms and checks """
    Cls = get_driver(Provider.RACKSPACE)
    driver = Cls(username, key)
    maas_limits = driver.ex_limits()
    return maas_limits


def percentage(used, quota):
    """ Takes two numbers return a percentage value in str format """
    perc = str(int((used / float(quota)) * 100)) + '%'
    return perc



#Gather required command line arguments
parse = argparse.ArgumentParser(description='Report on resource usage')
#parse.add_argument('-r', '--region', required=True, help='Region: dfw, ord, iad, hkg, syd, lon')
parse.add_argument('-u', '--username', required=True, help='API Username')
parse.add_argument('-a', '--account', required=True, help='Account number')
args = parse.parse_args()
#region = args.region.upper()
key = getpass.getpass(prompt='API Key: ')

#Setting Credentials
pyrax.set_setting("identity_type", "rackspace")
pyrax.set_credentials(args.username, key)

#Creating contexts to allow for multiple regions
ctx = pyrax.create_context()
ctx.set_credentials(args.username, password=key)
ctx.authenticate()

#Printing formatted output
output = PrettyTable(["Region", "Compute Ram (GB)", "Compute Instance", "Networks", "LBaaS", "CBS Disk (GB)", "CBS Volume"])
#x.align["Region"] = "l" # Left align city names
output.padding_width = 1

region_list = ['DFW', 'IAD', 'ORD', 'SYD', 'HKG']
count = 0

while count < len(region_list):
    #Obtaining and setting up vars for absolute limits
    compute_limits = get_compute_limits(region_list[count])
    cbs_limits = get_cbs_limits(region_list[count])
    clb_limits = get_clb_limits(region_list[count])
    
    ram_quota = compute_limits['absolute']['maxTotalRAMSize']
    instance_quota = compute_limits['absolute']['maxTotalInstances']
    networks_quota = compute_limits['absolute']['maxTotalPrivateNetworks']
    
    cbs_disk_quota =  cbs_limits['limits']['absolute']['maxTotalVolumeGigabytes']
    cbs_volume_quota =  cbs_limits['limits']['absolute']['maxTotalVolumes']
    
    clb_quota = clb_limits['absolute'][1]['value']

    maas_quota = get_mon_limits(args.username, key)
    maas_check_quota = maas_quota['resource']['checks']
    maas_alarm_quota = maas_quota['resource']['alarms']
    
    #Obtaining and setting up vars for current usage
    ram_usage = compute_limits['absolute']['totalRAMUsed']
    instance_usage = compute_limits['absolute']['totalInstancesUsed']
    networks_usage = compute_limits['absolute']['totalPrivateNetworksUsed']
    
    cbs_disk_usage = get_cbs_usage(region_list[count])[0]
    cbs_volume_usage = get_cbs_usage(region_list[count])[1]
    
    clb_usage = get_clb_usage(region_list[count])

    maas_alarms = get_mon_alarm_usage(args.username, key)
    maas_checks = get_mon_check_usage(args.username, key)

    output.add_row([region_list[count], str(ram_usage/1024) + '/' + \
    str(ram_quota/1024) + ' ' + percentage(ram_usage, ram_quota), \
    str(instance_usage) + '/' + str(instance_quota) + ' ' + \
    percentage(instance_usage, instance_quota), str(networks_usage) \
    + '/' + str(networks_quota) + ' ' + percentage(networks_usage, \
    networks_quota), str(clb_usage) + '/' + str(clb_quota) + ' ' + \
    percentage(clb_usage, clb_quota), str(cbs_disk_usage) + '/' + \
    str(cbs_disk_quota) + ' ' + percentage(cbs_disk_usage, cbs_disk_quota)\
    , str(cbs_volume_usage) + '/' + str(cbs_volume_quota) + ' ' + \
    percentage(cbs_volume_usage, cbs_volume_quota)])

    count = count + 1

output.add_column("MaaS Alarms",["","",str(maas_alarms) + '/' + str(maas_alarm_quota) + ' ' + percentage(maas_alarms, maas_alarm_quota),"",""])
output.add_column("MaaS Checks",["","",str(maas_checks) + '/' + str(maas_check_quota) + ' ' + percentage(maas_checks, maas_check_quota),"",""])


print output
