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
    def __init__(self):
        self.satellites = {}
        self.observer = ephem.Observer()

    def initGPS(self, gps_ops_file, lat=0, lon=0, ele=0,
                preasure=0, horizon="0:0"):
        self.observer.lat = str(lat)
        self.observer.long = str(lon)
        self.observer.elevation = ele
        self.observer.pressure = 0
        self.observer.horizon = horizon

        f = open(gps_ops_file)
        l1 = f.readline()
        while l1:
            l2 = f.readline()
            l3 = f.readline()
            # ephem.readtle() creates a PyEphem Body object from that TLE
            sat = ephem.readtle(l1, l2, l3)
            self.satellites[sat.name] = {"ephem": sat, "visible": False,
                                         "position": (0, 0, 0), "ray": None}
            l1 = f.readline()
        f.close()

    def determineRelevantSatellites(self, time_):
        self.observer.date = ephem.Date(datetime.datetime.fromtimestamp(time_))
        for name, sat in self.satellites.items():
            sat["ephem"].compute(self.observer)
            if sat["ephem"].alt > 0:
                self.satellites[name]["visible"] = True
                self.satellites[name]["position"] = sph2cart(
                            self.satellites[name]["ephem"].az,
                            self.satellites[name]["ephem"].alt,
                            self.satellites[name]["ephem"].range)
            else:
                self.satellites[name]["visible"] = False
        return self.satellites
