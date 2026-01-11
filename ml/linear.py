import numpy as np
from sklearn.linear_model import LinearRegression

# 构建数据样本
X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
y = np.array([1, 2, 3, 4])

# 创建线性回归模型
model = LinearRegression()

# 用数据样本训练模型
model.fit(X, y)

Z = np.array([[9, 10], [11, 12]])

# 用训练好的模型去预测样本
predictions = model.predict(Z)

# 打印输出
print('预测：', predictions)
print('系数：', model.coef_)
print('截距：', model.intercept_)
