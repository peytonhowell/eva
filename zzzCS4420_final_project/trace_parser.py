import csv
import numpy as np
import pandas as pd

data = pd.read_csv('trace.csv', header=None)

# indices_to_remove = []
# repeat_dict = dict()

# print(data.shape)

# for index, row in data.iterrows():
#     if row[1] == False:
#         if row[2] in repeat_dict:
#             indices_to_remove.append(index)
#             repeat_dict[row[2]] = index
#         else:
#             repeat_dict[row[2]] = index
# data.drop(indices_to_remove, axis = 0, inplace=True)
# data.to_csv('ftrace_newVideo.csv', index=False, header=False, mode='a')


repeat_dict = dict()
indices_to_remove = []
frame_ct = dict
for index, row in data.iterrows():
    if row[2] not in repeat_dict:
        repeat_dict[row[2]] = 0
    if row[1]:
        repeat_dict[row[2]] += 1
    else:
        repeat_dict[row[2]] -=1
    if (row[1] and repeat_dict[row[2]] == 1) or (not row[1] and repeat_dict[row[2]] == 0):
        pass
    else:
        indices_to_remove.append(index)

data.drop(indices_to_remove, axis = 0, inplace=True)
data.to_csv('ftrace_udf.csv', index=False, header=False, mode='a')


