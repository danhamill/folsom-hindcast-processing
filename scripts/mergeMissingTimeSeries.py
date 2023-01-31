from pydsstools.core import TimeSeriesContainer
from pydsstools.heclib.dss import HecDss
from glob import glob
import os

allDataFiles = glob(fr'outputAll\*\*.dss')

for allDataFile in allDataFiles:

    baseName = os.path.basename(allDataFile)
    pattern = allDataFile.split('\\')[-2]

    missingDataFile = rf'outputMissing\{pattern}\{baseName}'

    assert os.path.exists(missingDataFile)

    pathname_pattern ="/*/*/*/*/*/*/"
    with HecDss.Open(missingDataFile) as fid:

        catalog = fid.getPathnameList(pathname_pattern, sort=1)

        condensedCatalog = []
        for pname in catalog:
            parts = pname.split('/')
            parts[4] = ''
            condensedCatalog.append('/'.join(parts))
        condensedCatalog = list(set(condensedCatalog))

        for pname in condensedCatalog:

            ts = fid.read_ts(pname)

            new_tsc = TimeSeriesContainer()
            new_tsc.startDateTime = ts.startDateTime
            new_tsc.numberValues = ts.numberValues
            new_tsc.interval = ts.interval
            new_tsc.times = ts.times
            new_tsc.values = ts.values
            new_tsc.units = ts.units
            new_tsc.type = ts.type

            with HecDss.Open(allDataFile) as fidOut:
                fidOut.put_ts(new_tsc)



