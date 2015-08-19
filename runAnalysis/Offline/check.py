import setPYTHONPATH
setPYTHONPATH

import config
from worldmodel import ODEWorldModel
import matplotlib.pyplot as plt
import datetime
import numpy as np

# init
myGUI = ODEWorldModel('check.ini')
# calculate satellite position at a single point in time
mytime = myGUI.time
myGUI.calculateSatelliteVisibility(time = mytime[0],
                                   position = [0,0,30])

map_figure=plt.figure()
plt.plot()

plt.title("BLASDFA" + ": " + datetime.datetime.fromtimestamp(mytime[0]).isoformat())
plt.xlabel("    <west  east> [m]")
plt.ylabel("     <south  north> [m]")
for _, sat in myGUI.GPSSatelliteModel.satellites.items():
    if sat["visible"]:
        print sat
        (x,y,_) = sat['position']
        plt.plot([myGUI.scanTo[0] * np.cos(np.arctan2(y,x)), x], [myGUI.scanTo[1] * np.sin(np.arctan2(y,x)), y],'--r', lw=2)#, opacity=0.5)

        plt.xlim([myGUI.scanFrom[0]-100, myGUI.scanTo[0]+100])#+20])
        plt.ylim([myGUI.scanFrom[1]-100, myGUI.scanTo[1]+100])#+20])

    #    plt.imshow(config.defaultParam['image'],
    #                extent=(-self.image_width  * self.image_scale /2.,
#                             self.image_width  * self.image_scale /2.,
#                            -self.image_height * self.image_scale /2.,
#                             self.image_height * self.image_scale /2.))
plt.show()
print 'Aus Maus'
