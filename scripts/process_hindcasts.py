from glob import glob
import pandas as pd
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer


def main(rootFolder, sites, dssOut):

    files = glob(f'{rootFolder}\*')

    df = pd.DataFrame()
    for file in files:

        csvSites  = pd.read_csv(file, header = None, nrows=1).iloc[:,1:].stack().value_counts()

        idx=None
        for i in csvSites.index:
            tmpIdx = pd.MultiIndex.from_product([[i], range(1980, 1980+csvSites[i]), [file.split('\\')[-1].split('_')[0]]], names = ['site','year', 'fileDate'])
            if idx is None:
                idx = tmpIdx
            else: 
                idx = idx.union(tmpIdx)
        
        data = pd.read_csv(file, skiprows=2, header=None, names = idx, index_col=0, parse_dates=True)
        data.index = data.index.tz_localize('UTC').tz_convert('US/Pacific')
        data.index = pd.DatetimeIndex([i.replace(tzinfo=None) for i in data.index], name='date')
        df = pd.concat([df, data], axis=0)

    df = df.stack(level=[0,1,2])
    df.index.names = ['date','site','year', 'fileDate']
    df = df * 1000
    df = df.loc[df.index.get_level_values('site').isin(sites.keys()),:]

    for (site, year, fileDate), group in df.groupby(['site', 'year', 'fileDate']):
        

        group.name = 'flow'
        group = group.reset_index()

        pname = f'/AMERICAN/{site}/{sites[site]}//1HOUR/C:00{year}|{fileDate}/'

        print('here')
        
        tsc = TimeSeriesContainer()
        tsc.pathname = pname
        tsc.startDateTime = group.date.min().strftime('%d%b%Y %H:%M')
        tsc.numberValues = group.shape[0]
        tsc.granularity = 60
        tsc.units = 'cfs'
        tsc.type= 'INST-VAL'
        tsc.interval = 1
        tsc.values = group.flow.to_list()


        fid = HecDss.Open(dssOut, version=6)
        fid.put_ts(tsc)
        fid.close()

if __name__ == '__main__':

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
        # 'DUMMY': 'FLOW',
        # 'LOCAL_SF FOLC1L': 'FLOW-LOC',
        'RRGC1L': 'FLOW-LOC',
        'SPYC1F': 'FLOW-NAT',
        'RUFC1L': 'FLOW-LOC',
        'AKYC1': 'FLOW-IN',
        'CBAC1L': 'FLOW-LOC',
        'NMFC1': 'FLOW-IN',
        # 'LOCAL_NF FOLC1L': 'FLOW-LOC',
        'MFAC1F': 'FLOW-NAT',
        'CBAC1F': 'FLOW-NAT',
        'MFPC1F': 'FLOW-NAT',
        'RUFC1F': 'FLOW-NAT'
    }
    
    dssOut = rf'output\output.dss'

    for rootFolder in [r'data\1986_SF116',r'data\1997_SF116'][1:]:
        main(rootFolder, sites, dssOut)
