from glob import glob
import os
import json
import pandas as pd
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer
from utils.folsomSites import sites
import gc

def main(ensembleStartYear):

    patterns = glob(r'data\*')
    lookup = {}
    for pattern in patterns[1:]:

        patternYear = pattern.split('\\')[-1].split('_')[0]

        scalings = glob(f'{pattern}\*')
        eventScaling = scalings[0]
        scalings = scalings[1:]

        lookup[patternYear] = {}
        for scaling in scalings:
            
            returnInterval = scaling.split('\\')[-1]
            lookup[patternYear] = {}

            outDir = rf'outputNoShift2\{patternYear}'
            os.makedirs(outDir, exist_ok=True)
            dssOut = rf'{outDir}\{patternYear}_{returnInterval}.dss'
            print(f'Currently Processing {dssOut}...')

            hindcastFiles = glob(rf'{scaling}\*hefs*.csv')

            targetDate = pd.Period(year=2999, day=23, month=12, hour=4,  freq='h')
            offset = pd.Period(year=2999, day=23, month=12, hour=4,  freq='h')

            print('Currently Processing hefs files...')
            for hindcastFile in hindcastFiles:
                pathNames = []
                lookup[patternYear][returnInterval] = {}

                fileDate = hindcastFile.split('\\')[-1].split('_')[0]

                csvSites  = pd.read_csv(
                    hindcastFile, 
                    header = None, 
                    nrows=1
                ).iloc[:,1:].stack().to_list()
                csvSites += ['DUMMY']*41

                csvVariables = pd.read_csv(
                    hindcastFile, 
                    header = None, 
                    nrows=1, 
                    skiprows=1
                ).iloc[:,1:].stack().to_list()
                csvVariables += ['QINE']*41

                numEnsembles = pd.DataFrame(
                    data = {'sites':csvSites,'tsType':csvVariables}
                ).value_counts()
                
                ensembleYears = []
                for i in numEnsembles.index:
                    ensembleYears.extend(
                        [i for i in range(ensembleStartYear, ensembleStartYear+numEnsembles[i])]
                    )
                    
                fileDates = [fileDate] * len(ensembleYears)

                idx=pd.MultiIndex.from_tuples(
                    tuple(zip(csvSites, csvVariables, ensembleYears, fileDates)),  
                    names = ['site','tsType', 'year', 'fileDate']
                )

                data = pd.read_csv(
                    hindcastFile, 
                    skiprows=2, 
                    header=None, 
                    names = idx, 
                    index_col=0, 
                    parse_dates=True
                )

                data = data.fillna(0.0)

                data.columns.names = ['site','tsType', 'year', 'fileDate']

                data.index = data.index.tz_localize('UTC').tz_convert('US/Pacific')

                data.index = pd.DatetimeIndex(
                    [i.replace(tzinfo=None) for i in data.index], 
                    name='date'
                )

                data = data.stack(level=[0,1,2,3])
                data.index.names = ['date','site','tsType','year', 'fileDate']
                data = data * 1000
                data = data.loc[data.index.get_level_values('site').isin(sites.keys()),:]

                grouped = data.groupby(['site', 'year'])

                print('Currently Writing to dss...')          
                
                lookup[patternYear][returnInterval][fileDate] = {}
                
                for (site, year), group in grouped:
                                       
                    group.name = 'flow'
                    group = group.reset_index()

                    pname = f'/{returnInterval}/{site}/{sites[site]}//1HOUR/C:00{year}|{fileDate}/'

                    if pname not in pathNames:
                        pathNames.append(pname)
                    
                    tsc = TimeSeriesContainer()
                    tsc.pathname = pname
                    tsc.startDateTime = targetDate.strftime('%d%b%Y %H:%M')
                    tsc.numberValues = group.shape[0]
                    tsc.granularity = 60
                    tsc.units = 'cfs'
                    tsc.type= 'INST-VAL'
                    tsc.interval = 1
                    tsc.values = group.flow.to_list()


                    fid = HecDss.Open(dssOut, version=6)
                    fid.put_ts(tsc)
                    fid.close()
                    del tsc, group
                    gc.collect()

                del data, grouped

                
                lookup[patternYear][returnInterval][fileDate]['pathNames'] = pathNames
                lookup[patternYear][returnInterval][fileDate]['startDate'] = offset.strftime('%d%b%Y %H:%M')

                gc.collect()
                offset += 24

            # process in the determinsic run from YYYY_Event_Scalings
            print('here')

            data = pd.read_excel(
                eventScaling,
                sheet_name = returnInterval,
                skiprows = 7,
                header=None,
                names =['flow'],
                usecols = 'C'
            )
            site = 'FOLC1F'
            pname = f'/{returnInterval}/{site}/{sites[site]}//1HOUR//'

            tsc = TimeSeriesContainer()
            tsc.pathname = pname
            tsc.startDateTime = '20Dec2999 04:00'
            tsc.units = 'cfs'
            tsc.type = 'INST-VAL'
            tsc.interval=1
            tsc.numberValues = data.shape[0]
            tsc.values = data.flow.to_list()

            with HecDss.Open(dssOut) as fid:
                fid.put_ts(tsc)
            del site, pname, tsc, data
            gc.collect()

    with open(rf'{outDir.split(os.sep)[0]}\resSimLookup.json', 'w') as f:
        json.dump(lookup, f, ensure_ascii=False, indent=3)

if __name__ == '__main__':

    ensembleStartYear = 1980
    main(ensembleStartYear)

    # \\spk-netapp2\Hydrology\Studies\SAC-013\Folsom Dam Raise_SOU\2 Data Transfers\Incoming\Agencies\CNRFC\HindCast_Robustness\20221127 MI Scaled Hindcasts 1986 and 1997\forReview