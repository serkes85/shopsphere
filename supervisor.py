#!/usr/bin/env python3
"""
ShopSphere Supervisor v1.1
- Eski surecleri temizler
- Dosyalari yamalar ve dogrular
- Seed urunleri kontrol eder
- Botu baslatir ve izler
- .bashrc ile otomatik baslama
- termux-wake-lock aktif
Kullanim: python3 ~/supervisor.py
Durdurmak: pkill -f supervisor.py
"""
import subprocess, sys, os, time, signal, glob, shutil

BOT_DIR = os.path.expanduser("~/techdeals-bot")
MY_PID = os.getpid()

def log(msg):
    print(f"[SUP] {msg}", flush=True)

def kill_old():
    log("Eski surecler durduruluyor...")
    try:
        for line in os.popen("ps -eo pid,args").readlines():
            parts = line.strip().split(None, 1)
            if len(parts) < 2: continue
            pid, cmd = int(parts[0]), parts[1]
            if pid == MY_PID: continue
            if "bot.py" in cmd or "while true" in cmd:
                try:
                    os.kill(pid, signal.SIGKILL)
                    log(f"  PID {pid} olduruldu")
                except: pass
    except: pass
    time.sleep(3)
    log("Eski surecler temizlendi")

def patch():
    log("Dosyalar yamalaniyor...")
    p = 0
    try:
        fp = os.path.join(BOT_DIR, "bot.py")
        c = open(fp).read()
        if "_cnt < 50" in c:
            c = c.replace("_cnt < 50", "_cnt < 120")
            open(fp, "w").write(c)
            log("  bot.py: 50->120 OK"); p += 1
        elif "_cnt < 120" in c:
            log("  bot.py: zaten 120")
        else:
            log("  bot.py: esik bulunamadi!")
    except Exception as e:
        log(f"  bot.py hatasi: {e}")

    try:
        fp = os.path.join(BOT_DIR, "database.py")
        c = open(fp).read()
        if "Veritabani hazir (v8)" in c:
            c = c.replace("Veritabani hazir (v8)", "Veritabani hazir (v9)")
            open(fp, "w").write(c)
            log("  database.py: v8->v9 OK"); p += 1
        elif "Veritabani hazir (v9)" in c:
            log("  database.py: zaten v9")
        else:
            log("  database.py: versiyon bulunamadi!")
    except Exception as e:
        log(f"  database.py hatasi: {e}")
    return p

def clear_cache():
    for d in glob.glob(os.path.join(BOT_DIR, "__pycache__")):
        shutil.rmtree(d, ignore_errors=True)
    log("Cache temizlendi")

def verify():
    log("Dogrulama...")
    ok = True
    c = open(os.path.join(BOT_DIR, "bot.py")).read()
    if "_cnt < 120" in c:
        log("  bot.py: 120 DOGRULANDI")
    else:
        log("  bot.py: BASARISIZ!"); ok = False

    c = open(os.path.join(BOT_DIR, "database.py")).read()
    if "Veritabani hazir (v9)" in c:
        log("  database.py: v9 DOGRULANDI")
    else:
        log("  database.py: BASARISIZ!"); ok = False
    return ok

def check_seed():
    log("Seed kontrol...")
    try:
        import sqlite3
        db = os.path.join(BOT_DIR, "techdeals.db")
        conn = sqlite3.connect(db)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM shop_products WHERE user_id=0 AND currency='SEED' AND is_active=1")
        cnt = c.fetchone()[0]
        conn.close()
        log(f"  {cnt} seed urun mevcut")
    except Exception as e:
        log(f"  Seed kontrol hatasi: {e}")

def setup_bashrc():
    log("bashrc ayarlaniyor...")
    try:
        bashrc = os.path.expanduser("~/.bashrc")
        cmd = "python3 ~/supervisor.py &"
        existing = open(bashrc).read() if os.path.exists(bashrc) else ""
        if "supervisor.py" not in existing:
            open(bashrc, "a").write(f"\n# ShopSphere auto-start\n{cmd}\n")
            log("  .bashrc eklendi")
        else:
            log("  .bashrc zaten mevcut")
    except Exception as e:
        log(f"  bashrc hatasi: {e}")

def run():
    log("=" * 50)
    log("Bot baslatiliyor (Durdur: pkill -f supervisor.py)")
    log("=" * 50)
    while True:
        try:
            proc = subprocess.Popen(
                [sys.executable, "-B", "bot.py"],
                cwd=BOT_DIR,
                stdout=sys.stdout, stderr=sys.stderr
            )
            proc.wait()
            log(f"Bot durdu (kod:{proc.returncode}), 15sn sonra yeniden...")
            time.sleep(15)
        except KeyboardInterrupt:
            log("Durduruldu!")
            try: proc.terminate()
            except: pass
            break

def main():
    log("=" * 50)
    log("ShopSphere Supervisor v1.1")
    log("=" * 50)
    kill_old()
    os.chdir(BOT_DIR)
    clear_cache()
    patch()
    if not verify():
        log("UYARI: Yamalar basarisiz!")
    check_seed()
    try:
        subprocess.run(["termux-wake-lock"], capture_output=True)
        log("wake-lock aktif")
    except: pass
    setup_bashrc()
    run()

if __name__ == "__main__":
    main()
