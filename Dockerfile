# LyricFlow
# 自动为音乐库下载歌词和专辑封面
#
# Automatically download lyrics and album covers for your music library

FROM python:3.11-slim

LABEL maintainer="LyricFlow"
LABEL description="Automatically download lyrics and album covers for your music library"
LABEL description.zh="自动为音乐库下载歌词和专辑封面"

# Set working directory / 设置工作目录
WORKDIR /app

# Copy requirements first for better caching
# 先复制依赖文件以优化缓存
COPY requirements.txt .

# Install dependencies / 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code / 复制源代码
COPY src/ ./src/

# Set environment defaults / 设置环境变量默认值
# These can be overridden at runtime
# 运行时可以覆盖这些值

# Music path inside container / 容器内音乐路径
ENV MUSIC_PATH=/music

# Scan interval in days: 0=once, 1=daily, 7=weekly / 扫描间隔（天）：0=一次，1=每天，7=每周
ENV SCAN_INTERVAL_DAYS=0

# Download options / 下载选项
ENV DOWNLOAD_LYRICS=true
ENV DOWNLOAD_COVER=true
ENV OVERWRITE_LYRICS=false
ENV OVERWRITE_COVER=false

# Artist inference / 歌手推断
ENV DEFAULT_ARTIST=""
ENV USE_FOLDER_STRUCTURE=true

# Search platforms / 搜索平台
ENV PLATFORMS=netease,kuwo,qq

# Run the tool / 运行工具
CMD ["python", "-m", "src.main"]
