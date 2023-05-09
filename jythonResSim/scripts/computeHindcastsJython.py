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
import datetime

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

def convertHecTimeToDatetime(hecTime):

    date = datetime.datetime.strptime(hecTime.toString(), '%d %B %Y, %H:%M')
    return date

def formatSimulationTimeSeries(inputDssFile, oldPathNames, simulationDssFile, pattern):
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
    tmpTs = shiftNormalDatesToSimulation(mergeTsc, oldTs, targetTime, pattern)

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

def shiftNormalDatesToSimulation(mergeTsc, oldTs, targetTime, pattern):
    
    # Calculate time delta between simulation and normal date
    targetPyTime = convertHecTimeToDatetime(targetTime)
    inputPyTime = convertHecTimeToDatetime(oldTs.startHecTime)
    delta = targetPyTime - inputPyTime
    oldTsm = TimeSeriesMath(mergeTsc)

    # Shift the time series to simulation date
    newTsm = oldTsm.shiftInTime(str(delta.days)+'D')
    tmpTs = newTsm.getContainer()

    assert targetTime.equalTo(tmpTs.startHecTime), '%s not being shifted correctly, should be %s but is %s' %(pattern, targetTime, tmpTs.startHecTime)

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
def shiftSimulationBackToNormalDate(mergeTsc, targetTime, firstTsc, pattern):
    
    # Calculate the time delta between normal date and simulation dates
    targetPyTime = convertHecTimeToDatetime(targetTime)
    inputPyTime = convertHecTimeToDatetime(firstTsc.startHecTime)
    delta = targetPyTime - inputPyTime
    oldTsm = TimeSeriesMath(mergeTsc)

    # Shift the time series to the normal date
    newTsm = oldTsm.shiftInTime(str(delta.days)+'D')
    tmpTs = newTsm.getContainer()

    assert targetTime.equalTo(tmpTs.startHecTime), '%s not being shifted correctly, should be %s but is %s' %(pattern, targetTime, tmpTs.startHecTime)

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

def writeResultsToFile(pathNames, simulationDssFile, targetTime,resultsDssFile, forecastDate, scaling, pattern):
    oldTimeSeriesContiners =  getOldTimeSeriesContainers(pathNames, simulationDssFile)

    if len(oldTimeSeriesContiners) == 1:
        mergeTsc = oldTimeSeriesContiners[0].clone()
    else:
        mergeTsc = mergeTwoTimeSeriesContainers(oldTimeSeriesContiners)

    firstTsc = oldTimeSeriesContiners[0]
    tmpTs = shiftSimulationBackToNormalDate(mergeTsc, targetTime, firstTsc, pattern)

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

def writeDeterminsticTimeSereisToResults(pathNames, inputDssFile, resultsDssFile):

    oldTimeSeriesContiners =  getOldTimeSeriesContainers(pathNames, inputDssFile)

    if len(oldTimeSeriesContiners) == 1:
        mergeTsc = oldTimeSeriesContiners[0].clone()
    else:
        mergeTsc = mergeTwoTimeSeriesContainers(oldTimeSeriesContiners)

    parts = oldTimeSeriesContiners[0].fullName.split('/')
    parts[4] = ''
    newPathName = '/'.join(parts)

    newTs = TimeSeriesContainer()
    newTs.version = newPathName.split('/')[-2]
    newTs.fullName = newPathName
    newTs.timeGranularitySeconds = mergeTsc.timeGranularitySeconds
    newTs.type = mergeTsc.type
    newTs.units = mergeTsc.units
    newTs.interval = mergeTsc.interval
    newTs.numberValues = mergeTsc.numberValues
    newTs.times = mergeTsc.times
    newTs.values = mergeTsc.values

    results = HecDss.open(resultsDssFile)
    results.put(newTs)
    results.done()

def postPorcessHindcastSimulation(startDate, simulationDssFile, forecastDate, scaling, resultsDssFile, inputDssFile, pattern):

    targetTime = HecTime(startDate)
    simulationDParts = ['01DEC2999','01JAN3000']
    # Folsom Flow In
    for year in range(1980,2021):
        pathNames = []
        for dpart in simulationDParts:
            pathName = "//FOLSOM/FLOW-IN/%s/1HOUR/C:00%s|HC_ENSEMBL0/" % (dpart, year)
            pathNames.append(pathName)
        writeResultsToFile(pathNames, simulationDssFile, targetTime,resultsDssFile, forecastDate, scaling, pattern)

    # Fair Oaks Flow Unreg
    for year in range(1980,2021):
        pathNames = []
        for dpart in simulationDParts:
            pathName = "//FAIR OAKS/FLOW-UNREG/%s/1HOUR/C:00%s|HC_ENSEMBL0/" % (dpart, year)
            pathNames.append(pathName)
        writeResultsToFile(pathNames, simulationDssFile, targetTime,resultsDssFile, forecastDate, scaling, pattern)

    #lookbacks
    for bpart, cpart in LOOKBACKSITES.items():
        for year in range(1980,2021):
            pathNames = []
            for dpart in simulationDParts:
                pathName = "//%s/%s/%s/1HOUR/C:00%s|HC_ENSEMBL0/" % (bpart, cpart,dpart, year)
                pathNames.append(pathName)
            writeResultsToFile(pathNames, simulationDssFile, targetTime,resultsDssFile, forecastDate, scaling, pattern)

    if pattern == '1997':
        dparts = ['01DEC1996', '01JAN1997']
    elif pattern == '1986':
        dparts = ['01FEB1986', '01MAR1986']
    #Determistic data to compare against
    pathNames = []
    for dpart in dparts:
        pathName = '/%s/FOLC1F/FLOW-NAT/%s/1HOUR//' %(scaling, dpart)
        pathNames.append(pathName)
    writeDeterminsticTimeSereisToResults(pathNames, inputDssFile, resultsDssFile)

def runExtract(pattern, scaling, forecastDate, inputDssFile, simulationDssFile):

    if pattern == '1986':
        blockLookback = '01JAN%s' %{pattern}
        blockStart = '01FEB%s' %(pattern)
        blockEnd = '01MAR%s' %(pattern)

        dPartsLookback = [blockLookback, blockStart, blockEnd]
        dPartsOther = [ blockStart, blockEnd]
    else:
        blockEnd = '01JAN%s'  %(pattern)
        blockStart = '01DEC%s'%(pattern[:-1]+'6')
        dPartsLookback = [blockStart, blockEnd]
        dPartsOther = [blockStart, blockEnd]

    newPathNames = []
    for bpart, cpart in SITES.items():
        for year in range(1980,2021):
            pathNames = []
            for dpart in dPartsOther:
                pathName = "/%s/%s/%s/%s/1HOUR/C:00%s|%s/" % (scaling, bpart, cpart, dpart, year, forecastDate)
                pathNames.append(pathName)
            newPath = formatSimulationTimeSeries(inputDssFile, pathNames, simulationDssFile, pattern)
            newPathNames.append(newPath)

    for bpart, cpart in LOOKBACKSITES.items():
        for year in range(1980,2021):
            pathNames = []
            for dpart in dPartsLookback:
                pathName = "/%s/%s/%s/%s/1HOUR/C:00%s|%s/" % (scaling, bpart, cpart, dpart, year, forecastDate)
                pathNames.append(pathName)
            newPath = formatSimulationTimeSeries(inputDssFile, pathNames, simulationDssFile, pattern)
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
            '1996121512': '15Dec1996 04:00',
            '1996121612': '16Dec1996 04:00',
            '1996121712': '17Dec1996 04:00',
            '1996121812': '18Dec1996 04:00',
            '1996121912': '19Dec1996 04:00',
            '1996122012': '20Dec1996 04:00',
            '1996122112': '21Dec1996 04:00',
            '1996122212': '22Dec1996 04:00',
            '1996122312': '23Dec1996 04:00',
            '1996122412': '24Dec1996 04:00',
            '1996122512': '25Dec1996 04:00',
            '1996122612': '26Dec1996 04:00',
            '1996122712': '27Dec1996 04:00',
            '1996122812': '28Dec1996 04:00',
            '1996122912': '29Dec1996 04:00',
            '1996123012': '30Dec1996 04:00',
            '1996123112': '31Dec1996 04:00',
            '1997010112': '01Jan1997 04:00',
            '1997010212': '02Jan1997 04:00',
            '1997010312': '03Jan1997 04:00',
            '1997010412': '04Jan1997 04:00',
            '1997010512': '05Jan1997 04:00',
            '1997010612': '06Jan1997 04:00',
            '1997010712': '07Jan1997 04:00',
            '1997010812': '08Jan1997 04:00',
            '1997010912': '09Jan1997 04:00',
            '1997011012': '10Jan1997 04:00',
            '1997011112': '11Jan1997 04:00',
            '1997011212': '12Jan1997 04:00',
            '1997011312': '13Jan1997 04:00',
            '1997011412': '14Jan1997 04:00',
            '1997011512': '15Jan1997 04:00'
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

def myLogger(name, path):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(path, 'a')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def main(simulationDssFile, patterns, dataDir, watershedWkspFile, simName, altName ):
    
    simMode, simRun = configureResSim(watershedWkspFile, simName, altName)

    for pattern in patterns:
        
        loggingFile = r'%s/%s_results.log' %(dataDir, pattern)
        loggerMain = myLogger("main", loggingFile)
        
        resultsDssFile = r'%s/%s_results.dss' %(dataDir, pattern)
        if not os.path.exists(resultsDssFile):
            fid = HecDss.open(resultsDssFile, 6)
            fid.done()

        loggerMain.info('Results are stroed in  %s' %(resultsDssFile))
        
        for scaling in [str(x) for x in range(200, 510, 10)][:1]:

            loggerScaling = myLogger("scaling: %s" %(scaling), loggingFile)
            loggerScaling.info('Processing %s scale factor....'  %(scaling))
            
            for forecastDate, startDate in getStartDates(pattern).items():
                loggerForecast = myLogger("forecast: %s" %(forecastDate), loggingFile)
                loggerForecast.info('Processing forecast date %s....'  % (forecastDate))
                inputDssFile = r'%s/%s/%s_%s.dss' % (dataDir, pattern, pattern,scaling)
                assert os.path.exists(inputDssFile), "input DSS file does not exist:" + inputDssFile
                _ = runExtract(pattern, scaling, forecastDate, inputDssFile, simulationDssFile)
                
                simMode.computeRun(simRun, -1, Constants.TRUE, Constants.TRUE)
                ResSim.getCurrentModule().saveSimulation()

                # Post Process Results
                postPorcessHindcastSimulation(startDate, simulationDssFile, forecastDate, scaling, resultsDssFile,
                                              inputDssFile, pattern)
                
                HecDSSFileDataManager().closeAllFiles()
                os.remove(simulationDssFile)

        HecDSSFileDataManager().closeAllFiles()
        ResSim.closeWatershed()
        sys.exit("Finished Compute.....")
                    

if __name__ == '__main__':

    simulationDssFile = r"C:\workspace\git_clones\folsom-hindcast-processing\jythonResSim\model\J6R7HW_SOU_Hindcast_2023.04.05\rss\HC_1986E\simulation.dss"
    watershedWkspFile = r"C:\workspace\git_clones\folsom-hindcast-processing\jythonResSim\model\J6R7HW_SOU_Hindcast_2023.04.05\J6R7HW_SOU_Hindcast.wksp"
    simName = "HC_1986E"
    altName = "HC_Ensembl"
    dataDir = r'C:\workspace\git_clones\folsom-hindcast-processing\outputNormalDate4'
    patterns = ['1986','1997'][1:]
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