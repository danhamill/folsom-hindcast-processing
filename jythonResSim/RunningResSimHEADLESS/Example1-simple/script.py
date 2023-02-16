# name=test
# description=test
# displaytouser=true
from hec.script import *
from hec.script import ClientAppWrapper
from hec.script import ResSim
from hec.script import Constants
# from hec.hecmath import Constants
from hec.hecmath import *
from hec.client import ClientApp
from hec.heclib.util import HecTime
from java.lang import String
import jarray
import shutil

simName = "1986_260"
altName = "HC86_260"
watershedWkspFile = r"E:\J6R7HeadWater_SOU_Hindcast_Unreg_woDiversions_2022.08.26\J6R7HeadWater_SOU_Hindcast\J6R7HW_SOU_Hindcast.wksp"
watershedDir = r"E:\J6R7HeadWater_SOU_Hindcast_Unreg_woDiversions_2022.08.26\J6R7HeadWater_SOU_Hindcast"
# lookBackTime =  "29JUN2009,12:00"
# forecastTime = "30JUN2009,12:00"
# endTime = "05JUL2009,12:00"
overridesDir = "null"

#pad the alternative name with dashes to 10 characters
altNamePadded = altName
altNamePadded = altNamePadded.replace(' ', '$')
altNamePadded = altNamePadded.ljust(10)
altNamePadded = altNamePadded.replace(' ', '-')
altNamePadded = altNamePadded.replace('$', ' ')

# open the watershed
ResSim.openWatershed(watershedWkspFile)
# to set the main application window visible
# ClientApp.frame().setVisible(1)
# select the simulation module
ResSim.selectModule("Simulation")
# get the simulation module
simModule = ResSim.getCurrentModule()
#if the simulation exists, delete it. does not remove its directory
#if os.path.exists(watershedDir + "/rss/" + simName):
# if simModule.simulationExists(simName):
# 	simModule.deleteSimulation(simName)

alts = jarray.array([altNamePadded], String)
#create the simulation 1 hour time step
# simulation = simModule.createSimulation(simName,"test simulation", lookBackTime, forecastTime, endTime, 1, HecTime.HOUR_INCREMENT, alts)
#moves the overrides files into the new simulation
# overrideName = altNamePadded + "0.dss"
# if os.path.exists(overridesDir + "/" + overrideName):
# 	shutil.copy(overridesDir + "/" + overrideName, watershedDir + "/rss/" + simName+ "/rss/" + overrideName)

simRun = simModule.getSimulationRun(altName)
simModule.computeRun(simRun, -1, Constants.TRUE, Constants.TRUE)
#save the workspace
ClientApp.Workspace().saveWorkspace()

ClientApp.frame().exitApplication()