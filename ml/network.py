import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
# 新增：导入数据集和拆分工具
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 加载鸢尾花数据集（4个特征，适配input_dim=4）
iris = load_iris()
X = iris.data  # 150样本，4个特征（花萼长/宽、花瓣长/宽）
# 改成二分类：0=山鸢尾（原标签0），1=非山鸢尾（原标签1/2）
y = np.where(iris.target == 0, 0, 1)

# 拆分训练集（80%）和测试集（20%）
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=0
)

# 创建神经网络分类器
model = Sequential()  # 顺序模型：层按顺序堆叠
# 第一层：8个神经元，输入维度4，激活函数sigmoid
model.add(Dense(8, input_dim=4, activation='sigmoid'))
# 第二层：1个神经元（二分类输出），激活函数sigmoid
model.add(Dense(1, activation='sigmoid'))
# 编译模型：损失函数（衡量预测误差）+ 优化器（调整参数）+ 评估指标（准确率）
model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

# 训练模型：epochs=训练轮数，batch_size=每轮分批数
model.fit(X_train, y_train, epochs=20, batch_size=32, verbose=1)

# 预测新数据（sigmoid输出0~1的概率，>0.5归为1，否则0）
predictions = model.predict(X_test)
predictions_label = (predictions > 0.5).astype(int)  # 转成0/1标签

# 打印结果
print("\n预测概率（0=山鸢尾，1=非山鸢尾）：")
print(predictions)
print("\n预测标签：")
print(predictions_label.flatten())  # 展平成一维
print("\n真实标签：")
print(y_test)
# 计算准确率
accuracy = accuracy_score(y_test, predictions_label)
print("\n模型准确率：", round(accuracy, 2))
