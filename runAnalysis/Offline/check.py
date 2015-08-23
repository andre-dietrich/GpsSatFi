import setPYTHONPATH
setPYTHONPATH

import config
from worldmodel import Viz2DWorldModel
import datetime
import numpy as np

myWorldModel = Viz2DWorldModel('check.ini')
mytime = myWorldModel.time
[sat_configurations, visibility_matrix] = myWorldModel.calc_satellite_visibility()
#[sat_configurations, visibility_matrix] = myWorldModel.load_visibility_results()
myWorldModel.show_results(visibility_matrix = visibility_matrix, 
                          sat_configurations = sat_configurations)

print 'Aus Maus'
