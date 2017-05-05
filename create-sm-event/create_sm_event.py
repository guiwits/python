#!/usr/bin/python

import datetime, getopt, sys, time
from random import randint

def main(argv):
  # command line args
  eid = ''
  mag = ''
  lat = ''
  lon = ''
  dep = ''
  loc = ''
  fname = ''
  iteration = ''
  
  # time, date, and id data
  n         = datetime.datetime.now()
  eq_year   = n.year
  eq_month  = n.month
  eq_day    = n.day
  eq_hour   = n.hour
  eq_minute = n.minute
  eq_second = n.second
  unix_time = time.mktime(n.timetuple())
  eq_id     = randint(10000000,99999999) # needed if we don't want to use a command line quake id

  try:
    opts, args = getopt.getopt(argv,"hm:e:d:l:o:s:f:i:",
                 ["eid=", "mag=","dep=","lat=","lon=","location=", "filename=", "iteration="])
  except getopt.GetoptError:
    print 'create_event.py -e <eid> -m <mag> -l <lat> -o <lon> -d <depth> -s <loc> -f <filename> -i <iteration>'
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h':
      print 'create_event.py -e <eid> -m <mag> -l <lat> -o <lon> -d <depth> -s <loc> -f <filename> -i <iteration>'
      sys.exit()
    elif opt in ("-e", "--eid"):
      eid = arg
    elif opt in ("-m", "--mag"):
      mag = arg
    elif opt in ("-d", "--dep"):
      dep = arg
    elif opt in ("-l", "--lat"):
      lat = arg
    elif opt in ("-o", "--lon"):
      lon = arg
    elif opt in ("-s", "--location"):
      loc = arg
    elif opt in ("-f", "--filename"):
      fname = arg
    elif opt in ("-i", "--iteration"):
      iteration = arg

  xml_data = """
  <?xml version="1.0" encoding="US-ASCII" standalone="yes"?>
  <!DOCTYPE earthquake [
  <!ELEMENT earthquake EMPTY>
  <!ATTLIST earthquake
    id          ID      #REQUIRED
    lat         CDATA   #REQUIRED
    lon         CDATA   #REQUIRED
    mag         CDATA   #REQUIRED
    year        CDATA   #REQUIRED
    month       CDATA   #REQUIRED
    day         CDATA   #REQUIRED
    hour        CDATA   #REQUIRED
    minute      CDATA   #REQUIRED
    second      CDATA   #REQUIRED
    timezone    CDATA   #REQUIRED
    depth       CDATA   #REQUIRED
    type        CDATA   #REQUIRED
    locstring   CDATA   #REQUIRED
    pga         CDATA   #REQUIRED
    pgv         CDATA   #REQUIRED
    sp03        CDATA   #REQUIRED
    sp10        CDATA   #REQUIRED
    sp30        CDATA   #REQUIRED
    created     CDATA   #REQUIRED
  >
  ]>
  <earthquake id="%s" lat="%s" lon="%s" mag="%s" year="%s" month="%s" day="%s" hour="%s" minute="%s" second="%s" timezone="GMT" depth="%s" type="ALL" locstring="%s" created="%s" />
  """ % (eid, lat, lon, mag, eq_year, eq_month, eq_day, eq_hour, eq_minute, eq_second, dep, loc, unix_time)

  if fname == '' or iteration == '':
    print 'Filename and/or Iteration cannot be empty. Please use quotes on multi work string with spaces.'
    sys.exit(2)

  filename = fname + '_' + iteration + '.xml'
  with open(filename, "w") as xml_file:
    xml_file.write(xml_data)

if __name__ == "__main__":
  main(sys.argv[1:])
