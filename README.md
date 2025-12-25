# LyricFlow

[简体中文](README.zh-CN.md) | English

> Automatically download lyrics and album covers for your music library

## Features

- 🎵 Scan music folders (MP3, FLAC, M4A, WAV, etc.)
- 📝 Download lyrics as `.lrc` files
- 🖼️ Download album covers as `cover.jpg`
- 🔄 Incremental processing (skip existing files)
- ⏰ Scheduled scanning mode
- 🐳 Docker support

## Docker Images

| Registry | Image | Best For |
|----------|-------|----------|
| GitHub Container Registry | `ghcr.io/laoning666/lyricflow:latest` | Global users |
| Docker Hub | `laoning666/lyricflow:latest` | Alternative mirror |

## Quick Start

### Option 1: Docker Compose (Recommended)

1. Download configuration files:
```bash
curl -O https://raw.githubusercontent.com/laoning666/LyricFlow/main/docker-compose.yml
curl -O https://raw.githubusercontent.com/laoning666/LyricFlow/main/.env.example
cp .env.example .env
```

2. Edit `.env` and `docker-compose.yml` to set your music folder path:
```yaml
volumes:
  - /your/music/path:/music:rw
```

3. Run:
```bash
docker-compose up -d
```

### Option 2: Docker Run

```bash
# Run once (GitHub Container Registry)
docker run --rm \
  -v /your/music/path:/music \
  ghcr.io/laoning666/lyricflow:latest

# Or use Docker Hub mirror
docker run --rm \
  -v /your/music/path:/music \
  laoning666/lyricflow:latest

# Run with scheduled scanning (every hour)
docker run -d \
  -v /your/music/path:/music \
  -e SCAN_INTERVAL=3600 \
  --name lyricflow \
  ghcr.io/laoning666/lyricflow:latest
```

### Option 3: Local Python

```bash
# Install dependencies
pip install -r requirements.txt

# Set music path and run
export MUSIC_PATH=/path/to/your/music
python -m src.main
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MUSIC_PATH` | `/music` | Music folder path |
| `SCAN_INTERVAL` | `0` | Scan interval in seconds (0 = run once) |
| `DOWNLOAD_LYRICS` | `true` | Download lyrics (.lrc files) |
| `DOWNLOAD_COVER` | `true` | Download album covers (cover.jpg) |
| `OVERWRITE_LYRICS` | `false` | Overwrite existing lyrics |
| `OVERWRITE_COVER` | `false` | Overwrite existing covers |
| `USE_FOLDER_STRUCTURE` | `true` | Infer artist/album from folder structure |
| `DEFAULT_ARTIST` | `""` | Fallback artist name |
| `PLATFORMS` | `netease,kuwo,qq` | Search platform priority |

## Folder Structure

For best results, organize your music like this:

```
/music/
├── Artist Name/
│   ├── Album Name/
│   │   ├── song1.mp3
│   │   ├── song2.flac
│   │   ├── song1.lrc      ← Generated
│   │   ├── song2.lrc      ← Generated
│   │   └── cover.jpg      ← Generated
```

The tool will:
1. Read artist from folder name (or ID3 tag if available)
2. Search for lyrics and covers using TuneHub API
3. Save `.lrc` files with the same name as music files
4. Save `cover.jpg` in each album folder

## Multiple Folder Mapping

```yaml
volumes:
  - /volume1/music:/music/folder1:rw
  - /volume2/lossless:/music/folder2:rw
  - /volume3/backup:/music/folder3:rw
```

## Synology NAS Usage

1. Open **Container Manager** package
2. Go to **Project** → Create new project
3. Upload `docker-compose.yml`
4. Modify volume path to your music shared folder (e.g., `/volume1/music`)
5. Build and run

## API Source

This tool uses [TuneHub API](https://music-dl.sayqz.com) for searching and downloading lyrics/covers from multiple music platforms (NetEase, Kuwo, QQ Music).

## License

MIT
