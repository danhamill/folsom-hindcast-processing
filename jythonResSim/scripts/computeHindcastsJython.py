from hec.script import ResSim
from hec.script import Constants
from hec.heclib.dss import HecDss
from hec.io import TimeSeriesContainer
from hec.heclib.util import HecTime
from hec.heclib.dss import HecDSSFileDataManager
import json
import os
import sys

SITES = sites = {
    'FOLC1L': 'FLOW-LOC',
    'FOLC1F': 'FLOW-NAT',
    'NFDC1': 'FLOW-IN',
    'FMDC1': 'FLOW-IN',
    'HLLC1F': 'FLOW-NAT',
    'RBBC1F': 'FLOW-NAT',
    'HLLC1L': 'FLOW-LOC',
    'UNVC1F': 'FLOW-NAT',
    'LNLC1F': 'FLOW-NAT',
    'RRGC1F': 'FLOW-NAT',
    'ICHC1F': 'FLOW-NAT',
    'SVCC1L': 'FLOW-LOC',
    'MFAC1L': 'FLOW-LOC',
    'MFPC1L': 'FLOW-LOC',
    'DUMMY': 'FLOW',
    'RRGC1L': 'FLOW-LOC',
    'RUFC1L': 'FLOW-LOC',
    'AKYC1': 'FLOW-IN',
    'CBAC1L': 'FLOW-LOC',
    'NMFC1': 'FLOW-IN',
    'MFAC1F': 'FLOW-NAT',
    'CBAC1F': 'FLOW-NAT',
    'MFPC1F': 'FLOW-NAT',
    'RUFC1F': 'FLOW-NAT',
    'SPYC1':'FLOW'
}

def preProcessHindcastForSimulation(inputDssFile, oldPathNames, simulationDssFile):
    """
    Function to reformate DSS paths and write to a simulation file that will be used
    in a headless HEC-ResSim ensemble compute.
    :param inputDssFile: string
    :param oldPathNames: List[String] dss file paths
    :param simulationDssFile: Sting
    :return: newPathNames: List[String]
    """
    newPathNames = []
    for oldPathName in oldPathNames:
        parts = oldPathName.split('/')
        parts[1] = ''
        parts[6] = parts[6].split('|')[0] + '|'
        newPathName = '/'.join(parts)
        newPathNames.append(newPathName)

    for i, newPathName in enumerate(newPathNames):
        oldPathName = oldPathNames[i]

        inDss = HecDss.open(inputDssFile)
        ts = inDss.get(oldPathName)
        inDss.done()
        newTs = TimeSeriesContainer()
        newTs.version = newPathName.split('/')[-2]
        newTs.fullName = newPathName
        newTs.timeGranularitySeconds = 60
        newTs.type = 'INST-VAL'
        newTs.units = 'cfs'
        newTs.interval = 1
        newTs.numberValues = ts.numberValues
        newTs.times = ts.times
        newTs.values = ts.values
        newTs.startTime = ts.startTime
        outDss = HecDss.open(simulationDssFile, 6)
        outDss.put(newTs)
        outDss.done()

    return newPathNames

def postPorcessHindcastSimulation(startDate, simulationDssFile, folsomInflowPathname, forecastDate, scaling, resultsDssFile):

    for inflowPath in folsomInflowPathname:

        fid = HecDss.open(simulationDssFile)
        ts = fid.get(inflowPath)
        fid.done()
        start = HecTime(startDate)
        parts = inflowPath.split('/')
        parts[1] = scaling
        parts[6] = parts[6].split('|')[0] +'|%s' %(forecastDate)
        newPathName = '/'.join(parts)

        newTs = TimeSeriesContainer()
        newTs.version = newPathName.split('/')[-2]
        newTs.fullName = newPathName
        newTs.timeGranularitySeconds = 60
        newTs.type = 'INST-VAL'
        newTs.units = 'cfs'
        newTs.interval = 60
        newTs.numberValues = ts.numberValues

        times = []
        flows = ts.values
        for value in flows:
            times.append(start.value())
            start.add(60)

        newTs.times = times
        newTs.values = flows

        results = HecDss.open(resultsDssFile)
        results.put(newTs)


def buildInputPathnames(pattern, scaling, forecastDate):
    pathNames = []
    for bpart, cpart in SITES.items():
        for dpart in ['01DEC2999','01JAN3000']:
            for year in range(1980,2021):
                pathName = "/%s/%s/%s/%s/1HOUR/C:00%s|%s/" % (scaling, bpart, cpart, dpart, year, forecastDate)
                pathNames.append(pathName)
    pathNames = sorted(pathNames)

    return pathNames

def configureResSim(watershedWkspFile, simName, altName):

    #  Res Sim only likes unix-style path
    watershedWkspFile = watershedWkspFile.replace(os.sep, "/")
    ResSim.openWatershed(watershedWkspFile)
    ResSim.selectModule('Simulation')
    simMode = ResSim.getCurrentModule()
    simMode.resetWorkspace()
    simMode.openSimulation(simName)
    simulation = simMode.getSimulation()
    simulation.setComputeAll(1)
    simRun = simulation.getSimulationRun(altName)
    return simMode, simRun

def main(folsomInflowPathname, simulationDssFile, lookup, dataDir, watershedWkspFile, simName, altName ):
    
    simMode, simRun = configureResSim(watershedWkspFile, simName, altName)
    
    for pattern in lookup.keys():
        scalings = lookup[pattern]
        resultsDssFile = r'%s/%s_results.dss' %(dataDir, pattern)
        if not os.path.exists(resultsDssFile):
            fid = HecDss.open(resultsDssFile, 6)
            fid.done()
        for scaling in scalings.keys():
            forecastDates = scalings[scaling]
            i = 0
            for forecastDate in forecastDates.keys():
                startDate = forecastDates[forecastDate]['startDate']
                pathNames = buildInputPathnames(pattern, scaling, forecastDate)
                inputDssFile = r'%s/%s/%s_%s.dss' % (dataDir, pattern, pattern,scaling)
                assert os.path.exists(inputDssFile)

                # Run Extract on data
                newPathNames = preProcessHindcastForSimulation(inputDssFile, pathNames, simulationDssFile)
                
                simMode.computeRun(simRun, -1, Constants.TRUE, Constants.TRUE)
                ResSim.getCurrentModule().saveSimulation()
                
                # Post Process Results
                postPorcessHindcastSimulation(startDate, simulationDssFile, folsomInflowPathname, forecastDate, scaling, resultsDssFile)
                
                i += 1
                if i == 2:
                    HecDSSFileDataManager().closeAllFiles()
                    ResSim.closeWatershed()
                    sys.exit("Finished Compute.....")
                else: 
                    HecDSSFileDataManager().closeAllFiles()
                    os.remove(simulationDssFile)
                    

if __name__ == '__main__':

    # This should come from the resSim simulations,
    folsomInflowPathnames = ['//FOLSOM/FLOW-IN/%s/1HOUR/C:00%s|HC_ALL----0/' % (dpart,ensembleYear) 
                             for ensembleYear in range(1980,2021) 
                             for dpart in  ['01DEC2999','01JAN3000']]
    
    #This should be what the resSim alternative is looking to read from
    simulationDssFile = r'C:\workspace\git_clones\folsom-hindcast-processing\jythonResSim\model\J6R7HW_SOU_Hindcast\rss\1986_260\simulation.dss'
    watershedWkspFile = r"C:\workspace\git_clones\folsom-hindcast-processing\jythonResSim\model\J6R7HW_SOU_Hindcast\J6R7HW_SOU_Hindcast.wksp"
    simName = "1986_260"
    altName = "HC_ALL"
    lookup = json.load(open(r"C:\workspace\git_clones\folsom-hindcast-processing\outputNoShift3\resSimLookupNoPath.json"))
    dataDir = r'C:\workspace\git_clones\folsom-hindcast-processing\outputNoShift3'
    main(folsomInflowPathnames, simulationDssFile, lookup, dataDir, watershedWkspFile, simName, altName)