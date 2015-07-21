import odeViz.ode_visualization as viz
import ode
import vtk
from vtk.util import numpy_support
import math
import ephem
import numpy as np
import datetime
import dop
from itertools import product
from sys import stdout
import random

from joblib import Parallel, delayed
import multiprocessing

import matplotlib.pyplot as plt
from mayavi import mlab

from matplotlib2tikz import save as tikz_save

from pyevtk.hl import gridToVTK , pointsToVTK
import pickle


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

def sph2cart(azimuth,altitude,r):
            x = r * np.cos(altitude) * np.cos(math.pi/2-azimuth)
            y = r * np.cos(altitude) * np.sin(math.pi/2-azimuth)
            z = r * np.sin(altitude)
            return (x, y, z)

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

class GUI(viz.ODE_Visualization):
    def __init__(self, times):
        viz.ODE_Visualization.__init__(self, ode.World(), [ode.Space()])
        self.GetActiveCamera().SetPosition( 534.532069842, -2309.40051692, 724.034189778 )
        self.GetActiveCamera().SetFocalPoint( 0, 0, 0 )
        self.GetActiveCamera().SetViewUp( -0.00906125226669, 0.297235659949, 0.954761151368 )
        #self.GetActiveCamera().SetDistance(10000)

        self.setTimes(*times)
        self.initSlider()

    def setTimes(self, start, stop, increment):
        self.timeStart     = start
        self.timeStop      = stop
        self.timeIncrement = increment
        self.timeCurrent   = self.timeStart

    def initSlider(self):
        self.sliderRep  = vtk.vtkSliderRepresentation2D()
        self.sliderRep.SetMinimumValue(self.timeStart)
        self.sliderRep.SetMaximumValue(self.timeStop)
        self.sliderRep.SetValue(self.timeStart)
        self.sliderRep.SetTitleText("current time")
        self.sliderRep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
        self.sliderRep.GetPoint1Coordinate().SetValue(0.2, 0.92)
        self.sliderRep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
        self.sliderRep.GetPoint2Coordinate().SetValue(0.95, 0.92)
        self.sliderRep.SetSliderWidth(0.03)
        self.sliderRep.SetEndCapLength(0.03)
        self.sliderRep.SetEndCapWidth(0.03)
        self.sliderRep.SetTubeWidth(0.005)

        self.sliderWidget = vtk.vtkCenteredSliderWidget()
        self.sliderWidget.SetInteractor(self.iren)
        self.sliderWidget.SetRepresentation(self.sliderRep)
        self.sliderWidget.EnabledOn()

        self.sliderWidget.AddObserver("InteractionEvent", self.callback)

    def callback(self, obj, event):

        self.timeCurrent = int(obj.GetValue())
        #self.sliderRep.SetValue(self.timeCurrent)
        #self.calculate(self.timeCurrent)
        self.updateStatus()

    def start(self):
        """ starts the simulation, can be overwritten """
        self.iren.Initialize()
        self.iren.Start()

    def updateStatus(self):
        info = "Current Time: %s" % datetime.datetime.fromtimestamp(self.timeCurrent).ctime()
        self.setInfo(info)

    def calculate(self, time_):
        pass

    def loadModel(self, filename):
        faces     = []
        vertices  = []

        modelFile = open(filename, "r")
        for line in modelFile.readlines():
            line = line.strip()

            if len(line)==0 or line.startswith("#"):
                continue
            data = line.split(" ")
            if data[0]=="v":
                vertices.append((float(data[1].replace(",", ".")), float(data[2].replace(",", ".")), float(data[3].replace(",", "."))))
            if data[0]=="f":
                vertex1 = int(data[1].split("/")[0])-1
                vertex2 = int(data[2].split("/")[0])-1
                vertex3 = int(data[3].split("/")[0])-1
                faces.append((vertex1, vertex2, vertex3))

        data = ode.TriMeshData()
        data.build(vertices, faces)

        body = ode.Body(self.world)
        self.model = ode.GeomTriMesh(data, self.space[0])
        self.model.setBody(body)

        # rotate so that z becomes top
        self.addGeom(self.model, "model")
        self.model.setQuaternion((0.7071067811865476, 0.7071067811865475, 0, 0))
        #self.GetActor(self.model).RotateX(-90)
        self.update()


class GpsGUI(GUI):
    def __init__(self, times):
        GUI.__init__(self, times)

        self.satellites      = {}
        self.observer        = ephem.Observer()

    def initGPS(self, gps_ops_file, lat=0, lon=0, ele=0, preasure=0, horizon="0:0"):#'-0:32'):
        self.observer.lat       = str(lat)#np.deg2rad(lat)
        self.observer.long      = str(lon)#np.deg2rad(lon)
        self.observer.elevation = ele
        self.observer.pressure  = 0
        self.observer.horizon   = horizon

        f = open(gps_ops_file)
        l1 = f.readline()
        while l1:
            l2 = f.readline()
            l3 = f.readline()
            # ephem.readtle() creates a PyEphem Body object from that TLE
            sat = ephem.readtle(l1,l2,l3)
            self.satellites[sat.name] = {"ephem":sat, "visible":False, "position":(0,0,0), "ray":None}
            l1 = f.readline()
        f.close()

        for name in self.satellites.keys():
            body = ode.Body(self.world)
            ray = ode.GeomRay(self.space[0], 10000)
            ray.setBody(body)
            self.addGeom(ray, name)
            self.GetProperty(ray).SetColor(1,0,0)
            self.GetProperty(ray).SetLineWidth(3)
            self.GetActor(ray).SetVisibility(False)
            #ray.set((0,0,1), sat["pos"])
            self.satellites[name]["ray"] = ray

    def updateStatus(self):
        self.sliderRep.SetTitleText(datetime.datetime.fromtimestamp(self.timeCurrent).ctime())
        info = "Satellites:"# % datetime.datetime.fromtimestamp(self.timeCurrent).ctime()
        for name, sat in self.satellites.items():
            if sat["visible"]:
                info += "\n"+name+": "+str(sat["position"])
        self.setInfo(info)

    def updateSatellites(self):
        for _, sat in self.satellites.items():
            if sat["visible"]:
                self.GetActor(sat["ray"]).SetVisibility(True)
                sat["ray"].set((0,0,1), sat["position"])
            else:
                self.GetActor(sat["ray"]).SetVisibility(False)

        self.update()

    def calculate(self, time_):
        self.observer.date = ephem.Date(datetime.datetime.fromtimestamp(time_))

        for name, sat in self.satellites.items():
            sat["ephem"].compute(self.observer)
            if sat["ephem"].alt > 0:
                self.satellites[name]["visible"]  = True
                self.satellites[name]["position"] = sph2cart(self.satellites[name]["ephem"].az,
                                                             self.satellites[name]["ephem"].alt,
                                                             self.satellites[name]["ephem"].range)
            else:
                self.satellites[name]["visible"]  = False

        self.updateSatellites()

        return self.scan()

    def scan(self):
        pass

class MeasurementGUI(GpsGUI):
    def __init__(self, times):
        GpsGUI.__init__(self, times)
        self.setRange()

        self.setSatelliteImageProp()
        self.what = None

        self.sMode = ["S", "H", "P", "T", "G", "V"]
        self.iMode = 0

        self.folder = ""
        self.dpi    = 600
        self.jpeg   = True
        self.back   = False

        body = ode.Body(self.world)
        self.scan_ray = ode.GeomRay(self.space[0], 10000)
        self.scan_ray.setBody(body)

    def setRange(self, pStart=(-400.,-400.,1.), pStop=(400.,400.,1.), pInc=10):
        self.scanFrom = pStart
        self.scanTo   = pStop
        self.scanRes  = pInc

        self.dim = (int(math.ceil((pStop[2]-pStart[2])/pInc)),
                    int(math.ceil((pStop[1]-pStart[1])/pInc)),
                    int(math.ceil((pStop[0]-pStart[0])/pInc)))

        #self.initVolume()


    def setSatelliteImageProp(self, filename="", width=1, height=1, scale=1):
        self.image_width  = width
        self.image_height = height
        self.image_scale  = scale

        try:
            self.image = plt.imread(filename)
        except:
            self.image = None

    def initVolume(self):
        matrix = np.zeros(self.dim)
        self.v = vtk.vtkStructuredPoints()
        self.v.SetDimensions(matrix.shape)

        matrix = matrix.flatten()
        matrix = matrix.astype("uint16")

        self.v.GetPointData().SetScalars(numpy_support.numpy_to_vtk(matrix))

        # Create transfer mapping scalar value to opacity
        self.opacityTransferFunction = vtk.vtkPiecewiseFunction()
        self.opacityTransferFunction.AddPoint(0, 0.1)
        self.opacityTransferFunction.AddPoint(1, 0.01)
        self.opacityTransferFunction.AddPoint(9, 0.001)

        #for i in range(1,10,1):
        #    self.opacityTransferFunction.AddPoint(i, .9/i)
        #self.opacityTransferFunction.AddPoint(255, 0.8)

        # Create transfer mapping scalar value to color
        self.colorTransferFunction = vtk.vtkColorTransferFunction()
        self.colorTransferFunction.AddRGBPoint(0.0,  0.0, 0.0, 0.0)
        self.colorTransferFunction.AddRGBPoint(1.0,  1.0, 0.0, 0.0)
        self.colorTransferFunction.AddRGBPoint(9.0,  1.0, 1.0, 1.0)

        # The property describes how the data will look
        self.volumeProperty = vtk.vtkVolumeProperty()
        self.volumeProperty.SetColor(self.colorTransferFunction)
        self.volumeProperty.SetScalarOpacity(self.opacityTransferFunction)
        self.volumeProperty.ShadeOn()
        self.volumeProperty.SetInterpolationTypeToLinear()


        # The mapper / ray cast function know how to render the data
        self.compositeFunction = vtk.vtkVolumeRayCastCompositeFunction()
        self.volumeMapper = vtk.vtkVolumeRayCastMapper()
        self.volumeMapper.SetVolumeRayCastFunction(self.compositeFunction)
        self.volumeMapper.SetInput(self.v)

        self.volume = vtk.vtkVolume()
        self.volume.SetMapper(self.volumeMapper)
        self.volume.SetProperty(self.volumeProperty)

        #self.volume.RotateX(90)
        #self.volume.RotateY(-90)
        #self.volume.RotateX(180)
        #self.volume.RotateX(90)
        self.volume.SetScale(self.scanRes)

        self.ren.AddVolume(self.volume)

        self.update()

        self.volume.SetVisibility(False)

    def Keypress(self, key):
        if key == "s":
            print "scanning ", self.sMode[self.iMode]
            self.what = self.sMode[self.iMode]
            matrix = self.calculate(self.timeCurrent)
            #self.showVolume(matrix)
            self.plot(matrix)
            self.what = None
        elif key == "m":
            print "switch mode to",
            self.iMode = (self.iMode+1) % len(self.sMode)
            print self.sMode[self.iMode]
        elif key == "v":
            print "switch visualization"
            #self.volume.SetVisibility( not self.volume.GetVisibility() )
            if self.volume.GetVisibility():
                self.volume.SetVisibility(False)
                self.GetActor(self.model).SetVisibility(True)
            else:
                self.volume.SetVisibility(True)
                self.GetActor(self.model).SetVisibility(False)
        elif key == "r":
            print "run"
            self.autoScan()
        elif key == "a":
            print "average ", self.sMode[self.iMode]

            self.what = self.sMode[self.iMode]

            matrizes = np.zeros(self.dim)
            counter = 0
            for t in range(self.timeStart, self.timeStop, self.timeIncrement):
                self.sliderRep.SetValue(t)
                self.callback(self.sliderRep, "")
                matrizes += self.calculate(self.timeCurrent)
                counter += 1
                self.update()

            self.plot(matrizes/counter)
            self.what = None
        elif key == "t":
            print "save to tikz"
            self.what = self.sMode[self.iMode]
            matrix = self.calculate(self.timeCurrent)
            self.plot(matrix, ion=True)
            self.what = None
            tikz_save( 'myfile.tikz', figureheight='4cm', figurewidth='6cm' )

        elif key == "d":
            self.singleDiff()

        # plot dots representing a common satelite configuration
        elif key == "b":
            print "view dots"
            self.what = "D"
            matrix = self.calculate(self.timeCurrent)
            self.plot(matrix)
            self.what = None

#    def showVolume(self, matrix):
#        if not self.volume.GetVisibility():
#            return
#
#        m=np.zeros((matrix.shape[2],matrix.shape[1],matrix.shape[0]))
#
#        for i in range(matrix.shape[0]):
#            for j in range(matrix.shape[1]):
#                for k in range(matrix.shape[2]):
#                    m[k,j,i] = matrix[i,j,k]
#
#
#        matrix = m.flatten()
#        matrix = matrix.astype("uint16")
#        self.v.GetPointData().SetScalars(numpy_support.numpy_to_vtk(matrix))


    def autoScan(self):
        plt.ion()
        plt.show()
        self.what = self.sMode[self.iMode]
        for t in range(self.timeStart, self.timeStop, self.timeIncrement):
            self.sliderRep.SetValue(t)
            self.callback(self.sliderRep, "")
            matrix = self.calculate(self.timeCurrent)
            self.plot(matrix, True)
            if self.jpeg:
                plt.savefig(self.folder+"/"+ self.what+str(self.timeCurrent)+".jpg", dpi=self.dpi)
        self.what = None
        plt.ioff()

    def singleDiff(self):
        print "calc difference"

        origin    = np.zeros(((self.timeStop-self.timeStart)/self.timeIncrement, 32))
        scattered = np.zeros(((self.timeStop-self.timeStart)/self.timeIncrement, 32))

        for i, t in enumerate(range(self.timeStart, self.timeStop, self.timeIncrement)):
            self.sliderRep.SetValue(t)
            self.callback(self.sliderRep, "")

            o = np.zeros(32)
            s = np.zeros(32)

            self.observer.date = ephem.Date(datetime.datetime.fromtimestamp(t))

            for name, sat in self.satellites.items():
                sat["ephem"].compute(self.observer)
                pos = 32-int(name.split("(")[1][4:6])
                if sat["ephem"].alt > 0:
                    self.satellites[name]["visible"]  = True
                    self.satellites[name]["position"] = sph2cart(self.satellites[name]["ephem"].az,
                                                                 self.satellites[name]["ephem"].alt,
                                                                 self.satellites[name]["ephem"].range)
                    o[pos]=1

                    #self.scan_ray.set((-100,-40,17), self.satellites[name]["position"])
                    self.scan_ray.set((0,0,1), self.satellites[name]["position"])

                    self.GetProperty(self.satellites[name]["ray"]).SetColor(1,0,0)#SetLineWidth(3)

                    if ode.collide(self.model, self.scan_ray) != []:
                        s[pos]=1
                        self.GetProperty(self.satellites[name]["ray"]).SetColor(0,0,0) #.SetLineWidth(3)
                else:
                    self.satellites[name]["visible"]  = False

            self.updateSatellites()
            self.update()
            origin[i]   =o
            scattered[i]=s

        #print origin
        #print scattered

        plt.matshow(scattered.transpose(), fignum=100, cmap=plt.cm.gray)
        plt.show()

    def scan(self):
        import time
        t = time.time()

        if self.what == None:
            return np.zeros(self.dim)

        sat_visible = [sat["position"] for _, sat in self.satellites.items() if sat["visible"]]
        
        sat_visible_name=[]
        for name, sat in self.satellites.items():
            if sat["visible"] == True:
              sat_visible_name.append(name)

        if self.what == "S":
            # count visible satellites
            f = lambda _, sat: len(sat_position) if sat_position != [] else np.NaN
        elif self.what == "H":
            f = lambda pos, sat: dop.H(pos, sat_position)
        elif self.what == "P":
            f = lambda pos, sat: dop.P(pos, sat_position)
        elif self.what == "T":
            f = lambda pos, sat: dop.T(pos, sat_position)
        elif self.what == "G":
            f = lambda pos, sat: dop.G(pos, sat_position)
        elif self.what == "V":
            f = lambda pos, sat: dop.V(pos, sat_position)


        #checker_matrix = []

        #print "size:", colMatrix.size
        #print self.dim
        colMatrix = np.zeros(self.dim, dtype="float32")
        it = np.nditer(colMatrix, op_flags=['readwrite'])#flags=['f_index', ])

        sat_bak = 1
        val_bak = -1

        #bak = {}

        p = int((self.dim[0]*self.dim[1]*self.dim[2])/100.)
        count = 0

        areas = []
        colors = []
        # generation of virtual values for the regions
        color_values = np.random.random_sample((10000,))

        for z in np.arange(self.scanFrom[2], self.scanTo[2], self.scanRes):
            for y in np.arange(self.scanTo[1], self.scanFrom[1], -self.scanRes):
                for x in np.arange(self.scanFrom[0], self.scanTo[0], self.scanRes):

                    count += 1
                    if count % p == 0:
                        stdout.write(".")
                        stdout.flush()

                    # list containin all visible satellite positions
                    sat_position = [ ]
                    # list containin all visible satellite names
                    satellite_pattern = []
  
                    if self.what in ["S", "H", "P", "T", "G", "V"]:
                      for sat in sat_visible:
                          self.scan_ray.set((x,y,z), sat)
                          if ode.collide(self.model, self.scan_ray) == []:
                              sat_position.append(sat)
                      #DOP Calculations --------------------------------------
                      it[0][...] = f((x,y,z), sat_position)  
                              
                    if self.what == "D":  
                      for i in range(0,len(sat_visible)-1):
                          # look for shadowed satellites due to buildings
                          self.scan_ray.set((x,y,z), sat_visible[i])
                          if ode.collide(self.model, self.scan_ray) == []:
                              sat_position.append(sat_visible[i])
                              satellite_pattern.append(sat_visible_name[i])
                    
                      #add the new area typ
                      currentValue = []
                      if not satellite_pattern:
                        currentValue = None
                      else:
                        currentHash = hash(str(satellite_pattern))
                        # current configuration allready appeared?
                        for config in areas:
                          if currentHash == config["hash"]:
                            currentValue = config['value']
                            break
                        # new satellite configuration that have to be registered
                        if currentValue == []:
                            currentValue =  color_values[len(areas)]
                            print currentValue
                            areas.append({"hash": currentHash,
                                          "value": currentValue})
                      #write the stochastic configuration ID to Matrix
                      it[0][...] = currentValue
                   
                    # check ... does the iterator reach the last entry
                    if (z <= self.scanRes):
                       it.iternext()


        #print "done"
        #result = Parallel(n_jobs=-1)(delayed(dop.G)(p, s) for p, s in checker_matrix)
        #return np.array(result).reshape(self.dim)
        #print result

        #print "", time.time() - t
        #pickle.dump( colMatrix, open( "matrix.np", "wb" ) )
        print len(areas)
        return colMatrix
        

    def plot(self, matrix, ion=False):

        if ion == True:
            plt.clf()
        else:
            plt.figure()
            plt.plot()

        plt.title(self.what + ": " + datetime.datetime.fromtimestamp(self.timeCurrent).isoformat())
        plt.xlabel("    <west  east> [m]")
        plt.ylabel("     <south  north> [m]")

        for _, sat in self.satellites.items():
            if sat["visible"]:
                (x,y,_) = sat['position']
                plt.plot([self.scanTo[0] * np.cos(np.arctan2(y,x)), x], [self.scanTo[1] * np.sin(np.arctan2(y,x)), y],'--r', lw=2)#, opacity=0.5)

        if self.image != None:
            #plt.xlim([-self.image_width  * self.image_scale /2.,self.image_width  * self.image_scale /2.])
            #plt.ylim([-self.image_height * self.image_scale /2.,self.image_height * self.image_scale /2.])

            plt.xlim([self.scanFrom[0]-100, self.scanTo[0]+100])#+20])
            plt.ylim([self.scanFrom[1]-100, self.scanTo[1]+100])#+20])

            plt.imshow(self.image, extent=(-self.image_width  * self.image_scale /2.,
                                            self.image_width  * self.image_scale /2.,
                                           -self.image_height * self.image_scale /2.,
                                            self.image_height * self.image_scale /2.))
        else:
            plt.xlim([self.scanFrom[0], self.scanTo[0]])
            plt.ylim([self.scanFrom[1], self.scanTo[1]])

        if self.what == "S":
            plt.imshow(matrix[0],
                       cmap=cmSatellites,
                       alpha=0.5 if self.image!=None else 1,
                       vmin=0, vmax=12,
                       extent=(self.scanFrom[0],
                               self.scanTo[0],
                               self.scanFrom[1],
                               self.scanTo[1]))
            plt.colorbar(ticks=np.linspace(0, 12, 13, endpoint=True))

            #matrix=matrix.transpose()
            #mlab.pipeline.volume(mlab.pipeline.scalar_field(1/matrix))
            #mlab.axes()
            #mlab.show()
            
        elif self.what == "D":
            # determine the number of configurations
            values = matrix[0].reshape(1,matrix[0].size,order='F').copy()
            values = values[~np.isnan(values)]
            different_configs = np.unique(values)
            # generate map
            plt.imshow(matrix[0],
                       cmap=cmSatellites,
                       alpha=0.5 if self.image!=None else 1,
                       vmin=0, vmax=1,
                       extent=(self.scanFrom[0],
                               self.scanTo[0],
                               self.scanFrom[1],
                               self.scanTo[1]))

        else:
            #matrix = np.nan_to_num(matrix)
            #matrix[matrix >25] = 25
            plt.imshow(matrix[0],
                       cmap=cmDOP,
                       alpha= 0.5 if self.image!=None else 1,
                       vmin=1, vmax=25,
                       extent=(self.scanFrom[0],
                               self.scanTo[0],
                               self.scanFrom[1],
                               self.scanTo[1]))
            plt.colorbar(ticks=np.linspace(0, 25, 26, endpoint=True))

            #matrix=matrix.transpose()
            matrix = np.nan_to_num(matrix)
            matrix[matrix>25] = 25
            #matrix[matrix == 0] = 25
            print "fin"

            #xx = []
            #yy = []
            #zz = []
            #for z, _ in enumerate(np.arange(self.scanFrom[2], self.scanTo[2], self.scanRes)):
            #    for y, _ in enumerate(np.arange(self.scanTo[1], self.scanFrom[1], -self.scanRes)):
            #        for x, _ in enumerate(np.arange(self.scanFrom[0], self.scanTo[0], self.scanRes)):
            #            xx.append(x)
            #            yy.append(y)
            #            zz.append(z)

            #gridToVTK("./structured", np.array(xx), np.array(yy), np.array(zz), pointData = {"dop" : matrix.flatten().astype(np.float32)}, cellData = {"dop" : matrix.flatten().astype(np.float32)})
            #mlab.pipeline.volume(mlab.pipeline.scalar_field(matrix))
            ##mlab.axes()
            #mlab.show()

        if ion == True:
            plt.draw()
        else:
            plt.show()

if __name__ == "__main__":

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="file", metavar="FILE", default="../data/169e9c3f4684f96eaee9b3cc81032049.obj")

    #parser.add_option("-i", "--image",  dest="image", metavar="FILE", default="")
    parser.add_option("-i", "--image",  dest="image", metavar="FILE", default="../data/169e9c3f4684f96eaee9b3cc81032049.jpeg")
    parser.add_option("--image_params", dest="image_params", type="float", nargs=3, default=(800, 800, 2.90764936216))

    parser.add_option("-t", "--time",  dest="time",  type="int",   nargs=3, default=(1423004400, 1423090800, 29))

    parser.add_option("--scanFrom", dest="scanFrom", type="float", nargs=3, default=(-250, -200, 1))
    parser.add_option("--scanTo",   dest="scanTo",   type="float", nargs=3, default=( 250,  200, 140))
    parser.add_option("--scanInc",  dest="scanInc",  type="float",          default=4)

    parser.add_option("--folder",  dest="folder",  type="string",  default="data")
    parser.add_option("--dpi",     dest="dpi",     type="int",     default=500)
    parser.add_option("--auto",    dest="auto",    type="int",     default=0)

    parser.add_option("-m", "--mode",    dest="mode",    type="int",     default=0)

    parser.add_option("--ops", dest="ops", metavar="FILE", default="../data/gps-ops.txt")
    #parser.add_option("--center", dest="center", type="float", nargs=3, default=(52.5090004233191, 13.37605, 30))
    52.50978
    parser.add_option("--center", dest="center", type="float", nargs=3, default=(52.50978, 13.372995, 30))

    (op, args) = parser.parse_args()
    
    print op

#     sim = Simulation(options.file,
#                      options.image,
#                      options.scale, options.width, options.height,
#                      (options.x1, options.y1, options.z1, options.x2, options.y2, options.z2), options.resolution,
#                      (options.c0, options.c1, options.c2),
#                      (options.t_start, options.t_stop, options.t_inc))
#
#     # start the simulation
#     sim.start()

    gps = MeasurementGUI(op.time)
    gps.loadModel(op.file)
    gps.initGPS(op.ops, lat=op.center[0], lon=op.center[1], ele=op.center[2])
    gps.setRange(op.scanFrom, op.scanTo, op.scanInc)
    #gps.setTimes(*op.time)
    gps.dpi = op.dpi
    gps.folder = op.folder
    gps.setSatelliteImageProp(op.image, *op.image_params)
    gps.iMode = op.mode
    gps.start()
#===============================================================================
