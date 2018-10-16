# this library tries to abstract away all that annoys me when using Python to draw with FreeCAD 
# it tries to make pythong FreeCAD designing as easy as drawing things with OpenSCAD
# Written by Grey Christoforo <first name [at] last name [dot] net>

import sys
import warnings
import os

# use the previoulsy imported FreeCAD module here
if not 'FreeCAD' in sys.modules:
    raise ImportError('You must import the FreeCAD module')
else:
    FreeCAD = sys.modules['FreeCAD']
    import Part
    import Mesh
    import BOPTools
    BOPTools.importAll()
    import importSVG
    import importCSG

try:
    import importDXF
except:
    warnings.warn("Could not import the importDXF module, dxf related functions will be broken", ImportWarning)


mydoc = FreeCAD.newDocument("mydoc")

def cylinder (radius,height):
    '''Create cylinder centered at origin, height is in Z dir'''
    return Part.makeCylinder(radius,height)

def sphere(radius):
    return Part.makeSphere(radius)

def cone(r1,r2,height):
    return Part.makeCone(r1,r2,height)

# returns a rectangular face given x and y dims
def rectangle(xDim,yDim):
    return Part.makePlane(xDim,yDim)

def cube(xDim,yDim,zDim):
    '''Create cube with bottom left corner at origin'''
    return Part.makeBox(xDim,yDim,zDim)

# returns a circular face given a radius
def circle(radius):
    '''Create circle centered on origin (which plane?)'''
    circEdge = Part.makeCircle(radius)
    #circWire = Part.Wire(circEdge)
    circFace = Part.makeFilledFace([circEdge])
    return circFace

# r can accept a scalar or a list or tuple with 4 radii, drillCorners adds circles at the corners
# if r is a length 4 iterable, the edges will be rounded with radii = [northwest,northeast,southeast,southwest]
# if ear=True rounded leadins will be made on the southeast and southwest
# corners assuming that the south edge will later be connected to something and these will be a fillet to that
# then the southeast southwest radii specified will be used for those fillets
def roundedRectangle(xDim,yDim,r=None,drillCorners=False,ear=False):
    if drillCorners is False:
        drillCorners=[False,False,False,False]
    elif drillCorners is True:
        drillCorners=[True,True,True,True]
    elif type(drillCorners) is tuple:
        drillCorners = list(drillCorners)
    elif len(drillCorners) is not 4:
        print("Invalid value for drillCorners in roundedRectangle function")
        return None
    
    if r is None:
        radii=[0,0,0,0]
    elif (type(r) is float) or (type(r) is int):
        radii=[r,r,r,r]
    elif (type(r) is list) or (type(r) is tuple) and len(r) is 4:
        radii=[r[0],r[1],r[2],r[3]]
    else:
        print("Invalid value for r in roundedRectangle function")
        return None
    if (radii[0] + radii[3] > yDim) or (radii[1] + radii[2] > yDim) or (radii[0] + radii[1] > xDim) or (radii[3] + radii[2] > xDim):
        print("This rounded rectangle is impossible to draw!")
        return None
    
    p0 = FreeCAD.Vector(radii[0],yDim,0)
    p1 = FreeCAD.Vector(xDim-radii[1],yDim,0)
    p2 = FreeCAD.Vector(xDim,yDim-radii[1],0)
    p3 = FreeCAD.Vector(xDim,radii[2],0)
    p4 = FreeCAD.Vector(xDim-radii[2],0,0)
    p5 = FreeCAD.Vector(radii[3],0,0)
    p6 = FreeCAD.Vector(0,radii[3],0)
    p7 = FreeCAD.Vector(0,yDim-radii[0],0)
    
    polygonWire=Part.makePolygon([p0,p1,p2,p3,p4,p5,p6,p7],True)
    polygonFace=Part.Face(polygonWire)
    
    circles = []
    if radii[0]>0: # northwest
        c0 = circle(radii[0])
        cornerOffsetXY = radii[0]
        if drillCorners[0] is True:
            cornerOffsetXY = cornerOffsetXY*2**(0.5)/2
        c0 = translate(c0,cornerOffsetXY,yDim-cornerOffsetXY,0)
        circles.append(c0)
    if radii[1]>0: # northeast
        c1 = circle(radii[1])
        cornerOffsetXY = radii[1]
        if drillCorners[1] is True:
            cornerOffsetXY = cornerOffsetXY*2**(0.5)/2
        c1 = translate(c1,xDim-cornerOffsetXY,yDim-cornerOffsetXY,0)
        circles.append(c1)    
    if radii[2]>0: # southeast
        c2 = circle(radii[2])
        cornerOffsetXY = radii[2]
        if drillCorners[2] is True:
            cornerOffsetXY = cornerOffsetXY*2**(0.5)/2
        c2 = translate(c2,xDim-cornerOffsetXY,cornerOffsetXY,0)
        if ear is True:
            c2 = Part.makePlane(2*radii[2],radii[2])
            rounder = Part.makeCircle(radii[2], FreeCAD.Vector(2*radii[2],radii[2],0))
            rounder = Part.makeFilledFace([rounder])
            #rounder = Part.Face(rounder)
            c2 = c2.cut(rounder)
            c2.translate(FreeCAD.Vector((xDim-radii[2],0,0)))
        circles.append(c2.Faces[0])  
    if radii[3]>0: # southwest
        c3 = circle(radii[3])
        cornerOffsetXY = radii[3]
        if drillCorners[3] is True:
            cornerOffsetXY = cornerOffsetXY*2**(0.5)/2
        c3 = translate(c3,cornerOffsetXY,cornerOffsetXY,0)
        if ear is True:
            c3 = Part.makePlane(2*radii[3],radii[3])
            rounder = Part.makeCircle(radii[3], FreeCAD.Vector(0,radii[3],0))
            rounder = Part.makeFilledFace([rounder])
            #rounder = Part.Face(rounder)          
            c3 = c3.cut(rounder)
            c3.translate(FreeCAD.Vector((-radii[3],0,0)))
        circles.append(c3.Faces[0])
    
    if len(circles) > 0:
        roundedGuy = union(polygonFace, circles)
    else:
        roundedGuy = polygonFace;

    return roundedGuy

# only tested/working with solid+solid and face+face unions (with face+face only in a non-tilted plane)
def union(thingsA,thingsB,tol=1e-5):
    if type(thingsB) is not list:
        thingsB = [thingsB]
    if type(thingsA) is list:
        thingA = thingsA[0]
        if len(thingsA) > 1:
            thingsB += thingsA[1::]
    else:
        thingA = thingsA
    if (thingA.ShapeType == 'Face') and (thingsB[0].ShapeType == 'Face'):
        # face fusing is not working anymore, so we have to make them 3d then fuse, then section to get the proper fused face
        aCOM = thingA.CenterOfMass
        u, v = thingA.Surface.parameter(aCOM)
        x, y, z = thingA.normalAt(u, v)
        vNorm = thingA.normalAt(u, v)
        things3D = extrude(thingsB+[thingA], x, y, z)
        a3D = things3D[-1]
        b3D = things3D[0:-1]
        tol = 0
        pieces, map = a3D.generalFuse(b3D, tol)
        cpound = BOPTools.JoinAPI.connect(pieces.Solids, tolerance=tol)
        u3D = cpound.Solids[0].removeSplitter()
        bb = u3D.BoundBox
        dl = bb.DiagonalLength
        u3D.translate(-vNorm/2)
        u3DCOM = thingA.CenterOfMass
        cutPlane = Part.makePlane(dl, dl, aCOM, vNorm)
        cpCOM = cutPlane.CenterOfMass
        dCOM = u3DCOM - cpCOM
        cutPlane.translate(dCOM)
        sectionShape = u3D.section(cutPlane)
        u = [Part.makeFilledFace(sectionShape.Edges)]
    elif (thingA.ShapeType == 'Solid') and (thingsB[0].ShapeType == 'Solid'):
        pieces, map = thingA.generalFuse(thingsB, tol)
        cpound = BOPTools.JoinAPI.connect(pieces.Solids, tolerance=tol)
        u = cpound.Solids
    else:
        u = []
    if (len(u) is 1):
        return u[0]
    else:
        return u

# TODO: this cut is leaving breaks in circles, try to upgrade it to fuzzy logic with tolerance
# also I think remove splitter does nothing here
def difference(thingsA,thingsB):
    if type(thingsA) is not list:
        thingsA = [thingsA]
    if type(thingsB) is not list:
        thingsB = [thingsB]
    robjs=[]
    for thingA in thingsA:
        cutResult = _multiCut(thingA,thingsB)
        if type(cutResult) is list:
            robjs += cutResult
        else:
            robjs.append(cutResult)
    if (len(robjs) is 1):
        return robjs[0]
    else:
        return robjs
    
# _multiCut() subtracts a list of childObjects away from a parent object

# input objects can be faces or solids (don't even think about mixing 'em!)
# childObjects can be a list or one face/solid
# the output will be a list of faces/solids only if it needs to be
def _multiCut(parentObject,childObjects,tol=1e-5):
    if type(childObjects) is not list:
        childObjectsInternal = [childObjects]
    else:
        childObjectsInternal = list(childObjects)

    #if len(childObjectsInternal) > 1: #fuse cutting objects
        #childFuse = childObjectsInternal[0].multiFuse(childObjectsInternal[1::],tol).removeSplitter()
        #if len(childFuse.Solids) > 0:
            #childObjectsInternal = childFuse.Solids
        #else:
            #childObjectsInternal = childFuse.Faces

    cuttingTools = childObjectsInternal # we'll call our child objects cutting tools
    workpieces = [parentObject]
    while len(cuttingTools) is not 0: # let's cut away until our tools run out
        nPieces = len(workpieces)
        for i in range(nPieces):
            cutResult = workpieces[i].cut(cuttingTools[0], tol)
            
            try:
                cutResult.removeSplitter() # removeSplitter if possible
            except:
                pass
                
            if len(cutResult.Solids) > 0:
                cutResult = cutResult.Solids # there's a solid in our results, so we'll assume to be operating on those
            else:
                cutResult = cutResult.Faces # no solids, so we must be operating on faces
                
            # let's inspect the result of our cut. there are three options:
            if len(cutResult) is 0: # the cut has eliminated the workpiece
                workpieces[i] = [] # mark this workpiece for removal
            elif len(cutResult) > 1: # the workpiece has been segmented into two or more pieces by the cut
                workpieces[i] = [] # mark this workpiece for removal, it was split up
                workpieces += cutResult # add the new split pieces to our list of things to be cut
            else: # the piece being cut was not split and not consumed by the cut
                workpieces[i] = cutResult[0]
                
        # we've finished cutting all the workpieces; throw away the current cutting tool
        del cuttingTools[0] 
        
        # before we move onto the next cutting tool, delete all the extraneous workpieces
        workpieces = [x for x in workpieces if x != []]
    if len(workpieces) is 1:
        return workpieces[0]
    else:
        return workpieces

def save2DXF (things, outputFilename):
    """sends a projection of an object's edges onto the z=0 plane to a dxf file (in a layer named "0")
    """
    if type(things) is not list:
        things = [things]
    outList = []
    tmpParts = []
    for thing in things:
        tmpPart = mydoc.addObject("Part::Feature")
        tmpParts.append(tmpPart)
        tmpParts[-1].Shape = thing
    importDXF.export(tmpParts, outputFilename)
    
    for obj in mydoc.Objects:
        mydoc.removeObject(obj.Name)
    return

def save2SVG (things, outputFilename):
    """exports things to svg file
    """
    if type(things) is not list:
        things = [things]
    outList = []
    tmpParts = []
    for thing in things:
        tmpPart = mydoc.addObject("Part::Feature")
        tmpParts.append(tmpPart)
        tmpParts[-1].Shape = thing
    importSVG.export(tmpParts, outputFilename)
    
    for obj in mydoc.Objects:
        mydoc.removeObject(obj.Name)
    return

def save2FCStd (toSave, outputFullPath):
    """saves shapes to freecad document file"""
    if type(toSave) is not list:
        toSave = [toSave]
    else:
        toSave = list(toSave)
    parts = []
    for num, shape in enumerate(toSave):
        parts.append(mydoc.addObject("Part::Feature"))
        parts[num].Shape = shape
    mydoc.saveAs(outputFullPath)
    for obj in mydoc.Objects:
        mydoc.removeObject(obj.Name)
    return

# reads a dxf file
# returns a dict with where the keys are the layer names and the values are lists of shapes in that layer
def loadDXF (DXFFilename):
    # this adds some number of objects to mydoc (three maybe?)
    # the one we're interested in has the name
    importDXF.insert(DXFFilename,mydoc.Name)
    group = mydoc.getObject(os.path.splitext(os.path.split(DXFFilename)[1])[0])
    if group is None:
        group = mydoc.getObject('_d')

    #partFeature = mydoc.getObject("Block_PART__FEATURE")
    nLayers = len(group.OutList)
    retDict = {}
    for i in range(nLayers):
        layerName = str(group.OutList[i].Label)
        layerShapes = []
        nShapesInThisLayer = len(group.OutList[i].Group)
        for j in range (nShapesInThisLayer):
            layerShapes.append(group.OutList[i].Group[j].Shape)
        retDict[layerName] = layerShapes
        
    # clean it all up
    for obj in mydoc.Objects:
        mydoc.removeObject(obj.Name)
    return retDict

# reads an openSCAD file
# returns a dict with where the keys are the layer names and the values are lists of shapes in that layer
def loadCSG (openSCADFilename):
    # this adds some number of objects to mydoc
    importCSG.insert(openSCADFilename, mydoc.Name)
    stuff = mydoc.Objects
    
    # assume for now we only want the top level object (the last one)
    someShapes = [stuff[-1].Shape]

    # someShapes = []
    # for thing in stuff:
    #    if thing.Shape:
    #        someShapes.append(thing.Shape)

    # clean it all up
    for obj in mydoc.Objects:
        mydoc.removeObject(obj.Name)
    return someShapes

# sends a solid object to a step file
def solid2STEP (solids,outputFilenames):
    if type(solids) is not list:
        solids=[solids]
    if type(outputFilenames) is not list: # all the solids go into one file
        tmpParts = []
        for i in range(len(solids)):
            tmpParts.append(mydoc.addObject("Part::Feature"))
            tmpParts[i].Shape = solids[i]
        Part.export(tmpParts,outputFilenames)
    else: # list of filenames
        for i in range(len(solids)):
            solids[i].exportStep(outputFilenames[i])
    for obj in mydoc.Objects:
        mydoc.removeObject(obj.Name)    
    return

# sends a solid object(or list of objects) to a stl file(s)
def solid2STL (solids,outputFilenames,meshTol=0.01):
    if type(solids) is not list:
        solids=[solids]
        outputFilenames=[outputFilenames]
    for i in range(len(solids)):
        mesh = Mesh.Mesh(solids[i].tessellate(meshTol))
        mesh.write(outputFilenames[i],"STL")
    return

# loads a file(or a list of filenames) (probably handles things other than just STEP) and returns a solid shape
def STEP2Solid(stepFilenames):
    if type(stepFilenames) is not list:
        listIn = False
        stepFilenames=[stepFilenames]
    else:
        listIn=True
    robjs=[]
    for stepFilename in stepFilenames:
        robjs.append(Part.read(stepFilename))
    if (len(robjs) is 1) and (listIn is False):
        return robjs[0]
    else:
        return robjs

# extrudes a face (or list of faces) to make a 3d solid
def extrude (objs,x,y,z):
    if type(objs) is not list:
        listIn=False
        objs=[objs]
    else:
        listIn=True
    robjs=[]
    for obj in objs:
        robjs.append(obj.extrude(FreeCAD.Vector((x,y,z))))
    if (len(robjs) is 1) and (listIn is False):
        return robjs[0]
    else:
        return robjs

# mirrors an object (or a list of objects) across a plane defined by a point and a vector
def mirror(objs,x,y,z,dirx,diry,dirz):
    if type(objs) is not list:
        listIn=False
        objs=[objs]
    else:
        listIn=True
    robjs=[]
    for obj in objs:
        robjs.append(obj.mirror(FreeCAD.Vector(x,y,z),FreeCAD.Vector(dirx,diry,dirz)))
    if (len(robjs) is 1) and (listIn is False):
        return robjs[0]
    else:
        return robjs

# makes a circular array of objects around a point [px,py,pz]
# in a plane perpindicular to [dx,dy,dz]
def circArray(obj,n,px,py,pz,dx,dy,dz,fillAngle=360,startAngle=0):
    dTheta=fillAngle/n
    obj0 = obj.copy()
    if startAngle is not 0:
        obj0.rotate(FreeCAD.Vector(px,py,pz),FreeCAD.Vector(dx,dy,dz),dTheta-startAngle)
    objects=[obj0]
    for i in range (1,n):
        newObj= obj.copy()
        newObj.rotate(FreeCAD.Vector(px,py,pz),FreeCAD.Vector(dx,dy,dz),i*dTheta+startAngle)
        objects.append(newObj)
    return objects

# moves an object or a list of objects
def translate (objs,x,y,z):
    '''superflous as part has a translate(self, tuple/vect) method'''
    if type(objs) is not list:
        listIn=False
        objs=[objs]
    else:
        listIn=True
    robjs=[]
    for obj in objs:
        robj=obj.copy()
        robj.translate(FreeCAD.Vector((x,y,z)))
        robjs.append(robj)
    if (len(robjs) is 1) and (listIn is False):
        return robjs[0]
    else:
        return robjs
    
# rotate (an) object(s) around a point: [px,py,pz]
# xDeg, yDeg and zDeg degreees about those axes
def rotate(objs,xDeg,yDeg,zDeg,px=0,py=0,pz=0):
    if type(objs) is not list:
        listIn=False
        objs=[objs]
    else:
        listIn=True
    robjs=[]
    for obj in objs:
        robj = obj.copy()
        robj.rotate(FreeCAD.Vector(px,py,pz),FreeCAD.Vector(1,0,0),xDeg)
        robj.rotate(FreeCAD.Vector(px,py,pz),FreeCAD.Vector(0,1,0),yDeg)
        robj.rotate(FreeCAD.Vector(px,py,pz),FreeCAD.Vector(0,0,1),zDeg)
        robjs.append(robj)
    if (len(robjs) is 1) and (listIn is False):
        return robjs[0]
    else:
        return robjs

# given a solid and a z value, returns a list of wires
#  slices only in the X-Y plane
def section (solid, height="halfWay"):
    if type(solid) is not list:
        solids=[solid]
    else:
        solids = solid
    
    ret = []
    
    #  determine the cutting plane
    if height == "halfWay":
        comp = Part.makeCompound(solids)
        bb = comp.BoundBox
        zPos = bb.ZLength/2.0 + bb.ZMin
    else:
        zPos = height
    
    for s in solids:
        for wire in s.slice(FreeCAD.Vector(0,0,1), zPos):
            ret.append(wire)
    # sectionShape = solid.section(slicePlane)

    return ret

def text (string, fontFile='/usr/share/fonts/TTF/FreeMono.ttf', height=100, returnWires = False):
    """returns a list of faces corresponding to each character in a string that trace text letters
    maybe the default fontdir and font variables have only been tested in Arch Linux"""
    wires = Part.makeWireString(string, fontFile, height)
    if returnWires:
        # flat_wires = []
        # for letter in wires:
        #    for wire in letter:
        #        flat_wires.append(wire)
            
        flat_wires = [item for sublist in wires for item in sublist]
        return flat_wires
    else:
        faces = []
        for letter in wires:
            faces.append(Part.Face(letter))
    
        return faces
