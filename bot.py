import os
import shutil
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

import handlers

TOKEN = "8907056935:AAFPJzdtkZ9sslR9qwndwoVk_SfODVr4qU0"

TEMP_ROOT = "temp"
os.makedirs(TEMP_ROOT, exist_ok=True)

def get_user_dir(chat_id: int) -> str:
    user_dir = os.path.join(TEMP_ROOT, str(chat_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📸 Images to PDF", callback_data="menu_img2pdf")],
        [InlineKeyboardButton("📑 Merge PDFs", callback_data="menu_merge")],
        [InlineKeyboardButton("🖼️ PDF to Images", callback_data="menu_pdf2img")],
        [InlineKeyboardButton("🗜️ Compress PDF", callback_data="menu_compress_pdf")],
        [InlineKeyboardButton("✂️ Split PDF Pages", callback_data="menu_split_pdf")],
        [InlineKeyboardButton("📉 Compress Image (~100 KB)", callback_data="menu_compress_img")],
    ]
    return InlineKeyboardMarkup(keyboard)

# 1. Start Command: Seedha Menu dikhayega
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    msg = "👋 **PDF & Image Tool Bot me aapka swagat hai!**\n\nAapko kya karwana hai? Niche menu se select karein:"
    await update.message.reply_text(msg, reply_markup=get_main_menu(), parse_mode="Markdown")

# Menu dobara kholne ke liye /menu command
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("📋 **Main Menu:**\nApna option chuniye:", reply_markup=get_main_menu(), parse_mode="Markdown")

# 2. Menu Buttons Click Handler
async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    chat_id = query.message.chat_id
    user_dir = get_user_dir(chat_id)
    shutil.rmtree(user_dir, ignore_errors=True)
    os.makedirs(user_dir, exist_ok=True)

    # State reset
    context.user_data.clear()

    if data == "menu_img2pdf":
        context.user_data["action"] = "img2pdf"
        context.user_data["files"] = []
        await query.edit_message_text(
            "📸 **Images to PDF Chuna Gaya Hai**\n\n"
            "• Ab ek-ek karke ya ek sath saari photos bhejein.\n"
            "• Sab photos bhejne ke baad **/done** type karein.",
            parse_mode="Markdown"
        )

    elif data == "menu_merge":
        context.user_data["action"] = "merge"
        context.user_data["files"] = []
        await query.edit_message_text(
            "📑 **Merge PDFs Chuna Gaya Hai**\n\n"
            "• Ab ek-ek karke saari PDF files bhejein.\n"
            "• Sab PDFs bhejne ke baad **/done** type karein.",
            parse_mode="Markdown"
        )

    elif data == "menu_pdf2img":
        context.user_data["action"] = "pdf2img"
        await query.edit_message_text("🖼️ **PDF to Images:** Kripya apni **PDF file** bhejiye.")

    elif data == "menu_compress_pdf":
        context.user_data["action"] = "compress_pdf"
        await query.edit_message_text("🗜️ **Compress PDF:** Kripya apni **PDF file** bhejiye.")

    elif data == "menu_split_pdf":
        context.user_data["action"] = "split_pdf"
        await query.edit_message_text("✂️ **Split PDF:** Kripya apni **PDF file** bhejiye.")

    elif data == "menu_compress_img":
        context.user_data["action"] = "compress_img"
        await query.edit_message_text("📉 **Compress Image:** Kripya apni **Photo** bhejiye.")

# 3. File Receiver (Jo option chuna hai uske according process karega)
async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get("action")
    if not action:
        await update.message.reply_text(
            "Pehle batayein ki kya karna hai! Niche diye menu me se option chunein:",
            reply_markup=get_main_menu()
        )
        return

    chat_id = update.message.chat_id
    user_dir = get_user_dir(chat_id)

    # --- MULTIPLE IMAGES TO PDF ---
    if action == "img2pdf":
        photo_file = None
        if update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
        elif update.message.document and update.message.document.file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            photo_file = await update.message.document.get_file()

        if photo_file:
            count = len(context.user_data["files"]) + 1
            path = os.path.join(user_dir, f"img_{count}.jpg")
            await photo_file.download_to_drive(path)
            context.user_data["files"].append(path)
            await update.message.reply_text(f"📸 Image {count} receive ho gayi! Aur bhejein ya **/done** dabayein.", parse_mode="Markdown")
        else:
            await update.message.reply_text("Kripya image file bhejein.")
        return

    # --- MULTIPLE PDF MERGE ---
    if action == "merge":
        if update.message.document and update.message.document.file_name.lower().endswith(".pdf"):
            file = await update.message.document.get_file()
            count = len(context.user_data["files"]) + 1
            path = os.path.join(user_dir, f"doc_{count}.pdf")
            await file.download_to_drive(path)
            context.user_data["files"].append(path)
            await update.message.reply_text(f"📑 PDF {count} receive ho gayi! Aur bhejein ya **/done** dabayein.", parse_mode="Markdown")
        else:
            await update.message.reply_text("Kripya valid PDF document bhejein.")
        return

    # --- SINGLE FILE ACTIONS ---
    # File download check
    input_path = None
    if action in ["pdf2img", "compress_pdf", "split_pdf"]:
        if update.message.document and update.message.document.file_name.lower().endswith(".pdf"):
            file = await update.message.document.get_file()
            input_path = os.path.join(user_dir, "input.pdf")
            await file.download_to_drive(input_path)
        else:
            await update.message.reply_text("Kripya valid **PDF document** bhejein.", parse_mode="Markdown")
            return

    elif action == "compress_img":
        photo_file = None
        if update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
        elif update.message.document and update.message.document.file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            photo_file = await update.message.document.get_file()

        if photo_file:
            input_path = os.path.join(user_dir, "input.jpg")
            await photo_file.download_to_drive(input_path)
        else:
            await update.message.reply_text("Kripya valid **Image file** bhejein.", parse_mode="Markdown")
            return

    # Processing Start
    status_msg = await update.message.reply_text("⏳ Processing shuru hai... Kripya thoda intezar karein.")

    if action == "pdf2img":
        imgs = handlers.convert_pdf_to_images(input_path, user_dir)
        for img_path in imgs:
            await update.message.reply_photo(photo=open(img_path, "rb"))
        await update.message.reply_text("✅ Sabhi pages convert ho gaye!")

    elif action == "compress_pdf":
        out_pdf = os.path.join(user_dir, "compressed.pdf")
        handlers.compress_pdf_file(input_path, out_pdf)
        await update.message.reply_document(document=open(out_pdf, "rb"), caption="✅ Compressed PDF")

    elif action == "split_pdf":
        pages = handlers.split_pdf_all_pages(input_path, user_dir)
        for p in pages:
            await update.message.reply_document(document=open(p, "rb"))
        await update.message.reply_text("✅ Sabhi pages alag-alag split ho gaye!")

    elif action == "compress_img":
        out_img = os.path.join(user_dir, "compressed.jpg")
        handlers.compress_image_to_target_kb(input_path, out_img, target_kb=100)
        size_kb = os.path.getsize(out_img) // 1024
        await update.message.reply_document(document=open(out_img, "rb"), caption=f"✅ Compressed Image ({size_kb} KB)")

    # Cleanup & Back to Menu
    await status_msg.delete()
    shutil.rmtree(user_dir, ignore_errors=True)
    context.user_data.clear()
    await update.message.reply_text("Koi aur kaam karna hai? Niche se option chunein:", reply_markup=get_main_menu())

# 4. /done Command (Merge aur Multi-Image ke liye)
async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get("action")
    files = context.user_data.get("files", [])

    if action not in ["img2pdf", "merge"]:
        await update.message.reply_text("Abhi koi multi-file operation nahi chal raha. `/menu` se naya option chunein.", parse_mode="Markdown")
        return

    chat_id = update.message.chat_id
    user_dir = get_user_dir(chat_id)

    if action == "img2pdf":
        if not files:
            await update.message.reply_text("Aapne ek bhi photo nahi bheji. Kripya pehle photo bhejein.")
            return
        status = await update.message.reply_text(f"⏳ {len(files)} photos se PDF ban rahi hai...")
        out_pdf = os.path.join(user_dir, "combined_images.pdf")
        handlers.convert_multiple_images_to_pdf(files, out_pdf)
        await update.message.reply_document(document=open(out_pdf, "rb"), caption=f"✅ {len(files)} photos ki PDF taiyar hai!")
        await status.delete()

    elif action == "merge":
        if len(files) < 2:
            await update.message.reply_text("Merge karne ke liye kam se kam 2 PDF files bhejna zaroori hai.")
            return
        status = await update.message.reply_text(f"⏳ {len(files)} PDFs merge ho rahi hain...")
        out_pdf = os.path.join(user_dir, "merged.pdf")
        handlers.merge_pdf_files(files, out_pdf)
        await update.message.reply_document(document=open(out_pdf, "rb"), caption="✅ Sabhi PDFs ek sath merge ho gayi!")
        await status.delete()

    # Reset & show menu again
    shutil.rmtree(user_dir, ignore_errors=True)
    context.user_data.clear()
    await update.message.reply_text("Agla task chunne ke liye menu use karein:", reply_markup=get_main_menu())

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("done", done_command))
    app.add_handler(CallbackQueryHandler(handle_menu_selection))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_files))

    print("Bot polling start ho gaya hai...")
    app.run_polling()

if __name__ == "__main__":
    main()