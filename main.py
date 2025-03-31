import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from AnimeGANv2 import AnimeGAN
import cv2
import sys
sys.path.append('/app')

# Then import like this:
from AnimeGANv2.model import AnimeGANv2 as AnimeGAN


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global model instance (loaded once)
GHIBLI_MODEL = None

def initialize_model():
    """Initialize the Ghibli model once"""
    global GHIBLI_MODEL
    if GHIBLI_MODEL is None:
        logger.info("Loading Ghibli model...")
        GHIBLI_MODEL = AnimeGAN(pretrained="ghibli")
        logger.info("Model loaded successfully")

async def convert_to_ghibli(input_path: str, output_path: str) -> None:
    """Convert image to Ghibli style"""
    try:
        img = cv2.imread(input_path)
        result = GHIBLI_MODEL(img)
        cv2.imwrite(output_path, result)
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        raise

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message"""
    await update.message.reply_text(
        "🎨 *Ghibli Magic Bot* 🎨\n\n"
        "Send me any photo and I'll transform it into Studio Ghibli-style artwork!\n\n"
        "⚠️ Please note: High-resolution images may take longer to process.",
        parse_mode="Markdown"
    )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process incoming images"""
    try:
        message = await update.message.reply_text("🪄 Starting magic transformation...")
        
        # Download image
        photo_file = await update.message.photo[-1].get_file()
        input_path = "temp_input.jpg"
        await photo_file.download_to_drive(input_path)
        
        # Process image
        output_path = "ghibli_output.jpg"
        await convert_to_ghibli(input_path, output_path)
        
        # Send result
        await update.message.reply_chat_action(action="upload_photo")
        await update.message.reply_photo(
            photo=open(output_path, "rb"),
            caption="✨ Your Ghibli-fied masterpiece!",
            reply_to_message_id=update.message.message_id
        )
        
        # Clean up
        os.remove(input_path)
        os.remove(output_path)
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message.message_id)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await update.message.reply_text("❌ Transformation failed. Please try another image.")

def main() -> None:
    """Start the bot"""
    initialize_model()
    
    app = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    
    # Image handler
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    
    # Error handler
    app.add_error_handler(lambda update, context: logger.error(context.error))
    
    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
