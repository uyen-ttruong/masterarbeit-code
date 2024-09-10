import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Đọc dữ liệu
df = pd.read_csv('immobilien_analyse_ergebnisse.csv', delimiter=',', decimal=',')

# Hiển thị thống kê mô tả
print("Thống kê mô tả của cột Immobilienschaden:")
print(df['Immobilienschaden'].describe())

# Đếm số lượng giá trị 0
zero_count = (df['Immobilienschaden'] == 0).sum()
non_zero_count = (df['Immobilienschaden'] > 0).sum()

print(f"\nSố lượng giá trị 0: {zero_count}")
print(f"Số lượng giá trị khác 0: {non_zero_count}")

# Tạo bins cho giá trị khác 0
non_zero_data = df[df['Immobilienschaden'] > 0]['Immobilienschaden']

if len(non_zero_data) > 0:
    max_value = non_zero_data.max()
    bins = [0, 1, 10, 100, 1000, 10000, max_value]
    labels = ['0', '1-10', '11-100', '101-1000', '1001-10000', f'10001-{max_value:.0f}']

    # Phân loại dữ liệu vào các bin
    df['damage_category'] = pd.cut(df['Immobilienschaden'], bins=bins, labels=labels, include_lowest=True)

    # Hiển thị phân phối của các bin
    print("\nPhân phối của các khoảng giá trị:")
    damage_counts = df['damage_category'].value_counts().sort_index()
    print(damage_counts)

    # Tính phần trăm cho mỗi bin
    damage_percentage = damage_counts / len(df) * 100

    print("\nPhần trăm cho mỗi khoảng giá trị:")
    for category, percentage in damage_percentage.items():
        print(f"{category}: {percentage:.2f}%")

    # Vẽ biểu đồ cột
    plt.figure(figsize=(12, 6))
    damage_counts.plot(kind='bar')
    plt.title('Phân phối Immobilienschaden')
    plt.xlabel('Khoảng giá trị')
    plt.ylabel('Số lượng')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('immobilienschaden_distribution_adjusted.png')
    print("\nBiểu đồ phân phối đã được lưu dưới dạng 'immobilienschaden_distribution_adjusted.png'")

    # Vẽ histogram cho giá trị khác 0 (sử dụng thang logarit)
    plt.figure(figsize=(12, 6))
    plt.hist(non_zero_data, bins=50, edgecolor='black')
    plt.xscale('log')
    plt.title('Histogram của Immobilienschaden khác 0 (Thang logarit)')
    plt.xlabel('Giá trị Immobilienschaden (log scale)')
    plt.ylabel('Tần suất')
    plt.savefig('immobilienschaden_histogram_non_zero_log.png')
    print("\nHistogram cho giá trị khác 0 đã được lưu dưới dạng 'immobilienschaden_histogram_non_zero_log.png'")

else:
    print("Không có giá trị nào khác 0 trong dữ liệu.")

# Hiển thị thông tin về các giá trị ngoại lệ (chỉ cho giá trị khác 0)
if len(non_zero_data) > 0:
    print("\nThông tin về các giá trị ngoại lệ (chỉ cho giá trị khác 0):")
    Q1 = non_zero_data.quantile(0.25)
    Q3 = non_zero_data.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = non_zero_data[(non_zero_data < lower_bound) | (non_zero_data > upper_bound)]
    print(f"Số lượng giá trị ngoại lệ: {len(outliers)}")
    if len(outliers) > 0:
        print(f"Giá trị nhỏ nhất của outlier: {outliers.min()}")
        print(f"Giá trị lớn nhất của outlier: {outliers.max()}")
    else:
        print("Không có giá trị ngoại lệ.")
else:
    print("Không thể tính toán giá trị ngoại lệ vì không có giá trị nào khác 0.")