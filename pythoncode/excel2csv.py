import pandas as pd
import locale

# Đặt locale
locale.setlocale(locale.LC_NUMERIC, 'de_DE')

# Đọc dữ liệu
df = pd.read_csv('hypotest.csv', delimiter=';')

print(df.dtypes)

# In thống kê mô tả cho cột Schadensfaktor
print("\nThống kê mô tả cho Schadensfaktor:")
print(df["Ueberschwemmungstiefe"].describe())

#df.to_csv('hypotest.csv', index=False, decimal=',', sep=';')