import pandas as pd

# Đường dẫn đến tệp CSV gốc và tệp kết quả
input_csv_file = 'hypothekendata.csv'  # Đường dẫn đến tệp CSV của bạn
output_csv_file = 'hypotheken_with_id.csv'  # Tên tệp đầu ra

def add_id_column_to_csv(input_csv, output_csv):
    # Đọc tệp CSV gốc
    df = pd.read_csv(input_csv)
    
    # Thêm cột ID vào vị trí đầu tiên
    df.insert(0, 'ID', range(1, len(df) + 1))
    
    # Lưu kết quả vào tệp CSV mới
    df.to_csv(output_csv, index=False)

# Gọi hàm để thêm cột ID và lưu kết quả
add_id_column_to_csv(input_csv_file, output_csv_file)

print(f"Đã thêm cột ID và lưu kết quả vào {output_csv_file}")
