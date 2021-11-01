import csv
import numpy as np
import pandas as pd

data = pd.read_csv('trace4.csv', header=None)

repeat_dict = dict()
indices_to_remove = []
print(data.shape)

for index, row in data.iterrows():
    if row[1] == False:
        if row[2] in repeat_dict:
            indices_to_remove.append(index)
            repeat_dict[row[2]] = index
        else:
            repeat_dict[row[2]] = index
data.drop(indices_to_remove, axis = 0, inplace=True)
print(data.shape)
# print(data)
data.to_csv('overall_trace.csv', index=False, header=False, mode='a')