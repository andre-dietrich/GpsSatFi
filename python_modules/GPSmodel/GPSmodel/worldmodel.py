import ode
import datetime
from gpssim import GPSSatelliteModel
import config 
import matplotlib.pyplot as plt
import numpy as np
import math
import pandas as pd
from sys import stdout
import pickle
import sys


class WorldModelConfig():
    def __init__(self, config_file):
       myConfig = config.Configuration(config_file)
       self.modelFilename = myConfig.defaultParam['file']
       self.center = myConfig.defaultParam['center']
       self.gps_ops_file = myConfig.defaultParam['ops']
       self.time = myConfig.defaultParam['time']
       self.scanTo =  myConfig.defaultParam['scanTo']
       self.scanFrom =  myConfig.defaultParam['scanFrom']
       self.scanInc = myConfig.defaultParam['scanInc']
       self.modus = myConfig.defaultParam['mode']
       self.image_file = myConfig.defaultParam['image']
       self.image_params = myConfig.defaultParam['image_params']
       self.output = myConfig.defaultParam['output']
       
       self.set_range(self.scanFrom, self.scanTo, self.scanInc)
       
       
    def set_range(self, pStart=(-400.,-400.,1.), pStop=(400.,400.,1.), pInc=10):
        """determines the range of the result matrix"""
        self.scanFrom = pStart
        self.scanTo   = pStop
        self.scanRes  = pInc

        self.dim = (int(math.ceil((pStop[2]-pStart[2])/pInc)),
                    int(math.ceil((pStop[1]-pStart[1])/pInc)),
                    int(math.ceil((pStop[0]-pStart[0])/pInc)))
                    
    def setSatelliteImageProp(self, width=1, height=1, scale=1):
        self.image_width  = width
        self.image_height = height
        self.image_scale  = scale
        try:
            self.image = plt.imread(self.image_file)
        except:
            self.image = None

class ODEWorldModel():
    def __init__(self, modelFilename):
        self.modelFilename = modelFilename
        self.world = ode.World()
        self.space = [ode.Space()]
        self.initEnvironmentModel()
        
    def initEnvironmentModel(self):
        faces = []
        vertices = []
        modelFile = open(self.modelFilename, "r")
        
        for line in modelFile.readlines():
            line = line.strip()
            if len(line) == 0 or line.startswith("#"):
                continue
            data = line.split(" ")
            if data[0] == "v":
                vertices.append((float(data[1].replace(",", ".")),
                                 float(data[2].replace(",", ".")),
                                 float(data[3].replace(",", "."))))
            if data[0] == "f":
                vertex1 = int(data[1].split("/")[0])-1
                vertex2 = int(data[2].split("/")[0])-1
                vertex3 = int(data[3].split("/")[0])-1
                faces.append((vertex1, vertex2, vertex3))

        data = ode.TriMeshData()
        data.build(vertices, faces)
        body = ode.Body(self.world)
        self.model = ode.GeomTriMesh(data, self.space[0])
        self.model.setBody(body)
        self.model.setQuaternion((0.7071067811865476, 0.7071067811865475, 0, 0))
        
        body2 = ode.Body(self.world)
        self.scan_ray = ode.GeomRay(self.space[0], 10000)
        self.scan_ray.setBody(body2)


class WorldModel(WorldModelConfig):
    def __init__(self, config_file):
        WorldModelConfig.__init__(self, config_file)
        self.ODEWorldModel = ODEWorldModel(
                             modelFilename=self.modelFilename)
        self.GPSSatelliteModel = GPSSatelliteModel(
                             gps_ops_file=self.gps_ops_file,
                             lat=self.center[0],
                             lon=self.center[1],
                             ele=self.center[2])
        self.init_GPS_rays()     

    def init_GPS_rays(self):
        for sat in self.GPSSatelliteModel.satellites:
            body = ode.Body(self.ODEWorldModel.world)
            ray = ode.GeomRay(self.ODEWorldModel.space[0], 10000)
            ray.setBody(body)
            sat["ray"] = ray
            
    def calc_satellite_visibility(self, time=[], postion=[]):
        if time:
            sat_relevant = self.GPSSatelliteModel.get_relevant_satellites(time)
        else:
            sat_relevant = self.GPSSatelliteModel.get_relevant_satellites(self.time[0])
        
        visibility_matrix = np.zeros(self.dim, dtype="int16")
        it = np.nditer(visibility_matrix, op_flags=['readwrite'])#flags=['f_index', ])
        
        sat_configurations = []        

        p = int((self.dim[0]*self.dim[1]*self.dim[2])/100.)
        count = 0     

        for z in np.arange(self.scanFrom[2], self.scanTo[2], self.scanRes):
            for y in np.arange(self.scanTo[1], self.scanFrom[1], -self.scanRes):
                for x in np.arange(self.scanFrom[0], self.scanTo[0], self.scanRes):

                    count += 1
                    if count % p == 0:
                        stdout.write(".")
                        stdout.flush()
  
                    current_visible_sats = [ ] 
                    for sat in sat_relevant:
                        self.ODEWorldModel.scan_ray.set((x,y,z), sat['position'])
                        if ode.collide(self.ODEWorldModel.model, self.ODEWorldModel.scan_ray) == []:
                            current_visible_sats.append(sat['index'])

                    if current_visible_sats not in sat_configurations:
                        sat_configurations.append(current_visible_sats)
                    it[0][...] = sat_configurations.index(current_visible_sats)
                   
                    # check ... does the iterator reach the last entry
                    if (z <= self.scanRes):
                       it.iternext()   
                       
        stdout.write('\n')
        print sat_configurations[0]
        pickle.dump(sat_configurations, open("sat_configurations.data", "wb"))
        pickle.dump(visibility_matrix, open("visibility_matrix.data", "wb"))
        return [sat_configurations, visibility_matrix]

    def calc_number_of_sat(self, visibility_matrix, sat_configurations):
        number_matrix = np.zeros(self.dim, dtype="float")
        for i in range(len(sat_configurations)):
            itemindex = np.where(visibility_matrix == i)
            print len(sat_configurations[i])
            if len(sat_configurations[i]) > 0:
                number_matrix[itemindex[0],itemindex[1],itemindex[2]]=len(sat_configurations[i])
            else:
                number_matrix[itemindex[0],itemindex[1],itemindex[2]]=np.nan
        return number_matrix
        
    def calc_dops(self):
        # count visible satellites
        if self.output == "number":
            f = lambda _, sat: len(sat_position) if sat_position != [] else np.NaN
        elif self.output == "H":
            f = lambda pos, sat: dop.H(pos, sat_position)
        elif self.output == "P":
            f = lambda pos, sat: dop.P(pos, sat_position)
        elif self.output == "T":
            f = lambda pos, sat: dop.T(pos, sat_position)
        elif self.output == "G":
            f = lambda pos, sat: dop.G(pos, sat_position)
        elif self.output == "V":
            f = lambda pos, sat: dop.V(pos, sat_position)
            
        visibility_matrix = np.zeros(self.dim, dtype="float32")
        it = np.nditer(visibility_matrix, op_flags=['readwrite'])#flags=['f_index', ])    
        

class Viz2DWorldModel(WorldModel):
    def __init__(self, config_file):
        WorldModel.__init__(self, config_file)
        self.setSatelliteImageProp(*self.image_params)
                  
    def init_plot(self):
        self.figure = plt.figure()
        self.myplot = plt.plot()
        plt.title("BLASDFA" + ": " + datetime.datetime.fromtimestamp(self.time[0]).isoformat())
        plt.xlabel("    <west  east> [m]")
        plt.ylabel("    <south  north> [m]")
        plt.xlim([self.scanFrom[0]-100, self.scanTo[0]+100])#+20])
        plt.ylim([self.scanFrom[1]-100, self.scanTo[1]+100])#+20])
        
    def addplotLOSSatellites(self, visibility_matrix, sat_configurations):
        for sat in self.GPSSatelliteModel.satellites:
          if sat["visible"]:
            (x,y,_) = sat['position']
            plt.plot([self.scanTo[0] * np.cos(np.arctan2(y,x)), x], [self.scanTo[1] * np.sin(np.arctan2(y,x)), y],'--r', lw=3)#, opacity=0.5)
            
        if visibility_matrix != []:
             dimension =  visibility_matrix.shape
             config_index = visibility_matrix[0,int(math.ceil(dimension[1]/2)),int(math.ceil(dimension[2]/2))]
             for index in sat_configurations[config_index]:
                 (x,y,_) = self.GPSSatelliteModel.satellites[index]['position']
                 plt.plot([self.scanTo[0] * np.cos(np.arctan2(y,x)), x], [self.scanTo[1] * np.sin(np.arctan2(y,x)), y],'--b', lw=1)#, opacity=0.5)

    def addplotNumberofSatellites(self, number_matrix = []):
        print number_matrix
        plt.imshow(number_matrix[0],
                       alpha=0.5 if self.image!=None else 1,
                       extent=(self.scanFrom[0],
                               self.scanTo[0],
                               self.scanFrom[1],
                               self.scanTo[1]))
        plt.colorbar()
        
    def addbackgroudImage(self):
        plt.imshow(self.image, extent=(-self.image_width  * self.image_scale /2.,
                                            self.image_width  * self.image_scale /2.,
                                           -self.image_height * self.image_scale /2.,
                                            self.image_height * self.image_scale /2.))
      
    def show(self):
        plt.show()