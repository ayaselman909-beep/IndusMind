
# install pandas before run 
# Write in Trimnal " pip install pandas" 

import pandas as pd
from pandas import Series , DataFrame

Machine_Data = pd.read_csv('Dataset/ai4i2020.csv') 

print(Machine_Data.head())