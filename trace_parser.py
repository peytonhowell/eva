import csv
import numpy as np
import pandas as pd

data = pd.read_csv('trace.csv')

repeat_dict = dict()
indices_to_remove = []
print(data.shape)

for index, row in data.iterrows():
    if row[1] == False:
        print(row)
        print(index)
        if row[2] in repeat_dict:
            indices_to_remove.append(repeat_dict[row[2]])
            repeat_dict[row[2]] = index
        else:
            repeat_dict[row[2]] = index
print(indices_to_remove)
data.drop(indices_to_remove, axis = 0, inplace=True)
print(data.shape)

data.to_csv('new_trace.csv')