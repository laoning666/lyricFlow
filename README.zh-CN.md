# LyricFlow

简体中文 | [English](README.md)

> 自动为音乐库下载歌词和专辑封面

## 功能特性

- 🎵 扫描音乐文件夹（支持 MP3、FLAC、M4A、WAV 等格式）
- 📝 自动下载歌词，保存为 `.lrc` 文件
- 🖼️ 自动下载专辑封面，保存为 `cover.jpg`
- 🏷️ 将歌词和封面嵌入音频元数据（ID3/FLAC/MP4）
- 🔄 增量处理，跳过已有歌词/封面的文件
- ⏰ 支持定时扫描模式
- 🐳 Docker 容器化部署
- 📁 STRM 文件支持 - 支持网盘流媒体文件
- 🔌 多 API 提供商 - 支持 TuneHub 或 LrcApi

## Docker 镜像

| 镜像仓库 | 镜像地址 | 适用场景 |
|---------|---------|----------|
| GitHub Container Registry | `ghcr.io/laoning666/lyricflow:latest` | 全球用户 |
| Docker Hub | `laoning666/lyricflow:latest` | 备用镜像 |

## 快速开始

### 方式一：Docker Compose（推荐）

1. 下载 docker-compose.yml：
```bash
curl -O https://raw.githubusercontent.com/laoning666/LyricFlow/main/docker-compose.yml
```

2. 编辑 `docker-compose.yml`，修改音乐文件夹路径：
```yaml
volumes:
  - /你的音乐路径:/music:rw
```

3. 运行：
```bash
docker-compose up -d
```

> **提示**：你也可以使用 `.env` 文件进行配置。取消 docker-compose.yml 中 `env_file` 部分的注释，并下载 `.env.example` 文件。

### 方式二：Docker 命令

```bash
# 运行一次（GitHub Container Registry）
docker run --rm \
  -v /你的音乐路径:/music \
  ghcr.io/laoning666/lyricflow:latest

# 或使用 Docker Hub 镜像
docker run --rm \
  -v /你的音乐路径:/music \
  laoning666/lyricflow:latest

# 定时扫描（每天）
docker run -d \
  -v /你的音乐路径:/music \
  -e SCAN_INTERVAL_DAYS=1 \
  --name lyricflow \
  ghcr.io/laoning666/lyricflow:latest
```

### 方式三：本地 Python 运行

```bash
# 安装依赖
pip install -r requirements.txt

# 设置音乐路径并运行
export MUSIC_PATH=/path/to/your/music
python -m src.main
```

## 配置项

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `MUSIC_PATH` | `/music` | 音乐文件夹路径 |
| `SCAN_INTERVAL_DAYS` | `0` | 扫描间隔（天），0 = 只扫描一次，1 = 每天 |
| `DOWNLOAD_LYRICS` | `true` | 下载歌词（.lrc 文件） |
| `DOWNLOAD_COVER` | `true` | 下载封面（cover.jpg） |
| `OVERWRITE_LYRICS` | `false` | 覆盖已有歌词文件 |
| `OVERWRITE_COVER` | `false` | 覆盖已有封面文件 |
| `UPDATE_LYRICS` | `false` | 将歌词写入音频元数据 |
| `UPDATE_COVER` | `false` | 将封面写入音频元数据 |
| `UPDATE_BASIC_INFO` | `false` | 将 艺术家/标题/专辑 写入元数据 |
| `USE_FOLDER_STRUCTURE` | `true` | 从文件夹结构推断歌手/专辑 |
| `DEFAULT_ARTIST` | `""` | 备用默认歌手名 |
| `API_PROVIDER` | `tunehub` | API 提供商（`tunehub` 或 `lrcapi`） |
| `PLATFORMS` | `netease,kuwo,qq` | 搜索平台优先级（仅 TuneHub） |
| `LRCAPI_URL` | `https://api.lrc.cx` | LrcApi 服务器地址 |
| `LRCAPI_AUTH` | `""` | LrcApi 鉴权密钥（可选） |

## 文件夹结构

为获得最佳效果，请按以下结构整理音乐：

```
/music/
├── 歌手名/
│   ├── 专辑名/
│   │   ├── 歌曲1.mp3
│   │   └── cover.jpg
│   └── 歌曲2.mp3 (直接放在歌手目录下也可)
```

支持两种结构：
1. **歌手/专辑/歌曲.mp3**（推荐）：自动识别歌手和专辑。
2. **歌手/歌曲.mp3**：自动识别歌手（专辑留空）。

工具会：
1. 从文件夹名读取歌手（或使用 ID3 标签）
2. 使用 TuneHub API 搜索歌词和封面
3. 保存 `.lrc` 文件（与音乐文件同名）
4. 在每个专辑文件夹保存 `cover.jpg`

## 多文件夹映射

```yaml
volumes:
  - /volume1/music:/music/folder1:rw
  - /volume2/lossless:/music/folder2:rw
  - /volume3/backup:/music/folder3:rw
```

## 群晖 NAS 使用

1. 打开 **Container Manager** 套件
2. 进入 **项目** → 创建新项目
3. 上传 `docker-compose.yml`
4. 修改卷映射路径为你的音乐共享文件夹（如 `/volume1/music`）
5. 构建并运行

## STRM 文件支持

LyricFlow 支持 `.strm`（流媒体）文件，适用于基于网盘的音乐库管理。STRM 文件是包含远程音频 URL 的文本文件，常用于 Emby、Jellyfin 或 Plex。

### 工作原理

```
本地目录：                      云存储（网盘）：
/music/歌手/专辑/               阿里云盘、百度网盘等
├── 歌曲.strm ──────────────→  实际音频文件
├── 歌曲.lrc  ← LyricFlow 下载     
└── cover.jpg ← LyricFlow 下载     
```

- **歌曲.strm**：包含远程音频 URL（由你创建）
- **歌曲.lrc**：LyricFlow 下载的歌词
- **cover.jpg**：LyricFlow 下载的专辑封面

### 使用方法

1. 按 `歌手/专辑/` 文件夹结构整理 STRM 文件
2. LyricFlow 会从文件夹名和文件名提取歌手和歌曲信息
3. 歌词和封面会保存在 STRM 文件同目录
4. 媒体播放器（Emby/Jellyfin/Plex）会从网盘串流音频，同时读取本地元数据

> **注意**：STRM 文件是文本文件，不支持嵌入元数据。请使用 `DOWNLOAD_LYRICS=true` 和 `DOWNLOAD_COVER=true` 下载到本地文件。

## API 提供商

LyricFlow 支持多个 API 提供商用于搜索歌词和封面：

### TuneHub（默认）

聚合多个音乐平台（网易云、酷我、QQ音乐）的搜索结果。

```bash
# 默认，无需额外配置
docker run --rm -v /你的音乐路径:/music ghcr.io/laoning666/lyricflow:latest
```

### LrcApi

[LrcApi](https://github.com/HisAtri/LrcApi) 是一个可自建的歌词 API。你可以使用公开 API 或部署自己的实例。

```bash
# 使用公开 LrcApi
docker run --rm \
  -e API_PROVIDER=lrcapi \
  -v /你的音乐路径:/music \
  ghcr.io/laoning666/lyricflow:latest

# 使用自建 LrcApi（带鉴权）
docker run --rm \
  -e API_PROVIDER=lrcapi \
  -e LRCAPI_URL=http://192.168.1.100:28883 \
  -e LRCAPI_AUTH=你的鉴权密钥 \
  -v /你的音乐路径:/music \
  ghcr.io/laoning666/lyricflow:latest
```

## 开源协议

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) - 仅限非商业用途
