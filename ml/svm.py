import numpy as np
from sklearn.svm import SVC
# 导入鸢尾花数据集 + 数据拆分工具
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 加载鸢尾花数据集（150条样本，4个特征，3类标签）
iris = load_iris()
# 拆分训练集（80%）和测试集（20%）
X_train, X_test, y_train, y_test = train_test_split(
    iris.data,  # 特征数据（花萼长/宽、花瓣长/宽）
    iris.target,  # 标签数据（0/1/2对应3种鸢尾花）
    test_size=0.2,  # 测试集占比
    random_state=0  # 固定随机拆分结果，方便复现
)

# 创建SVM模型（线性核函数，适合鸢尾花这种线性可分数据）
model = SVC(kernel='linear', C=1.0)

# 训练模型
model.fit(X_train, y_train)

# 预测新数据
predictions = model.predict(X_test)

# 打印结果
print("SVM预测结果：", predictions)
print("测试集真实标签：", y_test)
# 计算准确率（鸢尾花数据集用线性SVM准确率通常95%+）
accuracy = accuracy_score(y_test, predictions)
print("模型准确率：", round(accuracy, 2))
