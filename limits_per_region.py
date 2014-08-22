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
    total_ram = 0
    total_volumes = len(all_cbs)
    x = 0
    while (x < len(all_cbs)):
        total_ram = total_ram + all_cbs[x].size
        x = x + 1
    return total_ram,total_volumes

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

def get_mon_usage(username, key):
    """ Returns the number (integer) of checks and alarms for the account """
    Cls = get_driver(Provider.RACKSPACE)
    driver = Cls(username, key)
    overview = driver.ex_views_overview()
    total_checks = 0
    total_alarms = 0
    x = 0
    while x < len(overview):
        total_alarms = total_alarms + len(overview[x]['alarms'])
        total_checks = total_checks + len(overview[x]['checks'])
        x = x + 1
    return total_checks,total_alarms

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
parse.add_argument('-r', '--region', required=True, help='Region: dfw, ord, iad, hkg, syd, lon')
parse.add_argument('-u', '--username', required=True, help='API Username')
parse.add_argument('-a', '--account', required=True, help='Account number')
args = parse.parse_args()
region = args.region.upper()
key = getpass.getpass(prompt='API Key: ')

#Setting Credentials
pyrax.set_setting("identity_type", "rackspace")
pyrax.set_credentials(args.username, key)

#Creating contexts to allow for multiple regions
ctx = pyrax.create_context()
ctx.set_credentials(args.username, password=key)
ctx.authenticate()

#Obtaining and setting up vars for absolute limits
compute_limits = get_compute_limits(region)
cbs_limits = get_cbs_limits(region)
clb_limits = get_clb_limits(region)

ram_quota = compute_limits['absolute']['maxTotalRAMSize']
instance_quota = compute_limits['absolute']['maxTotalInstances']
networks_quota = compute_limits['absolute']['maxTotalPrivateNetworks']

cbs_ram_quota =  cbs_limits['limits']['absolute']['maxTotalVolumeGigabytes']
cbs_volume_quota =  cbs_limits['limits']['absolute']['maxTotalVolumes']

clb_quota = clb_limits['absolute'][1]['value']

maas_quota = get_mon_limits(args.username, key)
maas_check_quota = maas_quota['resource']['checks']
maas_alarm_quota = maas_quota['resource']['alarms']

#Obtaining and setting up vars for current usage
ram_usage = compute_limits['absolute']['totalRAMUsed']
instance_usage = compute_limits['absolute']['totalInstancesUsed']
networks_usage = compute_limits['absolute']['totalPrivateNetworksUsed']

cbs_ram_usage = get_cbs_usage(region)[0]
cbs_volume_usage = get_cbs_usage(region)[1]

clb_usage = get_clb_usage(region)

maas_usage = get_mon_usage(args.username, key)
maas_checks = maas_usage[0]
maas_alarms = maas_usage[1]

#Printing formatted output
x = PrettyTable(["Region", "Compute Ram", "Compute Instance", "Networks", "LBaaS", "CBS Disk", "CBS Volume", "MaaS Alarms", "MaaS Checks"])
#x.align["Region"] = "l" # Left align city names
x.padding_width = 1
x.add_row([region, str(ram_usage) + 'MB/' + str(ram_quota) + 'MB ' + str(int((ram_usage / float(ram_quota)) * 100)) + '%', \
          str(instance_usage) + '/' + str(instance_quota) + ' ' + str(int((instance_usage / float(instance_quota)) * 100)) + '%', \
          str(networks_usage) + '/' + str(networks_quota) + ' ' + str(int((networks_usage / float(networks_quota)) * 100)) + '%', \
          str(clb_usage) + '/' + str(clb_quota) + ' ' + str(int((clb_usage / float(clb_quota)) * 100)) + '%', \
          str(cbs_ram_usage) + '/' + str(cbs_ram_quota) + ' ' + str(int((cbs_ram_usage / float(cbs_ram_quota)) * 100)) + '%', \
          str(cbs_volume_usage) + '/' + str(cbs_volume_quota) + ' ' + str(int((cbs_volume_usage / float(cbs_volume_quota)) * 100)) + '%', \
          str(maas_alarms) + '/' + str(maas_alarm_quota) + ' ' + percentage(maas_alarms, maas_alarm_quota), str(maas_checks) + '/' + \
          str(maas_check_quota) + ' ' + percentage(maas_checks, maas_check_quota)])


print x
