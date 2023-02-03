import sys
sys.path.append(r"C:\local_software\HEC-DSSVue 3.2.3\jar\sys\jythonUtils.jar")
sys.path.append(r"C:\local_software\HEC-DSSVue 3.2.3\jar\hec.jar")
sys.path.append(r"C:\local_software\HEC-DSSVue 3.2.3\jar\jython-standalone-2.7.0.jar")
sys.path.append(r"C:\local_software\HEC-DSSVue 3.2.3\jar\hec-dssvue-3.2.3.jar")
sys.path.append(r"C:\local_software\HEC-DSSVue 3.2.3\jar\rma.jar")
from hec.heclib.dss import HecDss
from hec.io import TimeSeriesContainer
from glob import glob
import json
import os


def preProcessHindcastForSimulation(inputDssFile, oldPathNames, simulationDssFile):

    newPathNames = []
    for oldPathName in oldPathNames:
        parts = oldPathName.split('/')
        parts[1] = ''
        parts[6] = parts[6].split('|')[0][2:]
        newPathName = '/'.join(parts)
        newPathNames.append(newPathName)
    print 'here'

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

def postPorcessHindcastSimulation(pathNames, startDate):
    pass

def main(folsomInflowPathname, simulationDssFile, lookup, dataDir ):

    for pattern in lookup.keys():
        scalings = lookup[pattern]
        for scaling in scalings.keys():
            forecastDates = scalings[scaling]
            for forecastDate in forecastDates.keys():
                pathNames = forecastDates[forecastDate]['pathNames']
                startDate = forecastDates[forecastDate]['startDate']
                inputDssFile = r'%s/%s/%s_%s.dss' % (dataDir, pattern, pattern,scaling)
                assert os.path.exists(inputDssFile)
                newPathNames = preProcessHindcastForSimulation(inputDssFile, pathNames, simulationDssFile)

                # Run ResSim Here

                # Post Process Results

                postPorcessHindcastSimulation(startDate, simulationDssFile, folsomInflowPathname)


        print 'here'

if __name__ == '__main__':

    # This should come from the res Sim simulations,
    folsomInflowPathname = ''

    #This should be what the resSim alternative is looking to read from
    simulationDssFile = 'simulation.dss'
    lookup = json.load(open(r"C:\workspace\git_clones\folsom-hindcast-processing\test.json"))
    dataDir = r'../../outputNoShift'
    main(folsomInflowPathname, simulationDssFile, lookup, dataDir)