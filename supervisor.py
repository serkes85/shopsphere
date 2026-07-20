#!/usr/bin/env python3
"""
ShopSphere Supervisor v1.0
- Tum surecleri temizler
- Dosyalari yamalar ve dogrular
- Seed urunleri DB'ye ekler
- Botu baslatir ve izler
- Gece 00:00 otomatik guncelleme (cron)
- Termux acilista otomatik baslama (.bashrc)
Kullanim: python3 ~/supervisor.py
Durdurmak: pkill -f supervisor.py
"""
import subprocess, sys, os, time, signal, glob, shutil

BOT_DIR = os.path.expanduser("~/techdeals-bot")
MY_PID = os.getpid()

def log(msg):
    print(f"[SUP] {msg}", flush=True)

def kill_old_processes():
    log("Eski surecler durduruluyor...")
    for line in os.popen("ps -eo pid,args").readlines():
        try:
            parts = line.strip().split(None, 1)
            if len(parts) < 2:
                continue
            pid = int(parts[0])
            cmd = parts[1]
            if pid == MY_PID:
                continue
            if "bot.py" in cmd or "while true" in cmd:
                os.kill(pid, signal.SIGKILL)
                log(f"  Olduruldu: PID {pid} ({cmd[:60]})")
        except (ValueError, ProcessLookupError, PermissionError):
            pass
    time.sleep(3)
    # Tekrar kontrol
    for line in os.popen("ps -eo pid,args").readlines():
        try:
            parts = line.strip().split(None, 1)
            if len(parts) < 2:
                continue
            pid = int(parts[0])
            cmd = parts[1]
            if pid == MY_PID:
                continue
            if "bot.py" in cmd:
                os.kill(pid, signal.SIGKILL)
                log(f"  Tekrar olduruldu: PID {pid}")
        except:
            pass
    time.sleep(2)
    log("Tum eski surecler temizlendi")

def patch_files():
    log("Dosyalar yamalaniyor...")
    patches_applied = 0

    # bot.py - seed threshold
    try:
        with open(os.path.join(BOT_DIR, "bot.py"), "r") as f:
            code = f.read()

        if "_cnt < 50" in code:
            code = code.replace("_cnt < 50", "_cnt < 120")
            with open(os.path.join(BOT_DIR, "bot.py"), "w") as f:
                f.write(code)
            log("  bot.py: seed threshold 50 -> 120")
            patches_applied += 1
        elif "_cnt < 120" in code:
            log("  bot.py: threshold zaten 120")
        else:
            log("  bot.py: threshold bulunamadi!")
    except Exception as e:
        log(f"  bot.py yama hatasi: {e}")

    # database.py - v8 -> v9
    try:
        with open(os.path.join(BOT_DIR, "database.py"), "r") as f:
            code = f.read()

        if "Veritabani hazir (v8)" in code:
            code = code.replace("Veritabani hazir (v8)", "Veritabani hazir (v9)")
            with open(os.path.join(BOT_DIR, "database.py"), "w") as f:
                f.write(code)
            log("  database.py: v8 -> v9")
            patches_applied += 1
        elif "Veritabani hazir (v9)" in code:
            log("  database.py: zaten v9")
        else:
            log("  database.py: versiyon bulunamadi!")
    except Exception as e:
        log(f"  database.py yama hatasi: {e}")

    return patches_applied

def clear_cache():
    for d in glob.glob(os.path.join(BOT_DIR, "__pycache__")):
        shutil.rmtree(d, ignore_errors=True)
    for f in glob.glob(os.path.join(BOT_DIR, "**/*.pyc"), recursive=True):
        try:
            os.remove(f)
        except:
            pass
    log("Cache temizlendi")

def verify_patches():
    log("Dogrulama yapiliyor...")
    ok = True

    with open(os.path.join(BOT_DIR, "bot.py")) as f:
        content = f.read()
    if "_cnt < 120" in content:
        log("  bot.py: threshold=120 DOGRULANDI")
    else:
        log("  bot.py: threshold DOGRULANAMADI!")
        ok = False

    with open(os.path.join(BOT_DIR, "database.py")) as f:
        content = f.read()
    if "Veritabani hazir (v9)" in content:
        log("  database.py: v9 DOGRULANDI")
    else:
        log("  database.py: v9 DOGRULANAMADI!")
        ok = False

    return ok

def add_seed_products():
    log("Seed urunler kontrol ediliyor...")
    try:
        import sqlite3
        db_path = os.path.join(BOT_DIR, "techdeals.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM shop_products WHERE user_id=0 AND currency='SEED' AND is_active=1")
        count = c.fetchone()["cnt"]
        conn.close()

        if count >= 120:
            log(f"  {count} seed urun yeterli")
            return

        log(f"  {count} seed urun var, ekleniyor...")

        # seed_products.py'den ekle
        sys.path.insert(0, BOT_DIR)
        try:
            from seed_products import seed_products_to_db
            added, updated = seed_products_to_db()
            log(f"  seed_products: +{added} yeni, ~{updated} guncelleme")
        except Exception as e:
            log(f"  seed_products hatasi: {e}")

        # db_fix.py calistir
        db_fix_path = os.path.join(BOT_DIR, "db_fix.py")
        if os.path.exists(db_fix_path):
            try:
                exec(open(db_fix_path).read())
                log("  db_fix.py calistirildi")
            except Exception as e:
                log(f"  db_fix.py hatasi: {e}")

        # Kontrol
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM shop_products WHERE user_id=0 AND currency='SEED' AND is_active=1")
        new_count = c.fetchone()[0]
        conn.close()
        log(f"  Toplam seed urun: {new_count}")

    except Exception as e:
        log(f"  Seed hatasi: {e}")

def setup_cron():
    log("Cron ayarlaniyor...")
    try:
        # cronie kontrol
        result = subprocess.run(["which", "crond"], capture_output=True)
        if result.returncode != 0:
            subprocess.run(["pkg", "install", "-y", "cronie"], capture_output=True, timeout=60)

        supervisor_path = os.path.expanduser("~/supervisor.py")
        cron_line = f"0 0 * * * python3 {supervisor_path} >> {BOT_DIR}/cron.log 2>&1"

        # Mevcut crontab oku
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        existing = result.stdout if result.returncode == 0 else ""

        if "supervisor.py" not in existing:
            new_cron = existing + cron_line + "\n"
            process = subprocess.run(["crontab", "-"], input=new_cron, text=True, capture_output=True)
            if process.returncode == 0:
                log("  Cron job eklendi (her gece 00:00)")
            else:
                log(f"  Cron ekleme hatasi: {process.stderr.decode()[:100]}")
        else:
            log("  Cron job zaten mevcut")

        # crond baslat
        subprocess.run(["crond"], capture_output=True)
        log("  crond baslatildi")

    except Exception as e:
        log(f"  Cron hatasi: {e}")

def setup_bashrc():
    log("bashrc ayarlaniyor...")
    try:
        bashrc = os.path.expanduser("~/.bashrc")
        supervisor_cmd = "python3 ~/supervisor.py &"

        existing = ""
        if os.path.exists(bashrc):
            with open(bashrc) as f:
                existing = f.read()

        if "supervisor.py" not in existing:
            with open(bashrc, "a") as f:
                f.write(f"\n# ShopSphere auto-start (supervisor)\n{supervisor_cmd}\n")
            log("  .bashrc otomatik baslatma eklendi")
        else:
            log("  .bashrc zaten yapilandirilmis")

    except Exception as e:
        log(f"  bashrc hatasi: {e}")

def setup_wakelock():
    try:
        subprocess.run(["termux-wake-lock"], capture_output=True)
        log("termux-wake-lock aktif")
    except:
        log("wake-lock ayarlanamadi (normal)")

def run_bot():
    log("=" * 50)
    log("Bot baslatiliyor ve izleniyor...")
    log("Durdurmak icin: pkill -f supervisor.py")
    log("=" * 50)

    while True:
        try:
            proc = subprocess.Popen(
                [sys.executable, "-B", "bot.py"],
                cwd=BOT_DIR,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            proc.wait()
            log(f"Bot durdu (kod: {proc.returncode}), 15sn sonra yeniden baslatilacak...")
            time.sleep(15)
        except KeyboardInterrupt:
            log("Kullanici durdurdu!")
            try:
                proc.terminate()
            except:
                pass
            break

def main():
    log("=" * 50)
    log("ShopSphere Supervisor v1.0")
    log("=" * 50)

    # 1. Eski surecleri oldur
    kill_old_processes()

    # 2. Klasore git
    os.chdir(BOT_DIR)
    if not os.path.exists(BOT_DIR):
        log(f"HA TA: {BOT_DIR} bulunamadi!")
        sys.exit(1)

    # 3. Cache temizle
    clear_cache()

    # 4. Dosyalari yamala
    patches = patch_files()

    # 5. Dogrula
    if not verify_patches():
        log("UYARI: Baz yamalar basarisiz, devam ediliyor...")

    # 6. Seed urunler
    add_seed_products()

    # 7. Wake lock
    setup_wakelock()

    # 8. Cron (gece 00:00 guncelleme)
    setup_cron()

    # 9. bashrc (Termux acilista baslatma)
    setup_bashrc()

    # 10. Botu baslat ve izle
    run_bot()

if __name__ == "__main__":
    main()
