import pandas as pd
import matplotlib.pyplot as plt
import os
import json
partitions = [0,1,2,3]
months = ["January", "February", "March"]
# iter through and try to read partition-N.json, json might not exist
month_data = {}
for partition in partitions:
    path = f"/files/partition-{partition}.json" 
    if os.path.isfile(path):
        # read file
        # file should be dict with partition, offset, [months] as keys
        with open(path) as f:
            data = json.load(f) # dict with keys = (offest, partition, months[january, february, ... , December])
            for month in months:
                if month in data.keys():
                    month_data[month] = (data[month]) # should be years : {...} 
print(month_data)
# find avg for latest recorded year for January, February, March
# month_data[month] conv keys to ints, find greatest key, use that to grab (avg)
month_year_avg = {}
for month in months:
    max_year = str(max(list(map(int, month_data[month].keys()))))
    key_name = f"{month}-{max_year}"
    month_year_avg[key_name] = month_data[month][max_year]["avg"]
print(month_year_avg)
month_series = pd.Series(month_year_avg)

fig, ax = plt.subplots()
month_series.plot.bar(ax=ax)
ax.set_ylabel('Avg. Max Temperature')
plt.tight_layout()
plt.savefig("/files/month.svg")
