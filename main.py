import os
import logging
import cv2
import torch
import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from AnimeGANv2.test import test

# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def load_animegan_model():
    """Load AnimeGANv2 model"""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_path = "AnimeGANv2/checkpoints/ghibli_model.pth"
    if not os.path.exists(model_path):
        raise FileNotFoundError("AnimeGANv2 model checkpoint not found!")
    return model_path, device

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎨 Hello! Send me an image, and I'll transform it into Ghibli-style artwork!")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("✨ Transforming your image into Ghibli magic...")

        # Get the highest resolution photo available
        photo_file = await update.message.photo[-1].get_file()
        input_path = 'user_input.jpg'
        await photo_file.download_to_drive(input_path)

        # Process image
        output_path = 'ghibli_output.jpg'
        convert_to_ghibli(input_path, output_path)

        # Send result
        await update.message.reply_photo(
            photo=open(output_path, 'rb'),
            caption="Here's your Ghibli-fied image! 🌸"
        )
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("⚠️ Oops! Something went wrong. Please try another image.")

def convert_to_ghibli(input_path, output_path):
    """Convert image to Ghibli style using AnimeGANv2"""
    model_path, device = load_animegan_model()
    img = cv2.imread(input_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Apply AnimeGANv2 transformation
    test(model_path=model_path, input_image=img, output_path=output_path, device=device)

if __name__ == '__main__':
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN environment variable not set")

    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))

    # Messages
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # Run bot
    app.run_polling()
