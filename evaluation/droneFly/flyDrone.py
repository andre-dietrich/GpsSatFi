## Reads one GPS prediction map, generates a volume and flys along a defined path
#
# Generate the movie by executing
# mencoder mf://*.jpeg -mf w=800:h=600:fps=25:type=jpeg -ovc lavc \-lavcopts vcodec=mpeg4:mbd=2:trell -oac copy -o output.avi

from mayavi import mlab
import numpy as np
import mayavi.sources.vtk_xml_file_reader

filename = "./gps-data/DOPP_1440504060.xml"

start_distance = 450
start_focalpoint = np.array([150/2, 150/2, 0])
start_elevation = 10
start_azimuth = 0
current={}

#movements determines changing camera perspectives between two phases
movements=[]
movements.append({'elevation': 35, 'focal_point': [0, 0, 100]})
movements.append({'azimuth': 90})
movements.append({'distance': 250})

def generatePoints(displacement, current, steps):
  delta={}
  keys = ['distance', 'elevation', 'focal_point', 'azimuth']
  for key in keys:
    if displacement.has_key(key):
      if 'focal_point' == key:
        if not delta.has_key('focal_point'):
          focal_dist=np.ones([3, steps], dtype=np.float64)
          focal_dist[0]=focal_dist[0]*current['focal_point'][0]
          focal_dist[1]=focal_dist[1]*current['focal_point'][1]
          focal_dist[2]=focal_dist[2]*current['focal_point'][2]
          delta['focal_point']=focal_dist
        for i in range(0,3):
          if displacement['focal_point'][i] != 0:
            resolution = (displacement['focal_point'][i] - current[key][i])/float(steps)
            focal_dist[i] = np.arange(current[key][i], displacement[key][i], resolution)
      else:
        resolution = (displacement[key] - current[key])/float(steps)
        delta[key] = np.arange(current[key], displacement[key], resolution)
    else:
      if 'focal_point' == key:
        focal_dist=np.ones([3, steps], dtype=np.float64)
        focal_dist[0]=focal_dist[0]*current['focal_point'][0]
        focal_dist[1]=focal_dist[1]*current['focal_point'][1]
        focal_dist[2]=focal_dist[2]*current['focal_point'][2]
        delta['focal_point']=focal_dist
      else:
        delta[key] = np.ones(steps) * current[key]
  return delta

fig_myv = mlab.figure(size=(640,480))
engine = mlab.get_engine()

streets = mayavi.sources.vtk_xml_file_reader.VTKXMLFileReader()
streets.initialize(filename)
print 'Model loaded'

volume_rotation = [0, -90, 0]
volume_translation = [150,0,0]

volume = mlab.pipeline.volume(streets)
volume.name = 'Volume'
volume.volume.orientation=volume_rotation
volume.volume.position = volume_translation
volume.visible = True

fig_myv.scene.disable_render = True # Super duper trick
text_filename = mlab.text(0.1, 0.1, 'filename')
text_parameter = mlab.text(0.1, 0.15, 'focal_point', width=0.25)
text_trajectorylenght = mlab.text(0.8, 0.85, 'distance', width = 0.13)
fig_myv.scene.disable_render = False # Super duper trick
print '3D environment initialised'

current['distance'] = start_distance
current['focal_point'] = start_focalpoint
current['elevation'] = start_elevation
current['azimuth'] = start_azimuth
print 'Camera initialised'

index = 0
steps = 150
traveled_distance = 0

for k in range(0, len(movements)):
  delta=generatePoints(movements[k], current, steps)
  print '-----------------------------------------------'
  print 'movement phase '+ str(k)
  for i in range (0, steps):
    print 'Phase ' + str(k) + ' - Step ' + str(i) + ' from ' + str(steps)

    current['distance'] = delta['distance'][i]
    current['focal_point'] = delta['focal_point'][:,i]
    current['elevation'] = delta['elevation'][i]
    current['azimuth'] = delta['azimuth'][i]

    mlab.view(azimuth = delta['azimuth'][i], elevation=delta['elevation'][i],
	    distance = delta['distance'][i], focalpoint = delta['focal_point'][:,i])

    text_filename.actor.input = filename
    text_parameter.actor.input = 'I' + '%4d'%(delta['focal_point'][0,i]) + \
				 '%4d'%(delta['focal_point'][1,i]) + \
                                 '%4d'%(delta['focal_point'][2,i]) + 'I' + \
				 '%4d'%(delta['distance'][i]) + \
                                 '%4d'%(delta['azimuth'][i]) + \
                                 '%4d'%(delta['elevation'][i])

    cam,foc = mlab.move()
    new_pose = cam+foc-start_focalpoint
    if traveled_distance != 0:
      traveled_distance = traveled_distance + np.linalg.norm(new_pose - old_pose)
      text_trajectorylenght.actor.input =  'Dist = %4.1f'%(traveled_distance) +'m'
    else:
      traveled_distance = 0.01
    old_pose=new_pose

    print cam+foc
    mlab.draw()
    mlab.savefig('./figures/'+'%03d'%(index)+'.jpeg')
    index = index + 1

print 'Aus Maus'