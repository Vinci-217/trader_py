import numpy as np
from sklearn.tree import DecisionTreeClassifier

# 构建样本数据
X = [[0, 0], [1, 1]]
Y = [0, 1]

# 创建决策树分类器
clf = DecisionTreeClassifier()

# 训练模型
clf = clf.fit(X, Y)

Z = [[2., 2.], [3., 3.]]

# 打印预测结果
print(clf.predict(Z))
