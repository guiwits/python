import getopt, sys
import ibm_db       # installed via pip 

def main(argv):
  username = ''
  password = ''
  database = ''
  query = ''

  try:
    opts, args = getopt.getopt(argv, "hu:p:d:q:", ["username=", "password=", "database=", "query="])
  except getopt.GetoptError:
    print 'db2_connect.py -u <username> -p <password> -d <database>'
    sys.exit(2)

  for opt, arg in opts:
    if opt == '-h':
      print 'db2_connect.py -u <username> -p <password> -d <database>'
      sys.exit()
    elif opt in ("-u", "--username"):
      username = arg
    elif opt in ("-p", "--password"):
      password = arg
    elif opt in ("-d", "--database"):
      database = arg
    elif opt in ("-q", "--query"):
      query = arg

  conn_string = 'DATABASE=%s; HOSTNAME=10.30.192.108; PORT=40331; PROTOCOL=TCPIP; UID=%s; PWD=%s;' % (database, username, password)
  conn = ibm_db.connect(conn_string, "", "") # takes 3 arguments. last two are optional but require blank strings if empty.

  sql = """
  SELECT
      TEAMS.EMPLOYEE.EMP_IS_ACTIVE,
      TEAMS.PERSON.PER_LAST_NAME,
      TEAMS.PERSON_EMAIL.PER_EMAIL_PRIVATE,
      TEAMS.PERSON_EMAIL.EMAIL_ID,
      TEAMS.EMAIL.EMAIL_ADDRESS
  FROM
      TEAMS.PERSON
  INNER JOIN
      TEAMS.PERSON_EMAIL
  ON
      (
          TEAMS.PERSON.PER_ID = TEAMS.PERSON_EMAIL.PER_ID)
  INNER JOIN
      TEAMS.EMPLOYEE
  ON
      (
          TEAMS.PERSON.PER_ID = TEAMS.EMPLOYEE.PER_ID)
  INNER JOIN
      TEAMS.EMAIL
  ON
      (
          TEAMS.PERSON_EMAIL.EMAIL_ID = TEAMS.EMAIL.EMAIL_ID)

  WHERE
      (
          TEAMS.PERSON.PER_LAST_NAME = '%s');
  """ % (query)

  stmt = ibm_db.exec_immediate(conn, sql)
  result = ibm_db.fetch_both(stmt)

  for key in result:
    print result[key]

if __name__ == "__main__":
  main(sys.argv[1:])
