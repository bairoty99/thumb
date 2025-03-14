import os
from telethon import TelegramClient, events
import ffmpeg

# Your Telegram API credentials
api_id = 25476455
api_hash = '4aef3ed4219eb63675a572d2c9e27e2a'
bot_token = '7206339621:AAH9cl6GdrZJjeUNSMUJsSJ6-1E3SmX6Fas'

# Initialize the bot
client = TelegramClient('bot', api_id, api_hash)

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
            # Define inputs
            video_input = ffmpeg.input(TEMP_VIDEO_PATH)  # Video with audio
            photo_input = ffmpeg.input(PHOTO_PATH)       # Photo for thumbnail

            # Process video with photo as thumbnail
            (
                ffmpeg
                .output(
                    video_input['v'],   # Video stream from video file
                    video_input['a'],   # Audio stream from video file
                    photo_input['v'],   # Video stream from photo (thumbnail)
                    OUTPUT_VIDEO_PATH,  # Output filename must come right after streams
                    vcodec='libx264',   # Re-encode video
                    acodec='aac',       # Re-encode audio
                    map=['0:v', '0:a', '1:v'],  # Map all streams
                    **{'c:v:1': 'mjpeg'},       # Encode photo as MJPEG
                    **{'disposition:v:1': 'attached_pic'},  # Set photo as thumbnail
                    shortest=True               # Use shortest duration
                )
                .overwrite_output()
                .run()
            )

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

        except ffmpeg.Error as e:
            # Safely handle stderr being None
            error_msg = e.stderr.decode('utf-8') if e.stderr else "Unknown FFmpeg error"
            await event.reply(f"FFmpeg error: {error_msg}")
            print(f"FFmpeg error: {error_msg}")
        except Exception as e:
            await event.reply(f"Error processing video: {str(e)}")
            print(f"Error: {e}")

# Start the bot
async def main():
    await client.start(bot_token=bot_token)
    print("Bot is running...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
