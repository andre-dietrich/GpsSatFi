# python main.py --scanInc 2 --scanFrom -200.0  -200.0 1.0  --scanTo 200  200 2 mode 1 --image_params 900 834 1.453798

import odeViz.ode_visualization as viz
from odeViz.ode_helper import loadObj
import ode
import vtk
#from vtk.util import numpy_support
import matplotlib.pyplot as plt
import math
import ephem
import numpy as np
import datetime
from sys import stdout
import analyze
import cmap as colorMap

def sph2cart(azimuth, altitude, r):
    x = r * np.cos(altitude) * np.cos(math.pi / 2 - azimuth)
    y = r * np.cos(altitude) * np.sin(math.pi / 2 - azimuth)
    z = r * np.sin(altitude)
    return (x, y, z)

###############################################################################

class World(viz.ODE_Visualization):
    def __init__(self):
        viz.ODE_Visualization.__init__(self, ode.World(), [ode.Space()])
        self.GetActiveCamera().SetPosition( 534.532069842,
                                          -2309.40051692,
                                            724.034189778 )
        self.GetActiveCamera().SetFocalPoint( 0, 0, 0 )
        self.GetActiveCamera().SetViewUp( -0.00906125226669,
                                           0.29723565994900,
                                           0.95476115136800 )



    def start(self):
        """ starts the simulation, can be overwritten """
        self.iren.Initialize()
        self.iren.Start()

    def loadModel(self, filename):
        mesh = loadObj(filename)

        body = ode.Body(self.world)
        self.model = ode.GeomTriMesh(mesh, self.space[0])
        self.model.setBody(body)

        # rotate so that z becomes top
        self.addGeom(self.model, "model")
        self.model.setQuaternion((0.7071067811865476, 0.7071067811865475, 0, 0))
        self.update()

class Satellites(World):
    def __init__(self):
        World.__init__(self)

        self.satellites      = {}
        self.observer        = ephem.Observer()

    def initGPS(self, gps_ops_file, lat=0, lon=0, ele=0, pressure=0, horizon="0:0"):#'-0:32'):
        self.observer.lat       = str(lat)#np.deg2rad(lat)
        self.observer.long      = str(lon)#np.deg2rad(lon)
        self.observer.elevation = ele
        self.observer.pressure  = pressure
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

class Measurement(Satellites):
    def __init__(self):
        Satellites.__init__(self)

        body = ode.Body(self.world)
        self.scan_ray = ode.GeomRay(self.space[0], 10000)
        self.scan_ray.setBody(body)

    def scan(self, time_, start, stop, inc):

        self.calculate(time_)
        sat_visible = [sat["position"] for _, sat in self.satellites.items() if sat["visible"]]

        dim = (int(math.ceil((stop[2]-start[2])/inc)),
               int(math.ceil((stop[1]-start[1])/inc)),
               int(math.ceil((stop[0]-start[0])/inc)))

        colMatrix = np.zeros(dim, dtype="int16")
        it = np.nditer(colMatrix, op_flags=['writeonly'])#flags=['f_index', ])

        # positions of satellites
        satConf = [None,[]]

        p = int((dim[0]*dim[1]*dim[2])/100.)
        count = 0

        for z in np.arange(start[2], stop[2], inc):
            for y in np.arange(stop[1], start[1], -inc):
                for x in np.arange(start[0], stop[0], inc):

                    count += 1
                    if count % p == 0:
                        stdout.write(".")
                        stdout.flush()

                    satellite_positions = []

                    # check if inside a building or not...
                    self.scan_ray.set((x, y, z), (x, y, 2000))
                    if ode.collide(self.model, self.scan_ray) == []:
                        for sat in sat_visible:
                            self.scan_ray.set((x, y, z), sat)
                            if ode.collide(self.model, self.scan_ray) == []:
                                satellite_positions.append(sat)
                    else:
                        satellite_positions = None

                    try:
                        it[0][...] = satConf.index(satellite_positions)
                    except:
                        it[0][...] = len(satConf)
                        satConf.append(satellite_positions)

                    it.iternext()

        # result is a vector with satellite positions and a matrix
        return {"config" : satConf,
                "matrix" : colMatrix,
                "time" : time_,
                "area" : {"start" : start, "stop" : stop, "inc" : inc},
                "dim" : colMatrix.shape,
                "observer" : { "lat" : float(self.observer.lat),
                               "long" : float(self.observer.long),
                               "elevation" : float(self.observer.elevation),
                               "pressure" : float(self.observer.pressure),
                               "horizon" : str(self.observer.horizon) }}

class Control(Measurement):
    def __init__(self):
        Measurement.__init__(self)

        #######################################################################
        self.sliderTime = vtk.vtkSliderRepresentation2D()
        self.sliderTime.SetTitleText("time")
        self.sliderTime.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
        self.sliderTime.GetPoint1Coordinate().SetValue(0.2, 0.92)
        self.sliderTime.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
        self.sliderTime.GetPoint2Coordinate().SetValue(0.95, 0.92)
        self.sliderTime.SetSliderWidth(0.03)
        self.sliderTime.SetEndCapLength(0.03)
        self.sliderTime.SetEndCapWidth(0.03)
        self.sliderTime.SetTubeWidth(0.005)

        self.sliderWidget = vtk.vtkCenteredSliderWidget()
        self.sliderWidget.SetInteractor(self.iren)
        self.sliderWidget.SetRepresentation(self.sliderTime)
        self.sliderWidget.EnabledOn()

        self.sliderWidget.AddObserver("InteractionEvent", self.callbackTime)

    def setTimes(self, start, stop, increment):
        self.timeStart = start
        self.timeStop = stop
        self.timeIncrement = increment
        self.timeCurrent = self.timeStart

        self.sliderTime.SetMinimumValue(self.timeStart)
        self.sliderTime.SetMaximumValue(self.timeStop)
        self.sliderTime.SetValue(self.timeStart)

    def scan(self, time_, start, stop, inc):
        self.timeCurrent = time_
        self.sliderTime.SetValue(time_)
        self.SatelliteScan = super(Control, self).scan(time_, start, stop, inc)
        return self.SatelliteScan

    def setRanges(self, start, stop, increment):
        self.positionStart = start
        self.positionStop = stop
        self.positionInc = increment

    def callbackTime(self, obj, event):
        self.timeCurrent = obj.GetRepresentation().GetValue()
        self.updateStatus()

        self.SatelliteScan = self.scan( self.timeCurrent,
                                        self.positionStart,
                                        self.positionStop,
                                        self.positionInc)

def SatCount(conf, element):
    return len(conf[element])


class Analysis(Control):

    def __init__(self, interactive=True):
        Control.__init__(self)

        self.sliderRange = vtk.vtkSliderRepresentation2D()
        #self.sliderRange.SetTitleText("height")
        self.sliderRange.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
        self.sliderRange.GetPoint1Coordinate().SetValue(0.94, 0.1)
        self.sliderRange.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
        self.sliderRange.GetPoint2Coordinate().SetValue(0.94, 0.9)
        self.sliderRange.SetSliderWidth(0.03)
        self.sliderRange.SetEndCapLength(0.03)
        self.sliderRange.SetEndCapWidth(0.03)
        self.sliderRange.SetTubeWidth(0.005)

        self.sliderWidget2 = vtk.vtkCenteredSliderWidget()
        self.sliderWidget2.SetInteractor(self.iren)
        self.sliderWidget2.SetRepresentation(self.sliderRange)
        self.sliderWidget2.EnabledOn()

        self.sliderWidget2.AddObserver("InteractionEvent", self.callbackRange)

        self.analyseMode = 0
        self.analyseList = analyze.FCT_LIST

        self.ion = interactive
        if self.ion:
            plt.ion()

    def analyse(self, method=None):
        if isinstance(method, str):
            for i, m in enumerate(self.analyseList):
                if m.__name__ == method:
                    self.analyseMode = i
                    break
        self.SatelliteResult = self.analyseList[self.analyseMode](self.SatelliteScan)
        return self.SatelliteResult

    def setRanges(self, start, stop, increment):
        super(Analysis, self).setRanges(start, stop, increment)

        self.sliderRange.SetMinimumValue(start[2])
        self.sliderRange.SetMaximumValue(stop[2])
        self.sliderRange.SetValue(start[2])
        self.rangeCurrent = start[2]

    def setSatelliteImage(self, filename="", width=1, height=1, scale=1):
        self.imageWidth  = width
        self.imageHeight = height
        self.imageScale  = scale

        try:
            self.image = plt.imread(filename)
        except:
            self.image = None

    def callbackTime(self, obj, event):
        super(Analysis, self).callbackTime(obj, event)
        self.analyse()

    def callbackRange(self, obj, event):
        self.rangeCurrent = obj.GetRepresentation().GetValue()
        try:
            pos = int((self.rangeCurrent - self.positionStart[2]) / self.positionInc)
        except:
            pos = 0

        self.plot( self.SatelliteResult[pos])

    def Keypress(self, key):
        if key == "m":
            self.analyseMode = (self.analyseMode+1) % len(self.analyseList)
            print "switch mode to", self.analyseList[self.analyseMode].__name__, "...",
            self.analyse()
            print "done"

            try:
                pos = int((self.rangeCurrent - self.positionStart[2]) / self.positionInc)
            except:
                pos = 0

            self.plot( self.SatelliteResult[pos] )

    def plot(self, matrix, title=None, vmin=None, vmax=None, frame=20, \
             satellites=True, cmap=None, filename=None, dpi=150):
        if self.ion:
            plt.clf()
        else:
            map_figure=plt.figure()
            plt.plot()

        if title == None:
            title = "%s: time %s (%d m)" %( self.analyseList[self.analyseMode].__name__,
                                            datetime.datetime.fromtimestamp(self.timeCurrent).isoformat(),
                                            self.rangeCurrent)

        if self.image != None:
            frame_x = ((self.positionStop[0] - self.positionStart[0]) / 100) * frame
            frame_y = ((self.positionStop[1] - self.positionStart[1]) / 100) * frame

            plt.xlim([self.positionStart[0]-frame_x, self.positionStop[0]+frame_x])
            plt.ylim([self.positionStart[1]-frame_y, self.positionStop[1]+frame_y])

            plt.imshow(self.image, extent=(-self.imageWidth  * self.imageScale /2.,
                                            self.imageWidth  * self.imageScale /2.,
                                           -self.imageHeight * self.imageScale /2.,
                                            self.imageHeight * self.imageScale /2.))
        else:
            plt.xlim([self.positionStart[0], self.positionStop[0]])
            plt.ylim([self.positionStart[1], self.positionStop[1]])


        if cmap == None:
            if self.analyseList[self.analyseMode].__name__[0:3] == "DOP":
                cmap = colorMap.cmapDOP
            elif self.analyseList[self.analyseMode].__name__ == "SatCount":
                cmap = colorMap.cmapSatellites

        plt.imshow(matrix, cmap=cmap,
                   alpha=0.5 if self.image != None else 1,
                   vmin=vmin if vmin != None else np.nanmin(matrix),
                   vmax=vmax if vmax != None else np.nanmax(matrix),
                   extent=(self.positionStart[0], self.positionStop[0],
                           self.positionStart[1], self.positionStop[1]))

        plt.title(title) # + ": " + datetime.datetime.fromtimestamp(self.timeCurrent).isoformat())
        plt.xlabel("    <west  east> [m]")
        plt.ylabel("     <south  north> [m]")

        if vmin == None:
            plt.colorbar()
        else:
            plt.colorbar(ticks = np.linspace(vmin, vmax-vmin, vmax-vmin+1, endpoint = True))

        if satellites:
            for _, sat in self.satellites.items():
                if sat["visible"]:
                    (x,y,_) = sat['position']
                    plt.plot([self.positionStop[0] * np.cos(np.arctan2(y,x)), x],
                             [self.positionStop[1] * np.sin(np.arctan2(y,x)), y],
                             '--r', lw=2) #, opacity=0.5)

        if self.ion:
            plt.draw()
        else:
            #plt.show()
            if filename != None:
                plt.savefig(filename, dpi=dpi)
            plt.close()

if __name__ == "__main__":

    import cPickle as pickle
    #import pickle
    from mayavi import mlab
    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option("-f", "--file", dest="file", metavar="FILE")
    parser.add_option("-i", "--image", dest="image", metavar="FILE")
    parser.add_option("--image_params", dest="image_params", type="float", nargs=3)
    parser.add_option("-t", "--time", dest="time", type="int", nargs=3)
    parser.add_option("--scanFrom", dest="scanFrom", type="float", nargs=3)
    parser.add_option("--scanTo", dest="scanTo", type="float", nargs=3)
    parser.add_option("--scanInc", dest="scanInc", type="float")
    parser.add_option("--folder", dest="folder", type="string")
    parser.add_option("--dpi", dest="dpi", type="int", default=150)
    parser.add_option("-o", "--output", dest="output", type="string")
    parser.add_option("--ops", dest="ops", metavar="FILE")
    parser.add_option("--center", dest="center", type="float", nargs=3)
    parser.add_option("--interactive", dest="interactive", action="store_true", default=False)

    (op, args) = parser.parse_args()

    gps = Analysis(op.interactive)

    gps.loadModel(op.file)
    gps.initGPS(op.ops, lat=op.center[0], lon=op.center[1], ele=op.center[2])
    gps.setRanges(op.scanFrom, op.scanTo, op.scanInc)
    gps.setTimes(*op.time)
    gps.setSatelliteImage(op.image, *op.image_params)

    if op.interactive:
        gps.start()
    else:
        # parse output formats
        outputs = []
        for out in op.output.split(","):
            out = out.split(" ")
            out = filter(lambda x: x!="" , out)
            outputs.append(out)

        for t in range(*op.time):
            raw = gps.scan(t, op.scanFrom, op.scanTo, op.scanInc)
            for method in outputs:
                if method[0] == "RAW":
                    #method.append("P")
                    #result = raw
                    pickle.dump(raw, open(op.folder+method[0]+'_'+str(t)+".p", "wb"))
                else:
                    result = gps.analyse(method[0])

                for format_ in method[1:]:
                    if format_ == "P":
                        pickle.dump(result, open(op.folder+method[0]+'_'+str(t)+".p", "wb"))

                    elif format_ == "JPG":
                        gps.plot(result[0], filename=op.folder+method[0]+'_'+str(t)+".jpg", dpi=op.dpi)

                    elif format_ == "VTK":
                        matrix = np.nan_to_num(result)
                        matrix[matrix > 25] = 25
                        vtk_matrix = mlab.pipeline.scalar_field(matrix)
                        vtk_matrix.save_output(op.folder+method[0]+'_'+str(t)+".vtk")
                        mlab.close()

                    elif format_ == "XML":
                        matrix = np.nan_to_num(result)
                        matrix[matrix > 25] = 25
                        vtk_matrix = mlab.pipeline.scalar_field(matrix)
                        vtk_matrix.save_output(op.folder+method[0]+'_'+str(t)+".xml")
                        mlab.close()
