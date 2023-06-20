from glob import glob
from unittest import skip
import pandas as pd
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer
from utils.folsomSites import sites
import gc

def main(ensembleStartYear):

    patterns = glob(r'data\hefs\hourly\*')

    for pattern in patterns:

        patternYear = pattern.split('\\')[-1]

        dssOut = rf'output\{patternYear}_hefs_hourly.dss'

        print(f'Currently Processing {dssOut}...')

        zipFiles = glob(rf'{pattern}\*.zip')

        data = pd.DataFrame()

        print(f'Currently Processing hefs files...')
        for zFile in zipFiles:

            fileDate = zFile.split('\\')[-1].split('_')[0]

            csvSites  = pd.read_csv(
                zFile, 
                header = None, 
                nrows=1
            ).iloc[:,1:].stack().to_list()

            csvVariables = pd.read_csv(
                zFile, 
                header = None, 
                nrows=1, 
                skiprows=1
            ).iloc[:,1:].stack().to_list()

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
                zFile, 
                skiprows=2, 
                header=None, 
                names = idx, 
                index_col=0, 
                parse_dates=True
            )

            data.columns.names = ['site','tsType', 'year', 'fileDate']

            data.index = data.index.tz_localize('UTC').tz_convert('US/Pacific')

            data.index = pd.DatetimeIndex(
                [i.replace(tzinfo=None) for i in data.index], 
                name='date'
            )

            # df = pd.concat(
            #     [df, data], axis=0
            # )



            data = data.stack(level=[0,1,2,3])
            data.index.names = ['date','site','tsType','year', 'fileDate']
            data = data * 1000
            data = data.loc[data.index.get_level_values('site').isin(sites.keys()),:]

            grouped = data.groupby(['site', 'year', 'fileDate', 'tsType'])

            print('Currently Writing to dss...')

            for (site, year, fileDate, tsType), group in grouped:
                

                group.name = 'flow'
                group = group.reset_index()

                pname = f'/AMERICAN/{site}/{sites[site]}//1HOUR/C:00{year}|{fileDate}|{tsType}/'
                
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
                del tsc, group
                gc.collect()

            del data, grouped

            gc.collect()


if __name__ == '__main__':

    ensembleStartYear = 1960
    main(ensembleStartYear)