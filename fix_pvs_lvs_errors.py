#!/usr/bin/env python
__author__ = "David Trigo Chavez"
__copyright__ = "Copyright 2018, "
__credits__ = ["David Trigo Chavez"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "David Trigo Chavez"
__email__ = "david.trigo@gmail.com"
__status__ = "Development"


import os,subprocess
import re

dry_run=True

disks_dir="/dev/disk/by-id/"
disks_vg_dir="/dev/mapper/"
log="/var/log/messages-20181223"

error_pattern="EXT4-fs.*error"
disk_pattern="dm-[0-9]{1,2}"

failed_disks=[]
all_disks={}
pcs_groups=[]

file=open(log,"r")



""" Find disks with failures """
for line in file:
        if re.search(error_pattern,line):
                searchObj = re.search(disk_pattern,line)
                failed_disks.append(searchObj.group())

file.close()

failed_disks=set(failed_disks)


""" Match all disks """

disks = os.listdir(disks_dir)
for disk in disks:
        link=os.readlink(disks_dir+disk)
        all_disks[link[6:]]=disk



""" Subprocess test """

proc = subprocess.Popen(["pcs", "resource","show"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
output, err = proc.communicate()
rc = proc.returncode




for line in output.splitlines():
        searchObj = re.search(" Resource Group: (.*)",line)
        if searchObj:
                pcs_groups.append(searchObj.group(1))


""" Stop PCS Services and fix LVM's volumes """
if dry_run:
        for group in pcs_groups:
                for disk in failed_disks:
                        search_obj = re.search("_"+group,all_disks[disk])
                        if search_obj:
                                #print(group,all_disks[disk])
                                print("Stoping Service: ")
                                print("pcs resource disable "+group)
                                print("Fix LVM")
                                print("e2fsck "+disks_vg_dir+all_disks[disk])
                                print("pcs resource enable"+group)
                                print("")
else:
        for group in pcs_groups:
                for disk in failed_disks:
                        search_obj = re.search("_"+group,all_disks[disk])
                        if search_obj:
                                # Stop Pacemaker Service
                                proc = subprocess.Popen(["pcs", "resource","disable",group], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                output, err = proc.communicate()
                                rc = proc.returncode
                                if rc != 0:
                                        print("Service "+group+" NOT Stopped")
                                        exit(1)
                                # Enable LV
                                proc = subprocess.Popen(["vgchange", "-a","y",disks_vg_dir+all_disks[disk]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                output, err = proc.communicate()
                                rc = proc.returncode
                                # FSCK
                                proc = subprocess.Popen(["fsck", "y",disks_vg_dir+all_disks[disk]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                output, err = proc.communicate()
                                rc = proc.returncode
                                # Start Pacemaker Service
                                proc = subprocess.Popen(["pcs", "resource","enable",group], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                output, err = proc.communicate()
                                rc = proc.returncode



