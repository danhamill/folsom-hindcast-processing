from glob import glob
import os
import json
import pandas as pd
import numpy as np
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer
from utils.folsomSites import sites, lookbackSites
import gc

def convertUtcToPacific(data: pd.DataFrame) -> pd.DataFrame:
    """
    Function to convert and localize a datetime index from UTC
    to US/Pacific

    Args:
        data (pd.DataFrame): A dataframe with datetime index in UTC

    Returns:
        pd.DataFrame: A dataframe with localized datetime index in Pacific
    """
    data.index = data.index.tz_localize('UTC').tz_convert('US/Pacific')
    data.index = pd.DatetimeIndex(
        [i.replace(tzinfo=None) for i in data.index], 
        name='date'
    )
    return data

def getLookbacks(lookbackWindow: list[str], patternYear: str, 
                 returnInterval: str, fileDates: list[str]) -> pd.DataFrame:
    """
    This function is used to get data from a lookback window. It reads data from a 
    DSS file and stores it in a pandas Dataframe. For each item in the lookback window, 
    it checks for the existence of the file and then reads the data from the file. 
    It then creates a MultiIndex with the columns containing the sites, units, ensemble years and file dates. 
    The values are stored in the Dataframe and then returned.

    Args:
        lookbackWindow (list[str]): A list of strings containing the date range for the lookback window
        patternYear (str):  A string containing the pattern year
        returnInterval (str): A string containing the return interval
        fileDates (list[str]): A list of strings containing the file dates

    Returns:
        pd.Dataframe: An ensemble-like datafame with lookback time series
    """

    lookbackDSssFile =rf'lookbackData\{patternYear}\D{returnInterval}_simulation.dss'
    assert os.path.exists(lookbackDSssFile), 'Cannot find lookback file:'
    
    output = pd.DataFrame()
    for bPart, cPart in lookbackSites.items():

        pname = f'//{bPart}/{cPart}//1HOUR/HC_DETERM-0/'
        
        with HecDss.Open(lookbackDSssFile) as fid:
            ts = fid.read_ts(pname, window=lookbackWindow, trim_missing=False)
            times = np.array(ts.pytimes)
            values = ts.values
            unit = ts.units
            idx = pd.Index(times, name = 'date')
        
        ensembleYears = [i for i in range(1980,2021)]
        sites = [bPart]*len(ensembleYears)
        units = [unit] *len(ensembleYears)

        colIdx=pd.MultiIndex.from_tuples(
                    tuple(zip(sites, units, ensembleYears, fileDates)),  
                    names = ['site','units', 'year', 'fileDate']
                )
        
        tmp = pd.DataFrame(index=idx, columns = colIdx)
        tmp[tmp.columns[0]] = values.copy()
        tmp = tmp.fillna(axis=1, method='ffill')
        output = pd.concat([output, tmp], axis=1)
        del tmp
    gc.collect()
    return output

def main(ensembleStartYear, outDir):

    patterns = glob(r'data\*')
    lookup = {}
    for pattern in patterns[:1]:

        patternYear = pattern.split('\\')[-1].split('_')[0]

        scalings = glob(f'{pattern}\*')
        eventScaling = scalings[0]
        scalings = scalings[11:12]

        lookup[patternYear] = {}
        for scaling in scalings:
            
            returnInterval = scaling.split('\\')[-1]
            lookup[patternYear][returnInterval] = {}

            outDir = rf'{outDir}\{patternYear}'
            os.makedirs(outDir, exist_ok=True)
            dssOut = rf'{outDir}\{patternYear}_{returnInterval}.dss'
            print(f'Currently Processing {dssOut}...')

            hindcastFiles = glob(rf'{scaling}\*hefs*.csv')

            targetDate = pd.Period(year=2999, day=23, month=12, hour=4,  freq='h')
            offset = pd.Period(year=2999, day=23, month=12, hour=4,  freq='h')
            
            print('Currently Processing hefs files...')
            for hindcastFile in hindcastFiles:
                
                fileDate = hindcastFile.split('\\')[-1].split('_')[0]
                lookup[patternYear][returnInterval][fileDate] = {}
                
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

                idxReadCsv = idx[idx.get_level_values(0) != 'DUMMY']
                idxAppend = idx[idx.get_level_values(0) == 'DUMMY']
                
                data = pd.read_csv(
                    hindcastFile, 
                    skiprows=2, 
                    header=None, 
                    names = idxReadCsv, 
                    index_col=0, 
                    parse_dates=True
                )

                data[[idxAppend]] = np.nan
                data = data.fillna(0.0)

                data.columns.names = ['site','tsType', 'year', 'fileDate']

                # Convert UTC to Pacific
                data = convertUtcToPacific(data)

                # get lookback time series using US/Pacific dates
                lookbackWindow = [i.strftime('%d%b%Y %H:%M')
                                             for i in [data.index.min(), data.index.min()+pd.Timedelta(hours=24)]]
                lookback = getLookbacks(lookbackWindow, patternYear, returnInterval, fileDates)

                print('Currently writing ensembles to dss...') 
                # Process ensemble hefs to dss
                data = data.stack(level=[0,1,2,3])
                data.index.names = ['date','site','tsType','year', 'fileDate']
                data = data * 1000
                data = data.loc[data.index.get_level_values('site').isin(sites.keys()),:]

                grouped = data.groupby(['site', 'year'])
                
                pathNames = []
                for (site, year), group in grouped:
                                       
                    group.name = 'flow'
                    group = group.reset_index()

                    pname = f'/{returnInterval}/{site}/{sites[site]}//1HOUR/C:00{year}|{fileDate}/'

                    if pname not in pathNames:
                        pathNames.append(pname)
                    
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

                #============================================
                lookback = lookback.stack(level=[0,1,2,3])
                lookback.index.names = ['date','site','unit','year', 'fileDate']

                grouped = lookback.groupby(['site', 'year'])

                print('Currently writing to lookbacks dss...')          
                
                for (site, year), group in grouped:
                                       
                    group.name = 'flow'
                    group = group.reset_index()

                    pname = f'/{returnInterval}/{site}/{lookbackSites[site]}//1HOUR/C:00{year}|{fileDate}/'

                    if pname not in pathNames:
                        pathNames.append(pname)
                    
                    tsc = TimeSeriesContainer()
                    tsc.pathname = pname
                    tsc.startDateTime = group.date.min().strftime('%d%b%Y %H:%M')
                    tsc.numberValues = group.shape[0]
                    tsc.granularity = 60
                    tsc.units = group.unit.unique()[0]
                    tsc.type= 'INST-VAL'
                    tsc.interval = 1
                    tsc.values = group.flow.to_list()


                    fid = HecDss.Open(dssOut, version=6)
                    fid.put_ts(tsc)
                    fid.close()
                    del tsc, group
                    gc.collect()

                del lookback, grouped



                #==============

                
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
                names =['date','time','flow'],
                usecols = 'A:C'
            )

            dateUTC = pd.to_datetime(data.date.astype(str) + ' '+ data.time.astype(str), format='%m-%d-%Y %H:%M:%S')
            dateLocal = convertUtcToPacific(pd.DataFrame(index=pd.DatetimeIndex(dateUTC)))

            site = 'FOLC1F'
            pname = f'/{returnInterval}/{site}/{sites[site]}//1HOUR//'

            tsc = TimeSeriesContainer()
            tsc.pathname = pname
            tsc.startDateTime = dateLocal.index.min().strftime('%d%b%Y %H:%M')
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
    outDir = rf'outputNormalDate3'
    ensembleStartYear = 1980
    main(ensembleStartYear, outDir)

    # \\spk-netapp2\Hydrology\Studies\SAC-013\Folsom Dam Raise_SOU\2 Data Transfers\Incoming\Agencies\CNRFC\HindCast_Robustness\20221127 MI Scaled Hindcasts 1986 and 1997\forReview