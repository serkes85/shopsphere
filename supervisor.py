#!/usr/bin/env python3
"""ShopSphere Supervisor v1.3 - Tek komutla her sey"""
import subprocess, sys, os, time, signal, glob, shutil, urllib.request

BOT_DIR = os.path.expanduser("~/techdeals-bot")
BOT_TOKEN = "8858951980:AAHzLRLqOlxsAcXXn_GM_XdkUnWWC0aTEIo"
MY_PID = os.getpid()

def log(m):
    print(f"[SUP] {m}", flush=True)

def kill_old():
    log("Eski surecler durduruluyor...")
    for i in range(5):
        subprocess.run(["pkill", "-9", "-f", "bot.py"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "while true"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "sleep 15"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "sleep 5"], capture_output=True)
        time.sleep(1)
    # Telegram'i zorla kes
    for i in range(3):
        try:
            urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true")
            log(f"  Webhook temizlendi ({i+1})")
        except: pass
        time.sleep(2)
    log("Eski surecler temizlendi")

def patch():
    log("Dosyalar yamalaniyor...")
    try:
        fp = os.path.join(BOT_DIR, "bot.py")
        c = open(fp, "r", encoding="utf-8").read()
        if "_cnt < 50" in c:
            c = c.replace("_cnt < 50", "_cnt < 120")
            open(fp, "w", encoding="utf-8").write(c)
            log("  bot.py: 50->120 OK")
        elif "_cnt < 120" in c:
            log("  bot.py: zaten 120")
    except Exception as e:
        log(f"  bot.py hatasi: {e}")

    try:
        fp = os.path.join(BOT_DIR, "database.py")
        c = open(fp, "r", encoding="utf-8").read()
        for old, new in [("Veritaban\u0131 haz\u0131r (v8)", "Veritaban\u0131 haz\u0131r (v9)"),
                         ("Veritabani hazir (v8)", "Veritabani hazir (v9)"),
                         ("(v8)", "(v9)")]:
            if old in c and "(v9)" not in c:
                c = c.replace(old, new)
                open(fp, "w", encoding="utf-8").write(c)
                log("  database.py: v8->v9 OK")
                break
        else:
            if "(v9)" in c:
                log("  database.py: zaten v9")
    except Exception as e:
        log(f"  database.py hatasi: {e}")

def clear_cache():
    for d in glob.glob(os.path.join(BOT_DIR, "__pycache__")):
        shutil.rmtree(d, ignore_errors=True)
    log("Cache temizlendi")

def verify():
    log("Dogrulama...")
    c = open(os.path.join(BOT_DIR, "bot.py"), "r", encoding="utf-8").read()
    log("  bot.py: " + ("120 OK" if "_cnt < 120" in c else "BASARISIZ!"))
    c = open(os.path.join(BOT_DIR, "database.py"), "r", encoding="utf-8").read()
    log("  database.py: " + ("v9 OK" if "(v9)" in c else "BASARISIZ!"))

def check_seed():
    try:
        import sqlite3
        conn = sqlite3.connect(os.path.join(BOT_DIR, "techdeals.db"))
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM shop_products WHERE user_id=0 AND currency='SEED' AND is_active=1")
        log(f"Seed urun: {c.fetchone()[0]}")
        conn.close()
    except Exception as e:
        log(f"Seed hatasi: {e}")

def run():
    log("=" * 50)
    log("Bot baslatiliyor (Durdur: pkill -f supervisor.py)")
    log("=" * 50)
    while True:
        try:
            # HER baslangicta webhook temizle - 409 Conflict onleme
            for i in range(3):
                try:
                    urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true")
                except: pass
                time.sleep(1)
            subprocess.run(["pkill", "-9", "-f", "bot.py"], capture_output=True)
            time.sleep(2)

            proc = subprocess.Popen(
                [sys.executable, "-B", "bot.py"],
                cwd=BOT_DIR, stdout=sys.stdout, stderr=sys.stderr
            )
            proc.wait()
            log(f"Bot durdu (kod:{proc.returncode}), 15sn sonra yeniden...")
            time.sleep(15)
        except KeyboardInterrupt:
            try: proc.terminate()
            except: pass
            break

def main():
    log("ShopSphere Supervisor v1.3")
    kill_old()
    os.chdir(BOT_DIR)
    clear_cache()
    patch()
    verify()
    check_seed()
    try:
        subprocess.run(["termux-wake-lock"], capture_output=True)
        log("wake-lock aktif")
    except: pass
    # bashrc
    try:
        bashrc = os.path.expanduser("~/.bashrc")
        existing = open(bashrc, "r", encoding="utf-8").read() if os.path.exists(bashrc) else ""
        if "supervisor.py" not in existing:
            open(bashrc, "a", encoding="utf-8").write("\n# ShopSphere\npython3 ~/supervisor.py &\n")
            log("bashrc eklendi")
    except: pass
    run()

if __name__ == "__main__":
    main()
