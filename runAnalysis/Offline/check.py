import setPYTHONPATH
setPYTHONPATH

import config
from worldmodel import Viz2DWorldModel
import datetime
import numpy as np

# init
myWorldModel = Viz2DWorldModel('check.ini')
# calculate satellite position at a single point in time
mytime = myWorldModel.time
[sat_configurations, visibility_matrix] = myWorldModel.calc_satellite_visibility()
number_matrix = myWorldModel.calc_number_of_sat(visibility_matrix = visibility_matrix, 
                                                sat_configurations = sat_configurations)

myWorldModel.init_plot()
myWorldModel.addbackgroudImage()
myWorldModel.addplotLOSSatellites(visibility_matrix = visibility_matrix, 
                                  sat_configurations = sat_configurations)
myWorldModel.addplotNumberofSatellites(number_matrix)
myWorldModel.show()

print 'Aus Maus'
