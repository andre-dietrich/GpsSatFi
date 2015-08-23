import ephem
import math
import numpy as np
import datetime


def sph2cart(azimuth, altitude, r):
            x = r * np.cos(altitude) * np.cos(math.pi/2-azimuth)
            y = r * np.cos(altitude) * np.sin(math.pi/2-azimuth)
            z = r * np.sin(altitude)
            return (x, y, z)


class GPSSatelliteModel():
    def __init__(self, gps_ops_file, lat=0, lon=0, ele=0,
                preasure=0, horizon="0:0"):
        self.satellites = []
        self.observer = ephem.Observer()
        self.gps_ops_file= gps_ops_file
        self.observer.lat = str(lat)
        self.observer.long = str(lon)
        self.observer.elevation = ele
        self.observer.pressure = 0
        self.observer.horizon = horizon
        self.initGPS()

    def initGPS(self):
        f = open(self.gps_ops_file)
        l1 = f.readline()
        while l1:
            l2 = f.readline()
            l3 = f.readline()
            # ephem.readtle() creates a PyEphem Body object from that TLE
            sat = ephem.readtle(l1, l2, l3)
            self.satellites.append({"ephem": sat, "visible": False,
                                     "position": (0, 0, 0), "ray": None,
                                     "name": sat.name, 
                                     "index": len(self.satellites)})
            l1 = f.readline()
        f.close()

    def determine_relevant_satellites(self, time_):
        self.observer.date = ephem.Date(datetime.datetime.fromtimestamp(time_))
        for sat in self.satellites:
            sat["ephem"].compute(self.observer)
            if sat["ephem"].alt > 0:
                sat["visible"] = True
                sat["position"] = sph2cart(
                            sat["ephem"].az,
                            sat["ephem"].alt,
                            sat["ephem"].range)
            else:
                sat["visible"] = False
        return self.satellites
        
    def get_relevant_satellites(self, time_):
        '''Reduces the number of satellites to those that are visible'''
        self.determine_relevant_satellites(time_)
        return [sat 
                for sat in self.satellites 
                if sat["visible"]]
