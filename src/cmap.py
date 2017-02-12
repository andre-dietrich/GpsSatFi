import matplotlib as mpl
from numpy import linspace, random

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

    bit_rgb = linspace(0, 1, 256)
    if position == None:
        position = linspace(0, 1, len(colors))
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

    cmap = mpl.colors.LinearSegmentedColormap('my_colormap', cdict, 256)
    return cmap

def make_scattered_cmap(length):
    return [(random.randint(255), random.randint(255), random.randint(255))
            for _ in range(length)]

cmapSatellites = make_cmap([(0, 34, 102), # 0
                            (24, 116, 205), # 1
                            (28, 134, 238), # 2
                            (205, 12, 192), # 3
                            (255, 20, 147),
                            (255, 0, 0),
                            (204, 200, 51),
                            (255, 255, 155),
                            (200, 255, 133),
                            (0, 255, 0),
                            (0, 200, 0),
                            (0, 140, 0),
                            (0, 130, 0)], bit=True)

cmapDOP = make_cmap([(0, 155, 0), # 1
                     (0, 255, 0), # 2
                     (255, 255, 100), (255, 255, 150), (255, 127, 0), # 4
                     (215, 0, 0), (225, 0, 0), (235, 0, 0), (245, 0, 0), (255, 0, 0), # 9
                     (255, 20, 147), (255, 20, 147), (255, 20, 147), (255, 20, 147), (255, 20, 147), (255, 20, 147), (255, 20, 147), (255,20,147), (255,20,147), (255,20,147), (255,20,147),
                     (28, 134, 238), (28, 134, 238), (24, 116, 205), (24, 116, 205), (24, 116, 205), (0, 34, 102)], bit=True)
