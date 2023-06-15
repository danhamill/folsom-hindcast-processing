# folsom-hindcast-processing
utility scripts to convert CNFRC hindcast to HecDSS format

## nomenclature

- normal dates — refers to time series in US/Pacific
- hefs dates — refers to time series in UTC
- simulation dates — refers to time series in 2999/3000

## Data directory 

To use these scripts, you need to have the data directory organized in a particular way.  It is assumed the `1986_scalings` and `1997_scalings` data folders from CNFRC are provided in the structure below.  Thee `YYYY_event_scalings.xls` files should be nested in the appropriate `YYYY_scalings` folder.
```cmd
├───data
│   ├───1986_scalings
│   │   ├───1986_event_scalings.xls
│   │   ├───200
│   │   ├───NNN <- Discontitnuity here
│   │   └───500
│   └───1997_scalings
│       ├───1997_event_scalings.xls
│       ├───200
│       └───NNN <- Discontitnuity here
│       └───500
├───lookbackData
│   └───1986
│           D200_simulation.dss <- This is from ResSim ran over simulation dates
│           D200_simulation_normalDate.dss <- this is the same data converted to normalDates
│           DNNN_simulation.dss <- Discontitnuity here
│           DNN_simulation_normalDate.dss <- Discontitnuity here
│           D500_simulation.dss
│           D500_simulation_normalDate.dss
```
