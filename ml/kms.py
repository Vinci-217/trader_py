import numpy as np
from sklearn.cluster import KMeans

# 构建样本数据
X = np.array([[1, 2], [1, 4], [1, 0], [4, 2], [4, 4], [4, 0]])

# 创建KMeans模型
model = KMeans(n_clusters=2, random_state=0, n_init='auto')

# 训练模型
model.fit(X)

# 预测新数据
predictions = model.predict([[0, 0], [4, 4]])

# 打印预测结果
print(predictions)
