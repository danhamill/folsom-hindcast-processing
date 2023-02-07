import sys
sys.path.append(r"C:\local_software\HEC-DSSVue 3.2.3\jar\sys\jythonUtils.jar")
sys.path.append(r"C:\local_software\HEC-DSSVue 3.2.3\jar\hec.jar")
sys.path.append(r"C:\local_software\HEC-DSSVue 3.2.3\jar\jython-standalone-2.7.0.jar")
sys.path.append(r"C:\local_software\HEC-DSSVue 3.2.3\jar\hec-dssvue-3.2.3.jar")
sys.path.append(r"C:\local_software\HEC-DSSVue 3.2.3\jar\rma.jar")
from hec.heclib.dss import HecDss
from hec.io import TimeSeriesContainer
from hec.heclib.util import HecTime
import json
import os

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

        for year in range(1980,2021):
            pathName = "/%s/%s/%s//1HOUR/C:00%s|%s/" % (scaling, bpart, cpart, year, forecastDate)
            pathNames.append(pathName)
    pathNames = sorted(pathNames)

    return pathNames


def main(folsomInflowPathname, simulationDssFile, lookup, dataDir ):

    for pattern in lookup.keys():
        scalings = lookup[pattern]
        resultsDssFile = r'%s/%s_results.dss' %(dataDir, pattern)
        if not os.path.exists(resultsDssFile):
            fid = HecDss.open(resultsDssFile, 6)
            fid.done()
        for scaling in scalings.keys():
            forecastDates = scalings[scaling]
            for forecastDate in forecastDates.keys():
                startDate = forecastDates[forecastDate]['startDate']
                pathNames = buildInputPathnames(pattern, scaling, forecastDate)
                inputDssFile = r'%s/%s/%s_%s.dss' % (dataDir, pattern, pattern,scaling)
                assert os.path.exists(inputDssFile)
                newPathNames = preProcessHindcastForSimulation(inputDssFile, pathNames, simulationDssFile)

                # Run ResSim Here
                # open watershed
                # set Module
                # open simulation
                # get alternative
                # compute run

                # Post Process Results
                # simulationDssFile = r'C:\workspace\git_clones\folsom-hindcast-processing\resultsFromUI\simulation.dss'
                postPorcessHindcastSimulation(startDate, simulationDssFile, folsomInflowPathname, forecastDate, scaling, resultsDssFile)

if __name__ == '__main__':

    # This should come from the resSim simulations,
    folsomInflowPathnames = [
         '//FOLSOM/FLOW-IN//1HOUR/C:001980|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001981|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001982|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001983|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001984|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001985|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001986|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001987|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001988|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001989|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001990|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001991|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001992|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001993|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001994|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001995|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001996|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001997|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001998|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:001999|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002000|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002001|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002002|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002003|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002004|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002005|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002006|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002007|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002008|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002009|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002010|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002011|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002012|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002013|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002014|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002015|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002016|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002017|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002018|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002019|HC86_260--0/',
         '//FOLSOM/FLOW-IN//1HOUR/C:002020|HC86_260--0/'
    ]
    #This should be what the resSim alternative is looking to read from
    simulationDssFile = 'simulation.dss'


    lookup = json.load(open(r'../../outputNoShift3/resSimLookupNoPath.json'))
    dataDir = r'../../outputNoShift3'
    main(folsomInflowPathnames, simulationDssFile, lookup, dataDir)