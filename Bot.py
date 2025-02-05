import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# Define states
CHOOSE_COUNTRY, ENTER_NUMBER = range(2)

# Predefined country codes
COUNTRY_CODES = {
    "India 🇮🇳": "IN",
    "Nepal 🇳🇵": "NP",
    "United States 🇺🇸": "US",
    "United Kingdom 🇬🇧": "GB",
    "Canada 🇨🇦": "CA",
    "Australia 🇦🇺": "AU",
    "Germany 🇩🇪": "DE",
    "France 🇫🇷": "FR",
    "Italy 🇮🇹": "IT",
    "Spain 🇪🇸": "ES"
}

# Dictionary to store user input
user_data = {}

# Function to start bot
def start(update: Update, context: CallbackContext) -> int:
    keyboard = [[key] for key in COUNTRY_CODES.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text("Please select your country:", reply_markup=reply_markup)
    return CHOOSE_COUNTRY

# Function to store selected country code
def choose_country(update: Update, context: CallbackContext) -> int:
    selected_country = update.message.text
    if selected_country in COUNTRY_CODES:
        user_data[update.message.chat_id] = {"country_code": COUNTRY_CODES[selected_country]}
        update.message.reply_text(f"You selected {selected_country}. Now, send the phone number (without country code).")
        return ENTER_NUMBER
    else:
        update.message.reply_text("Invalid selection. Please choose a valid country.")
        return CHOOSE_COUNTRY

# Function to fetch phone number details
def enter_number(update: Update, context: CallbackContext) -> int:
    chat_id = update.message.chat_id
    if chat_id not in user_data:
        update.message.reply_text("Please start again by selecting your country.")
        return CHOOSE_COUNTRY

    phone_number = update.message.text.strip()
    country_code = user_data[chat_id]["country_code"]

    # Make API request
    api_url = f"https://ar-api-08uk.onrender.com/arcaller?number={phone_number}&countryCode={country_code}"
    response = requests.get(api_url)
    
    if response.status_code != 200:
        update.message.reply_text("Error fetching data. Please try again later.")
        return ConversationHandler.END

    data = response.json()

    # Extract relevant details
    try:
        name = data.get("data", {}).get("name", "Unknown")
        carrier = data.get("phones", {}).get("carrier", "Unknown")
        number_format = data.get("phones", {}).get("nationalFormat", "Unknown")
        country = data.get("addresses", [{}])[0].get("city", "Unknown")
        whatsapp_link = data.get("links", {}).get("whatsapp", "Not available")
        telegram_link = data.get("links", {}).get("telegram", "Not available")
        viber_link = data.get("links", {}).get("viber", "Not available")

        # Send formatted response to user
        message = (
            f"📞 **Phone Number Details:**\n"
            f"🔹 **Name:** {name}\n"
            f"🔹 **Carrier:** {carrier}\n"
            f"🔹 **Number Format:** {number_format}\n"
            f"🔹 **Location:** {country}\n\n"
            f"📲 **Contact Links:**\n"
            f"➡️ [WhatsApp]({whatsapp_link})\n"
            f"➡️ [Telegram]({telegram_link})\n"
            f"➡️ [Viber]({viber_link})"
        )

        update.message.reply_text(message, parse_mode="Markdown")
    except Exception as e:
        update.message.reply_text("Error processing response. Please try again.")

    return ConversationHandler.END

# Function to cancel conversation
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Operation canceled.")
    return ConversationHandler.END

# Main function to set up bot
def main():
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Replace with your bot token
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_COUNTRY: [MessageHandler(Filters.text & ~Filters.command, choose_country)],
            ENTER_NUMBER: [MessageHandler(Filters.text & ~Filters.command, enter_number)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
