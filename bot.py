import os
import sys
import shutil
import subprocess
import zipfile
import time
import logging
import threading
import urllib.parse
from datetime import datetime
from telebot import TeleBot, types
from pymongo import MongoClient

# --- CONFIGURATION ---
TOKEN = "8339449456:AAEvQ_3GvKHynRSn2gf4xXekLOzuAzh833U"
ADMIN_ID = 8504263842
# এখানে চ্যানেলের ইউজারনেমগুলো লিস্ট আকারে দিন
REQUIRED_CHANNELS = ["@Dark_Epic_Modder"] 
LOGO_URL = "https://raw.githubusercontent.com/du-modz/File-Blogger-Website-DUModZ/refs/heads/main/Img/dumodz-logo.webp"
WHL_FILE = "hbctool-0.1.5-96-py3-none-any.whl"

# --- DATABASE CONNECTION ---
raw_uri = "mongodb+srv://darkepicmodder:" + urllib.parse.quote_plus("#DeM04%App@#") + "@cluster0.9iolf0h.mongodb.net/?appName=Cluster0"
client = MongoClient(raw_uri)
db = client['hermes_ultra_db']
users_col = db['users']

bot = TeleBot(TOKEN, parse_mode="HTML", threaded=True, num_threads=30)
logging.basicConfig(level=logging.INFO)

# --- CONCURRENCY CONTROL (Max 5 Users) ---
MAX_CONCURRENT_TASKS = 5
active_tasks = 0
task_lock = threading.Lock()

# --- DATABASE FUNCTIONS ---
def sync_user(user):
    existing = users_col.find_one({"user_id": user.id})
    if not existing:
        users_col.insert_one({
            "user_id": user.id,
            "username": f"@{user.username}" if user.username else "N/A",
            "name": user.first_name,
            "joined_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "active",
            "total_tasks": 0
        })
        return "NEW"
    else:
        users_col.update_one({"user_id": user.id}, {"$set": {"last_seen": datetime.now()}})
        return "OLD"

def is_banned(user_id):
    user = users_col.find_one({"user_id": user_id})
    return user.get("status") == "banned" if user else False

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
    except: pass

# --- MULTI-CHANNEL VERIFY ---
def check_join(user_id):
    if user_id == ADMIN_ID: return True
    for channel in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except: return False
    return True

def get_start_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📂 My Profile", callback_data="my_profile"),
        types.InlineKeyboardButton("📜 Commands", callback_data="help_cmd"),
        types.InlineKeyboardButton("📢 Channel", url="https://t.me/Dark_Epic_Modder"),
        types.InlineKeyboardButton("👤 Developer", url="https://t.me/DarkEpicModderBD0x1")
    )
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel"))
    return markup

# --- COMMAND HANDLERS ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_chat_action(message.chat.id, 'typing')
    if is_banned(message.from_user.id):
        return bot.reply_to(message, "🚫 You are banned from using this bot.")
    
    status = sync_user(message.from_user)
    
    if not check_join(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        for idx, chan in enumerate(REQUIRED_CHANNELS, 1):
            markup.add(types.InlineKeyboardButton(f"📢 Channel {idx}", url=f"https://t.me/{chan[1:]}"))
        markup.add(types.InlineKeyboardButton("🔄 Verify Join", callback_data="verify"))
        
        bot.send_photo(message.chat.id, LOGO_URL, 
                       caption=f"<b>⚠️ Access Denied!</b>\n\nDear {message.from_user.first_name}, you must join all our channels to use the Hermes Engine.",
                       reply_markup=markup)
        return

    welcome_text = (
        f"<b>🔥 HERMES ENGINE PRO v96 ACTIVE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>Welcome back, {message.from_user.first_name}!</b>\n"
        f"Status: <code>{status} USER</code>\n"
        f"Engine: <code>Hermes High-Speed v96</code>\n"
        f"Live Tasks: <code>{active_tasks}/{MAX_CONCURRENT_TASKS}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>The most advanced decompiler is now at your service.</i>"
    )
    bot.send_photo(message.chat.id, LOGO_URL, caption=welcome_text, reply_markup=get_start_keyboard(message.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "verify":
        if check_join(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Verified!")
            start_cmd(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Not joined yet!", show_alert=True)

    elif call.data == "my_profile":
        u = users_col.find_one({"user_id": call.from_user.id})
        profile = (
            f"<b>👤 YOUR PREMIUM PROFILE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"ID: <code>{u['user_id']}</code>\n"
            f"Name: <b>{u['name']}</b>\n"
            f"Tasks Done: <code>{u['total_tasks']}</code>\n"
            f"Status: <code>{u['status'].upper()}</code>"
        )
        bot.edit_message_caption(profile, call.message.chat.id, call.message.message_id, reply_markup=get_start_keyboard(call.from_user.id))

# --- ENGINE PROCESSING ---
def process_engine(mode, message, status_msg):
    global active_tasks
    start_time = time.time()
    work_id = f"{message.from_user.id}_{int(time.time())}"
    work_dir = f"workspace_{work_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        import hbctool
        # Download
        bot.send_chat_action(message.chat.id, 'record_video')
        bot.edit_message_text("📥 <b>Downloading Resources... [15%]</b>", message.chat.id, status_msg.message_id)
        
        file_info = bot.get_file(message.reply_to_message.document.file_id)
        file_size = round(file_info.file_size / (1024*1024), 2)
        downloaded = bot.download_file(file_info.file_path)
        input_file = os.path.join(work_dir, "input_data")
        with open(input_file, 'wb') as f: f.write(downloaded)

        # Processing Animation
        bot.edit_message_text("⚙️ <b>Engine Booting: Hermes v96... [45%]</b>", message.chat.id, status_msg.message_id)
        time.sleep(1)
        bot.edit_message_text("🚀 <b>Processing: Injecting Core Logic... [75%]</b>", message.chat.id, status_msg.message_id)

        if mode == "disasm":
            out_path = os.path.join(work_dir, "out")
            hbctool.disasm(input_file, out_path)
            
            zip_name = f"Result_{message.from_user.id}.zip"
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as z:
                for r, _, fs in os.walk(out_path):
                    for f in fs: z.write(os.path.join(r, f), os.path.relpath(os.path.join(r, f), out_path))
            
            bot.send_chat_action(message.chat.id, 'upload_document')
            with open(zip_name, 'rb') as f:
                bot.send_document(message.chat.id, f, caption=f"✅ <b>Decompiled Successfully!</b>\n⏱ <b>Speed:</b> {round(time.time()-start_time, 2)}s\n📦 <b>Size:</b> {file_size} MB")
            os.remove(zip_name)
        else:
            extract_dir = os.path.join(work_dir, "extract")
            with zipfile.ZipFile(input_file, 'r') as z: z.extractall(extract_dir)
            bundle_out = os.path.join(work_dir, "index.android.bundle")
            hbctool.asm(extract_dir, bundle_out)
            
            bot.send_chat_action(message.chat.id, 'upload_document')
            with open(bundle_out, 'rb') as f:
                bot.send_document(message.chat.id, f, caption=f"✅ <b>Compiled Successfully!</b>\n⏱ <b>Speed:</b> {round(time.time()-start_time, 2)}s")

        users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"total_tasks": 1}})
        bot.delete_message(message.chat.id, status_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ <b>Engine Failure:</b>\n<code>{str(e)}</code>", message.chat.id, status_msg.message_id)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
        with task_lock:
            active_tasks -= 1

@bot.message_handler(commands=['disasmdem', 'asmdem'])
def handle_engine(message):
    global active_tasks
    if not check_join(message.from_user.id): return
    if not message.reply_to_message:
        return bot.reply_to(message, "❌ Please reply to a bundle or zip file!")
    
    # Concurrency Control (Admin Bypass)
    if message.from_user.id != ADMIN_ID:
        if active_tasks >= MAX_CONCURRENT_TASKS:
            return bot.reply_to(message, f"⚠️ <b>Server Busy!</b>\nCurrently {active_tasks} users are using the engine. Please wait 1-2 minutes.")

    with task_lock:
        active_tasks += 1

    mode = "disasm" if message.text == "/disasmdem" else "asm"
    status = bot.send_message(message.chat.id, "🚀 <b>Initializing High-Speed Engine...</b>")
    threading.Thread(target=process_engine, args=(mode, message, status)).start()

# --- 24/7 POLLING LOGIC ---
if __name__ == "__main__":
    bootstrap_engine()
    print("✨ Hermes Bot Started!")
    while True:
        try:
            bot.infinity_polling(timeout=90, long_polling_timeout=40)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5) text:
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
