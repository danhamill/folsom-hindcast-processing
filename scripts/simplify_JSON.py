
import json
from utils.folsomSites import sites

lookup = json.load(open(r'outputNoShift3\resSimLookup.json'))

for pattern in lookup.keys():                                     
    scalings = lookup[pattern]                                    
    for scaling in scalings.keys():                               
        forecastDates = scalings[scaling]                         
        for forecastDate in forecastDates.keys(): 
            target = forecastDates[forecastDate]['pathNames'] 
            pathNames = []
            for bpart, cpart in sites.items():
                
                for year in range(1980,2021):
                    
                    pathName = "/%s/%s/%s//1HOUR/C:00%s|%s/" %(scaling, bpart,cpart,year,forecastDate)
                    pathNames.append(pathName)
            pathNames = sorted(pathNames)
            print('here')

            del forecastDates[forecastDate]['pathNames'] 



with open(r'outputNoShift3\resSimLookupNoPath.json', 'w') as f:
    json.dump(lookup, f, ensure_ascii=False, indent=3)
print('here')