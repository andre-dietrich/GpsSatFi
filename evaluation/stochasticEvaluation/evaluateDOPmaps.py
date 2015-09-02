import os
from mayavi import mlab
import numpy as np
import mayavi.sources.vtk_xml_file_reader
import pickle

data_folder = "./gps-data/"
data_file = "DOPP_1440504060.xml"

fig_myv = mlab.figure(size=(640,480))
engine = mlab.get_engine()

streets = mayavi.sources.vtk_xml_file_reader.VTKXMLFileReader()
filename = data_folder+data_file
print filename
streets.initialize(filename)
print 'Model loaded'

volume_rotation = [0, -90, 0]
volume_translation = [150,0,0]
volume = mlab.pipeline.volume(streets)
volume.name = 'Volume'
volume.volume.orientation=volume_rotation
volume.volume.position = volume_translation
volume.visible = True

results = []
for DOP in range(2,25):
    print DOP
    dop = mlab.pipeline.iso_surface(streets)
    dop.contour.contours[0:1] = [DOP]
    dop.actor.mapper.scalar_visibility = False
    dop.contour.auto_contours = False
    dop.actor.property.opacity = 0.5
    dop.actor.property.ambient_color = (0.0, 0.0, 1.0)
    dop.actor.property.specular_color = (0.0, 0.0, 1.0)
    dop.actor.property.diffuse_color = (0.0, 0.0, 1.0)
    dop.actor.actor.orientation=volume_rotation
    dop.actor.actor.position = volume_translation

    DOParray = dop.contour.outputs[0].points.to_array()
    print DOParray
    print DOParray[:,0]
    results.append(DOParray[:,0])

pickle.dump( results, open( "results.p", "wb" ) )
print 'Aus Maus'