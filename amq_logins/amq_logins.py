#!/usr/bin/python

import datetime
import getopt
import sys
import time

#
# Prints out a report to send/log weekly to keep track offline
# who is logged into which DM broker and from where.
#
def print_report(users, ifn):
  # Open file for writing out results
  lfn = ifn.split('.')[0] + '_connection_results.txt'
  full_path = '/dir/to/logs/' + lfn
  print full_path
  f = open(full_path, 'w')
  
  for key, value in users.iteritems():
    userstr="User:   %s" % key
    datesstr="Dates:  %s" % value['Dates']
    hostsstr="Hosts:  %s" % value['Hosts']
    connstr="Conns:  %s" % value['Connects']
    disconnstr="Discos: %s" % value['Disconnects']
    data = (userstr, datesstr, hostsstr, connstr, disconnstr)
    s = str(data)
    s = s + "\n\n"
    f.write (s)

  f.close()
      
#
# evaluate_users function
# Prints out values of the users dictionary
#
def nagios_check(users):
  ignore_users = [
    'ha',
    'onsite',
    'elarms',
    'decimode',
    'dm',
    'vs',
    'eewserver'
    'monitor'
    ]

  offenders   = {} # tell on people who connect often   
  
  for key, value in users.iteritems():
    if key not in ignore_users:
      total_connects = value['Connects'] - value['Disconnects']
      if total_connects > 3:
        offenders.append( key )
        status = "User:   %s, Connections: %s, Disconnects: %s" \
                 % (key, value['Connects'], value['Disconnects'])
        print status
        sys.exit(2)

  sys.exit(0)
    
#
# main function.
# Reads in a amq 'actions_<data>.log file located in /amq/log/dir/admin
# and parsed the data to find out who has logged in (connects and disconnects)
# and from what server (IP/Hostname)
#
def main(argv):
  ifn = ''
  report = False
  nagios = False
  users = {}
  log_dir = '/dir/to/amq/admin/logs/admin'
  yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime('%Y%m%d')
  log_file = log_dir + '/' + 'actions_' + yesterday + '.log'
    
  try:
    opts, args = getopt.getopt(argv, "hnrf:",["file="])
  except getopt.GetoptError:
    print "Getopt parse error ..."
    sys.exit(2)

  for opt, arg in opts:
    if opt == '-h':
      print 'Usage: python amq_logins.py [--file=<file>] [-r] [-n]'
      print 'Usage: -r runs the results report check which will output the data to a file'
      print 'Usage: -n runs a nagios check to see if there are people with mismatched logins'
      sys.exit(0)
    elif opt == '-r':
      report = True
    elif opt == '-n':
      nagios = True
    elif opt in ("-f", "--file"):
      ifn = arg

  # No file passed in at command line. Setting it to 'yesterdays' logfile.
  if ifn == '':
    ifn = log_file
    
  with open(ifn) as f:
    content = f.readlines()

  f.close()

  for line in content:
    data = line.split('|')
    if ((data[1] in users) and (data[3] == "connect" or data[3] == "disconnect")):
      if data[3] == "connect":
        connect_count = users[data[1]]['Connects'] + 1
        users[data[1]]['Dates'].append( data[0] )
        users[data[1]]['Hosts'].append( data[2] )
        users[data[1]]['Connects'] = connect_count
      elif data[3] == "disconnect":
        disconnect_count = users[data[1]]['Disconnects'] + 1
        users[data[1]]['Dates'].append( data[0] )
        users[data[1]]['Hosts'].append( data[2] )
        users[data[1]]['Disconnects'] = disconnect_count
      elif data[3] == "connect":
        users[data[1]] = {'Name': data[1], 'Command': data[3], 'Hosts': [data[2]],
                          'Dates': [data[0]], 'Connects': 1, 'Disconnects': 0 }
      elif data[3] == "disconnect":
        users[data[1]] = {'Name': data[1], 'Command': data[3], 'Hosts': [data[2]],
                          'Dates': [data[0]], 'Connects': 0, 'Disconnects': 1 }

  if nagios == True:
    nagios_check(users)
    
  if report == True:
    print_report(users, ifn.split('/')[-1]) # only want filename of ifn. Not full path

#
# Program entry point
#
if __name__ == "__main__":
  main(sys.argv[1:])
