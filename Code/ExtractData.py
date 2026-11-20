from data_loader import load_dataset

Machine_Data = load_dataset()

print("first 5 recourds: ", Machine_Data.head())

print("\nDataset shape:", Machine_Data.shape)

print("\nDataset info:", Machine_Data.info())

print("\nDataset Colmns:", Machine_Data.columns.tolist())