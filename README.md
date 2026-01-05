# VideoDownloader

A powerful Telegram bot for downloading and uploading videos, PDFs, and other media from various sources. Built with Pyrogram and yt-dlp.

## Features

- **Multi-Source Support**: Download from YouTube, JWPlayer, M3U8 streams, Google Drive, and direct PDF links
- **Batch Processing**: Process multiple links from a text file (format: `Name:link` per line)
- **Quality Selection**: Choose video resolution (360p, 480p, 720p, etc.)
- **Authentication**: Support for cookies to bypass restrictions on platforms like YouTube
- **Progress Tracking**: Real-time download and upload progress with progress bars
- **Thumbnail Generation**: Automatic thumbnail creation for videos
- **Flexible Upload**: Upload as video or document based on file type

## Supported Formats

- YouTube videos (with quality selection)
- JWPlayer embedded videos
- M3U8/HLS streams
- PDF files
- Google Drive links
- Generic video links

## Prerequisites

- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- API ID and Hash (from [my.telegram.org](https://my.telegram.org))

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ayush24kr/VideoDownloader.git
   cd PyroNoobCodeX
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```


### YouTube Cookies (Optional but Recommended)

To download age-restricted or private YouTube videos:

1. Install yt-dlp locally
2. Export cookies from your browser:
   ```bash
   yt-dlp --cookies-from-browser chrome --cookies cookies.txt
   ```
3. Place the `cookies.txt` file in the project root

## Usage

1. **Start the bot:**
   ```bash
   python main.py
   ```

2. **Bot Commands:**
   - `/start` - Welcome message with instructions
   - `/pyro` - Batch download from text file
   - `/jw` - Download JWPlayer links
   - `/cancel` - Cancel ongoing downloads
   - `/restart` - Restart the bot

3. **Batch Download:**
   - Send a text file with links in format: `Video Name:link`
   - Reply with `/pyro` to start batch processing
   - Choose quality when prompted

4. **Single Downloads:**
   - Send individual links
   - The bot will automatically detect and download

## Deployment

### Local/VPS

- Ensure Python 3.10+ is installed
- Install ffmpeg for video processing
- Run `python main.py`

## Project Structure

```
VideoDownloader/
├── main.py              # Main bot script
├── helper.py            # Utility functions
├── p_bar.py             # Progress bar implementation
├── Easy_F.py            # Additional utilities
├── cookies.txt          # YouTube cookies
├── requirements.txt     # Python dependencies
├── runtime.txt          # Python version for Heroku
└── README.md            # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Troubleshooting

- **YouTube downloads failing**: Update `cookies.txt` with fresh cookies
- **ffmpeg errors**: Ensure ffmpeg is installed (`apt install ffmpeg`)
- **Permission errors**: Check file permissions and environment variables
- **Bot not responding**: Verify bot token and API credentials

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

- Built with [Pyrogram](https://github.com/pyrogram/pyrogram)
- Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Inspired by various Telegram download bots

## Disclaimer

This bot is for educational purposes only. Please respect copyright laws and platform terms of service when downloading content.
