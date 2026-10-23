
# install pandas before run 
# Write in Trimnal " pip install pandas" 

import pandas as pd
from pandas import Series , DataFrame

Machine_Data = pd.read_csv('Dataset/ai4i2020.csv') 
# يا رب نفهم و ياريت نقرا التعليقات و نقراالريد مى بعد اذنكم عشان لو حصل مشكله انا ماليش دعوة انا قولت مرتين 
print(Machine_Data.head())