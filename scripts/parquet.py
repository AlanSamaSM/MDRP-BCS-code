import pandas as pd

df = pd.read_parquet("delivery_jl.parquet")   # tu ruta
print(df.head())
print(df.info())
