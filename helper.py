import subprocess
import datetime
import asyncio
import os
import time
import aiohttp
import aiofiles
import logging
from p_bar import progress_bar

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def duration(filename):
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                 "format=duration", "-of",
                                 "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        return float(result.stdout)
    except Exception as e:
        logger.error(f"Error getting duration: {e}")
        return 0.0

async def aio(url, name):
    k = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                async with aiofiles.open(k, mode='wb') as f:
                    await f.write(await resp.read())
    return k

async def download(url, name):
    ka = f'{name}.pdf'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                async with aiofiles.open(ka, mode='wb') as f:
                    await f.write(await resp.read())
    return ka

def vid_info(info):
    info = info.strip()
    info = info.split("\n")
    new_info = dict()
    temp = []
    
    for i in info:
        i = str(i)
        if "[" not in i and '---' not in i:
            while "  " in i:
                i = i.replace("  ", " ")
            i = i.strip()
            parts = i.split("|")[0].split(" ", 3)
            
            try:
                # parts[0] is usually ID/format code, parts[2] is resolution
                if len(parts) > 2:
                    res = parts[2]
                    fmt_code = parts[0]
                    
                    if "RESOLUTION" not in res and res not in temp and "audio" not in res:
                        temp.append(res)
                        new_info[res] = fmt_code
            except Exception as e:
                logger.error(f"Error parsing video info line: {i} - {e}")
                pass
                
    return new_info

async def run(cmd):
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        stdout, stderr = await proc.communicate()
        
        if proc.returncode == 0:
            return stdout.decode() if stdout else ""
        else:
            logger.error(f"Command '{cmd}' failed with return code {proc.returncode}")
            return False
    except Exception as e:
        logger.error(f"Error running command '{cmd}': {e}")
        return False

def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0 or unit == 'PB':
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"

def time_name():
    date = datetime.date.today()
    now = datetime.datetime.now()
    current_time = now.strftime("%H%M%S")
    return f"{date} {current_time}.mp4"

async def download_video(url, cmd, name):
    # Remove aria2c to prevent file locking issues on Windows
    download_cmd = f"{cmd} -R 25 --fragment-retries 25"
    logger.info(f"Downloading: {download_cmd}")
    
    # Run the download command
    # Using run() wrapper or direct subprocess based on preference, but here we use os.system in original
    # Switching to asyncio.subprocess for non-blocking behavior would be better, but sticking to logic structure for now
    # However, one major fix: os.system waits. We should use await run(download_cmd) if possible, 
    # but run() captures output. Let's use create_subprocess_shell for void execution.
    
    process = await asyncio.create_subprocess_shell(download_cmd)
    await process.wait()

    try:
        if os.path.isfile(name):
            return name
        elif os.path.isfile(f"{name}.webm"):
            return f"{name}.webm"
        
        # Check for other extensions
        base_name = name.split(".")[0] if "." in name else name
        extensions = [".mkv", ".mp4", ".mp4.webm"]
        
        for ext in extensions:
            if os.path.isfile(f"{base_name}{ext}"):
                return f"{base_name}{ext}"

        return name
    except Exception as e:
        logger.error(f"Error finding downloaded file: {e}")
        return name + ".mp4"

async def send_vid(bot, m, cc, filename, thumb, name, prog):
    
    # Generate thumbnail if needed
    if not os.path.isfile(f"{filename}.jpg"):
        cmd = f'ffmpeg -i "{filename}" -ss 00:01:00 -vframes 1 "{filename}.jpg"'
        await run(cmd)
    
    await prog.delete(revoke=True)
    reply = await m.reply_text(f"**Uploading ...** - `{name}`")
    
    try:
        thumbnail = thumb if thumb != "no" else f"{filename}.jpg"
        if not os.path.isfile(thumbnail):
             thumbnail = None
    except Exception:
        thumbnail = None

    dur = int(duration(filename))
    start_time = time.time()

    try:
        await m.reply_video(
            filename,
            caption=cc,
            supports_streaming=True,
            height=720,
            width=1280,
            thumb=thumbnail,
            duration=dur,
            progress=progress_bar,
            progress_args=(reply, start_time)
        )
    except Exception as e:
        logger.warning(f"Video upload failed, trying as document: {e}")
        await m.reply_document(
            filename,
            caption=cc,
            progress=progress_bar,
            progress_args=(reply, start_time)
        )

    # Cleanup
    if os.path.exists(filename):
        os.remove(filename)
    
    if os.path.exists(f"{filename}.jpg"):
        os.remove(f"{filename}.jpg")
        
    await reply.delete(revoke=True)

async def send_doc(bot, m, cc, filename, thumb, name, prog):
    # Generate thumbnail if needed (for document thumb)
    if not os.path.isfile(f"{filename}.jpg"):
        cmd = f'ffmpeg -i "{filename}" -ss 00:01:00 -vframes 1 "{filename}.jpg"'
        await run(cmd)
    
    await prog.delete(revoke=True)
    reply = await m.reply_text(f"**Uploading as Doc ...** - `{name}`")
    
    try:
        thumbnail = thumb if thumb != "no" else f"{filename}.jpg"
        if not os.path.isfile(thumbnail):
             thumbnail = None
    except Exception:
        thumbnail = None

    start_time = time.time()

    try:
        await m.reply_document(
            filename,
            caption=cc,
            thumb=thumbnail,
            progress=progress_bar,
            progress_args=(reply, start_time)
        )
    except Exception as e:
        logger.error(f"Deep document upload failed: {e}")
        await m.reply_text(f"Upload failed: {e}")

    # Cleanup
    if os.path.exists(filename):
        os.remove(filename)
    
    if os.path.exists(f"{filename}.jpg"):
        os.remove(f"{filename}.jpg")
        
    await reply.delete(revoke=True)
