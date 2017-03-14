import sys
import getopt
import obspy.geodetics as gps
#import obspy.core.util.geodetics as gps

#
# process_grid: reads in the grid.xyz file and puts the data into
# lists for processing.
#
def process_grid(pfile, ofile, atime):
  tolerance       = 0.5                              # Tolerance (consider alert correct if within this range; typical value is 0.5)
  mmi_thresholds  = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0]   # MMI thresholds
  true_pos_rate   = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]   # True positive rate for certain MMI
  false_pos_rate  = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]   # False positive rate for certain MMI
  true_pos_rate2  = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]   # True positive rate for certain MMI (timeliness)
  false_pos_rate2 = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]   # False positive rate for certain MMI (timeliness)
  s_wave_velocity = 3.0                              # S-wave velocity (to estimate peak shaking arrival time)
  pred_grid_data  = []                               # Predicted grid 2D array (read in from file)
  obs_grid_data   = []                               # Observed grid 2D array  (read in from file)
  distance_grid   = []                               # grid to hold the distances between obs and pred

  # Data structure to count each type of positive or negative result
  # when calculating the ROC curve. 
  # https://en.wikipedia.org/wiki/Receiver_operating_characteristic
  num_true_pos  = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  num_false_pos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  num_true_neg  = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  num_false_neg = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

  # when considering timeliness (time from eq to station alert)
  num_true_pos_timeliness  = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  num_false_pos_timeliness = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  num_true_neg_timeliness  = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  num_false_neg_timeliness = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

  with open (pfile, 'r') as predicted_file:
    pred_data = predicted_file.read()

  with open (ofile, 'r') as observed_file:
    obs_data = observed_file.read()

  # predicted data values
  pred_header     = pred_data.split('\n', 1)[0]
  pred_grid       = pred_data.split('\n')
  pred_alert_time = atime                       # for now it is the time passed into the function. Should get from Analysis results
  pred_eq_lat     = pred_header.split(' ')[2] 
  pred_eq_lon     = pred_header.split(' ')[3] 

  # observed data values
  obs_header     = obs_data.split('\n', 1)[0]
  obs_grid       = obs_data.split('\n')
  obs_alert_time = atime                        # for now it is the time passed into the function. Should get from Shakemap
  obs_eq_lat     = obs_header.split(' ')[2] 
  obs_eq_lon     = obs_header.split(' ')[3] 

  # populate pred_grid_data with grid.xyz from predicted shakemap
  for i, g in enumerate(pred_grid):
    if i != 0:
      pred_grid_data.append(g.split(' '))

  # populate obs_grid_data with grid.xyz from observed shakemap
  for i, g in enumerate(obs_grid):
    if i != 0:
      obs_grid_data.append(g.split(' '))

  pred_grid_size = len(pred_grid_data)
  obs_grid_size  = len(obs_grid_data)

  #
  # compute distances grids
  #
  for i, pred_data in enumerate(pred_grid_data[:-1]):
    meters, az, baz = gps.gps2DistAzimuth(float(obs_eq_lat), float(obs_eq_lon), 
                                          float(pred_grid_data[i][1]), float(pred_grid_data[i][0]))
    distance_grid.append(meters) 

  #
  # comparing the two grids not taking into account timeliness
  # ignoring the timeliness calculations
  #
  for j, mmi in enumerate(mmi_thresholds): # j, mmi values = 0 - 4 / 2 - 7
    for i, obs_data in enumerate(obs_grid_data[:-1]): # i = 0 thru obs_grid_size - 1. Last entry is a emtpy string.
      if float(obs_data[4]) > mmi_thresholds[j]:
        if float(pred_grid_data[i][4]) + tolerance > mmi_thresholds[j]:
          num_true_pos[j] = num_true_pos[j] + 1.0
        else:
          num_false_neg[j] = num_false_neg[j] + 1.0
      else:
        if float(pred_grid_data[i][4]) - tolerance > mmi_thresholds[j]:
          num_false_pos[j] = num_false_pos[j] + 1.0
        else:
          num_true_neg[j] = num_true_neg[j] + 1.0

    if num_true_pos[j] + num_false_neg[j] != 0.0:
      true_pos_rate[j]  = num_true_pos[j] / (num_true_pos[j] + num_false_neg[j])
      false_pos_rate[j] = num_false_pos[j] / (num_true_pos[j] + num_false_neg[j])

  #
  # Timeliness calculations
  #
  for j, mmi in enumerate(mmi_thresholds): # values = 0 - 4 / 2 - 7
    for i, obs_data in enumerate(obs_grid_data[:-1]): # i = 0 thru obs_grid_size - 1. Last entry is emtpy string.
      dist_km = distance_grid[i] / 1000.0
      ground_motion_time = dist_km / s_wave_velocity
      if float(obs_grid_data[i][4]) > mmi_thresholds[j]:
        if float(pred_grid_data[i][4]) + tolerance > mmi_thresholds[j]:
          if float(obs_alert_time) <= float(ground_motion_time):  # obs_alert_time might need to be type cast to float.
            num_true_pos_timeliness[j] = num_true_pos_timeliness[j] + 1.0
          else:
            num_false_neg_timeliness[j] = num_false_neg_timeliness[j] + 1.0
        else:
            num_false_neg_timeliness[j] = num_false_neg_timeliness[j] + 1.0
      else:
        if float(pred_grid_data[i][4]) - tolerance > mmi_thresholds[j]:
          num_false_pos_timeliness[j] = num_false_pos_timeliness[j] + 1.0
        else:
          num_true_neg_timeliness[j] = num_true_neg_timeliness[j] + 1.0

    if num_true_pos_timeliness[j] + num_false_neg_timeliness[j] != 0.0:
      true_pos_rate2[j]  = num_true_pos_timeliness[j] / (num_true_pos_timeliness[j] + num_false_neg_timeliness[j])
      false_pos_rate2[j] = num_false_pos_timeliness[j] / (num_true_pos_timeliness[j] + num_false_neg_timeliness[j])


  print "Non-timeliness"
  print "true pos rate {}".format(true_pos_rate)
  print "false pos rate {}".format(false_pos_rate)
  print "\n"
  print "Timeliness"
  print "true pos rate (timeliness) {}".format(true_pos_rate2)
  print "false pos rate (timeliness) {}".format(false_pos_rate2)
        
#
# main function ...
#
def main(argv):
  predicted_file = ''
  observed_file = ''
  alert_time = 0.0

  if len(argv) == 0:
    print "gmpe_eval.py -p <predicted_file> -o <observed_file> -a <alert time>"
    sys.exit(2)

  try:
    opts, args = getopt.getopt(argv, "hp:o:a:", ["help", "pfile=", "ofile=", "atime="])
  except getopt.GetoptError as err:
    print str(err)
    print "gmpe_eval.py -p <predicted_file> -o <observed_file> -a <alert time>"
    sys.exit(2)

  for opt, arg in opts:
    if opt in ("-h", "--help"):
      print "gmpe_eval.py -p <predicted_file> -o <observed_file> -t <alert time>"
      sys.exit(0)
    elif opt in ("-p", "--pfile"):
      predicted_file = arg
    elif opt in ("-o", "--ofile"):
      observed_file = arg
    elif opt in ("-a", "--atime"):
      alert_time = arg
    else:
      assert False, "unhandled option"

  process_grid (predicted_file, observed_file, alert_time)
  sys.exit(0)

#
# main entry ...
#
if __name__ == "__main__":
  main(sys.argv[1:])
