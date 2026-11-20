from data_loader import load_dataset

df=load_dataset()

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
        outliers = []

        for idx, row in df[(df[col] < lower_bound) | (df[col] > upper_bound)].iterrows():

            outliers.append({
                "UDI": int(row["UDI"]),
                "value": round(float(row[col]), 2)
            })
            
        results[col] = {
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'outliersCount': len(outliers),
            'outliers': outliers
        }
    return results
results = detect_iqr_outliers(df, columns)
for col, res in results.items():
    print(f"\nFeature: {col}")
    print(f"Lower Bound: {res['lower_bound']:.2f}")
    print(f"Upper Bound: {res['upper_bound']:.2f}")
    print(f"Outliers Count: {res['outliersCount']}")
    print("Outliers:")
    for item in res['outliers'][:5]:
        print(item)
def detect_zscore_outliers(df, columns):
    results ={}
    for col in columns:
        mean = df[col].mean()
        std = df[col].std()
        z_scores = (df[col] - mean) / std
        outliers =[]
        for idx, row in df[(z_scores < -3) | (z_scores > 3)].iterrows():
        
            outliers.append({
                "UDI": int(row["UDI"]),
                "value": round(float(row[col]), 2)
            })
          
        results[col] = {
            'mean': mean,
            'std': std,
            'outliersCount': len(outliers),
            'outliers': outliers
        }
    return results
results = detect_zscore_outliers(df, columns)
for col, res in results.items():
    print(f"\nFeature: {col}")
    print(f"Mean: {res['mean']:.2f}")
    print(f"Std: {res['std']:.2f}")
    print(f"Outliers Count: {res['outliersCount']}")
    print("Outliers:")
    for item in res['outliers'][:5]:
        print(item)
