import pandas as pd
import numpy as np

# Đọc file test.csv
df = pd.read_csv('test.csv')

# Thêm cột ID là số thứ tự
df.insert(0, 'ID', range(1, len(df) + 1))

# Định nghĩa phân bố Energieklasse
energy_classes = ['A+', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
percentages = [0.06, 0.06, 0.06, 0.15, 0.16, 0.15, 0.12, 0.12, 0.12]

# Tính số lượng cho mỗi Energieklasse
num_samples = len(df)
num_per_class = [int(p * num_samples) for p in percentages]

# Điều chỉnh số lượng nếu cần để đảm bảo tổng số bằng num_samples
diff = num_samples - sum(num_per_class)
num_per_class[-1] += diff

# Tạo danh sách Energieklasse dựa trên phân bố
energieklasse = np.concatenate([np.repeat(ec, n) for ec, n in zip(energy_classes, num_per_class)])

# Xáo trộn danh sách để đảm bảo tính ngẫu nhiên
np.random.shuffle(energieklasse)

# Thêm cột Energieklasse vào DataFrame
df['Energieklasse'] = energieklasse

# Sắp xếp lại các cột để Energieklasse nằm sau cột landkreis
columns = ['ID', 'ort', 'landkreis', 'latitude', 'longitude', 'GEB_HQ', 'flood_risk', 'Energieklasse']
df = df[columns]

# Lưu DataFrame đã cập nhật vào file CSV mới
output_file = 'testepc.csv'  # Thay đổi tên file output thành testepc.csv
df.to_csv(output_file, index=False)

print(f"Đã xử lý xong và lưu kết quả vào file '{output_file}'")

# Hiển thị một số thống kê
print("\nPhân bố Energieklasse:")
print(df['Energieklasse'].value_counts(normalize=True).sort_index())

print("\nNăm hàng đầu tiên của DataFrame:")
print(df.head())