import sys
import os

sys.path.append("python_modules/GPSmodel/GPSmodel")

import config
from worldmodel import Viz2DWorldModel
import datetime
import numpy as np

myWorldModel = Viz2DWorldModel()
for t in range(*myWorldModel.time):
    print t
    [sat_configurations, visibility_matrix] = myWorldModel.calc_satellite_visibility(t)
#[sat_configurations, visibility_matrix] = myWorldModel.load_visibility_results()
    myWorldModel.show_results(visibility_matrix = visibility_matrix,
                          sat_configurations = sat_configurations,
                          time = t)

print 'Aus Maus'
