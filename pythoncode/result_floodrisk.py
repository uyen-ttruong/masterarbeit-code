import pandas as pd
import matplotlib.pyplot as plt

# Đọc dữ liệu
df = pd.read_csv('data\hypothekendaten_final_with_statistics.csv', delimiter=';')

# Hàm chuyển đổi linh hoạt
def flexible_numeric_conversion(series):
    if pd.api.types.is_numeric_dtype(series):
        return series
    else:
        return pd.to_numeric(series.str.replace(',', '.'), errors='coerce')

# Chuyển đổi các cột sang dạng số
numeric_columns = ['aktuelles_LtV', 'darlehenbetrag', 'aktueller_immobilienwert', 'Schadensfaktor', 'AEP', 'Risikogewicht']
for col in numeric_columns:
    if col in df.columns:
        df[col] = flexible_numeric_conversion(df[col])

# Lọc các hàng có 'Schadensfaktor' > 0 và loại bỏ NaN
df = df[df['Schadensfaktor'] > 0].dropna(subset=numeric_columns)

# Hàm tính toán các giá trị mới với debug
def calculate_values_debug(row):
    aktueller_immobilienwert = row['aktueller_immobilienwert']
    schadenfaktor = row['Schadensfaktor']
    darlehenbetrag = row['darlehenbetrag']
    
    immobilienschaden = aktueller_immobilienwert * schadenfaktor
    new_immobilienwert = aktueller_immobilienwert - immobilienschaden
    new_LtV = darlehenbetrag / new_immobilienwert if new_immobilienwert > 0 else float('inf')
    
    print(f"Debug for row:")
    print(f"  Aktueller Immobilienwert: {aktueller_immobilienwert}")
    print(f"  Schadenfaktor: {schadenfaktor}")
    print(f"  Darlehenbetrag: {darlehenbetrag}")
    print(f"  Immobilienschaden: {immobilienschaden}")
    print(f"  New Immobilienwert: {new_immobilienwert}")
    print(f"  Old LtV: {row['aktuelles_LtV']}")
    print(f"  New LtV: {new_LtV}")
    print("--------------------")
    
    return pd.Series({
        'Neuer Immobilienwert': new_immobilienwert,
        'Neue LtV': new_LtV
    })

# Áp dụng tính toán và kết hợp kết quả
df_results = pd.concat([df, df.apply(calculate_values_debug, axis=1)], axis=1)

# In thông tin tổng quan
print("\nOverview:")
print(df_results[['aktueller_immobilienwert', 'Neuer Immobilienwert', 'aktuelles_LtV', 'Neue LtV']].describe())

# Kiểm tra số lượng trường hợp LTV mới cao hơn LTV cũ
ltv_increased = (df_results['Neue LtV'] > df_results['aktuelles_LtV']).sum()
print(f"\nSố trường hợp LTV mới cao hơn LTV cũ: {ltv_increased} / {len(df_results)}")

# In ra các trường hợp có LTV mới thấp hơn LTV cũ
print("\nCác trường hợp có LTV mới thấp hơn LTV cũ:")
unusual_cases = df_results[df_results['Neue LtV'] <= df_results['aktuelles_LtV']]
print(unusual_cases[['aktueller_immobilienwert', 'Neuer Immobilienwert', 'aktuelles_LtV', 'Neue LtV', 'Schadensfaktor']])

# Hàm tạo biểu đồ
def create_chart(data, y_columns, title, y_label, filename, is_percentage=False):
    plt.figure(figsize=(15, 8))
    for col in y_columns:
        values = data[col] * 100 if is_percentage else data[col] / 1000
        plt.plot(range(len(data)), values, '-o', label=col)
    
    plt.xlabel('Immobilien')
    plt.ylabel(y_label)
    plt.title(title)
    plt.xticks(range(len(data)), [f'Immobilie {i+1}' for i in range(len(data))])
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
# Tạo biểu đồ cho Immobilienwert
create_chart(
    df_results,
    ['aktueller_immobilienwert', 'Neuer Immobilienwert'],
    'Änderungen im Immobilienwert',
    'Immobilienwert (Tausend €)',
    'immobilienwert_chart.png'
)

# Tạo biểu đồ cho LtV
create_chart(
    df_results,
    ['aktuelles_LtV', 'Neue LtV'],
    'Änderungen in LtV',
    'LtV (%)',
    'ltv_chart.png',
    is_percentage=True
)

print("Biểu đồ đã được lưu dưới dạng 'immobilienwert_chart.png' và 'ltv_chart.png'")