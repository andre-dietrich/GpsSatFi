import os
from mayavi import mlab
import numpy as np
import mayavi.sources.vtk_xml_file_reader

data_folder = "./gps-data/"
data_folder = "../../data/manhattan/gps-data/"

start = {}
start['distance'] = 350
start['focalpoint'] = np.array([150/2, 150/2, 50])
start['elevation'] = 75
start['azimuth'] = 45

filelist = []
for file in os.listdir(data_folder):
    if file.endswith(".xml"):
        filelist.append(file)
print str(len(filelist)) + ' DOP-maps found'

# Determine time interval
filelist.sort()
aux = filelist[0].replace('.', '_')
_, timestamp_0, _ = aux.split('_')
aux = filelist[1].replace('.', '_')
_, timestamp_1, _ = aux.split('_')
print 'Time interval ' + str(int(timestamp_1)-int(timestamp_0)) + ' Seconds'

for data_file in filelist:
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

    mlab.view(azimuth = start['azimuth'], elevation=start['elevation'],
           distance = start['distance'], focalpoint = start['focalpoint'])

    text_filename = mlab.text(0.1, 0.1, filename,  width=0.45)

    mlab.draw()
    aux = filelist[0].replace('.', '_')
    _, timestamp, _ = aux.split('_')
    mlab.savefig('./figures/'+str(timestamp)+'.jpeg')
    mlab.close()