from datetime import datetime 

def getStartDates(pattern):
    return {
        '1986': {
            '1986020112': '01Feb1986 04:00',
            '1986020212': '02Feb1986 04:00',
            '1986020312': '03Feb1986 04:00',
            '1986020412': '04Feb1986 04:00',
            '1986020512': '05Feb1986 04:00',
            '1986020612': '06Feb1986 04:00',
            '1986020712': '07Feb1986 04:00',
            '1986020812': '08Feb1986 04:00',
            '1986020912': '09Feb1986 04:00',
            '1986021012': '10Feb1986 04:00',
            '1986021112': '11Feb1986 04:00',
            '1986021212': '12Feb1986 04:00',
            '1986021312': '13Feb1986 04:00',
            '1986021412': '14Feb1986 04:00',
            '1986021512': '15Feb1986 04:00',
            '1986021612': '16Feb1986 04:00',
            '1986021712': '17Feb1986 04:00',
            '1986021812': '18Feb1986 04:00',
            '1986021912': '19Feb1986 04:00',
            '1986022012': '20Feb1986 04:00',
            '1986022112': '21Feb1986 04:00',
            '1986022212': '22Feb1986 04:00',
            '1986022312': '23Feb1986 04:00',
            '1986022412': '24Feb1986 04:00',
            '1986022512': '25Feb1986 04:00',
            '1986022612': '26Feb1986 04:00',
            '1986022712': '27Feb1986 04:00',
            '1986022812': '28Feb1986 04:00'
        },
        '1997': {
            '1996121512': '15Dec1996 04:00',
             '1996121612': '16Dec1996 04:00',
             '1996121712': '17Dec1996 04:00',
             '1996121812': '18Dec1996 04:00',
             '1996121912': '19Dec1996 04:00',
             '1996122012': '20Dec1996 04:00',
             '1996122112': '21Dec1996 04:00',
             '1996122212': '22Dec1996 04:00',
             '1996122312': '23Dec1996 04:00',
             '1996122412': '24Dec1996 04:00',
             '1996122512': '25Dec1996 04:00',
             '1996122612': '26Dec1996 04:00',
             '1996122712': '27Dec1996 04:00',
             '1996122812': '28Dec1996 04:00',
             '1996122912': '29Dec1996 04:00',
             '1996123012': '30Dec1996 04:00',
             '1996123112': '31Dec1996 04:00',
             '1997010112': '01Jan1997 04:00',
             '1997010212': '02Jan1997 04:00',
             '1997010312': '03Jan1997 04:00',
             '1997010412': '04Jan1997 04:00',
             '1997010512': '05Jan1997 04:00',
             '1997010612': '06Jan1997 04:00',
             '1997010712': '07Jan1997 04:00',
             '1997010812': '08Jan1997 04:00',
             '1997010912': '09Jan1997 04:00',
             '1997011012': '10Jan1997 04:00',
             '1997011112': '11Jan1997 04:00',
             '1997011212': '12Jan1997 04:00',
             '1997011312': '13Jan1997 04:00',
             '1997011412': '14Jan1997 04:00',
             '1997011512': '15Jan1997 04:00'
        }
    }[pattern]

targetTime = datetime(2999,12,23,4)

for pattern in ['1986','1997']:

    startDates = getStartDates(pattern)

    for forecastDate, normalDate in startDates.items():

        forecastDate = datetime.strptime(forecastDate, '%Y%m%d%H')
        normalDate = datetime.strptime(normalDate, '%d%b%Y %H:%M')

        timeDelta = targetTime - normalDate
        print('here')
