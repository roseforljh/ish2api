# 步骤 1: 使用官方的、轻量的 Python 镜像作为基础
FROM python:3.11-slim

# 步骤 2: 在容器内创建一个工作目录
WORKDIR /app

# 步骤 3: 复制依赖文件到工作目录
# 将这一步与复制源码分开，可以利用 Docker 的层缓存机制，
# 如果依赖不变，后续构建会更快。
COPY requirements.txt .

# 步骤 4: 安装所有依赖项
# --no-cache-dir 选项可以减小最终镜像的体积
RUN pip install --no-cache-dir -r requirements.txt

# 步骤 5: 将你的应用程序代码复制到工作目录
COPY main.py .

# 步骤 6: 声明容器在运行时监听的端口
EXPOSE 8000

# 步骤 7: 定义容器启动时要执行的命令
# 使用 "0.0.0.0" 来允许从容器外部访问服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]



