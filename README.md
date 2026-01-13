# LyricFlow

[简体中文](README.zh-CN.md) | English

> Automatically download lyrics and album covers for your music library

## Features

- 🎵 Scan music folders (MP3, FLAC, M4A, WAV, etc.)
- 📝 Download lyrics as `.lrc` files
- 🖼️ Download album covers as `cover.jpg`
- 🏷️ Embed lyrics and covers into audio metadata (ID3/FLAC/MP4)
- 🔄 Incremental processing (skip existing files)
- ⏰ Scheduled scanning mode
- 🐳 Docker support
- 📁 STRM file support - Works with cloud storage streaming files
- 🔌 Multiple API providers - TuneHub or LrcApi

## Docker Images

| Registry | Image | Best For |
|----------|-------|----------|
| GitHub Container Registry | `ghcr.io/laoning666/lyricflow:latest` | Global users |
| Docker Hub | `laoning666/lyricflow:latest` | Alternative mirror |

## Quick Start

### Option 1: Docker Compose (Recommended)

1. Download docker-compose.yml:
```bash
curl -O https://raw.githubusercontent.com/laoning666/LyricFlow/main/docker-compose.yml
```

2. Edit `docker-compose.yml` to set your music folder path:
```yaml
volumes:
  - /your/music/path:/music:rw
```

3. Run:
```bash
docker-compose up -d
```

> **Tip**: You can also use `.env` file for configuration. Uncomment the `env_file` section in docker-compose.yml and download `.env.example`.

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

# Run with scheduled scanning (daily)
docker run -d \
  -v /your/music/path:/music \
  -e SCAN_INTERVAL_DAYS=1 \
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
| `SCAN_INTERVAL_DAYS` | `0` | Scan interval in days (0 = run once, 1 = daily) |
| `DOWNLOAD_LYRICS` | `true` | Download lyrics (.lrc files) |
| `DOWNLOAD_COVER` | `true` | Download album covers (cover.jpg) |
| `OVERWRITE_LYRICS` | `false` | Overwrite existing lyrics files |
| `OVERWRITE_COVER` | `false` | Overwrite existing cover files |
| `UPDATE_LYRICS` | `false` | Write lyrics to audio metadata |
| `UPDATE_COVER` | `false` | Write cover to audio metadata |
| `UPDATE_BASIC_INFO` | `false` | Write artist/title/album to metadata |
| `USE_FOLDER_STRUCTURE` | `true` | Infer artist/album from folder structure |
| `DEFAULT_ARTIST` | `""` | Fallback artist name |
| `API_PROVIDER` | `tunehub` | API provider (`tunehub` or `lrcapi`) |
| `PLATFORMS` | `netease,kuwo,qq` | Search platform priority (TuneHub only) |
| `LRCAPI_URL` | `https://api.lrc.cx` | LrcApi server URL |
| `LRCAPI_AUTH` | `""` | LrcApi authentication key (optional) |

## Folder Structure

For best results, organize your music like this:

```
/music/
├── Artist Name/
│   ├── Album Name/
│   │   ├── song1.mp3
│   │   └── cover.jpg
│   └── song2.mp3 (Directly under Artist folder)
```

Two structures are supported:
1. **Artist/Album/Song.mp3** (Recommended): Automatically infers Artist and Album.
2. **Artist/Song.mp3**: Automatically infers Artist (Album will be empty).

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

## STRM Files Support

LyricFlow supports `.strm` (streaming) files for cloud-based music libraries. STRM files are text files containing URLs pointing to remote audio files, commonly used with Emby, Jellyfin, or Plex.

### How It Works

```
Local:                          Cloud Storage:
/music/Artist/Album/            (Aliyun, Baidu, etc.)
├── song.strm  ──────────────→  Actual audio file
├── song.lrc   ← Downloaded     
└── cover.jpg  ← Downloaded     
```

- **song.strm**: Contains URL to remote audio (created by you)
- **song.lrc**: Lyrics downloaded by LyricFlow
- **cover.jpg**: Album cover downloaded by LyricFlow

### Usage

1. Organize your STRM files in `Artist/Album/` folder structure
2. LyricFlow will extract artist and title from folder names and filenames
3. Lyrics and covers are saved locally alongside the STRM files
4. Media players (Emby/Jellyfin/Plex) will stream audio from cloud while reading local metadata

> **Note**: Embedding metadata into STRM files is not supported (they are text files). Use `DOWNLOAD_LYRICS=true` and `DOWNLOAD_COVER=true` instead.

## API Providers

LyricFlow supports multiple API providers for searching lyrics and covers:

### TuneHub (Default)

Aggregates results from multiple music platforms (NetEase, Kuwo, QQ Music).

```bash
# Default, no configuration needed
docker run --rm -v /your/music:/music ghcr.io/laoning666/lyricflow:latest
```

### LrcApi

[LrcApi](https://github.com/HisAtri/LrcApi) is a self-hosted lyrics API. You can use the public API or deploy your own instance.

```bash
# Using public LrcApi
docker run --rm \
  -e API_PROVIDER=lrcapi \
  -v /your/music:/music \
  ghcr.io/laoning666/lyricflow:latest

# Using self-hosted LrcApi with authentication
docker run --rm \
  -e API_PROVIDER=lrcapi \
  -e LRCAPI_URL=http://192.168.1.100:28883 \
  -e LRCAPI_AUTH=your_auth_key \
  -v /your/music:/music \
  ghcr.io/laoning666/lyricflow:latest
```

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) - Non-commercial use only
