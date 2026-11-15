import pandas as pd

df=pd.read_csv('Dataset/ai4i2020.csv')

columns = [
    'Air temperature [K]',
    'Rotational speed [rpm]',
    'Torque [Nm]',
    'Tool wear [min]'
]

def detect_iqr_outliers(df, columns):
    results ={}
    for col in columns:

        q1=df[col].quantile(0.25)
        q3=df[col].quantile(0.75)

        iqr=q3-q1
        lower_bound=q1-1.5*iqr
        upper_bound=q3+1.5*iqr
        outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col].tolist()
        results[col] = {
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'outliersCount': len(outliers),
            'outliers': outliers
        }
    return results
results = detect_iqr_outliers(df, columns)
for col, res in results.items():
    print(col,res)

def detect_zscore_outliers(df, columns):
    results ={}
    for col in columns:
        mean = df[col].mean()
        std = df[col].std()
        z_scores = (df[col] - mean) / std
        outliers = df[(z_scores < -3) | (z_scores > 3)][col].tolist()
        results[col] = {
            'mean': mean,
            'std': std,
            'outliersCount': len(outliers),
            'outliers': outliers
        }
    return results
results = detect_zscore_outliers(df, columns)
for col, res in results.items():
    print(col,res)
