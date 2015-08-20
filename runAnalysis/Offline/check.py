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
visibleSats = myWorldModel.calc_satellite_visibility()
myWorldModel.init_plot()
myWorldModel.addbackgroudImage()
myWorldModel.addplotLOSSatellites(visibleSats)
myWorldModel.show()

print 'Aus Maus'
