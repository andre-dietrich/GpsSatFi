import ode
import ephem
import datetime
from gpssim import GPSSatelliteModel
import config 


class WorldModelConfig():
    def __init__(self, config_file):
       myConfig = config.Configuration(config_file)
       self.modelFilename = myConfig.defaultParam['file']
       self.center = myConfig.defaultParam['center']
       self.gps_ops_file = myConfig.defaultParam['ops']
       self.time = myConfig.defaultParam['time']
       self.scanTo =  myConfig.defaultParam['scanTo']
       self.scanFrom =  myConfig.defaultParam['scanFrom']

class ODEWorldModel(WorldModelConfig):
    def __init__(self, config_file):
        WorldModelConfig.__init__(self, config_file)
        self.world = ode.World()
        self.space = [ode.Space()]

        self.GPSSatelliteModel = GPSSatelliteModel()
        self.GPSSatelliteModel.initGPS(gps_ops_file=self.gps_ops_file,
                             lat=self.center[0],
                             lon=self.center[1],
                             ele=self.center[2])
        self.initEnvironmentModel()
        self.initRays()

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

    def initRays(self):
        for name in self.GPSSatelliteModel.satellites.keys():
            body = ode.Body(self.world)
            ray = ode.GeomRay(self.space[0], 10000)
            ray.setBody(body)
            self.GPSSatelliteModel.satellites[name]["ray"] = ray

    def calculateSatelliteVisibility(self, time, position):
        self.GPSSatelliteModel.determineRelevantSatellites(time)
        sat_relevant = [sat["position"] for _, sat in self.GPSSatelliteModel.satellites.items() if sat["visible"]]
        sat_visible = []
        for sat in sat_relevant:
            self.scan_ray.set((position[0],position[1],position[2]), sat)
            if ode.collide(self.model, self.scan_ray) == []:
                sat_visible.append(sat)
        print sat_visible
