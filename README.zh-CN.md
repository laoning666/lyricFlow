# LyricFlow

简体中文 | [English](README.md)

> 自动为音乐库下载歌词和专辑封面

## 功能特性

- 🎵 扫描音乐文件夹（支持 MP3、FLAC、M4A、WAV 等格式）
- 📝 自动下载歌词，保存为 `.lrc` 文件
- 🖼️ 自动下载专辑封面，保存为 `cover.jpg`
- 🔄 增量处理，跳过已有歌词/封面的文件
- ⏰ 支持定时扫描模式
- 🐳 Docker 容器化部署

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
| `DOWNLOAD_LYRICS` | `true` | 是否下载歌词（.lrc 文件） |
| `DOWNLOAD_COVER` | `true` | 是否下载封面（cover.jpg） |
| `OVERWRITE_LYRICS` | `false` | 是否覆盖已有歌词 |
| `OVERWRITE_COVER` | `false` | 是否覆盖已有封面 |
| `USE_FOLDER_STRUCTURE` | `true` | 从文件夹结构推断歌手/专辑 |
| `DEFAULT_ARTIST` | `""` | 备用默认歌手名 |
| `PLATFORMS` | `netease,kuwo,qq` | 搜索平台优先级 |

## 文件夹结构

为获得最佳效果，请按以下结构整理音乐：

```
/music/
├── 歌手名/
│   ├── 专辑名/
│   │   ├── 歌曲1.mp3
│   │   ├── 歌曲2.flac
│   │   ├── 歌曲1.lrc      ← 自动生成
│   │   ├── 歌曲2.lrc      ← 自动生成
│   │   └── cover.jpg      ← 自动生成
```

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

## API 来源

本工具使用 [TuneHub API](https://music-dl.sayqz.com) 从多个音乐平台（网易云、酷我、QQ音乐）搜索和下载歌词/封面。

## 开源协议

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) - 仅限非商业用途
