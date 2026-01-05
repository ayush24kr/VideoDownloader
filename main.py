import os
import shutil
import sys
import asyncio
import logging
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod import listen
import helper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Bot
bot = Client(
    "bot",
    api_id=23285995,
    api_hash="e361383a58365bf08ef61587dae02dca",
    bot_token="8476031679:AAFV8-3rhuYB-8uI69ncF6rymDjs6X8I5_Q"
)

cancel_process = False

@bot.on_message(filters.command(["start"]))
async def start_handler(bot: Client, m: Message):
    await m.reply_text(
        "Hello! I am a txt file downloader.\n"
        "Press /pyro to download links listed in a txt file (Name:link).\n"
        "Press /jw for JWPlayer signed links.\n\n"
        "Bot made by BATMAN"
    )

@bot.on_message(filters.command(["cancel"]))
async def cancel_handler(_, m):
    global cancel_process
    cancel_process = True
    await m.reply_text("Cancelling all processes. Please wait...")

@bot.on_message(filters.command("restart"))
async def restart_handler(_, m):
    await m.reply_text("Restarted!", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command(["pyro", "jw"]))
async def batch_download_handler(bot: Client, m: Message):
    global cancel_process
    cancel_process = False
    
    is_jw = m.command[0] == "jw"
    
    # 1. Get the TXT file
    editable = await m.reply_text("Please send the **txt file** containing Name:Link pairs.")
    input_msg: Message = await bot.listen(editable.chat.id)
    
    if not input_msg.document or not input_msg.document.file_name.endswith(".txt"):
         await m.reply_text("Invalid file. Please send a .txt file.")
         return

    file_path = await input_msg.download()
    await input_msg.delete(True)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().splitlines()
        os.remove(file_path)
    except Exception as e:
        await m.reply_text(f"Error reading file: {e}")
        return

    links = []
    for line in content:
        if ":" in line:
            links.append(line.split(":", 1))
    
    if not links:
        await m.reply_text("No valid links found in the file.")
        return

    # 2. Get User Inputs
    editable = await m.reply_text(f"Found **{len(links)}** links.\nEnter starting index (default 0):")
    input_start: Message = await bot.listen(editable.chat.id)
    try:
        start_index = int(input_start.text)
    except ValueError:
        start_index = 0

    await m.reply_text("**Enter Batch Title/Caption:**")
    input_title: Message = await bot.listen(editable.chat.id)
    batch_title = input_title.text

    await m.reply_text("**Enter Resolution (e.g., 360, 480, 720):**")
    input_res: Message = await bot.listen(editable.chat.id)
    target_res = input_res.text

    # Ask for upload mode
    await m.reply_text("**Upload as Video or Document? (v/d):**")
    input_mode: Message = await bot.listen(editable.chat.id)
    upload_mode = input_mode.text.lower().strip()
    is_doc = upload_mode.startswith('d')

    await m.reply_text("Send **Thumb URL** or type **no**:")
    input_thumb: Message = await bot.listen(editable.chat.id)
    thumb_url = input_thumb.text
    
    thumb_path = "no"
    if thumb_url.startswith(("http://", "https://")):
         thumb_path = "thumb.jpg"
         # Use asyncio run or similar if possible, but keep simple for now
         os.system(f"wget '{thumb_url}' -O '{thumb_path}'")

    # 3. Process Links
    count = start_index + 1 if start_index > 0 else 1
    
    # Logic for start index in list slicing
    # The user enters 0-based index logically, but might want to start from "Link #5"
    # The original code used input directly as start index for the loop.
    
    for i in range(start_index, len(links)):
        if cancel_process:
            await m.reply_text("Process canceled by user.")
            break

        name_part, url_part = links[i]
        # Sanitize filename for Windows
        name_clean = name_part.strip()
        for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
             name_clean = name_clean.replace(char, ' ')
        name_clean = name_clean.strip()
        
        url = url_part.strip()
        
        # JWPlayer Specific Logic
        if is_jw and "jwplayer" in url:
            try:
                url = get_jw_signed_url(url)
            except Exception as e:
                logger.error(f"Error getting JW link: {e}")
                await m.reply_text(f"Failed to sign JW link: {name_clean}")
                continue

        # Determine Quality/Format
        # We'll use a simplified selection logic or the helper
        try:
             # Basic resolution map for clarity, though vid_info below does the heavy lifting
            cmd_opts = ""
            
            # Check info
            if "youtu" in url or "jwplayer" in url or "m3u8" in url:
                 cmd = await get_ytdlp_command(url, name_clean, target_res, count)
            elif ".pdf" in url or "drive" in url:
                 cmd = "pdf"
            else:
                 # Cookies check for generic links too
                 cookies_arg = ""
                 if os.path.isfile("cookies.txt"):
                     cookies_arg = "--cookies cookies.txt"
                     
                 cmd = f'yt-dlp {cookies_arg} --ffmpeg-location /usr/bin/ffmpeg -o "{name_clean}.mp4" --no-keep-video --remux-video mkv "{url}"'
            
            # Display Progress
            msg_text = (
                f"**Downloading:**\n"
                f"**Name:** `{name_clean}`\n"
                f"**Quality:** `{target_res}`\n"
                f"**Mode:** `{'Document' if is_doc else 'Video'}`\n"
                f"**Index:** `{count}`"
            )
            prog_msg = await m.reply_text(msg_text)

            # Download and Upload
            final_filename = ""
            caption = f"**Title »** {name_clean}\n**Caption »** {batch_title}\n**Index »** {str(count).zfill(3)}"
            
            if cmd == "pdf":
                 final_filename = await helper.download(url, name_clean)
                 await prog_msg.delete(True)
                 await m.reply_document(final_filename, caption=caption)
            else:
                 # Video
                 # We need to format the name properly for the helper
                 # The original code had complex naming logic. We try to simplify.
                 
                 final_filename = await helper.download_video(url, cmd, name_clean)
                 if final_filename and os.path.exists(final_filename):
                     if is_doc:
                         await helper.send_doc(bot, m, caption, final_filename, thumb_path, name_clean, prog_msg)
                     else:
                         await helper.send_vid(bot, m, caption, final_filename, thumb_path, name_clean, prog_msg)
                 else:
                     await m.reply_text(f"Download failed for {name_clean}")
            
            count += 1
            await asyncio.sleep(2) # Non-blocking sleep

        except Exception as e:
            logger.error(f"Error processing link {i}: {e}")
            await m.reply_text(f"Error on link {i}: {str(e)}")
            continue

    await m.reply_text("Batch processing complete.")
    if os.path.exists("thumb.jpg"):
        os.remove("thumb.jpg")

def get_jw_signed_url(url):
    # This logic matches the original extraction
    headers = {
        'Host': 'api.classplusapp.com',
        'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30.hM33P2ai6ivdzxPPfm01LAd4JWv-vnrSxGXqvCirCSpUfhhofpeqyeHPxtstXwe0',
        'user-agent': 'Mobile-Android',
        'app-version': '1.4.37.1',
        'api-version': '18',
        'device-id': '5d0d17ac8b3c9f51',
        'device-details': '2848b866799971ca_2848b8667a33216c_SDK-30',
        'accept-encoding': 'gzip',
    }
    params = (('url', f'{url}'),)
    response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
    jw_url = response.json()['url']
    
    headers1 = {
        'User-Agent': 'ExoPlayerDemo/1.4.37.1 (Linux;Android 11) ExoPlayerLib/2.14.1',
        'Accept-Encoding': 'gzip',
        'Host': 'cdn.jwplayer.com',
        'Connection': 'Keep-Alive',
    }
    response1 = requests.get(jw_url, headers=headers1)
    # Parsing the response text as typical for m3u8 or similar redirect
    # The original code did split on newline and took index 2. This is fragile but we'll keep it if it works for their specific case
    # or improve it if possible.
    try:
        return response1.text.split("\n")[2]
    except IndexError:
        return jw_url

async def get_ytdlp_command(url, name, resolution, index):
    # Use yt-dlp's built-in format selection logic which is more robust
    # We ask for best video no larger than 'resolution' height
    
    try:
        height = int(resolution)
        # format: best video with height <= target + best audio, OR best (fallback)
        f_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
    except ValueError:
        # If resolution is not an integer (e.g. "best"), just use best
        f_str = "bestvideo+bestaudio/best"
    
    # Check for cookies.txt
    cookies_arg = ""
    if os.path.isfile("cookies.txt"):
        cookies_arg = "--cookies cookies.txt"

    return f'yt-dlp {cookies_arg} --js-runtimes node --ffmpeg-location /usr/bin/ffmpeg -f "{f_str}" --merge-output-format mkv --no-keep-video --remux-video mkv "{url}" -o "{name}.%(ext)s" -R 25 --fragment-retries 25'

if __name__ == "__main__":
    bot.run()
