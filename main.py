import os
import torch
from torchvision import transforms
from PIL import Image
import cv2
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHANNEL_ID = os.getenv("FORWARD_CHANNEL_ID")  # The channel where original images are saved
MODEL_PATH = "ghibli_model.pth"

# Ensure model exists
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Please place 'ghibli_model.pth' in the project directory.")

# Load the pre-trained style transfer model
model = torch.jit.load(MODEL_PATH).eval()

# Image preprocessing and transformation
transform = transforms.Compose([
    transforms.Resize((512, 512)),
    transforms.ToTensor(),
    transforms.Lambda(lambda x: x.mul(255))
])

def apply_style(input_path, output_path):
    """Applies the Ghibli style transfer model to an image."""
    img = Image.open(input_path).convert("RGB")
    img_tensor = transform(img).unsqueeze(0)
    
    with torch.no_grad():
        output_tensor = model(img_tensor)
    output_img = output_tensor.squeeze(0).clamp(0, 255).byte().permute(1, 2, 0).numpy()
    cv2.imwrite(output_path, cv2.cvtColor(output_img, cv2.COLOR_RGB2BGR))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎨 Send me an image, and I'll transform it into a Ghibli-style masterpiece!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    input_path = "images/input.jpg"
    output_path = "images/output.jpg"
    file_id = update.message.photo[-1].file_id
    user_id = update.message.chat_id
    
    # Download the image
    await file.download_to_drive(input_path)
    
    # Forward original image to the channel
    await context.bot.send_photo(chat_id=CHANNEL_ID, photo=InputFile(input_path), caption=f"📸 Image from User: {user_id}")
    
    # Process the image
    apply_style(input_path, output_path)
    
    # Send the processed image back to the user
    await update.message.reply_photo(photo=InputFile(output_path), caption="Here's your Ghibli-style image! 🌸")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
