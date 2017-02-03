#!/usr/bin/python

import datetime, getopt, sys, time
from random import randint

def main(argv):
  # command line args
  mag = ''
  lat = ''
  lon = ''
  dep = ''
  loc = ''
  
  # time, date, and id data
  n         = datetime.datetime.now()
  eq_year   = n.year
  eq_month  = n.month
  eq_day    = n.day
  eq_hour   = n.hour
  eq_minute = n.minute
  eq_second = n.second
  unix_time = time.mktime(n.timetuple())
  eq_id     = randint(10000000,99999999)

  try:
    opts, args = getopt.getopt(argv,"hm:d:l:o:s:",
            ["mag=","dep=","lat=","lon=","location="])
  except getopt.GetoptError:
    print 'create_event.py -m <mag> -l <lat> -o <lon> -d <depth> -s <loc>'
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h':
      print 'create_event.py -m <mag> -l <lat> -o <lon> -d <depth> -s <loc>'
      sys.exit()
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

  xml_data = """
  <?xml version="1.0" encoding="US-ASCII" standalone="yes"?>
  <!DOCTYPE earthquake [
  <!ELEMENT  earthquake EMPTY>
  <!ATTLIST earthquake
    id 		ID	#REQUIRED
    lat		CDATA	#REQUIRED
    lon		CDATA	#REQUIRED
    mag		CDATA	#REQUIRED
    year        CDATA   #REQUIRED
    month       CDATA   #REQUIRED
    day         CDATA   #REQUIRED
    hour        CDATA   #REQUIRED
    minute      CDATA   #REQUIRED
    second      CDATA   #REQUIRED
    timezone    CDATA   #REQUIRED
    depth       CDATA	#REQUIRED
    type	CDATA	#REQUIRED
    locstring	CDATA	#REQUIRED
    pga		CDATA   #REQUIRED
    pgv		CDATA   #REQUIRED
    sp03	CDATA   #REQUIRED
    sp10	CDATA   #REQUIRED
    sp30	CDATA   #REQUIRED
    created	CDATA	#REQUIRED
  >
  ]>
  <earthquake id="%s" lat="%s" lon="%s" mag="%s" year="%s" month="%s" day="%s" hour="%s" minute="%s" second="%s" timezone="GMT" depth="%s" type="ALL" locstring="%s" created="%s" />
  """ % (eq_id, lat, lon, mag, eq_year, eq_month, eq_day, eq_hour, eq_minute, 
         eq_second, dep, loc, unix_time)

  with open("event_test.xml", "w") as xml_file:
    xml_file.write(xml_data)

if __name__ == "__main__":
  main(sys.argv[1:])
