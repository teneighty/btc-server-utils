#!/usr/bin/env python

import datetime, json, os, socket, subprocess, sys, time, urllib2

BLOCK_DELAY=1 * 60
ALLOWED_HOSTS=['127.0.0.1', '127.0.0.2']
OBELISK_PORT=9091
OTHER_OBELISKS=[]
FW=["INPUT", "-p", "tcp", "-i", "eth0", "--dport", str(OBELISK_PORT)]
ALLOW_FW=FW + ["-j", "ACCEPT"]
BLOCK_FW=FW + ["-j", "REJECT"]

def is_blocked():
    FNULL = open(os.devnull, 'w')
    return subprocess.call(["/sbin/iptables", "-C"] + BLOCK_FW, stderr=FNULL) == 0

def open_bs():
    print 'Opening firewall: ',
    if is_blocked():
        print 'opened'
        for h in ALLOWED_HOSTS:
            subprocess.call(["/sbin/iptables", "-D"] + ALLOW_FW + ["-s", h])
        subprocess.call(["/sbin/iptables", "-D"] + BLOCK_FW)
    else:
        print 'already opened'

def block_oblelisk():
    print 'Closing firewall: ',
    if not is_blocked():
        if check_others_open():
            for h in ALLOWED_HOSTS:
                subprocess.call(["/sbin/iptables", "-A"] + ALLOW_FW + ["-s", h])
            subprocess.call(["/sbin/iptables", "-A"] + BLOCK_FW)
            print 'blocked'
        else:
            print 'others already blocked'
    else:
        print 'already blocked'

def get_bcinfo_height():
    content = urllib2.urlopen("https://blockchain.info/latestblock", timeout=10).read()
    j = json.loads(content)
    return j["height"], j["time"]

def bs_height():
    return int(subprocess.check_output(["/usr/local/bin/bx", "fetch-height", "tcp://localhost:9091"]))

def iso8601_to_timestamp(d):
    d = d.replace('.000Z', '')
    return int(time.mktime(datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%S").timetuple()))

def check_others_open():
    for o in OTHER_OBELISKS:
        if check_bs(o):
            return True
    return True

def check_bs(o):
    try:
        ip = socket.gethostbyname(o)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((ip, OBELISK_PORT))
        return result == 0
    except:
        print '{} failed'.format(o)
        return False

try:
    (bcheight, bctime) = get_bcinfo_height()
except:
    bcheight, bctime = 0, 0

try:
    ob = bs_height()

    if bcheight == 0:
        raise Exception("Could not connect to servers")

    print 'Using Blockchain.info'
    height, height_time = bcheight, bctime
except Exception as e:
    print "Unknown - Error connecting to servers"
    print e
    open_bs()
    sys.exit(3)

if height == ob:
    print 'BS Matches!!!'
    open_bs()
else:
    print 'BS Mismatches: Actual:{}, BS:{}'.format(height, ob)
    now = time.time()
    # If we are only off by one
    if abs(height - ob) == 1 and (now - height_time) < BLOCK_DELAY:
        print 'Off by 1, but close enough'
        open_bs()
    else:
        block_oblelisk()

# vim:set ft=python sw=4 ts=4 et:
