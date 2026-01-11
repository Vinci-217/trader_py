import numpy as np
from sklearn.linear_model import LogisticRegression

# 构建数据样本
X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
y = np.array([0, 1, 0, 1])

# 创建逻辑回归模型
model = LogisticRegression()

# 训练模型
model.fit(X, y)

Z = np.array([[9, 10], [11, 12], [13, 14], [15, 16]])

# 对数据进行预测量
predictions = model.predict(Z)

# 打印预测结果
print(predictions)
