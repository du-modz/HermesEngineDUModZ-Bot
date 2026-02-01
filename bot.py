import os
import sys
import shutil
import subprocess
import zipfile
import time
import logging
import threading
import urllib.parse
import signal
from datetime import datetime
from telebot import TeleBot, types
from pymongo import MongoClient

# --- CONFIGURATION ---
TOKEN = "8339449456:AAEvQ_3GvKHynRSn2gf4xXekLOzuAzh833U"
ADMIN_ID = 8504263842
CHANNEL_USERNAMES = ["@Dark_Epic_Modder"]  # Add more if needed
CHANNEL_URLS = {
    "@Dark_Epic_Modder": "https://t.me/Dark_Epic_Modder",
}
WHL_FILE = "hbctool-0.1.5-96-py3-none-any.whl"
MAX_CONCURRENT_USERS = 5
LOGO_URL = "https://raw.githubusercontent.com/du-modz/File-Blogger-Website-DUModZ/refs/heads/main/Img/dumodz-logo.webp"

# --- MONGODB CONNECTION ---
raw_uri = "mongodb+srv://darkepicmodder:" + urllib.parse.quote_plus("#DeM04%App@#") + "@cluster0.9iolf0h.mongodb.net/?appName=Cluster0"
client = MongoClient(raw_uri, connectTimeoutMS=10000, socketTimeoutMS=15000)
db = client['hermes_ultra_db']
users_col = db['users']
sessions_col = db['active_sessions']

bot = TeleBot(TOKEN, parse_mode="HTML", threaded=True, num_threads=30)
logging.basicConfig(level=logging.INFO)

# --- GRACEFUL SHUTDOWN ---
def graceful_exit(signum, frame):
    logging.info("🛑 Graceful shutdown initiated...")
    sessions_col.delete_many({})
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_exit)
signal.signal(signal.SIGINT, graceful_exit)

# --- SESSION MANAGEMENT ---
def get_active_user_count():
    return sessions_col.count_documents({})

def add_session(user_id):
    if user_id == ADMIN_ID:
        return True
    active = get_active_user_count()
    if active >= MAX_CONCURRENT_USERS:
        return False
    sessions_col.update_one(
        {"user_id": user_id},
        {"$set": {"started_at": time.time(), "user_id": user_id}},
        upsert=True
    )
    return True

def remove_session(user_id):
    sessions_col.delete_one({"user_id": user_id})

# --- DATABASE FUNCTIONS ---
def sync_user(user):
    existing = users_col.find_one({"user_id": user.id})
    if not existing:
        users_col.insert_one({
            "user_id": user.id,
            "username": f"@{user.username}" if user.username else "N/A",
            "name": user.first_name,
            "joined_at": datetime.now().strftime("%Y-%m-%d"),
            "status": "active",
            "total_tasks": 0,
            "last_seen": datetime.now()
        })
    else:
        users_col.update_one({"user_id": user.id}, {"$set": {"last_seen": datetime.now()}})

def is_banned(user_id):
    user = users_col.find_one({"user_id": user_id})
    return bool(user and user.get("status") == "banned")

def increment_task(user_id):
    users_col.update_one({"user_id": user_id}, {"$inc": {"total_tasks": 1}})

# --- ENGINE BOOTSTRAP ---
def bootstrap_engine():
    try:
        if os.path.exists(WHL_FILE):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", WHL_FILE])
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "hbctool"])
        import hbctool.hbc
        if 96 not in hbctool.hbc.HBC:
            latest_v = max(hbctool.hbc.HBC.keys())
            hbctool.hbc.HBC[96] = hbctool.hbc.HBC[latest_v]
    except Exception as e:
        logging.error(f"Engine bootstrap failed: {e}")

# --- UI HELPERS ---
def get_main_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("📂 My Profile", callback_data="my_profile")
    btn2 = types.InlineKeyboardButton("📜 Commands", callback_data="help_cmd")
    btn3 = types.InlineKeyboardButton("📢 Channel", url=CHANNEL_URLS["@Dark_Epic_Modder"])
    btn4 = types.InlineKeyboardButton("👤 Developer", url="https://t.me/DarkEpicModderBD0x1")
    markup.add(btn1, btn2, btn3, btn4)
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel"))
    return markup

def get_verify_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in CHANNEL_USERNAMES:
        url = CHANNEL_URLS.get(ch, f"https://t.me/{ch.lstrip('@')}")
        markup.add(types.InlineKeyboardButton(f"📢 Join {ch}", url=url))
    markup.add(types.InlineKeyboardButton("✅ Verify Now", callback_data="verify"))
    return markup

def check_join_all(user_id):
    if user_id == ADMIN_ID:
        return True
    for ch in CHANNEL_USERNAMES:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

# --- ANIMATED PROCESSING ---
def send_processing_animation(chat_id):
    stages = [
        "🔄 Initializing Hermes Engine...",
        "⚙️ Loading v96 Core Modules...",
        "🌀 Analyzing Bytecode Structure...",
        "⚡ Optimizing Neural Decompiler...",
        "🧠 Mapping Symbolic References...",
        "🚀 Finalizing Output Package..."
    ]
    msg = bot.send_message(chat_id, stages[0])
    for i in range(1, len(stages)):
        time.sleep(0.7)
        try:
            bot.edit_message_text(stages[i], chat_id, msg.message_id)
        except:
            break
    return msg

# --- COMMAND HANDLERS ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if is_banned(message.from_user.id):
        return bot.reply_to(message, "🚫 You are banned from using this bot.")
    
    sync_user(message.from_user)
    
    if check_join_all(message.from_user.id):
        caption = (
            "<b>🔥 HERMES ENGINE PRO v96 ACTIVE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Hello, <b>{message.from_user.first_name}!</b>\n"
            "Welcome to the most advanced Hermes Decompiler/Compiler bot.\n\n"
            "🚀 <b>Engine Status:</b> <code>Online</code>\n"
            "🛡 <b>Access:</b> <code>Premium</code>\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        bot.send_photo(
            message.chat.id,
            LOGO_URL,
            caption=caption,
            reply_markup=get_main_keyboard(message.from_user.id)
        )
    else:
        bot.send_photo(
            message.chat.id,
            LOGO_URL,
            caption="<b>⚠️ Access Denied!</b>\nYou must join all required channels to use the engine.",
            reply_markup=get_verify_markup()
        )

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    try:
        if call.data == "my_profile":
            u = users_col.find_one({"user_id": call.from_user.id})
            if not u:
                sync_user(call.from_user)
                u = users_col.find_one({"user_id": call.from_user.id})
            profile = (
                f"<b>👤 YOUR PROFILE</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"ID: <code>{u['user_id']}</code>\n"
                f"Name: <b>{u['name']}</b>\n"
                f"Username: {u['username']}\n"
                f"Joined: <code>{u['joined_at']}</code>\n"
                f"Tasks Done: <code>{u['total_tasks']}</code>\n"
                f"Status: <code>{u['status'].upper()}</code>"
            )
            bot.edit_message_caption(profile, call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(call.from_user.id))

        elif call.data == "help_cmd":
            help_text = (
                "<b>📥 USER COMMANDS</b>\n\n"
                "⚡ <code>/disasmdem</code> - Reply to index.android.bundle to decompile.\n"
                "⚡ <code>/asmdem</code> - Reply to zip file to compile.\n"
                "⚡ <code>/start</code> - Restart the bot interface.\n\n"
                "<i>Note: Process may take 1-2 mins based on file size.</i>"
            )
            bot.edit_message_caption(help_text, call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(call.from_user.id))

        elif call.data == "admin_panel" and call.from_user.id == ADMIN_ID:
            total = users_col.count_documents({})
            adm_text = (
                f"<b>🛠 ADMIN DASHBOARD</b>\n\n"
                f"Total Users: <code>{total}</code>\n"
                f"Active Sessions: <code>{get_active_user_count()}</code>\n"
                f"Engine: <code>Hermes v96</code>\n\n"
                f"<b>Admin Commands:</b>\n"
                f"/stats - Full stats\n"
                f"/broadcast - Message all\n"
                f"/ban [ID] - Block user\n"
                f"/unban [ID] - Unblock user\n"
                f"/user [ID] - View user info\n"
                f"/clearlogs - Clear session logs"
            )
            bot.edit_message_caption(adm_text, call.message.chat.id, call.message.message_id, reply_markup=get_main_keyboard(call.from_user.id))

        elif call.data == "verify":
            if check_join_all(call.from_user.id):
                bot.answer_callback_query(call.id, "✅ Verified!")
                start_cmd(call.message)
            else:
                bot.answer_callback_query(call.id, "❌ Not joined all channels!", show_alert=True)
    except Exception as e:
        logging.error(f"Callback error: {e}")
        bot.answer_callback_query(call.id, "⚠️ An error occurred. Please restart with /start.")

# --- ENGINE PROCESSING ---
def process_engine(mode, message, original_status_msg):
    user_id = message.from_user.id
    if not add_session(user_id):
        bot.edit_message_text(
            f"⚠️ <b>Server Busy!</b>\nOnly {MAX_CONCURRENT_USERS} users allowed simultaneously.\nPlease try again later.",
            message.chat.id, original_status_msg.message_id
        )
        return

    work_id = f"{user_id}_{int(time.time())}"
    work_dir = f"workspace_{work_id}"
    os.makedirs(work_dir, exist_ok=True)

    try:
        bot.send_chat_action(message.chat.id, 'typing')
        time.sleep(0.3)
        bot.send_chat_action(message.chat.id, 'upload_document')

        anim_msg = send_processing_animation(message.chat.id)

        file_info = bot.get_file(message.reply_to_message.document.file_id)
        file_size = message.reply_to_message.document.file_size
        downloaded = bot.download_file(file_info.file_path)
        input_file = os.path.join(work_dir, "input_data")
        with open(input_file, 'wb') as f:
            f.write(downloaded)

        size_mb = round(file_size / (1024 * 1024), 2)
        bot.edit_message_text(
            f"📊 <b>File Info</b>\nSize: <code>{size_mb} MB</code>\nSpeed: <code>~12.4 MB/s</code>\nETA: <code>~{max(5, int(size_mb/12))} sec</code>",
            message.chat.id, anim_msg.message_id
        )
        time.sleep(1)

        import hbctool
        increment_task(user_id)

        if mode == "disasm":
            out_path = os.path.join(work_dir, "out")
            hbctool.disasm(input_file, out_path)
            zip_name = f"Result_{work_id}.zip"
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                for root, _, files in os.walk(out_path):
                    for f in files:
                        z.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), out_path))
            with open(zip_name, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="✅ <b>Decompiled Successfully!</b>")
            os.remove(zip_name)
        else:
            extract_dir = os.path.join(work_dir, "extract")
            with zipfile.ZipFile(input_file, 'r') as z:
                z.extractall(extract_dir)
            bundle_out = os.path.join(work_dir, "index.android.bundle")
            hbctool.asm(extract_dir, bundle_out)
            with open(bundle_out, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="✅ <b>Compiled Successfully!</b>")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ <b>Error:</b>\n<code>{str(e)[:200]}</code>")
    finally:
        remove_session(user_id)
        shutil.rmtree(work_dir, ignore_errors=True)
        try:
            bot.delete_message(message.chat.id, original_status_msg.message_id)
        except:
            pass

@bot.message_handler(commands=['disasmdem', 'asmdem'])
def handle_engine(message):
    if is_banned(message.from_user.id):
        return
    if not check_join_all(message.from_user.id):
        return bot.reply_to(message, "❌ Please join all channels first!")
    if not message.reply_to_message or not getattr(message.reply_to_message, 'document', None):
        return bot.reply_to(message, "❌ Please reply to a valid file!")

    mode = "disasm" if message.text == "/disasmdem" else "asm"
    status = bot.send_message(message.chat.id, "⏳ <b>Checking resources...</b>")
    threading.Thread(target=process_engine, args=(mode, message, status), daemon=True).start()

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['broadcast'])
def broadcast_msg(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace("/broadcast ", "").strip()
    if not text:
        return bot.reply_to(message, "Usage: <code>/broadcast Hello!</code>")
    sent = 0
    for user in users_col.find({}):
        try:
            bot.send_message(user['user_id'], f"📢 <b>ANNOUNCEMENT</b>\n\n{text}")
            sent += 1
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Broadcast sent to <code>{sent}</code> users.")

@bot.message_handler(commands=['ban', 'unban'])
def ban_unban(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "Usage: <code>/ban 123456789</code>")
    try:
        uid = int(parts[1])
        action = "ban" if "ban" in message.text else "unban"
        result = users_col.update_one({"user_id": uid}, {"$set": {"status": "banned" if action == "ban" else "active"}})
        if result.matched_count == 0:
            bot.send_message(ADMIN_ID, "User not found in database.")
        else:
            bot.send_message(ADMIN_ID, f"{'🛑' if action=='ban' else '🟢'} User <code>{uid}</code> {'banned' if action=='ban' else 'unbanned'}.")
    except ValueError:
        bot.send_message(ADMIN_ID, "Invalid user ID.")

@bot.message_handler(commands=['user'])
def view_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        uid = int(message.text.split()[1])
        u = users_col.find_one({"user_id": uid})
        if not u:
            return bot.send_message(ADMIN_ID, "User not found.")
        info = (
            f"<b>👤 USER INFO</b>\n"
            f"ID: <code>{u['user_id']}</code>\n"
            f"Name: {u['name']}\n"
            f"Username: {u['username']}\n"
            f"Joined: {u['joined_at']}\n"
            f>Status: <code>{u['status'].upper()}</code>\n"
            f"Tasks: <code>{u['total_tasks']}</code>"
        )
        bot.send_message(ADMIN_ID, info)
    except:
        bot.send_message(ADMIN_ID, "Usage: <code>/user 123456789</code>")

@bot.message_handler(commands=['clearlogs'])
def clear_logs(message):
    if message.from_user.id == ADMIN_ID:
        sessions_col.delete_many({})
        bot.send_message(ADMIN_ID, "🧹 Active sessions cleared.")

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    total = users_col.count_documents({})
    banned = users_col.count_documents({"status": "banned"})
    active_sess = get_active_user_count()
    recent = users_col.find().sort("_id", -1).limit(5)
    res = f"📊 <b>BOT STATISTICS</b>\n\nTotal: {total}\nBanned: {banned}\nActive Now: {active_sess}\n\n<b>Recent:</b>\n"
    for r in recent:
        res += f"- {r['name']} ({r['user_id']})\n"
    bot.send_message(ADMIN_ID, res)

# --- MAIN ENTRY ---
if __name__ == "__main__":
    bootstrap_engine()
    print("✨ Hermes Bot Premium Started! (PID: {})".format(os.getpid()))
    bot.infinity_polling(timeout=60, long_polling_timeout=30)     message.chat.id, anim_msg.message_id
        )
        time.sleep(1.5)

        import hbctool
        increment_task(user_id)

        if mode == "disasm":
            out_path = os.path.join(work_dir, "out")
            hbctool.disasm(input_file, out_path)
            zip_name = f"Result_{work_id}.zip"
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                for r, _, fs in os.walk(out_path):
                    for f in fs:
                        z.write(os.path.join(r, f), os.path.relpath(os.path.join(r, f), out_path))
            with open(zip_name, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="✅ <b>Decompiled Successfully!</b>")
            os.remove(zip_name)
        else:
            extract_dir = os.path.join(work_dir, "extract")
            with zipfile.ZipFile(input_file, 'r') as z:
                z.extractall(extract_dir)
            bundle_out = os.path.join(work_dir, "index.android.bundle")
            hbctool.asm(extract_dir, bundle_out)
            with open(bundle_out, 'rb') as f:
                bot.send_document(message.chat.id, f, caption="✅ <b>Compiled Successfully!</b>")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ <b>Error:</b>\n<code>{str(e)[:200]}</code>")
    finally:
        remove_session(user_id)
        shutil.rmtree(work_dir, ignore_errors=True)
        try:
            bot.delete_message(message.chat.id, original_status_msg.message_id)
        except:
            pass

@bot.message_handler(commands=['disasmdem', 'asmdem'])
def handle_engine(message):
    if is_banned(message.from_user.id):
        return
    if not check_join_all(message.from_user.id):
        return bot.reply_to(message, "❌ Please join all channels first!")
    if not message.reply_to_message or not message.reply_to_message.document:
        return bot.reply_to(message, "❌ Please reply to a valid file!")

    mode = "disasm" if message.text == "/disasmdem" else "asm"
    status = bot.send_message(message.chat.id, "⏳ <b>Checking resources...</b>")
    threading.Thread(target=process_engine, args=(mode, message, status), daemon=True).start()

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['broadcast'])
def broadcast_msg(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace("/broadcast ", "").strip()
    if not text:
        return bot.reply_to(message, "Usage: <code>/broadcast Hello!</code>")
    sent = 0
    for user in users_col.find({}):
        try:
            bot.send_message(user['user_id'], f"📢 <b>ANNOUNCEMENT</b>\n\n{text}")
            sent += 1
        except: pass
    bot.send_message(ADMIN_ID, f"✅ Broadcast sent to <code>{sent}</code> users.")

@bot.message_handler(commands=['ban', 'unban'])
def ban_unban(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "Usage: <code>/ban 123456789</code>")
    uid = int(parts[1])
    action = "ban" if "ban" in message.text else "unban"
    users_col.update_one({"user_id": uid}, {"$set": {"status": "banned" if action == "ban" else "active"}}, upsert=False)
    bot.send_message(ADMIN_ID, f"{'🛑' if action=='ban' else '🟢'} User <code>{uid}</code> {'banned' if action=='ban' else 'unbanned'}.")

@bot.message_handler(commands=['user'])
def view_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        uid = int(message.text.split()[1])
        u = users_col.find_one({"user_id": uid})
        if not u:
            return bot.send_message(ADMIN_ID, "User not found.")
        info = (
            f"<b>👤 USER INFO</b>\n"
            f"ID: <code>{u['user_id']}</code>\n"
            f"Name: {u['name']}\n"
            f"Username: {u['username']}\n"
            f"Joined: {u['joined_at']}\n"
            f>Status: <code>{u['status'].upper()}</code>\n"
            f"Tasks: <code>{u['total_tasks']}</code>"
        )
        bot.send_message(ADMIN_ID, info)
    except:
        bot.send_message(ADMIN_ID, "Usage: <code>/user 123456789</code>")

@bot.message_handler(commands=['clearlogs'])
def clear_logs(message):
    if message.from_user.id == ADMIN_ID:
        sessions_col.delete_many({})
        bot.send_message(ADMIN_ID, "🧹 Active sessions cleared.")

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    total = users_col.count_documents({})
    banned = users_col.count_documents({"status": "banned"})
    active_sess = get_active_user_count()
    recent = users_col.find().sort("_id", -1).limit(5)
    res = f"📊 <b>BOT STATISTICS</b>\n\nTotal: {total}\nBanned: {banned}\nActive Now: {active_sess}\n\n<b>Recent:</b>\n"
    for r in recent: res += f"- {r['name']} ({r['user_id']})\n"
    bot.send_message(ADMIN_ID, res)

# --- AUTO RESTART SAFE LOOP ---
def auto_restart():
    while True:
        time.sleep(20000)  # ~5.5 hours
        os._exit(0)

if __name__ == "__main__":
    bootstrap_engine()
    threading.Thread(target=auto_restart, daemon=True).start()
    print("✨ Hermes Bot Premium Started!")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)disasmdem" else "asm"
    status = bot.send_message(message.chat.id, "🚀 <b>Initializing Hermes Engine...</b>")
    threading.Thread(target=process_engine, args=(mode, message, status)).start()

# --- ADMIN FEATURES ---
@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    total = users_col.count_documents({})
    bot.send_message(ADMIN_ID, f"📊 <b>LIVE STATS</b>\n\nTotal Users: {total}\nActive Tasks: {active_tasks}/{MAX_CONCURRENT_TASKS}")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    text = message.text.replace("/broadcast ", "")
    users = users_col.find({})
    for u in users:
        try: bot.send_message(u['user_id'], f"📢 <b>Notification:</b>\n\n{text}")
        except: pass

@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        target = int(message.text.split()[1])
        users_col.update_one({"user_id": target}, {"$set": {"status": "banned"}})
        bot.reply_to(message, "✅ User Banned.")
    except: bot.reply_to(message, "Use: /ban [ID]")

# --- AUTO RESTART ---
def auto_restart():
    time.sleep(21000) # ~6 hours
    os._exit(0)

if __name__ == "__main__":
    bootstrap_engine()
    threading.Thread(target=auto_restart, daemon=True).start()
    print("✨ Bot is Online!")
    bot.infinity_polling(timeout=90)  recent = users_col.find().sort("_id", -1).limit(5)
    
    res = f"📊 <b>BOT STATISTICS</b>\n\nTotal: {total}\nBanned: {banned}\n\n<b>Recent:</b>\n"
    for r in recent: res += f"- {r['name']} ({r['user_id']})\n"
    bot.send_message(ADMIN_ID, res)

# --- 24/7 AUTO RESTART ---
def auto_restart():
    time.sleep(20000) # 5.5 hours
    os._exit(0)

if __name__ == "__main__":
    bootstrap_engine()
    threading.Thread(target=auto_restart, daemon=True).start()
    print("✨ Bot Started Successfully!")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)
