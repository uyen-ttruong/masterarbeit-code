import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar
from scipy.special import erf

def cdf_normal(x, mu, sigma):
    return 0.5 * (1 + erf((x - mu) / (sigma * np.sqrt(2))))

def objective(mu, target_prob, x, prob):
    sigma = (x - mu) / stats.norm.ppf(1 - target_prob)
    return np.sum((cdf_normal(x, mu, sigma) - prob)**2)

# Dữ liệu từ Bảng 3.1
x = np.array([0.75, 1.0])  # Giá trị VtL
prob = np.array([0.005, 0.081])  # Xác suất tích lũy

# Tối ưu hóa để tìm mu (mean)
target_prob = 1 - 0.918  # 91.8% của danh mục có VtL > 100%
result = minimize_scalar(lambda mu: objective(mu, target_prob, x, prob), 
                         bounds=(1.0, 2.0), method='bounded')

mu = result.x
sigma = (1.0 - mu) / stats.norm.ppf(target_prob)

print(f"Ước tính mean VtL: {mu:.3f}")
print(f"Ước tính standard deviation của VtL: {sigma:.3f}")