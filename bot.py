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
from telebot import TeleBot, types, logger
from pymongo import MongoClient

# --- CONFIGURATION ---
TOKEN = "8339449456:AAEvQ_3GvKHynRSn2gf4xXekLOzuAzh833U"
ADMIN_ID = 8504263842
REQUIRED_CHANNELS = ["@Dark_Epic_Modder"] 
LOGO_URL = "https://raw.githubusercontent.com/du-modz/File-Blogger-Website-DUModZ/refs/heads/main/Img/dumodz-logo.webp"
WHL_FILE = "hbctool-0.1.5-96-py3-none-any.whl"

# Logging setup for debugging
logger.setLevel(logging.INFO)

# --- MONGODB CONNECTION ---
try:
    raw_uri = "mongodb+srv://darkepicmodder:" + urllib.parse.quote_plus("#DeM04%App@#") + "@cluster0.9iolf0h.mongodb.net/?appName=Cluster0"
    client = MongoClient(raw_uri, serverSelectionTimeoutMS=5000)
    db = client['hermes_ultra_db']
    users_col = db['users']
    client.admin.command('ping') # Check connection
    print("✅ MongoDB Connected!")
except Exception as e:
    print(f"❌ DB Error: {e}")
    sys.exit(1)

bot = TeleBot(TOKEN, parse_mode="HTML", threaded=True, num_threads=40)

# --- TASK CONTROL ---
MAX_CONCURRENT_TASKS = 5
active_tasks = 0
task_lock = threading.Lock()

# --- HELPER FUNCTIONS ---
def sync_user(user):
    try:
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
    except: pass

def check_join(user_id):
    if user_id == ADMIN_ID: return True
    for channel in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(channel, user_id).status
            if status not in ['member', 'administrator', 'creator']: return False
        except: return False
    return True

# --- ENGINE BOOTSTRAP ---
def bootstrap_engine():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        if os.path.exists(WHL_FILE):
            subprocess.check_call([sys.executable, "-m", "pip", "install", WHL_FILE])
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "hbctool"])
        
        import hbctool.hbc
        # Fix for version 96 support
        if 96 not in hbctool.hbc.HBC:
            latest_v = max(hbctool.hbc.HBC.keys())
            hbctool.hbc.HBC[96] = hbctool.hbc.HBC[latest_v]
            print(f"✅ Hermes v96 mapped to v{latest_v}")
    except Exception as e:
        print(f"⚠️ Bootstrap Warning: {e}")

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    sync_user(message.from_user)
    if not check_join(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        for idx, chan in enumerate(REQUIRED_CHANNELS, 1):
            markup.add(types.InlineKeyboardButton(f"📢 Join Channel {idx}", url=f"https://t.me/{chan[1:]}"))
        markup.add(types.InlineKeyboardButton("🔄 Verify Join", callback_data="verify"))
        bot.send_photo(message.chat.id, LOGO_URL, caption="⚠️ <b>Access Denied!</b>\nPlease join our channels to use this premium tool.", reply_markup=markup)
        return

    welcome = f"🚀 <b>Hermes Engine Pro v96</b>\n\nHello {message.from_user.first_name}!\nStatus: <code>Premium Active</code>\n\nSend me a .bundle file to decompile."
    bot.send_photo(message.chat.id, LOGO_URL, caption=welcome)

# (বাকি ইঞ্জিন লজিক আগের কোডের মতোই থাকবে...)

# --- CRITICAL FIX FOR 24/7 ---
if __name__ == "__main__":
    bootstrap_engine()
    print("✨ Bot is starting...")
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=30, skip_pending=True)
        except Exception as e:
            print(f"⚠️ Polling Error: {e}")
            time.sleep(5) # ৫ সেকেন্ড অপেক্ষা করে আবার রিস্টার্ট হবে_to_message.document.file_id)
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
