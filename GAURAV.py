import logging
import sqlite3
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import datetime

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
conn = sqlite3.connect('referral_bot.db', check_same_thread=False)
cursor = conn.cursor()

# Create required tables
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    invite_code TEXT UNIQUE,
    referrals INTEGER DEFAULT 0,
    join_date TIMESTAMP
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS referrals (
    referrer_id INTEGER,
    referred_id INTEGER,
    join_date TIMESTAMP,
    PRIMARY KEY (referrer_id, referred_id)
)''')

conn.commit()

# Start command: generate unique referral link
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    invite_code = f"{user_id}_invite"
    
    # Store invite code if not already present
    cursor.execute("INSERT OR REPLACE INTO users (user_id, invite_code, join_date) VALUES (?, ?, ?)",
                   (user_id, invite_code, datetime.datetime.now()))
    conn.commit()

    # Send invite link to the user
    update.message.reply_text(f"Welcome! Your referral link: https://t.me/myqrcod1xv{update.message.from_user.username}?start={invite_code}")

# Track referral join
def track_referral(update: Update, context: CallbackContext) -> None:
    referrer_invite_code = context.args[0] if context.args else None
    if referrer_invite_code:
        user_id = update.message.from_user.id
        
        # Check if user is already in the database (to avoid duplicate entries)
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            update.message.reply_text("You are already registered!")
            return

        # Get the referrer user_id from invite_code
        referrer_id = referrer_invite_code.split('_')[0]
        
        # Add referral to the database
        cursor.execute("INSERT INTO users (user_id, invite_code, join_date) VALUES (?, ?, ?)", 
                       (user_id, f"{user_id}_invite", datetime.datetime.now()))
        conn.commit()
        
        # Track the referral
        cursor.execute("INSERT INTO referrals (referrer_id, referred_id, join_date) VALUES (?, ?, ?)",
                       (referrer_id, user_id, datetime.datetime.now()))
        conn.commit()
        
        # Update referrer’s referral count
        cursor.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (referrer_id,))
        conn.commit()

        update.message.reply_text(f"Thank you for joining via {referrer_invite_code}!")

    else:
        update.message.reply_text("Invalid referral code.")

# Show referral status and eligibility
def status(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    cursor.execute("SELECT referrals FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if result:
        referrals = result[0]
        eligible = "Yes" if referrals >= 10 else "No"
        update.message.reply_text(f"Your referral count: {referrals}\nEligible for giveaway: {eligible}")
    else:
        update.message.reply_text("You are not registered yet. Please use /start to get your referral link.")

# Admin commands
def admin_panel(update: Update, context: CallbackContext) -> None:
    admin_id = update.message.from_user.id
    
    # Check if admin is valid (replace with actual admin user_id)
    if admin_id != 6539807903:
        update.message.reply_text("You are not authorized to view the admin panel.")
        return

    cursor.execute("SELECT user_id, referrals FROM users ORDER BY referrals DESC")
    all_referrals = cursor.fetchall()
    
    message = "Referral Leaderboard:\n"
    for user in all_referrals:
        message += f"User {user[0]}: {user[1]} referrals\n"
    
    update.message.reply_text(message)

def main():
    # Bot Token from BotFather
    token = '7286374610:AAE1h3g6kPCpnCxWOqga_BlypttX7lOdyKY'
    
    # Set up the Updater and Dispatcher
    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher

    # Commands
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('track_referral', track_referral, pass_args=True))
    dispatcher.add_handler(CommandHandler('status', status))
    dispatcher.add_handler(CommandHandler('admin', admin_panel))

    # Start the bot
    updater.start_polling()

    # Run the bot until Ctrl-C is pressed
    updater.idle()

if __name__ == '__main__':
    main()
