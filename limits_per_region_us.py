#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, pyrax, argparse, json, requests, getpass, math
from prettytable import PrettyTable

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
output = PrettyTable(["Region", "Compute Ram", "Compute Instance", "Networks", "LBaaS", "CBS Disk", "CBS Volume"])
#x.align["Region"] = "l" # Left align city names
output.padding_width = 1

region_list = ['DFW', 'ORD', 'IAD', 'SYD', 'HKG']
count = 0

while count < len(region_list):
    #Obtaining and setting up vars for absolute limits
    compute_limits = get_compute_limits(region_list[count])
    cbs_limits = get_cbs_limits(region_list[count])
    clb_limits = get_clb_limits(region_list[count])
    
    ram_quota = compute_limits['absolute']['maxTotalRAMSize']
    instance_quota = compute_limits['absolute']['maxTotalInstances']
    networks_quota = compute_limits['absolute']['maxTotalPrivateNetworks']
    
    cbs_ram_quota =  cbs_limits['limits']['absolute']['maxTotalVolumeGigabytes']
    cbs_volume_quota =  cbs_limits['limits']['absolute']['maxTotalVolumes']
    
    clb_quota = clb_limits['absolute'][1]['value']
    
    #Obtaining and setting up vars for current usage
    ram_usage = compute_limits['absolute']['totalRAMUsed']
    instance_usage = compute_limits['absolute']['totalInstancesUsed']
    networks_usage = compute_limits['absolute']['totalPrivateNetworksUsed']
    
    cbs_ram_usage = get_cbs_usage(region_list[count])[0]
    cbs_volume_usage = get_cbs_usage(region_list[count])[1]
    
    clb_usage = get_clb_usage(region_list[count])

    output.add_row([region_list[count], str(ram_usage) + 'MB/' + str(ram_quota) + 'MB ' + str(int((ram_usage / float(ram_quota)) * 100)) + '%', \
              str(instance_usage) + '/' + str(instance_quota) + ' ' + str(int((instance_usage / float(instance_quota)) * 100)) + '%', \
              str(networks_usage) + '/' + str(networks_quota) + ' ' + str(int((networks_usage / float(networks_quota)) * 100)) + '%', \
              str(clb_usage) + '/' + str(clb_quota) + ' ' + str(int((clb_usage / float(clb_quota)) * 100)) + '%', \
              str(cbs_ram_usage) + '/' + str(cbs_ram_quota) + ' ' + str(int((cbs_ram_usage / float(cbs_ram_quota)) * 100)) + '%', \
              str(cbs_volume_usage) + '/' + str(cbs_volume_quota) + ' ' + str(int((cbs_volume_usage / float(cbs_volume_quota)) * 100)) + '%'])
    count = count + 1


print output
