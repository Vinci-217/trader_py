import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn import datasets
from sklearn.model_selection import train_test_split

# 加载训练集和测试集数据
iris = datasets.load_iris()
X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, test_size=0.2)

# 创建KNN模型
model = KNeighborsClassifier(n_neighbors=5)

# 训练模型
model.fit(X_train, y_train)

# 预测新数据
predictions = model.predict(X_test)

# 打印预测结果
print(predictions)
