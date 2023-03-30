from glob import glob
import os
from unittest import skip
import pandas as pd
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer

import gc

sites = {
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
    'SPYC1':'FLOW',
    'FMDC1I':'FLOW-LOC',
    'UNVC1I':'FLOW-LOC'
}

def main():

    
    outDir = r'outputDeterminstic'
    os.makedirs(outDir, exist_ok=True)

    patterns = glob(r'data\*')

    for pattern in patterns:

        patternYear = pattern.split('\\')[-1].split('_')[0]
        outDss = fr'{outDir}\{patternYear}_output_determinstic_v3.dss'
        determiniticFiles = glob(f'{pattern}\*\*export.csv')

        for determiniticFile in determiniticFiles:

            scaling = str(determiniticFile.split('\\')[-2])
            targetDate = pd.Period(year=2999, day=23, month=12, hour=4,  freq='h')

            df  = pd.read_csv(
                determiniticFile, 
                header = [0,1], 
                index_col=0,
                parse_dates=True
            )

            df = df.loc[:, df.columns.get_level_values(1).str.contains('SQIN')]
            df = df.loc[:, df.columns.get_level_values(0).isin(sites.keys())]
            df = df.groupby(level=0, axis=1).max()

            df.index = df.index.tz_localize('UTC').tz_convert('US/Pacific')
            df.index = pd.DatetimeIndex(
                [i.replace(tzinfo=None) for i in df.index], 
                name='date'
            )

            df[df>-500] = df[df>0]*1000
            df[df<-500] = -901.0

            df = df.stack()
            df.index.names = ['date','site']
            df.name = 'flow'

            for site, data in df.groupby('site'):

                data.index = data.index.droplevel(1)
                pname = f'/{scaling}/{site}/{sites[site]}//1HOUR/CNFRC-DETERMINSTIC/'
                
                tsc = TimeSeriesContainer()
                tsc.pathname = pname
                tsc.startDateTime = data.index.min().strftime('%d%b%Y %H:%M')
                tsc.numberValues = data.shape[0]
                tsc.granularity = 60
                tsc.units = 'cfs'
                tsc.type= 'INST-VAL'
                tsc.interval = 1
                tsc.values = data.to_list()

                fid = HecDss.Open(outDss, version=6)
                fid.put_ts(tsc)
                fid.close()



if __name__ == '__main__':

    main()

    # \\spk-netapp2\Hydrology\Studies\SAC-013\Folsom Dam Raise_SOU\2 Data Transfers\Incoming\Agencies\CNRFC\HindCast_Robustness\20221127 MI Scaled Hindcasts 1986 and 1997\forReview