# -*- coding: utf-8 -*-
from hec.script import ResSim
from hec.script import Constants
import os

simName = "1986_260"
altName = "HC_ALL"
watershedWkspFile = r"C:\workspace\git_clones\folsom-hindcast-processing\jythonResSim\model\J6R7HW_SOU_Hindcast\J6R7HW_SOU_Hindcast.wksp"
assert os.path.isfile(watershedWkspFile), 'watershed file does exist'

#  Res Sim only likes unix-style path
watershedWkspFile = watershedWkspFile.replace(os.sep, "/")


watershedDir = r"C:\workspace\git_clones\folsom-hindcast-processing\jythonResSim\model\J6R7HW_SOU_Hindcast"

# # open the watershed
ResSim.openWatershed(watershedWkspFile)
print '#===================================================='
print 'ResSim Watershed Name:', ResSim.getWatershedName()
print '#===================================================='
if ResSim.getWatershedName() != 'J6R7HW_SOU_Hindcast' :
    raise Exception("Unable to open watershed %s" % watershedWkspFile)
ResSim.selectModule('Simulation')


simMode = ResSim.getCurrentModule()
simMode.resetWorkspace()  #<<<<---------------  WHAT WE NEEDED!!!
print '#===================================================='
print type(simMode)
print simMode.getName()
print '#===================================================='
simMode.openSimulation(simName)
simulation = simMode.getSimulation()
simulation.setComputeAll(1)
print '#===================================================='
print type(simulation)
print '#===================================================='

simRun = simulation.getSimulationRun(altName)
print '#===================================================='
print simRun.getName()
print type(simRun)
print '#===================================================='

simMode.computeRun(simRun, -1, Constants.TRUE, Constants.TRUE)
ResSim.getCurrentModule().saveSimulation()
ResSim.closeWatershed()