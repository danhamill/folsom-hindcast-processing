from hec.script import ResSim
from hec.script import Constants
from hec.heclib.dss import HecDss
from hec.io import TimeSeriesContainer
from hec.heclib.util import HecTime
from hec.hecmath import TimeSeriesMath
from hec.heclib.dss import HecDSSFileDataManager
import os
import sys
import logging

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
LOOKBACKSITES = {
        'ICE HOUSE-POOL': 'STOR',
        'ICE HOUSE-GATED SPILLWAY': 'FLOW',
        'ICE HOUSE-LOW-LEVEL OUTLET': 'FLOW',
        'ICE HOUSE-JONES FORK POWER': 'FLOW',
        'UNION VALLEY-POOL': 'STOR',
        'UNION VALLEY-PENSTOCK TUNNEL': 'FLOW',
        'UNION VALLEY-GATED SPILLWAY': 'FLOW',
        'LOON LAKE-POOL': 'STOR',
        'LOON LAKE-LOW-LEVEL OUTLET 1': 'FLOW',
        'LOON LAKE-LOW-LEVEL OUTLET 2': 'FLOW',
        'LOON LAKE-UNGATED SPILLWAY': 'FLOW',
        'HELL HOLE-POOL': 'STOR',
        'HELL HOLE-DIVERSION TUNNEL TO MF PH': 'FLOW',
        'HELL HOLE-OUTLET WORKS': 'FLOW',
        'HELL HOLE-UNGATED SPILLWAY': 'FLOW',
        'FRENCH MEADOWS-POOL': 'STOR',
        'FRENCH MEADOWS-LOW-LEVEL OUTLET': 'FLOW',
        'FRENCH MEADOWS-GATED SPILLWAY': 'FLOW'
    }

def formatSimulationTimeSeries(inputDssFile, oldPathNames, simulationDssFile):
    """
    Function to reformate DSS paths and write to a simulation file that will be used
    in a headless HEC-ResSim ensemble compute.
    :param inputDssFile: string
    :param oldPathNames: List[String] dss file paths
    :param simulationDssFile: Sting
    :return: newPathNames: List[String]
    """

    parts = oldPathNames[0].split('/')
    parts[1] = ''
    parts[4] = ''
    parts[6] = parts[6].split('|')[0] + '|'
    newPathName = '/'.join(parts)

    oldTimeSeriesContiners = getOldTimeSeriesContainers(oldPathNames, inputDssFile)
    # merge time series blocks together
    if len(oldTimeSeriesContiners) == 1:
        mergeTsc = oldTimeSeriesContiners[0].clone()
    else:
        mergeTsc = mergeTwoTimeSeriesContainers(oldTimeSeriesContiners)

    targetTime = HecTime('23Dec2999 04:00')
    oldTs = oldTimeSeriesContiners[0]

    # Shift times to simulation time
    tmpTs = shiftNormalDatesToSimulation(mergeTsc, oldTs, targetTime)

    writeSimulationTimeSeries(newPathName, tmpTs, simulationDssFile)

    return newPathName

def writeSimulationTimeSeries(newPathName, tmpTs, simulationDssFile):
    newTs = TimeSeriesContainer()
    newTs.version = newPathName.split('/')[-2]
    newTs.fullName = newPathName
    newTs.timeGranularitySeconds = tmpTs.timeGranularitySeconds
    newTs.type = tmpTs.type
    newTs.units = tmpTs.units
    newTs.interval = tmpTs.interval
    newTs.numberValues = tmpTs.numberValues
    newTs.times = tmpTs.times
    newTs.values = tmpTs.values
    newTs.startTime = tmpTs.startTime
    outDss = HecDss.open(simulationDssFile, 6)
    outDss.put(newTs)
    outDss.done()

def shiftNormalDatesToSimulation(mergeTsc, oldTs, targetTime):
    oldTsm = TimeSeriesMath(mergeTsc)
    daysToShift = oldTs.startHecTime.dayOfYear() + (365-targetTime.dayOfYear())
    newTsm = oldTsm.shiftInTime(str(3000 - oldTs.startHecTime.year() )+"Y").shiftInTime('-'+str(daysToShift)+'D')
    tmpTs = newTsm.getContainer()
    return tmpTs

def mergeTwoTimeSeriesContainers(oldTimeSeriesContiners):

    timeList1 = list(oldTimeSeriesContiners[0].times)
    timeList2 = list(oldTimeSeriesContiners[1].times)
    newTimeList = []
    newTimeList.extend(timeList1)
    newTimeList.extend(timeList2)

    valuesList1 =list(oldTimeSeriesContiners[0].values)
    valuesList2 =list(oldTimeSeriesContiners[1].values)
    newValueList = []
    newValueList.extend(valuesList1)
    newValueList.extend(valuesList2)
    mergeTsc = TimeSeriesContainer()
    mergeTsc.values = newValueList
    mergeTsc.times = newTimeList
    mergeTsc.type = oldTimeSeriesContiners[0].type
    mergeTsc.units = oldTimeSeriesContiners[0].units
    mergeTsc.interval = oldTimeSeriesContiners[0].interval
    mergeTsc.numberValues = len(newTimeList)
    mergeTsc.startTime = oldTimeSeriesContiners[0].startTime

    return mergeTsc

def shiftSimulationBackToNormalDate(mergeTsc, targetTime, firstTsc):
    oldTsm = TimeSeriesMath(mergeTsc)
    daysToShift = targetTime.dayOfYear() + (365-firstTsc.startHecTime.dayOfYear())
    newTsm = oldTsm.shiftInTime('-'+str(firstTsc.startHecTime.year() - targetTime.year() )+"Y").shiftInTime(str(daysToShift)+'D')
    tmpTs = newTsm.getContainer()

    return tmpTs

def getOldTimeSeriesContainers(pathNames, simulationDssFile):
    oldTimeSeriesContiners = []

    for i, oldPathName in enumerate(pathNames):
        simDss = HecDss.open(simulationDssFile)
        if simDss.recordExists(oldPathName):
            oldTs = simDss.get(oldPathName)
            oldTimeSeriesContiners.append(oldTs)
        simDss.done()
    return oldTimeSeriesContiners

def writeResultsToFile(pathNames, simulationDssFile, targetTime,resultsDssFile, forecastDate, scaling):
    oldTimeSeriesContiners =  getOldTimeSeriesContainers(pathNames, simulationDssFile)

    if len(oldTimeSeriesContiners) == 1:
        mergeTsc = oldTimeSeriesContiners[0].clone()
    else:
        mergeTsc = mergeTwoTimeSeriesContainers(oldTimeSeriesContiners)

    firstTsc = oldTimeSeriesContiners[0]
    tmpTs = shiftSimulationBackToNormalDate(mergeTsc, targetTime, firstTsc)

    parts = firstTsc.fullName.split('/')
    parts[1] = scaling
    parts[4] = ''
    parts[6] = parts[6].split('|')[0] +'|%s' %(forecastDate)
    newPathName = '/'.join(parts)

    newTs = TimeSeriesContainer()
    newTs.version = newPathName.split('/')[-2]
    newTs.fullName = newPathName
    newTs.timeGranularitySeconds = tmpTs.timeGranularitySeconds
    newTs.type = tmpTs.type
    newTs.units = tmpTs.units
    newTs.interval = tmpTs.interval
    newTs.numberValues = tmpTs.numberValues
    newTs.times = tmpTs.times
    newTs.values = tmpTs.values

    results = HecDss.open(resultsDssFile)
    results.put(newTs)
    results.done()

def postPorcessHindcastSimulation(startDate, simulationDssFile, forecastDate, scaling, resultsDssFile):

    targetTime = HecTime(startDate)

    # Folsom Flow In
    for year in range(1980,2021):
        pathNames = []
        for dpart in ['01DEC2999','01JAN3000']:
            pathName = "//FOLSOM/FLOW-IN/%s/1HOUR/C:00%s|HC_ENSEMBL0/" % (dpart, year)
            pathNames.append(pathName)
        writeResultsToFile(pathNames, simulationDssFile, targetTime,resultsDssFile, forecastDate, scaling)

    # Fair Oaks Flow Unreg
    for year in range(1980,2021):
        pathNames = []
        for dpart in ['01DEC2999','01JAN3000']:
            pathName = "//FAIR OAKS/FLOW-UNREG/%s/1HOUR/C:00%s|HC_ENSEMBL0/" % (dpart, year)
            pathNames.append(pathName)
        writeResultsToFile(pathNames, simulationDssFile, targetTime,resultsDssFile, forecastDate, scaling)

    #lookbacks
    for bpart, cpart in LOOKBACKSITES.items():
        for year in range(1980,2021):
            pathNames = []
            for dpart in ['01DEC2999','01JAN3000']:
                pathName = "//%s/%s/%s/1HOUR/C:00%s|HC_ENSEMBL0/" % (bpart, cpart,dpart, year)
                pathNames.append(pathName)
            writeResultsToFile(pathNames, simulationDssFile, targetTime,resultsDssFile, forecastDate, scaling)

def runExtract(pattern, scaling, forecastDate, inputDssFile, simulatioinDssFile):

    if pattern == '1986':
        blockStart = '01FEB%s' %(pattern)
        blockEnd = '01MAR%s' %(pattern)

    newPathNames = []
    for bpart, cpart in SITES.items():
        for year in range(1980,2021):
            pathNames = []
            for dpart in [blockStart, blockEnd]:
                pathName = "/%s/%s/%s/%s/1HOUR/C:00%s|%s/" % (scaling, bpart, cpart, dpart, year, forecastDate)
                pathNames.append(pathName)
            newPath = formatSimulationTimeSeries(inputDssFile, pathNames, simulatioinDssFile)
            newPathNames.append(newPath)

    for bpart, cpart in LOOKBACKSITES.items():
        for year in range(1980,2021):
            pathNames = []
            for dpart in [blockStart, blockEnd]:
                pathName = "/%s/%s/%s/%s/1HOUR/C:00%s|%s/" % (scaling, bpart, cpart, dpart, year, forecastDate)
                pathNames.append(pathName)
            newPath = formatSimulationTimeSeries(inputDssFile, pathNames, simulatioinDssFile)
            newPathNames.append(newPath)
    pathNames = sorted(newPathNames)

    return pathNames

def getStartDates(pattern):
    return {
        '1986': {
            '1986020112': '01Feb1986 04:00',
            '1986020212': '02Feb1986 04:00',
            '1986020312': '03Feb1986 04:00',
            '1986020412': '04Feb1986 04:00',
            '1986020512': '05Feb1986 04:00',
            '1986020612': '06Feb1986 04:00',
            '1986020712': '07Feb1986 04:00',
            '1986020812': '08Feb1986 04:00',
            '1986020912': '09Feb1986 04:00',
            '1986021012': '10Feb1986 04:00',
            '1986021112': '11Feb1986 04:00',
            '1986021212': '12Feb1986 04:00',
            '1986021312': '13Feb1986 04:00',
            '1986021412': '14Feb1986 04:00',
            '1986021512': '15Feb1986 04:00',
            '1986021612': '16Feb1986 04:00',
            '1986021712': '17Feb1986 04:00',
            '1986021812': '18Feb1986 04:00',
            '1986021912': '19Feb1986 04:00',
            '1986022012': '20Feb1986 04:00',
            '1986022112': '21Feb1986 04:00',
            '1986022212': '22Feb1986 04:00',
            '1986022312': '23Feb1986 04:00',
            '1986022412': '24Feb1986 04:00',
            '1986022512': '25Feb1986 04:00',
            '1986022612': '26Feb1986 04:00',
            '1986022712': '27Feb1986 04:00',
            '1986022812': '28Feb1986 04:00'
        },
        '1997': {
            '1996121512': '23Dec2999 04:00',
            '1996121612': '24Dec2999 04:00',
            '1996121712': '25Dec2999 04:00',
            '1996121812': '26Dec2999 04:00',
            '1996121912': '27Dec2999 04:00',
            '1996122012': '28Dec2999 04:00',
            '1996122112': '29Dec2999 04:00',
            '1996122212': '30Dec2999 04:00',
            '1996122312': '31Dec2999 04:00',
            '1996122412': '01Jan3000 04:00',
            '1996122512': '02Jan3000 04:00',
            '1996122612': '03Jan3000 04:00',
            '1996122712': '04Jan3000 04:00',
            '1996122812': '05Jan3000 04:00',
            '1996122912': '06Jan3000 04:00',
            '1996123012': '07Jan3000 04:00',
            '1996123112': '08Jan3000 04:00',
            '1997010112': '09Jan3000 04:00',
            '1997010212': '10Jan3000 04:00',
            '1997010312': '11Jan3000 04:00',
            '1997010412': '12Jan3000 04:00',
            '1997010512': '13Jan3000 04:00',
            '1997010612': '14Jan3000 04:00',
            '1997010712': '15Jan3000 04:00',
            '1997010812': '16Jan3000 04:00',
            '1997010912': '17Jan3000 04:00',
            '1997011012': '18Jan3000 04:00',
            '1997011112': '19Jan3000 04:00',
            '1997011212': '20Jan3000 04:00',
            '1997011312': '21Jan3000 04:00',
            '1997011412': '22Jan3000 04:00',
            '1997011512': '23Jan3000 04:00'
        }
    }[pattern]

def configureResSim(watershedWkspFile, simName, altName):

    #  Res Sim only likes unix-style path
    watershedWkspFile = watershedWkspFile.replace(os.sep, "/")
    ResSim.openWatershed(watershedWkspFile)
    ResSim.selectModule('Simulation')
    simMode = ResSim.getCurrentModule()
    # Not sure what this does, but this is the only way to open a simulation
    simMode.resetWorkspace()
    simMode.openSimulation(simName)
    simulation = simMode.getSimulation()
    # force compute everything
    simulation.setComputeAll(1)
    simRun = simulation.getSimulationRun(altName)
    return simMode, simRun

def main(simulationDssFile, patterns, dataDir, watershedWkspFile, simName, altName ):
    
    simMode, simRun = configureResSim(watershedWkspFile, simName, altName)



    for pattern in patterns:
        
        loggingFile = r'%s/%s_results.log' %(dataDir, pattern)
        logging.basicConfig(filename=loggingFile, level=logging.INFO, format='%(asctime)s %(message)s')
        logging.info('Processing pattern %s...' %(pattern))
        
        resultsDssFile = r'%s/%s_results.dss' %(dataDir, pattern)
        if not os.path.exists(resultsDssFile):
            fid = HecDss.open(resultsDssFile, 6)
            fid.done()
        logging.info('Results are stroed in  %s' %(resultsDssFile))
        for scaling in [str(x) for x in range(200, 510, 10)][10:11]:
            logging.info('Processing %s scale factor....'  %(scaling))
            for forecastDate, startDate in getStartDates(pattern).items():
                logging.info('Processing forecast date %s....'  % (forecastDate))
                inputDssFile = r'%s/%s/%s_%s.dss' % (dataDir, pattern, pattern,scaling)
                assert os.path.exists(inputDssFile), "input DSS file does not exist:" + inputDssFile
                _ = runExtract(pattern, scaling, forecastDate, inputDssFile, simulationDssFile)

                simMode.computeRun(simRun, -1, Constants.TRUE, Constants.TRUE)
                ResSim.getCurrentModule().saveSimulation()

                # Post Process Results
                postPorcessHindcastSimulation(startDate, simulationDssFile, forecastDate, scaling, resultsDssFile)

                HecDSSFileDataManager().closeAllFiles()
                os.remove(simulationDssFile)

            HecDSSFileDataManager().closeAllFiles()
            ResSim.closeWatershed()
            sys.exit("Finished Compute.....")
                    

if __name__ == '__main__':

    simulationDssFile = r"C:\workspace\git_clones\folsom-hindcast-processing\jythonResSim\model\J6R7HW_SOU_Hindcast_2023.04.05\rss\2023.04.14-0900\simulation.dss"
    watershedWkspFile = r"C:\workspace\git_clones\folsom-hindcast-processing\jythonResSim\model\J6R7HW_SOU_Hindcast_2023.04.05\J6R7HW_SOU_Hindcast.wksp"
    simName = "2023.04.14-0900"
    altName = "HC_Ensembl"
    dataDir = r'C:\workspace\git_clones\folsom-hindcast-processing\outputNormalDate'
    patterns = ['1986','1997'][:1]
    main(simulationDssFile, patterns, dataDir, watershedWkspFile, simName, altName)

    """


    Review process

    1. All product under review will be in US/PAcific time within their respecrive historical time window
    2. Would be nice to store input data along with a few simulated time series
    3. Simulated time series to review
        - Fair Oaks - Flow Unreg
        - Folsom - Flow In
    4. Lookbacks
        - Lookback and extended simulation time series

    Action Items:
        - Run all forecasts within the 260 scaling for the 1986 pattern
    """