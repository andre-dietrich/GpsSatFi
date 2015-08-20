import ode
import ephem
import datetime
from gpssim import GPSSatelliteModel
import config 
import matplotlib.pyplot as plt
import numpy as np


class WorldModelConfig():
    def __init__(self, config_file):
       myConfig = config.Configuration(config_file)
       self.modelFilename = myConfig.defaultParam['file']
       self.center = myConfig.defaultParam['center']
       self.gps_ops_file = myConfig.defaultParam['ops']
       self.time = myConfig.defaultParam['time']
       self.scanTo =  myConfig.defaultParam['scanTo']
       self.scanFrom =  myConfig.defaultParam['scanFrom']
       self.modus = myConfig.defaultParam['mode']
       self.image_file = myConfig.defaultParam['image']
       self.image_params = myConfig.defaultParam['image_params']

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
        self.scan_ray = ode.GeomRay(self.space[0], 10000)
        self.scan_ray.setBody(body)


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
        for name in self.GPSSatelliteModel.satellites.keys():
            body = ode.Body(self.ODEWorldModel.world)
            ray = ode.GeomRay(self.ODEWorldModel.space[0], 10000)
            ray.setBody(body)
            self.GPSSatelliteModel.satellites[name]["ray"] = ray

    def calc_satellite_visibility(self, time=[], postion=[]):
        time = self.time[0]
        position = [0, 0, 30]
        self.GPSSatelliteModel.determineRelevantSatellites(time)
        sat_relevant = [sat["position"] for _, sat in self.GPSSatelliteModel.satellites.items() if sat["visible"]]
        sat_visible = []
        for sat in sat_relevant:
            self.ODEWorldModel.scan_ray.set((position[0],position[1],position[2]), sat)
            if ode.collide(self.ODEWorldModel.model, self.ODEWorldModel.scan_ray) == []:
                sat_visible.append(sat)
        return sat_visible

class Viz2DWorldModel(WorldModel):
    def __init__(self, config_file):
        WorldModel.__init__(self, config_file)
        self.setSatelliteImageProp(*self.image_params)
       
    def setSatelliteImageProp(self, width=1, height=1, scale=1):
        self.image_width  = width
        self.image_height = height
        self.image_scale  = scale
        try:
            self.image = plt.imread(self.image_file)
        except:
            self.image = None
            
    def init_plot(self):
        map_figure=plt.figure()
        self.myplot=plt.plot()
        plt.title("BLASDFA" + ": " + datetime.datetime.fromtimestamp(self.time[0]).isoformat())
        plt.xlabel("    <west  east> [m]")
        plt.ylabel("    <south  north> [m]")
        plt.xlim([self.scanFrom[0]-100, self.scanTo[0]+100])#+20])
        plt.ylim([self.scanFrom[1]-100, self.scanTo[1]+100])#+20])
        
    def addplotLOSSatellites(self, visibleSats = []):
        for _, sat in self.GPSSatelliteModel.satellites.items():
          if sat["visible"]:
            (x,y,_) = sat['position']
            plt.plot([self.scanTo[0] * np.cos(np.arctan2(y,x)), x], [self.scanTo[1] * np.sin(np.arctan2(y,x)), y],'--r', lw=3)#, opacity=0.5)
            
        if visibleSats:
          for sat in visibleSats:
            (x,y,_) = sat
            plt.plot([self.scanTo[0] * np.cos(np.arctan2(y,x)), x], [self.scanTo[1] * np.sin(np.arctan2(y,x)), y],'--b', lw=1)#, opacity=0.5)

    def addbackgroudImage(self):
        plt.imshow(self.image, extent=(-self.image_width  * self.image_scale /2.,
                                            self.image_width  * self.image_scale /2.,
                                           -self.image_height * self.image_scale /2.,
                                            self.image_height * self.image_scale /2.))
      
    def show(self):
        plt.show()