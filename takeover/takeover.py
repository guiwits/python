#!/usr/bin/python
from threading import Thread
import subprocess
from Queue import Queue
import time
import datetime;
import socket;
import smtplib;
import os
import getopt
import sys
from email.MIMEText import MIMEText;

CS1PVT = "1xx.xxx.xxx.xx1"
CS2PVT = "1xx.xxx.xxx.xx1"
CS3PVT = "1xx.xxx.xxx.xx1"
CS4PVT = "1xx.xxx.xxx.xx1"

CS1PUB = "1xx.xxx.xx.x4"
CS2PUB = "1xx.xxx.xx.x4"
CS3PUB = "1xx.xxx.xx.x4"
CS4PUB = "1xx.xxx.xx.x4"

pvt_ips = [CS1PVT, CS2PVT, CS3PVT, CS4PVT]
pub_ips = [CS1PUB, CS2PUB, CS3PUB, CS4PUB]

ips = {'cs-import1_pvt' : 'x.x.x.x',  'cs-import2_pvt' : 'x.x.x.x',
       'cs-import3_pvt' : 'x.x.x.x'   'cs-import4_pvt' : 'x.x.x.x',
       'cs-import1'     : 'x.x.x.x'   'cs-import2'     : 'x.x.x.x'
       'cs-import3'     : 'x.x.x.x'   'cs-import4'     : 'x.x.x.x'


hosts = {'x.x.x.x' : 'cs-import1_pvt', 'x.x.x.x'  : 'cs-import2_pvt',
         'x.x.x.x' : 'cs-import3_pvt', 'x.x.x.x'  : 'cs-import4_pvt',
	 'x.x.x.x' : 'cs-import1',     'x.x.x.x'  : 'cs-import2',
         'x.x.x.x' : 'cs-import3',     'x.x.x.x'  : 'cs-import4'}

netmon_start       = "/app/aqms/comserv/bin/run_netmon"
netmon_restart     = "/app/aqms/comserv/bin/netmon -r"
netmon_start_all   = "/app/aqms/comserv/bin/netmon -s"
netmon_terminate   = "/app/aqms/comserv/bin/netmon -t"
snw_restart        = "/app/aqms/utils/snw/snwctl.sh restart"

### Calls the systems' ping command for initial check ###
def PingServer (server_ip):
    ip = server_ip
    print "Pinging hostname %s [IP %s]." % ((GetHostname (ip)), ip)
    ret = subprocess.call ("/bin/ping -c 5 %s" % ip, shell = True, 
              stdout = open ('/dev/null', 'w'), stderr = subprocess.STDOUT)

    if ret != 0: 
        return GetHostname (ip) 
    else: 
        return 0
### END PingServer ###

### Ping the specific server again as it prepares to take over.  ###
### This is done over a time interval in case the server comes   ###
### back on-line for whatever reason. We don't want the machines ###
### fighting to take control. Not good for the Q330's.           ###
def PingServerAgain (ip):
    ret = subprocess.call ("/bin/ping -c 5 %s" % ip, shell = True,
              stdout = open ('/dev/null', 'w'), stderr = subprocess.STDOUT)
    return ret
### END PingServerAgain ###

### A server is down, time for the partner to take over ###
def Takeover (ip):
    print "Trying to ping hostname %s [IP %s] again in 60 seconds." % ((GetHostname (ip)), ip)
    time.sleep (60) # Give machine a minute to ping again. Afer that, take over.
    ret = PingServerAgain (ip)
    if ret == 0:
        print "Hostname %s [IP %s] is alive. Aborting takeover" % ((GetHostname (ip)), ip)
        return
    else:
        print "Hostname %s [IP %s] is still down. Taking over stations" % ((GetHostname (ip)), ip)
        # Check to see if we have already taken over, if yes, quit otherwise proceed #
        if HaveTakenOver (GetHostname (ip)) == True:
            print "Already have taken over host %s. Exiting." % (GetHostname (ip))
            return 
    
    text = '%s can\'t ping hostname: %s. Taking over now' % (socket.gethostname(), GetHostname (ip))
    SendMail (text, ip)
	
    if (GetHostname (ip)) == 'cs-import1' or (GetHostname (ip)) == 'cs-import1_pvt':
        CreateStationsFile ("cs-import1")
        RestartNetmonService ()
    elif (GetHostname (ip)) == 'cs-import2' or (GetHostname (ip)) == 'cs-import2_pvt':
        CreateStationsFile ("cs-import2")
        RestartNetmonService ()
    elif (GetHostname (ip)) == 'cs-import3' or (GetHostname (ip)) == 'cs-import3_pvt':
        CreateStationsFile ("cs-import3")
        RestartNetmonService ()
    elif (GetHostname (ip)) == 'cs-import4' or (GetHostname (ip)) == 'cs-import4_pvt':
        CreateStationsFile ("cs-import4")
        RestartNetmonService ()
    else:
        print "ERROR: Unable to fine ip [%s]. Aborting." % ip
### END Takeover ###

### A method to make sure that machine taking over stations is actually ok ###
### to do so. We are tyring to prevent the case that the reason pings fail ###
### aren't because the pinging machine is offline.                         ###
def amIOk ():
    google = "www.google.com";
    yahoo  = "www.yahoo.com";
    unix1  = "unix1.pvt.scsn.org";
    unix2  = "unix2.pvt.scsn.org";
    print "Pinging google."
    googlerc = subprocess.call ("/bin/ping -c 5 %s" % google, shell = True,
               stdout = open   ('/dev/null', 'w'), stderr = subprocess.STDOUT)
    print "Pinging yahoo."
    yahoorc  = subprocess.call ("/bin/ping -c 5 %s" % yahoo, shell = True,
               stdout = open   ('/dev/null', 'w'), stderr = subprocess.STDOUT)
    print "Pinging unix1."
    unix1rc  = subprocess.call ("/bin/ping -c 5 %s" % unix1, shell = True,
               stdout = open   ('/dev/null', 'w'), stderr = subprocess.STDOUT)
    print "Pinging unix2."
    unix2rc  = subprocess.call ("/bin/ping -c 5 %s" % unix2, shell = True,
               stdout = open   ('/dev/null', 'w'), stderr = subprocess.STDOUT)

    ### If more than 3 are successful, we are ok ###
    if (googlerc == 0  and yahoorc == 0 and
        unix1rc  == 0  and unix2rc == 0):
        print "Able to ping every server.\n"
        return 0
    elif (googlerc == 0 and unix1rc == 0  and unix2rc == 0):
        return 0
    elif (yahoorc == 0  and unix1rc == 0  and unix2rc == 0):
        return 0
    elif (yahoorc == 0  and googlerc == 0 and unix1rc == 0):
        return 0
    elif (yahoorc == 0  and googlerc == 0 and unix2rc == 0):
        return 0
    else:
        return 1
### End amIOk ###

### Takes an IP address and returns the server name ###
def GetHostname (ip):
    return hosts [ip]
### END GetHostname ###

### Takes a hostname and returns its IP address ###
def GetIpAddr (host): 
    print host
    return ips [host]
### END GetIpAddr ###

### Look to see if netmon, qmaserv, and cs2mcast procs are running ###
def CheckServices (ip):
    qmaservSearchString = 'ps aux | grep qmaserv | grep -v grep | wc -l'
    stationsSearchString = 'cat /etc/stations.ini | wc -l'
    ssh = subprocess.Popen(["ssh", "%s" % GetHostname(ip), "%s" %  qmaservSearchString], shell=False,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ssh2 = subprocess.Popen(["ssh", "%s" % GetHostname(ip), "%s" %  stationsSearchString], shell=False,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result  = ssh.stdout.readlines()
    result2 = ssh2.stdout.readlines()

    if result == []:
        error = ssh.stderr.readlines()
        print >>sys.stderr, "ERROR: %s" % error
    else:
        qmaservProcs = int (result[0])

    if result2 == []:
        error = ssh2.stderr.readlines()
        print >>sys.stderr, "ERROR: %s" % error
    else:
        stationLines = int (result2[0])

    if (stationLines == 0):
        return "OK"
    elif (stationLines == 1 and qmaservProcs > 10):
        return "OK"
    elif (stationLines == 2 and qmaservProcs > 30):
        return "OK"
    elif (stationLines == 3 and qmaservProcs > 50):
        return "OK"
    elif (stationLines == 4 and qmaservProcs > 70):
        return "OK"
    else:
        return "notOK"
### END CheckServices ###

### Create a new stations.ini file based upon which host's stations are being taken over ###
def CreateStationsFile (hostname):
    print "Setting up stations.ini file to take over stations from host %s" % hostname
    cmd = subprocess.Popen (["hostname", "-s"], stdout = subprocess.PIPE)
    localHostname = cmd.stdout.read()

    #var2 = subprocess.Popen (["cat", "/etc/stations.ini"], stdout = subprocess.PIPE)
    #var3 = subprocess.Popen (["wc", "-l"], stdin = var2.stdout, stdout = subprocess.PIPE)
    #numberOfStationGroups = var3.stdout.read()
    #print "Local hostname = %s, number of station groups = %d" % (localHostname, int (numberOfStationGroups))
    #print "Hostname to check is %s" % hostname

    ### copy stations.ini file to a backup, cat new group + old backup group ###
    os.system ('cp /app/aqms/comserv/etc/stations.ini /app/aqms/comserv/etc/stations.ini.takeover')

    ### Write the new @include to the stations.ini file for the host to takeover ###
    if hostname == "cs-import1":
        os.system ('echo "@/app/aqms/comserv/etc/stations_1.ini" >> /app/aqms/comserv/etc/stations.ini')
    elif hostname == "cs-import2":
        os.system ('echo "@/app/aqms/comserv/etc/stations_2.ini" >> /app/aqms/comserv/etc/stations.ini')
    elif hostname == "cs-import3":
        os.system ('echo "@/app/aqms/comserv/etc/stations_3.ini" >> /app/aqms/comserv/etc/stations.ini')
    elif hostname == "cs-import4":
	    os.system ('echo "@/app/aqms/comserv/etc/stations_4.ini" >> /app/aqms/comserv/etc/stations.ini')
    else:
        print "ERROR: hostname not recognized. Aborting." 
        return -1

    return 0
### END CreateStationsFile ###
    
### Restart the netmon service on the localhost ###
def RestartNetmonService ():
    print "Restarting the netmon service with command %s." % (netmon_restart)
    ### check to see if netmon is running. If it is, restart it. If not, start it. ###
    pipe = subprocess.Popen ("ps aux | grep netmon | grep -v grep | awk '{print $2}'", 
                             shell=True, stdout=subprocess.PIPE).stdout
    netmonPid = pipe.read()

    if netmonPid == '':
        print "netmon not running. Starting it"
        StartNetmon()
    else:
        print "netmon is running with pid", netmonPid
        os.system (netmon_restart)    # adds stations ==> netmon -r 
        time.sleep (120)              # 2 min wait. would be better to monitor cmd directory 
        os.system (netmon_start_all)  # adds stations ==> netmon -s
       
    ###SNWRestart()
    return
### END RestartNetmonService ###

### Start/Restart the SNW agents ###
def SNWRestart():
    os.system (snw_restart)
### END SNWRestart ###

### Terminates the netmon service on the machine we're taking over ###
def TerminateNetmonService():
    counter = 0
    os.system (netmon_terminate)
    while (os.system ('ps aux | grep qmaserv | grep -v grep | wc -l')) != 0:
        counter = counter + 1
        print "qmaserv still running. Waiting for it to stop"
        time.sleep (10)
        if counter == 25:
            print "Counter has reached its patience limit. Killing off processes."
            for i in (os.system ("ps aux | grep qmaserv | grep -v grep | awk '{print $2}'")):
                try:
                    os.kill (int (i), 9)
                    raise Exception ("""wasn't able to kill the process.""")
                except OSError as ex:
                    continue

    ### get PID of netmon to kill it ###
    pipe = subprocess.Popen ("ps aux | grep netmon | grep -v grep | awk '{print $2}'", 
                              shell=True, stdout=subprocess.PIPE).stdout
    pid = pipe.read()
    print "PID of netmon is", pid
    try:
        os.kill (int (pid), 9)
        raise Exception ("""wasn't able to kill the process.""")
    except OSError as ex:
        print "Unable to kill the PID os netmon."
    
    return
### END TerminateNetmonService ###

### Kill off netmon and restart it after the correct stations.ini file has been constructed ###
def StartNetmon():
    print "Starting netmon with command %s" % (netmon_start)
    os.system (netmon_start)
    time.sleep (10)
    os.system (netmon_start_all)  # adds stations to netmon but doesn't start (when runnable)
    return
### END StartNetmon ###

### Mail off a message when a system is going to be taken over ###
def SendMail (message, ip):
    server_ip = ip
    mail_message = message
    now = datetime.datetime.now();
    sender = sender = 'aqms@%s' % socket.gethostname()
    recipients = ['xxx@gps.caltech.edu', 'xxx@gps.caltech.edu', 'xxx@gps.caltech.edu', 'xxx@bort.gps.caltech.edu']
    msg = MIMEText (mail_message);
    msg['Subject'] = '%s can\'t ping host %s at time: %s' % (socket.gethostname(), GetHostname (server_ip), now)
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)
    s = smtplib.SMTP('localhost')
    s.sendmail(sender, recipients, msg.as_string())
    s.quit()
    return
### END SendMail ###

### Check if the downed server(s) have already been taken over ###
def HaveTakenOver (station):
    f = open('/etc/stations.ini', 'r')
    lines = f.read().splitlines()
    f.close()
    for line in lines:
        if line == "@/app/aqms/comserv/etc/stations_1.ini" and station == "cs-import1":
            return True
        if line == "@/app/aqms/comserv/etc/stations_2.ini" and station == "cs-import2":
            return True
        if line == "@/app/aqms/comserv/etc/stations_3.ini" and station == "cs-import3":
            return True
        if line == "@/app/aqms/comserv/etc/stations_4.ini" and station == "cs-import4":
            return True
    return False
    
### Displays the usage to the user upon -h flag or error ###
def Usage():
    print "This script either runs automatically and watches certain machines"
    print "for processes and network connectivity before it takes over certain"
    print "groups of stations or it is run manually by giving it a group of stations"
    print "to takeover. Options are: [cs-import1, cs-import2, cs-import3, cs-import4]."
    print "Usage: python takeover.py  --OR-- python takeover.py -s [cs-importX]." 
### END Usage ###

### Main ... ###
def Main():
    try:
        opts, args = getopt.getopt (sys.argv[1:], "hs:v", ["help", "stations="])
    except getopt.GetoptError, err:
        print str (err) # will print something like "option -s not recognized"
        Usage ()
        sys.exit (2)

    stations  = None
    verbose   = False
    hostname  = subprocess.Popen (["hostname", "-s"], stdout = subprocess.PIPE)
    localhost = hostname.stdout.read().rstrip('\n')
    #localhost    = os.getenv ('HOSTNAME').split('.')[0]
    for o, s in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            Usage ()
            sys.exit ()
        elif o in ("-s", "--stations"):
            stations = s
            print "Manually taking over stations %s.\n" % str (stations)
        else:
            assert False, "unhandled option"

    if stations != None:
        print "Command line argument given: %s" % (stations)
        for item in hosts:
            if hosts[item] == stations:
                ip = item
        Takeover (ip)
    else:
        print "*** Checking cs-import cluster private interface ***"
        for server_ip in pvt_ips:
            retcode = PingServer (server_ip)
            procsOK_priv = CheckServices (server_ip)
            if (procsOK_priv != "OK"):
                text = 'Number of procs on hostname: %s seem off. Please check.' % GetHostname (server_ip)
                SendMail (text, ip)
            if (retcode != 0):
                print "Can't ping %s's private interface. Checking public interface on %s" % (retcode, retcode)
                badPrivateHost = retcode
                bph = badPrivateHost[:10]
                pubHost = PingServer (GetIpAddr (bph))
                procsOK = CheckServices (GetIpAddr (bph))
                if (procsOK != "OK"):
                    text = 'Number of procs on hostname: %s seem off. Please check.' % GetHostname (server_ip)
                    SendMail (text, ip)
                if (pubHost != 0): 
                    print "Both public and private interfaces are down on host %s." % (bph) 
                    print "Checking to see if I am ok and if I am, I will take over host %s" % (bph)
                    print "if I am the next peer in line to take over."
                    okToTakeover = amIOk() 
                    if (okToTakeover == 0): 
                        print "I am ok to take over host %s. Calling the takeover method." % (bph) 
                        ### Machine hasn't recovered, going to take over the stations ###
                        ### cs 1 <----> cs 2 (primary concern)
                        ### cs 3 <----> cs 4 (primary concern)
                        ### cs 1 <----> cs 3 (secondary concern)
                        ### cs 2 <----> cs 4 (secondary concern)
	                ### cs 1 <----> cs 4 (tertiary concern)
	                ### cs 2 <----> cs 3 (tertiary concern)
                        ################################################################## 
                        print "Hostname is %s" % (localhost)
                        print "Host to takeover is %s" % (bph)

                        # cs-import1 priorities #
                        # Primary is cs-import2 #
                        if localhost == "cs-import1" and bph == "cs-import2": 
                            time.sleep (5) 
                            print "cs-import1 taking over %s" % (bph)
                            Takeover (GetIpAddr (bph))
                        elif localhost == "cs-import1" and bph == "cs-import4": 
                            time.sleep (10) 
                            if (PingServer ((GetIpAddr ('cs-import3'))) == 0):
                                print "cs-import3 pingable. Leaving %s alone." % (bph) 
                            else:
                                print "cs-import1 taking over %s" % (bph)
                                Takeover (GetIpAddr (bph)) 
                        elif localhost == "cs-import1" and bph == "cs-import3": 
                            time.sleep (15) 
                            # ping cs-import2 and cs-import4 to see if they are alive #
                            # to take over                                            #
                            if (PingServer ((GetIpAddr ('cs-import2'))) == 0) or \
                               (PingServer ((GetIpAddr ('cs-import4'))) == 0):
                                print "cs-import2 or cs-import4 are pingable. Leaving %s alone." % (bph) 
                            else:
                                print "cs-import1 taking over %s" % (bph)
                                Takeover (GetIpAddr (bph)) 

                        # cs-import2 priorities #
                        # Primary is cs-import1 #
                        if localhost == "cs-import2" and bph == "cs-import1": 
                            time.sleep (5) 
                            print "cs-import2 taking over %s" % (bph)
                            Takeover (GetIpAddr (bph)) 
                        elif localhost == "cs-import2" and bph == "cs-import3": 
                            time.sleep (10) 
                            if (PingServer ((GetIpAddr ('cs-import4'))) == 0):
                                print "cs-import4 pingable. Leaving %s alone." % (bph)
                            else:
                                print "cs-import2 taking over %s" % (bph)
                                Takeover (GetIpAddr (bph))
                        elif localhost == "cs-import2" and bph == "cs-import4": 
                            time.sleep (15) 
                            if (PingServer ((GetIpAddr ('cs-import1'))) == 0) or \
                               (PingServer ((GetIpAddr ('cs-import3'))) == 0):
                                print "cs-import1 or cs-import3 are pingable. Leaving %s alone." % (bph) 
                            else:
                                print "cs-import2 taking over %s" % (bph)
                                Takeover (GetIpAddr (bph)) 

                        # cs-import3 priorities #
                        # Primary is cs-import4 #
                        if localhost == "cs-import3" and bph == "cs-import4": 
                            time.sleep (5) 
                            print "cs-import3 taking over %s" % (bph)
                            Takeover (GetIpAddr (bph)) 
                        elif localhost == "cs-import3" and bph == "cs-import2": 
                            time.sleep (10) 
                            if (PingServer ((GetIpAddr ('cs-import1'))) == 0):
                                print "cs-import1 pingable. Leaving %s alone." % (bph)
                            else:
                                print "cs-import3 taking over %s" % (bph)
                                Takeover (GetIpAddr (bph))
                        elif localhost == "cs-import3" and bph == "cs-import1": 
                            time.sleep (15) 
                            if (PingServer ((GetIpAddr ('cs-import2'))) == 0) or \
                               (PingServer ((GetIpAddr ('cs-import4'))) == 0):
                                print "cs-import2 or cs-import4 are pingable. Leaving %s alone." % (bph)
                            else:
                                print "cs-import3 taking over %s" % (bph)
                                Takeover (GetIpAddr (bph))
                        # cs-import4 priorities #
                        if localhost == "cs-import4" and bph == "cs-import3": 
                            time.sleep (5) 
                            print "cs-import4 taking over %s" % (bph)
                            Takeover (GetIpAddr (bph)) 
                        elif localhost == "cs-import4" and bph == "cs-import1": 
                            time.sleep (10) 
                            if (PingServer ((GetIpAddr ('cs-import2'))) == 0):
                                print "cs-import2 pingable. Leaving %s alone." % (bph)
                            else:
                                print "cs-import4 taking over %s" % (bph)
                                Takeover (GetIpAddr (bph))
                        elif localhost == "cs-import4" and bph == "cs-import2": 
                            time.sleep (15) 
                            if (PingServer ((GetIpAddr ('cs-import1'))) == 0) or \
                               (PingServer ((GetIpAddr ('cs-import3'))) == 0):
                                print "cs-import1 or cs-import3 are pingable. Leaving %s alone." % (bph)
                            else:
                                print "cs-import4 taking over %s" % (bph)
                                Takeover (GetIpAddr (bph))
                        else: 
                            print "Host %s." % localhost 
                else: 
                    print "I don't seem to be ok. Aborting any type of takeover." 
                    sys.exit (2)
        
    print "Program completed. Exiting."
### END Main ###

if __name__ == "__main__":
    Main()

