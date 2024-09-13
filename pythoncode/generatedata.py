import pandas as pd
import numpy as np

# Đọc file CSV
df = pd.read_csv("C:\Users\uyen truong\Downloads\hypothekendaten4_updated.csv", delimiter=';')

# Danh sách các cột số cần xử lý
numeric_columns = ['Quadratmeterpreise', 'wohnflaeche', 'AEP', 'aktueller_immobilienwert', 'aktuelles_LtV', 'darlehenbetrag']

# Chuyển đổi kiểu dữ liệu sang số và xử lý lỗi
for col in numeric_columns:
    if df[col].dtype == 'object':
        df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')
    else:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# 1. Điều chỉnh 'wohnflaeche' để có giá trị trung bình trong khoảng 100-150
def adjust_wohnflaeche(x):
    if pd.isna(x) or x < 80:
        return np.random.uniform(80, 100)
    elif x > 250:
        return np.random.uniform(200, 250)
    return x

df['wohnflaeche'] = df['wohnflaeche'].apply(adjust_wohnflaeche)

target_avg_wohnflaeche = np.random.uniform(100, 150)
current_avg_wohnflaeche = df['wohnflaeche'].mean()

df['wohnflaeche'] = df['wohnflaeche'] * (target_avg_wohnflaeche / current_avg_wohnflaeche)

# 2. Điều chỉnh 'darlehenbetrag' để có giá trị trung bình chính xác 163700
target_avg_darlehenbetrag = 163700

# Tính 'darlehenbetrag' bằng công thức: LTV * Immobilienwert
df['darlehenbetrag'] = df['aktuelles_LtV'] * df['aktueller_immobilienwert']

# Đảm bảo 'darlehenbetrag' có giá trị trung bình là 163700
df['darlehenbetrag'] = df['darlehenbetrag'] * (target_avg_darlehenbetrag / df['darlehenbetrag'].mean())

# 3. Điều chỉnh 'aktuelles_LtV' với giới hạn phân phối theo yêu cầu
def adjust_ltv(x):
    if pd.isna(x) or x < 0.4:
        return np.random.uniform(0.4, 0.5)
    elif 0.4 <= x <= 0.6:
        return np.random.uniform(0.4, 0.6)
    elif 0.6 < x <= 0.7:
        return np.random.uniform(0.6, 0.7)
    elif 0.7 < x <= 0.8:
        return np.random.uniform(0.7, 0.8)
    elif 0.8 < x <= 0.9:
        return np.random.uniform(0.8, 0.9)
    elif 0.9 < x <= 1.0:
        return np.random.uniform(0.9, 1.0)
    else:
        return np.random.uniform(1.0, 1.1)

df['aktuelles_LtV'] = df['aktuelles_LtV'].apply(adjust_ltv)

# Kiểm tra phân phối LTV sau điều chỉnh
ltv_distribution = [
    (df['aktuelles_LtV'] <= 0.6).mean(),
    ((df['aktuelles_LtV'] > 0.6) & (df['aktuelles_LtV'] <= 0.7)).mean(),
    ((df['aktuelles_LtV'] > 0.7) & (df['aktuelles_LtV'] <= 0.8)).mean(),
    ((df['aktuelles_LtV'] > 0.8) & (df['aktuelles_LtV'] <= 0.9)).mean(),
    ((df['aktuelles_LtV'] > 0.9) & (df['aktuelles_LtV'] <= 1.0)).mean(),
    (df['aktuelles_LtV'] > 1.0).mean()
]

# Cập nhật giá trị 'aktueller_immobilienwert' theo công thức 'wohnflaeche' * 'Quadratmeterpreise'
df['aktueller_immobilienwert'] = df['wohnflaeche'] * df['Quadratmeterpreise']

# Tạo thống kê mô tả cho các cột số
desc_stats = df[numeric_columns].describe()

# In thống kê mô tả
print("\nThống kê mô tả cho các cột số:")
print(desc_stats.round(2))

# Kiểm tra giá trị trung bình của 'wohnflaeche'
print(f"\nGiá trị trung bình của wohnflaeche: {df['wohnflaeche'].mean():.2f}")
print(f"Giá trị tối thiểu của wohnflaeche: {df['wohnflaeche'].min():.2f}")
print(f"Giá trị tối đa của wohnflaeche: {df['wohnflaeche'].max():.2f}")

# Kiểm tra giá trị trung bình của 'darlehenbetrag'
print(f"Giá trị trung bình của darlehenbetrag: {df['darlehenbetrag'].mean():.2f}")

# Kiểm tra giá trị LTV nhỏ nhất và lớn nhất
print(f"Giá trị LTV nhỏ nhất: {df['aktuelles_LtV'].min():.2f}")
print(f"Giá trị LTV lớn nhất: {df['aktuelles_LtV'].max():.2f}")

# Lưu kết quả vào file CSV mới
df.to_csv('data/hypothekendaten4_cleaned.csv', index=False, sep=';')

print("\nĐã xử lý và lưu dữ liệu vào file 'hypothekendaten4_cleaned.csv'")
