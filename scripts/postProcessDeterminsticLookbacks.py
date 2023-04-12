from glob import glob
import os
import json
import pandas as pd
import numpy as np
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer

lookbackSites = {
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

def readDss(bPart: str, cPart: str, dssFile: str, window: list[str]):

    pname = f'//{bPart}/{cPart}//1HOUR/HC_DETERM-0/'
    
    with HecDss.Open(dssFile) as fid:
        ts = fid.read_ts(pname, window=window, trim_missing=False)
        times = np.array(ts.pytimes)
        values = ts.values
        units = ts.units
        idx = pd.Index(times, name = 'date')
        tmp = pd.DataFrame(data = {cPart:values}, index=idx)
    return tmp.reset_index(), units


def main():

    patterns = glob(r'lookbackData\*')
    
    for pattern in patterns:
        scalings = glob(f'{pattern}\*')
        patternYear = pattern.split('\\')[-1]
        for scalingDssFile in scalings[6:]:

            scaling = scalingDssFile.split('\\')[-1].split('_')[0][1:]

            hindcastFiles = glob(rf'data\{patternYear}_scalings\{scaling}\*hefs*.csv')
            targetDate = pd.Period(year=2999, day=23, month=12, hour=4,  freq='h')
            
            # These are the moving window boundaries
            offsetStart = pd.Period(year=2999, day=23, month=12, hour=4,  freq='h')
            offsetEnd = offsetStart + 24

            outDir = rf'outputNoShift4\{patternYear}'
            os.makedirs(outDir, exist_ok=True)
            dssOut = rf'{outDir}\{patternYear}_{scaling}.dss'

            for hindcastFile in hindcastFiles:

                fileDate = hindcastFile.split('\\')[-1].split('_')[0]

                window = [offsetStart.strftime('%d%b%Y %H:%M'),offsetEnd.strftime('%d%b%Y %H:%M')]

                for bPart, cPart in lookbackSites.items():

                    print('here')
                    
                    df, units = readDss(bPart, cPart, scalingDssFile, window)
                    
                    for ensembleYear in range(1980,2021):
                        pname = f'/{scaling}/{bPart}/{cPart}//1HOUR/C:00{ensembleYear}|{fileDate}/'

                        
                        tsc = TimeSeriesContainer()
                        tsc.pathname = pname
                        tsc.startDateTime = offsetStart.strftime('%d%b%Y %H:%M')
                        tsc.numberValues = df.shape[0]
                        tsc.granularity = 60
                        tsc.units = units
                        tsc.type= 'INST-VAL'
                        tsc.interval = 1
                        tsc.values = df.loc[:,cPart].to_list()


                        fid = HecDss.Open(dssOut, version=6)
                        fid.put_ts(tsc)
                        fid.close()
                        del tsc, group
                offsetStart +24
                offsetEnd + 24



                    
                    



if __name__ == '__main__':

    main()

'''
new model to use : "\\spk-netapp2\Hydrology\Studies\SAC-013\Folsom Dam Raise_SOU\99-Working Files\Hamill\Folsom Model\J6R7HW_SOU_Hindcast_2023.04.05.7z"
- simulation and alternative names changed will need to update all processing

THing to code to: SF 260 year
- dss file: "\\spk-netapp2\Hydrology\Studies\SAC-013\Folsom Dam Raise_SOU\99-Working Files\Hamill\Folsom Model\1986E\simulation.dss"

Source data we want to pull lookbacks from:
- \\spk-netapp2\Hydrology\Studies\SAC-013\Folsom Dam Raise_SOU\99-Working Files\Hamill\Folsom Model\1986D


'Determinstic time series should be shiftd -7 days to start on 12/15/2999
'''