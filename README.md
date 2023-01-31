# folsom-hindcast-processing
utility scripts to convert CNFRC hindcast to HecDSS format

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
```
