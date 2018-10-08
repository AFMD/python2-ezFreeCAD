#!/usr/bin/env python2

from __future__ import division

import sys
sys.path.append('/usr/lib/freecad/lib') # path to your FreeCAD.so or FreeCAD.dll file
sys.path.append('/usr/lib/freecad') # path to your FreeCAD.so or FreeCAD.dll file
import FreeCAD

import warnings
import ezFreeCAD as ezfc

myCone = ezfc.cone(10, 0, 30)
mySphere = ezfc.sphere(10)
mySphere = ezfc.translate(mySphere,0,0,25)
pawn = ezfc.union(myCone,mySphere)
pawn = ezfc.rotate(pawn,-90,0,0)
myCircle = ezfc.circle(25)
myDisc = ezfc.extrude(myCircle,0,0,-15)
#myDisc = rotate(myDisc,-90,0,0)
myDisc = ezfc.translate(myDisc,0,25,3)

osThingy = ezfc.difference(myDisc, pawn)
background = ezfc.roundedRectangle(50, 50,r=(2,5,7,9),drillCorners=(False,True,True,True),ear=True)
background = ezfc.extrude(background, 0, 0, -5)
background = ezfc.translate(background, -25, 0, -15+3+2)
osThingy = ezfc.union(osThingy, background)
osThingy2 = osThingy
osThingy2 = ezfc.translate(osThingy2, 70, 0, 0)
osThingys = [osThingy,osThingy2]
osThingys = ezfc.translate(osThingys, 0, 10, 0)

drillCylinder = ezfc.cylinder(5/2, 300)
drillCylinder = ezfc.rotate(drillCylinder, 0, 90, 0)
drillCylinder = ezfc.translate(drillCylinder, -300/2, 50/2, -5)
drillCylinder2 = ezfc.translate(drillCylinder, 0, 20, 0)
drillCylinders = [drillCylinder, drillCylinder2]

osThingys = ezfc.difference(osThingys, drillCylinders)

thingySlice = ezfc.section(osThingys[0])
try:
    ezfc.save2DXF(thingySlice, "osThingySlice.dxf")
    sliceReadBack = ezfc.loadDXF("osThingySlice.dxf") # this writes to a layer named "0"
    ezfc.solid2STEP(sliceReadBack["0"], "sliceWriteout.step")
except:
    warnings.warn("DXF read/write is not working")

ezfc.solid2STEP(osThingys[0], "osThingy.step")
ezfc.solid2STEP(osThingys[1], "osThingy2.step")

osThingy3 = ezfc.STEP2Solid("osThingy.step")

osThingys = ezfc.circArray(osThingy, 3, 0, -50, 0, 0, 0, 1)

ezfc.solid2STEP(osThingys[0], "osThingyA.step")
ezfc.solid2STEP(osThingys[1], "osThingyB.step")
ezfc.solid2STEP(osThingys[2], "osThingyC.step")

# multicut test:

parent= ezfc.rectangle(10,10)
child1 = ezfc.translate(ezfc.rectangle(1,10),1,0,0)
child2 = ezfc.translate(ezfc.rectangle(1,10),4,0,0)
child3 = ezfc.translate(ezfc.rectangle(10,1),0,5,0)
result = ezfc.difference(parent, [child1,child2,child3])

print "Done"
