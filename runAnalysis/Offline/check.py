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
myWorldModel.calc_satellite_visibility(time = mytime[0],
                                   position = [0,0,30])
myWorldModel.init_plot()
myWorldModel.addplotLOSSatellites()
myWorldModel.show()

print 'Aus Maus'
