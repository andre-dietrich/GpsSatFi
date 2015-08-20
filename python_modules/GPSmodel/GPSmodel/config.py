import ConfigParser
from optparse import OptionParser


class Configuration():
    def __init__(self, filename=[]):
        if not filename:
            parser = OptionParser()
            parser.add_option("-i", "--inifile", dest="inifile",
                              metavar="FILE")
            (op, args) = parser.parse_args()
            filename = op.inifile
        self.Config = ConfigParser.ConfigParser()
        print "---------------------------------------------"
        print ("Reading from file %s" % filename)
        self.Config.read(filename)
        self.defaultParam = {}
        if self.ConfigSectionMap():
            print 'All parameters read - parameterfile valid'
        print "---------------------------------------------"


    def ConfigSectionMap(self, section='GpsSatFi'):
        sections = self.Config.sections()
        if section in sections:
            parameters_req = {'mode': 'string',
                              'ops': 'string',
                              'center': 'float',
                              'file': 'string',
                              'image': 'string',
                              'image_params': 'float',
                              'dpi': 'int',
                              'scanInc': 'int',
                              'scanFrom': 'float',
                              'scanTo': 'float',
                              'time': 'int'}
            valid = 1
            for option_req in parameters_req:
                try:
                    self.defaultParam[option_req] = self.Config.get(section,
                                                                    option_req)
                except:
                    print("Parameter '%s' not found in ini file!" % option_req)
                    valid = -1
        else:
            valid = -1
        for option in self.defaultParam:
            output = "%s" % self.defaultParam[option]
            if parameters_req[option] == 'int':
                aux = [int(i) for i in self.defaultParam[option].split(',')]
                self.defaultParam[option] = aux
            elif parameters_req[option] == 'float':
                aux = [float(i) for i in self.defaultParam[option].split(',')]
                self.defaultParam[option] = aux
            if len(self.defaultParam[option]) == 1:
                self.defaultParam[option] = self.defaultParam[option][0]
            print ("%10s : %s" % (option, output))
        return valid

    #def calcSatPositions(self, )

if __name__ == "__main__":
    myConfig = Configuration()
    print myConfig
