import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Đọc dữ liệu
df = pd.read_csv('data/hypothekendaten2.csv', delimiter=';')

# Hàm chuyển đổi linh hoạt
def flexible_numeric_conversion(series):
    if pd.api.types.is_numeric_dtype(series):
        return series
    else:
        return pd.to_numeric(series.str.replace(',', '.'), errors='coerce')

# Chuyển đổi các cột sang dạng số
numeric_columns = ['aktuelles_LtV', 'darlehenbetrag', 'aktueller_immobilienwert', 'Schadensfaktor', 'AEP']
for col in numeric_columns:
    df[col] = flexible_numeric_conversion(df[col])

# In thông tin về các cột số sau khi chuyển đổi
for col in numeric_columns:
    print(f"\nThông tin về cột '{col}':")
    print(df[col].describe())

