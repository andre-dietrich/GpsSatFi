import ode 

def loadObj(filename)
    triangles = []
    vertices  = []
    
    modelFile = open(filename, "r")
    for line in modelFile.readlines():
        line = line.strip()
        if len(line)==0 or line.startswith("#"):
            continue
        data = line.split(" ")
        if data[0]=="v":
            vertices.append((float(data[1]),float(data[2]),float(data[3])))
        if data[0]=="f":
            vertex1 = vertices[int(data[1].split("/")[0])-1]
            vertex2 = vertices[int(data[2].split("/")[0])-1]
            vertex3 = vertices[int(data[3].split("/")[0])-1]
            triangles.append((vertex1,vertex2,vertex3))
    
    data = ode.TriMeshData()
    data.build(vertices, triangles)
    
    return data
    