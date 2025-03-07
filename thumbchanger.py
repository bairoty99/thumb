import os
from telethon import TelegramClient, events
import ffmpeg

# Your Telegram API credentials
api_id = 25476455
api_hash = '4aef3ed4219eb63675a572d2c9e27e2a'
bot_token = '7206339621:AAH9cl6GdrZJjeUNSMUJsSJ6-1E3SmX6Fas'

# Initialize the bot
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# File paths
PHOTO_PATH = 'stored_photo.jpg'
TEMP_VIDEO_PATH = 'temp_video.mp4'
OUTPUT_VIDEO_PATH = 'output_video_with_thumbnail.mp4'

# Progress callback function
async def progress_callback(current, total, event, action):
    percentage = (current / total) * 100
    if percentage % 10 == 0:  # Update every 10%
        await event.reply(f"{action}: {percentage:.1f}% complete")

# Handler for receiving photos
@client.on(events.NewMessage)
async def handle_photo(event):
    if event.photo:
        await event.reply("Starting photo download...")
        await event.download_media(
            file=PHOTO_PATH,
            progress_callback=lambda c, t: progress_callback(c, t, event, "Photo download")
        )
        await event.reply("Photo downloaded and stored successfully!")
        print(f"Photo saved as {PHOTO_PATH}")

# Handler for receiving videos
@client.on(events.NewMessage)
async def handle_video(event):
    if event.video:
        if not os.path.exists(PHOTO_PATH):
            await event.reply("Please send a photo first to use as the thumbnail!")
            return

        await event.reply("Starting video download...")
        await event.download_media(
            file=TEMP_VIDEO_PATH,
            progress_callback=lambda c, t: progress_callback(c, t, event, "Video download")
        )
        await event.reply("Video downloaded, processing thumbnail...")

        try:
            # Use ffmpeg to re-encode video and set thumbnail
            stream = ffmpeg.input(TEMP_VIDEO_PATH)
            stream = ffmpeg.output(
                stream,
                OUTPUT_VIDEO_PATH,
                **{'c:v': 'libx264'},  # Re-encode video with H.264
                **{'c:a': 'aac'},     # Re-encode audio with AAC
                map_metadata='-1',    # Remove existing metadata
                **{'disposition:v:0': 'attached_pic', 'i': PHOTO_PATH}  # Attach photo as thumbnail
            )
            ffmpeg.run(stream, overwrite_output=True)

            await event.reply("Starting video upload with new thumbnail...")
            await client.send_file(
                event.chat_id,
                OUTPUT_VIDEO_PATH,
                caption="Here’s your video with the new thumbnail!",
                video=True,
                progress_callback=lambda c, t: progress_callback(c, t, event, "Video upload")
            )
            await event.reply("Video processed and uploaded successfully!")

            # Clean up
            os.remove(TEMP_VIDEO_PATH)
            os.remove(OUTPUT_VIDEO_PATH)

        except Exception as e:
            await event.reply(f"Error processing video: {str(e)}")
            print(f"Error: {e}")

# Start the bot
async def main():
    await client.start()
    print("Bot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
