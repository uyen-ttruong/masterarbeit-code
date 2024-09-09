import pandas as pd
import numpy as np

# Đọc file CSV
df = pd.read_csv('testepcm2_updated.csv', sep=';', decimal=',')

# Tạo giá trị LtV
def generate_ltv():
    categories = ['10-60', '60-70', '70-80', '80-90', '90-100', '100-110']
    probabilities = [0.392, 0.150, 0.164, 0.102, 0.082, 0.110]
    category = np.random.choice(categories, p=probabilities)
    low, high = map(int, category.split('-'))
    return np.random.uniform(max(10, low), high) / 100  # Đảm bảo LTV tối thiểu là 10%

df['aktuelles_LtV'] = np.array([generate_ltv() for _ in range(len(df))])

# Tính darlehenbetrag ban đầu
target_mean = 163700
df['darlehenbetrag'] = np.random.lognormal(mean=np.log(target_mean), sigma=0.5, size=len(df))

# Tính aktueller_immobilienwert dựa trên darlehenbetrag và aktuelles_LtV
df['aktueller_immobilienwert'] = df['darlehenbetrag'] / df['aktuelles_LtV']

# Tính wohnflaeche dựa trên aktueller_immobilienwert và Quadratmeterpreise
df['wohnflaeche'] = df['aktueller_immobilienwert'] / df['Quadratmeterpreise']

# Áp dụng ràng buộc cho wohnflaeche (ít nhất 60m2)
df['wohnflaeche'] = np.maximum(df['wohnflaeche'], 60)

# Cập nhật lại aktueller_immobilienwert và darlehenbetrag sau khi điều chỉnh wohnflaeche
df['aktueller_immobilienwert'] = df['wohnflaeche'] * df['Quadratmeterpreise']
df['darlehenbetrag'] = df['aktueller_immobilienwert'] * df['aktuelles_LtV']

# Điều chỉnh darlehenbetrag để đạt được giá trị trung bình chính xác
current_mean = df['darlehenbetrag'].mean()
adjustment_factor = target_mean / current_mean
df['darlehenbetrag'] *= adjustment_factor

# Cập nhật lại aktuelles_LtV sau khi điều chỉnh darlehenbetrag
df['aktuelles_LtV'] = df['darlehenbetrag'] / df['aktueller_immobilienwert']

# Làm tròn các giá trị số
df['wohnflaeche'] = df['wohnflaeche'].round(2)
df['aktueller_immobilienwert'] = df['aktueller_immobilienwert'].round(2)
df['darlehenbetrag'] = df['darlehenbetrag'].round(2)
df['aktuelles_LtV'] = df['aktuelles_LtV'].round(4)  # Làm tròn đến 4 chữ số thập phân

# Lưu DataFrame đã cập nhật vào file CSV mới
df.to_csv('testepcm2ltv_adjusted.csv', sep=';', index=False, decimal=',')

print("File CSV đã được cập nhật và lưu dưới tên 'testepcm2ltv_adjusted.csv'")

# Hiển thị thông tin thống kê về cột darlehenbetrag
print("\nThông tin thống kê về cột darlehenbetrag:")
print(df['darlehenbetrag'].describe())

print(f"\nGiá trị trung bình (mean) của darlehenbetrag: {df['darlehenbetrag'].mean():.2f}")
print(f"Giá trị trung vị (median) của darlehenbetrag: {df['darlehenbetrag'].median():.2f}")
print(f"Độ lệch chuẩn của darlehenbetrag: {df['darlehenbetrag'].std():.2f}")

# Hiển thị phân phối của darlehenbetrag
print("\nPhân phối của darlehenbetrag:")
bins = [0, 100000, 200000, 300000, 400000, 500000, float('inf')]
labels = ['0-100k', '100k-200k', '200k-300k', '300k-400k', '400k-500k', '500k+']
df['darlehenbetrag_category'] = pd.cut(df['darlehenbetrag'], bins=bins, labels=labels)
print(df['darlehenbetrag_category'].value_counts(normalize=True).sort_index())

# Kiểm tra phân phối LtV số
ltv_numeric_distribution = pd.cut(df['aktuelles_LtV'],
                                  bins=[0, 0.6, 0.7, 0.8, 0.9, 1.0, float('inf')],
                                  labels=['10-60%', '60-70%', '70-80%', '80-90%', '90-100%', '> 100%'])
print("\nPhân phối LtV số thực tế:")
print(ltv_numeric_distribution.value_counts(normalize=True).sort_index())

# In thông tin về các cột
print("\nThông tin về các cột:")
print(df[['wohnflaeche', 'aktueller_immobilienwert', 'aktuelles_LtV', 'Quadratmeterpreise', 'darlehenbetrag']].describe())

# Kiểm tra phân phối của wohnflaeche
print("\nPhân phối của wohnflaeche:")
wohnflaeche_bins = [60, 100, 150, 200, np.inf]
wohnflaeche_labels = ['60-100', '100-150', '150-200', '200+']
df['wohnflaeche_category'] = pd.cut(df['wohnflaeche'], bins=wohnflaeche_bins, labels=wohnflaeche_labels)
print(df['wohnflaeche_category'].value_counts(normalize=True).sort_index())