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
# এখানে চ্যানেলের ইউজারনেম দাও (নতুন চ্যানেল যোগ করতে শুধু লিস্টে লিখে দাও)
REQUIRED_CHANNELS = ["@Dark_Epic_Modder"] 
LOGO_URL = "https://raw.githubusercontent.com/du-modz/File-Blogger-Website-DUModZ/refs/heads/main/Img/dumodz-logo.webp"
WHL_FILE = "hbctool-0.1.5-96-py3-none-any.whl"

# --- DATABASE ---
raw_uri = "mongodb+srv://darkepicmodder:" + urllib.parse.quote_plus("#DeM04%App@#") + "@cluster0.9iolf0h.mongodb.net/?appName=Cluster0"
client = MongoClient(raw_uri)
db = client['hermes_ultra_db']
users_col = db['users']

bot = TeleBot(TOKEN, parse_mode="HTML", threaded=True, num_threads=30)

# --- TASK MANAGEMENT (5 User Limit) ---
MAX_TASKS = 5
current_active_tasks = 0
task_lock = threading.Lock()

def sync_user(user):
    u = users_col.find_one({"user_id": user.id})
    if not u:
        users_col.insert_one({
            "user_id": user.id, "name": user.first_name,
            "joined_at": datetime.now().strftime("%Y-%m-%d"),
            "status": "active", "total_tasks": 0
        })
    else:
        users_col.update_one({"user_id": user.id}, {"$set": {"last_seen": datetime.now()}})

def check_join(user_id):
    if user_id == ADMIN_ID: return True
    for channel in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ['member', 'administrator', 'creator']: return False
        except: return False
    return True

# --- UI HELPERS ---
def get_main_markup(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👤 Profile", callback_data="profile"),
        types.InlineKeyboardButton("📜 Help", callback_data="help"),
        types.InlineKeyboardButton("📢 Channel", url="https://t.me/Dark_Epic_Modder"),
        types.InlineKeyboardButton("👨‍💻 Admin", url="https://t.me/DarkEpicModderBD0x1")
    )
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_stats"))
    return markup

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_chat_action(message.chat.id, 'typing')
    sync_user(message.from_user)
    
    if not check_join(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        for c in REQUIRED_CHANNELS:
            markup.add(types.InlineKeyboardButton(f"Join {c}", url=f"https://t.me/{c[1:]}"))
        markup.add(types.InlineKeyboardButton("🔄 Verify Join", callback_data="verify"))
        bot.send_photo(message.chat.id, LOGO_URL, caption="❌ <b>Access Denied!</b>\nYou must join our channels to use the Hermes Pro Engine.", reply_markup=markup)
        return

    welcome = (
        f"🔥 <b>HERMES PRO ENGINE v96 ACTIVE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Welcome, <b>{message.from_user.first_name}</b>\n"
        f"Server Status: <code>Stable 24/7</code>\n"
        f"Active Tasks: <code>{current_active_tasks}/{MAX_TASKS}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Please use the commands below to start.</i>"
    )
    bot.send_photo(message.chat.id, LOGO_URL, caption=welcome, reply_markup=get_main_markup(message.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    if call.data == "verify":
        if check_join(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Verified!")
            start(call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Join all channels first!", show_alert=True)
    
    elif call.data == "profile":
        u = users_col.find_one({"user_id": call.from_user.id})
        text = f"👤 <b>USER PROFILE</b>\n\nName: {u['name']}\nTasks Done: {u['total_tasks']}\nStatus: {u['status']}"
        bot.edit_message_caption(text, call.message.chat.id, call.message.message_id, reply_markup=get_main_markup(call.from_user.id))

# --- ENGINE PROCESSING ---
def run_engine(mode, message, status_msg):
    global current_active_tasks
    start_time = time.time()
    work_dir = f"task_{message.from_user.id}_{int(time.time())}"
    os.makedirs(work_dir, exist_ok=True)

    try:
        import hbctool
        # Download
        bot.edit_message_text("📥 <b>Downloading bundle...</b>", message.chat.id, status_msg.message_id)
        file_info = bot.get_file(message.reply_to_message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        input_file = os.path.join(work_dir, "input.data")
        with open(input_file, 'wb') as f: f.write(downloaded)

        # Processing Animation
        bot.edit_message_text("⚙️ <b>Engine: Optimizing v96 Core...</b>", message.chat.id, status_msg.message_id)
        time.sleep(1)
        
        if mode == "disasm":
            bot.edit_message_text("🚀 <b>Decompiling... Please wait.</b>", message.chat.id, status_msg.message_id)
            out = os.path.join(work_dir, "out")
            hbctool.disasm(input_file, out)
            zip_f = f"Result_{message.from_user.id}.zip"
            with zipfile.ZipFile(zip_f, 'w') as z:
                for r,d,fs in os.walk(out):
                    for f in fs: z.write(os.path.join(r,f), os.path.relpath(os.path.join(r,f), out))
            with open(zip_f, 'rb') as f:
                bot.send_document(message.chat.id, f, caption=f"✅ <b>Done!</b> Time: {round(time.time()-start_time, 2)}s")
            os.remove(zip_f)
        else:
            bot.edit_message_text("🚀 <b>Assembling... Please wait.</b>", message.chat.id, status_msg.message_id)
            # Assemble logic...
            
        bot.delete_message(message.chat.id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ <b>Error:</b>\n<code>{str(e)}</code>", message.chat.id, status_msg.message_id)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
        with task_lock: current_active_tasks -= 1

@bot.message_handler(commands=['disasmdem', 'asmdem'])
def handle_task(message):
    global current_active_tasks
    if not check_join(message.from_user.id): return
    if not message.reply_to_message:
        return bot.reply_to(message, "❌ Reply to a bundle/zip file!")

    if message.from_user.id != ADMIN_ID:
        if current_active_tasks >= MAX_TASKS:
            return bot.reply_to(message, f"⚠️ <b>Server Full!</b>\nCurrently {MAX_TASKS} users are using the engine. Please wait.")

    with task_lock: current_active_tasks += 1
    
    mode = "disasm" if message.text == "/disasmdem" else "asm"
    status = bot.send_message(message.chat.id, "🚀 <b>Initializing Engine...</b>")
    threading.Thread(target=run_engine, args=(mode, message, status)).start()

# --- BOOTSTRAP ---
def bootstrap():
    try:
        if os.path.exists(WHL_FILE):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", WHL_FILE])
        import hbctool.hbc
        if 96 not in hbctool.hbc.HBC:
            hbctool.hbc.HBC[96] = hbctool.hbc.HBC[max(hbctool.hbc.HBC.keys())]
    except: pass

if __name__ == "__main__":
    bootstrap()
    print("✨ Bot Started Successfully!")
    # Infinity polling with restart logic to prevent 18s success bug
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5) time.sleep(1.5)

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
