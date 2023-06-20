from pydsstools.heclib.dss import HecDss
import pandas as pd
import numpy as np
import os


def getPathNamesForIssueDate(dssFile, fPartPattern):
    with HecDss.Open(dssFile) as fid:
        
        plist = fid.getPathnameList(f'/*/FOLSOM/FLOW-IN/*/*/*|{fPartPattern}/')

    output = []
    for i in plist:
        parts = i.split('/')
        if parts not in output:
            output.append(parts) 

    res = pd.DataFrame(data = output, columns = ['start','PartA','PartB','PartC','PartD', 'PartE','PartF','end'])

    output = {}
    for scaling, group in res.groupby('PartA'):

        group = group.apply(
            lambda row: "/".join(["", row.PartA, row.PartB, row.PartC, row.PartD, row.PartE, row.PartF, ""]),
            axis=1,
        ).to_list()

        output.update({scaling:group})


    return output

def getIssueDates(pattern):
    return {
        '1986': [
            '1986020112',
            '1986020212',
            '1986020312',
            '1986020412',
            '1986020512',
            '1986020612',
            '1986020712',
            '1986020812',
            '1986020912',
            '1986021012',
            '1986021112',
            '1986021212',
            '1986021312',
            '1986021412',
            '1986021512',
            '1986021612',
            '1986021712',
            '1986021812',
            '1986021912',
            '1986022012',
            '1986022112',
            '1986022212',
            '1986022312',
            '1986022412',
            '1986022512',
            '1986022612',
            '1986022712',
            '1986022812'
        ],
        '1997': [
            '1996121512',
            '1996121612',
            '1996121712',
            '1996121812',
            '1996121912',
            '1996122012',
            '1996122112',
            '1996122212',
            '1996122312',
            '1996122412',
            '1996122512',
            '1996122612',
            '1996122712',
            '1996122812',
            '1996122912',
            '1996123012',
            '1996123112',
            '1997010112',
            '1997010212',
            '1997010312',
            '1997010412',
            '1997010512',
            '1997010612',
            '1997010712',
            '1997010812',
            '1997010912',
            '1997011012',
            '1997011112',
            '1997011212',
            '1997011312',
            '1997011412',
            '1997011512'
        ]
    }[pattern]

if __name__ == '__main__':
    dataDirs = {
    '1986': r'C:\workspace\git_clones\folsom-hindcast-processing\outputNormalDate4\1986_results.dss',
    '1997': r'C:\workspace\git_clones\folsom-hindcast-processing\outputNormalDate4\1997_results.dss',
    }

    outputDir = r'outputRegulated'

    timeSeriesLength = 361
    for pattern, dssFile in dataDirs.items():

        for issueDate in getIssueDates(pattern):
            
            pnames = getPathNamesForIssueDate(dssFile, issueDate)

            for scaling, dssPaths in pnames.items():

                output = pd.DataFrame(columns = ['times'] +list(range(1980, 2021)))

                # Read in Ensemble data from DSS Collection
                for member in range(1980,2021):
                    
                    if output.times.empty:
                        doTimes = True
                    else:
                        doTimes = False

                    subPathNames = [i for i in dssPaths if f'C:00{member}|' in i.split('/')[-2]]
                    
                    # Single Block
                    if len(subPathNames) == 1:

                        with HecDss.Open(dssFile) as fid:
                            ts = fid.read_ts(subPathNames[0])
                            values = ts.values
                            
                        if doTimes:
                           times = ts.pytimes
                           times = [i.strftime('%Y-%m-%d %H:%M:%S') for i in times]
                           output.loc[:,'times'] = times     
                        output.loc[:,member] = values.copy()
                    else:


                        outputValues = []
                        with HecDss.Open(dssFile) as fid:
                            ts = fid.read_ts(subPathNames[0])
                            values = ts.values
                            if doTimes: 
                                timesFirstBlock = ts.pytimes
                            valuesFirstBlock = values.copy()
                        del values
                        with HecDss.Open(dssFile) as fid:
                            ts = fid.read_ts(subPathNames[1])
                            values = ts.values
                            if doTimes:
                                timesSecondBlock = ts.pytimes
                            valuesSecondBlock = values.copy()
                        mergeValues = np.append(valuesFirstBlock, valuesSecondBlock)
                        assert len(mergeValues) == timeSeriesLength, 'missing data during DSS read'

                        if doTimes:
                            mergeTimes = timesFirstBlock+timesSecondBlock
                            assert len(mergeTimes) == timeSeriesLength, 'missing data during dss read'

                            mergeTimes = [i.strftime('%Y-%m-%d %H:%M:%S') for i in mergeTimes]
                            output.loc[:,'times'] = mergeTimes
                        output.loc[:,member] = mergeValues.copy()



                        print('here')
                # convert cfs to kfcs
                output.loc[:, output.columns[1:]] = output.loc[:, output.columns[1:]].div(1000)
                
                header = pd.DataFrame(
                    columns = ['times'] + list(range(1980,2021)), 
                    data = [['GMT'] + ['FOLSOM']*len(range(1980,2021)),
                            ['']    + ['SQIN']*len(range(1980,2021))]
                )
                
                output = pd.concat([header, output])

                outputFileSubDirectory = fr'{outputDir}\{pattern}\{scaling}'
                os.makedirs(outputFileSubDirectory, exist_ok=True)
                output.to_csv(rf'{outputFileSubDirectory}\{issueDate}_american_hefs_csv_hourly.csv', index=False, header=False)

                print('here')
                



