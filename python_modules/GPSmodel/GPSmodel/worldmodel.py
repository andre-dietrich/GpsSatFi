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
import dop
from mayavi import mlab

def make_cmap(colors, position=None, bit=False):
    '''
    make_cmap takes a list of tuples which contain RGB values. The RGB
    values may either be in 8-bit [0 to 255] (in which bit must be set to
    True when called) or arithmetic [0 to 1] (default). make_cmap returns
    a cmap with equally spaced colors.
    Arrange your tuples so that the first color is the lowest value for the
    colorbar and the last is the highest.
    position contains values from 0 to 1 to dictate the location of each color.
    '''
    import matplotlib as mpl

    bit_rgb = np.linspace(0,1,256)
    if position == None:
        position = np.linspace(0,1,len(colors))
    else:
        if len(position) != len(colors):
            print "position length must be the same as colors"
        elif position[0] != 0 or position[-1] != 1:
            print "position must start with 0 and end with 1"
    if bit:
        for i in range(len(colors)):
            colors[i] = (bit_rgb[colors[i][0]],
                         bit_rgb[colors[i][1]],
                         bit_rgb[colors[i][2]])
    cdict = {'red':[], 'green':[], 'blue':[]}
    for pos, color in zip(position, colors):
        cdict['red'].append((pos, color[0], color[0]))
        cdict['green'].append((pos, color[1], color[1]))
        cdict['blue'].append((pos, color[2], color[2]))

    cmap = mpl.colors.LinearSegmentedColormap('my_colormap',cdict,256)
    return cmap

##########################################################################################################
cmSatellites = make_cmap([(0,34,102), # 0
                          (24,116,205), # 1
                          (28,134,238), # 2
                          (205, 12,192), # 3
                          (255,20,147),
                          (255,  0,  0),
                          (204,200, 51),
                          (255,255,155),
                          (200,255,133),
                          (  0,255,  0),
                          (  0,200,  0),
                          (  0,140,  0),
                          (  0,130,  0)], bit=True)

cmDOP         =make_cmap([(  0,155,  0), # 1
                          (  0,255,  0), # 2
                          (255,255,100), (255,255,150), (255,127,0), # 4
                          (215,  0,  0), (225,  0,  0), (235,  0,  0), (245,  0,  0), (255,  0,  0), # 9
                          (255,20,147), (255,20,147), (255,20,147), (255,20,147), (255,20,147), (255,20,147), (255,20,147), (255,20,147), (255,20,147), (255,20,147), (255,20,147),
                          (28,134,238), (28,134,238), (24,116,205), (24,116,205), (24,116,205), (0,34,102)], bit=True)
##########################################################################################################

class ModelConfig():
    def __init__(self, config_file):
       myConfig = config.Configuration(config_file)
       self.modelFilename = myConfig.defaultParam['file']
       self.center = myConfig.defaultParam['center']
       self.gps_ops_file = myConfig.defaultParam['ops']
       self.time = myConfig.defaultParam['time']
       self.scanTo =  myConfig.defaultParam['scanTo']
       self.scanFrom =  myConfig.defaultParam['scanFrom']
       self.scanInc = myConfig.defaultParam['scanInc']
       self.image_file = myConfig.defaultParam['image']
       self.image_params = myConfig.defaultParam['image_params']
       self.output = myConfig.defaultParam['output']
       self.folder = myConfig.defaultParam['folder']
       self.dpi = myConfig.defaultParam['dpi']
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

class ODEGroundModel():
    def __init__(self, modelFilename):
        self.modelFilename = modelFilename
        self.world = ode.World()
        self.space = [ode.Space()]
        self.initEnvironmentModel()

    def initEnvironmentModel(self):
        faces = []
        vertices = []
        print self.modelFilename
        print "---------------------------------"
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


class WorldModel(ModelConfig):
    def __init__(self, config_file = []):
        ModelConfig.__init__(self, config_file)
        self.ODEWorldModel = ODEGroundModel(
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
        print "Determine satellite visibility"
        sat_relevant = self.GPSSatelliteModel.get_relevant_satellites(time)

        visibility_matrix = np.zeros(self.dim, dtype="int16")
        it = np.nditer(visibility_matrix, op_flags=['readwrite'])

        sat_configurations = []

        p = int((self.dim[0]*self.dim[1]*self.dim[2])/70.)
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
                    #if z <= self.scanRes:
                    it.iternext()

        stdout.write(' [ok] \n')
        pickle.dump(sat_configurations, open(self.folder+"satconfig"+'_'+str(time)+".p", "wb"))
        pickle.dump(visibility_matrix, open(self.folder+"vismatrix"+'_'+str(time)+".p", "wb"))
        return [sat_configurations, visibility_matrix]

    def load_visibility_results(self):
        sat_configurations = []
        visibility_matrix = []
        try:
            sat_configurations = pickle.load(open("sat_configurations.data", "rb" ))
            visibility_matrix = pickle.load(open("visibility_matrix.data", "rb" ))
        except:
            print 'No precalculated results found! Start calc_satellite_visibility!'
        return [sat_configurations, visibility_matrix]

    def calc_number_of_sat(self, visibility_matrix, sat_configurations):
        print "Evaluate number of satellites"
        matrix = np.zeros(self.dim, dtype="float")
        for i in range(len(sat_configurations)):
            matrix[np.where(visibility_matrix==i)] = len(sat_configurations[i])
        matrix[np.where(matrix == 0)]=np.nan
        return matrix

    def calc_dops(self, visibility_matrix, sat_configurations, output):
        if   output == "DOPH":
            f = lambda pos, sat: dop.H(pos, sat_pos)
        elif output == "DOPP":
            f = lambda pos, sat: dop.P(pos, sat_pos)
        elif output == "DOPT":
            f = lambda pos, sat: dop.T(pos, sat_pos)
        elif output == "DOPG":
            f = lambda pos, sat: dop.G(pos, sat_pos)
        elif output == "DOPV":
            f = lambda pos, sat: dop.V(pos, sat_pos)

        dop_matrix = np.zeros(self.dim, dtype="float32")
        for config_index in range(len(sat_configurations)-1):
            sat_pos = [ ]
            for sat_index in sat_configurations[config_index]:
                sat_pos.append(self.GPSSatelliteModel.satellites[sat_index]['position'])
            x=0
            y=0
            z=self.center[2]
            dop_matrix[np.where(visibility_matrix == config_index)]=f((x,y,z), sat_pos)
        return dop_matrix


class Viz2DWorldModel(WorldModel):
    def __init__(self, config_file = []):
        WorldModel.__init__(self, config_file)
        self.setSatelliteImageProp(*self.image_params)

    def init_plot(self):
        self.figure = plt.figure()
        self.myplot = plt.plot()
        plt.xlabel("    <west  east> [m]")
        plt.ylabel("    <south  north> [m]")
        plt.xlim([self.scanFrom[0]-100, self.scanTo[0]+100])
        plt.ylim([self.scanFrom[1]-100, self.scanTo[1]+100])

    def show_results(self, visibility_matrix, sat_configurations, time):
        for output in self.output:
            self.init_plot()
            self.add_background_image()
            self.add_plot_satellite_rays(visibility_matrix, sat_configurations)

            output, dataType = output.split('_')
            if output == 'SatCount':
                matrix = self.calc_number_of_sat(visibility_matrix,
                                                 sat_configurations)
                self.add_plot_satellite_count(matrix)
                if dataType == 'VTK':
                    matrix = np.nan_to_num(matrix)
                    vtk_matrix = mlab.pipeline.scalar_field(matrix)
            elif output in ['DOPH', 'DOPV', 'DOPP', 'DOPT', 'DOPG']:
                matrix = self.calc_dops(visibility_matrix,
                                           sat_configurations,
                                           output)
                self.add_plot_DOP(matrix)
                if dataType == 'VTK':
                    matrix = np.nan_to_num(matrix)
                    matrix[matrix > 25] = 25
                    vtk_matrix = mlab.pipeline.scalar_field(matrix)

            plt.title(output + ": " + datetime.datetime.fromtimestamp(time).isoformat())
            plt.savefig(self.folder+output+'_'+str(time)+".jpg", dpi=self.dpi)
            if dataType == 'VTK':
                vtk_matrix.save_output(self.folder+output+'_'+str(time)+".xml")
            else:
                pickle.dump(matrix, open(self.folder+output+'_'+str(time)+".p", "wb"))

    def add_plot_satellite_rays(self, visibility_matrix, sat_configurations):
        for sat in self.GPSSatelliteModel.satellites:
            if sat["visible"]:
                (x,y,_) = sat['position']
                plt.plot([self.scanTo[0] * np.cos(np.arctan2(y,x)), x], [self.scanTo[1] * np.sin(np.arctan2(y,x)), y],'--r', lw=3)#, opacity=0.5)

        # if visibility_matrix != []:
        #      dimension = visibility_matrix.shape
        #      config_index = visibility_matrix[0,int(math.ceil(dimension[1]/2)),int(math.ceil(dimension[2]/2))]
        #      for index in sat_configurations[config_index]:
        #          (x,y,_) = self.GPSSatelliteModel.satellites[index]['position']
        #          plt.plot([self.scanTo[0] * np.cos(np.arctan2(y,x)), x], [self.scanTo[1] * np.sin(np.arctan2(y,x)), y],'--b', lw=1)#, opacity=0.5)

    def add_plot_DOP(self, number_matrix = []):
        plt.imshow(number_matrix[0],
                       cmap=cmDOP,
                       alpha= 0.5 if self.image!=None else 1,
                       vmin=1, vmax=25,
                       extent=(self.scanFrom[0],
                               self.scanTo[0],
                               self.scanFrom[1],
                               self.scanTo[1]))
        plt.colorbar(ticks=np.linspace(0, 25, 26, endpoint=True))

    def add_plot_satellite_count(self, number_matrix = []):
        plt.imshow(number_matrix[40],
                               cmap=cmSatellites,
                               alpha=0.5 if self.image!=None else 1,
                               vmin=0, vmax=12,
                               extent=(self.scanFrom[0],
                                       self.scanTo[0],
                                       self.scanFrom[1],
                                       self.scanTo[1]))
        plt.colorbar(ticks=np.linspace(0, 12, 13, endpoint=True))

    def add_background_image(self):
        plt.imshow(self.image, extent=(-self.image_width * self.image_scale /2.,
                                            self.image_width * self.image_scale /2.,
                                           -self.image_height * self.image_scale /2.,
                                            self.image_height * self.image_scale /2.))
