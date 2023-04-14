from glob import glob
import os
import json
import pandas as pd
import numpy as np
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer

def readCatalog(dssFile: str) -> list:
    """
    Function to return condensed DSS catalog for all records

    Args:
        dssFile (str): file path to dss file

    Returns:
        list: condensed dss catalog
    """
    with HecDss.Open(dssFile) as fid:
        plist = fid.getPathnameList('/*/*/*/*/*/*/')

    output = []
    for i in plist:
        parts = i.split('/')
        parts[4] = ''
        if parts not in output:
            output.append(parts) 

    res = pd.DataFrame(data = output, columns = ['start','PartA','PartB','PartC','PartD', 'PartE','PartF','end'])

    res = res.apply(lambda row: "/".join(["", row.PartA, row.PartB, row.PartC, "", row.PartE, row.PartF, ""]),
                    axis=1,
                    )
    catalog = res.tolist()

    return catalog

dssFiles = glob(r'lookbackData\1986\*.dss')

for dssFile in dssFiles:
    dssOut = dssFile.split('.')[0]+ '_normalDate.dss'
    catalog = readCatalog(dssFile)

    for pname in catalog:

        with HecDss.Open(dssFile) as fid:
            ts = fid.read_ts(pname)

        tsc = TimeSeriesContainer()
        tsc.pathname = pname
        tsc.startDateTime = '21Jan1986 04:00' # <- this is in US/Pacific
        tsc.numberValues = ts.numberValues
        tsc.interval = ts.interval
        tsc.units = ts.units
        tsc.values = ts.values

        with HecDss.Open(dssOut, version=6) as fid:
            fid.put_ts(tsc)

        del tsc, ts, pname

print('here')
