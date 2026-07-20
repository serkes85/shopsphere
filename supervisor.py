#!/usr/bin/env python3
"""ShopSphere Supervisor v2.0 - Tek komutla her sey
- Lock file ile cift calisma onleme
- deleteWebhook + drop_pending_updates (409 Conflict cozumu)
- 5 tur agresif kill
- database.py v8->v9 yama (Turkce karakter destegi)
- bashrc OTO-BASLATMA KALDIRILDI (cift supervisor onleme)
- PID dosyasi ile izleme
"""
import subprocess, sys, os, time, signal, glob, shutil, urllib.request, urllib.error

BOT_DIR = os.path.expanduser("~/techdeals-bot")
BOT_TOKEN = "8858951980:AAHzLRLqOlxsAcXXn_GM_XdkUnWWC0aTEIo"
LOCK_FILE = "/tmp/shopsphere_supervisor.lock"
PID_FILE = "/tmp/shopsphere_supervisor.pid"
MY_PID = os.getpid()

def log(m):
    ts = time.strftime("%H:%M:%S")
    print(f"[SUP {ts}] {m}", flush=True)

def check_lock():
    """Cift calismayi onle"""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                old_pid = f.read().strip()
            if old_pid and old_pid != str(MY_PID):
                # Eski surec hala yasiyor mu?
                try:
                    os.kill(int(old_pid), 0)  # Signal 0 = check only
                    log(f"⚠️ Supervisor zaten calisiyor (PID: {old_pid})!")
                    log(f"   Eski supervisor durduruluyor...")
                    os.kill(int(old_pid), signal.SIGKILL)
                    time.sleep(2)
                except (ProcessLookupError, ValueError):
                    pass  # Eski surec olmus, lock dosyasini temizle
        except:
            pass
        try:
            os.remove(LOCK_FILE)
        except:
            pass
    
    # Lock dosyasi olustur
    with open(LOCK_FILE, 'w') as f:
        f.write(str(MY_PID))
    log(f"Lock dosyasi olusturuldu (PID: {MY_PID})")

def clean_lock():
    """Lock dosyasini temizle"""
    try:
        os.remove(LOCK_FILE)
    except:
        pass
    try:
        os.remove(PID_FILE)
    except:
        pass

def kill_old():
    """Eski surecleri DURDUR - once while loop, sonra bot"""
    log("🔪 Eski surecler durduruluyor (5 tur)...")
    
    for i in range(5):
        # ONCE while true döngülerini oldur (onlar bot'u yeniden baslatiyor!)
        subprocess.run(["pkill", "-9", "-f", "while true"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "while true; do python"], capture_output=True)
        
        # Sonra supervisor sureclerini oldur
        subprocess.run(["pkill", "-9", "-f", "supervisor.py"], capture_output=True)
        
        # Sonra bot sureclerini oldur
        subprocess.run(["pkill", "-9", "-f", "bot.py"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "python3 bot.py"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "python bot.py"], capture_output=True)
        
        # Sleep sureclerini temizle
        subprocess.run(["pkill", "-9", "-f", "sleep 15"], capture_output=True)
        subprocess.run(["pkill", "-9", "-f", "sleep 5"], capture_output=True)
        
        # Flask sureclerini temizle
        subprocess.run(["pkill", "-9", "-f", "flask"], capture_output=True)
        
        time.sleep(1)
        
        # Kontrol
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        remaining = [l for l in result.stdout.split('\n') 
                     if ('bot.py' in l or 'supervisor.py' in l) and 'grep' not in l and str(MY_PID) not in l]
        
        if not remaining:
            log(f"  Tur {i+1}: Tum surecler temizlendi ✓")
            break
        else:
            log(f"  Tur {i+1}: {len(remaining)} surec hala calisiyor, tekrar deneniyor...")
    
    # Telegram webhook temizle - 409 Conflict cozumu
    log("🌐 Telegram webhook temizleniyor...")
    for i in range(3):
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, timeout=10)
            log(f"  Webhook temizlendi ({i+1}/3) ✓")
        except Exception as e:
            log(f"  Webhook temizleme ({i+1}/3): {e}")
        time.sleep(2)
    
    log("✅ Eski surecler temizlendi")

def clean_bashrc():
    """bashrc'deki otomatik baslatmayi kaldir (cift supervisor onleme)"""
    bashrc = os.path.expanduser("~/.bashrc")
    if not os.path.exists(bashrc):
        return
    
    try:
        with open(bashrc, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        cleaned = []
        skip_next = False
        for line in lines:
            if 'supervisor.py' in line or '# ShopSphere' in line:
                continue
            cleaned.append(line)
        
        if len(cleaned) != len(lines):
            with open(bashrc, 'w', encoding='utf-8') as f:
                f.writelines(cleaned)
            log("✅ bashrc temizlendi (otomatik baslatma kaldirildi)")
            log("   💡 Termux:Boot ile otomatik baslatma kullanin (daha guvenli)")
    except Exception as e:
        log(f"  bashrc temizleme hatasi: {e}")

def patch():
    """Dosyalari yamala"""
    log("📝 Dosyalar yamalaniyor...")
    
    # bot.py: 50 -> 120
    try:
        fp = os.path.join(BOT_DIR, "bot.py")
        c = open(fp, "r", encoding="utf-8").read()
        if "_cnt < 50" in c:
            c = c.replace("_cnt < 50", "_cnt < 120")
            open(fp, "w", encoding="utf-8").write(c)
            log("  bot.py: 50→120 ✓")
        elif "_cnt < 120" in c:
            log("  bot.py: zaten 120 ✓")
        else:
            log("  bot.py: esik bulunamadi (muhtemelen guncel)")
    except Exception as e:
        log(f"  bot.py hatasi: {e}")

    # database.py: v8 -> v9 (Turkce karakter destegi)
    try:
        fp = os.path.join(BOT_DIR, "database.py")
        c = open(fp, "r", encoding="utf-8").read()
        patched = False
        
        # Yontem 1: Tam eslesme (Turkce karakterler ile)
        for old, new in [
            ("Veritaban\u0131 haz\u0131r (v8)", "Veritaban\u0131 haz\u0131r (v9)"),  # Veritabanı hazır (v8)
            ("Veritabani hazir (v8)", "Veritabani hazir (v9)"),  # ASCII fallback
            ("Veritabani hazır (v8)", "Veritabani hazır (v9)"),  # Kısmi Türkçe
            ("Veritabanı hazir (v8)", "Veritabanı hazir (v9)"),  # Kısmi Türkçe 2
        ]:
            if old in c and "(v9)" not in c:
                c = c.replace(old, new)
                open(fp, "w", encoding="utf-8").write(c)
                log(f"  database.py: v8→v9 ✓ (yontem: tam eslesme)")
                patched = True
                break
        
        # Yontem 2: Generic (v8) -> (v9) fallback
        if not patched and "(v8)" in c and "(v9)" not in c:
            c = c.replace("(v8)", "(v9)")
            open(fp, "w", encoding="utf-8").write(c)
            log("  database.py: v8→v9 ✓ (yontem: generic)")
            patched = True
        
        if not patched:
            if "(v9)" in c:
                log("  database.py: zaten v9 ✓")
            else:
                log("  database.py: (v8) bulunamadi, muhtemelen guncel")
    except Exception as e:
        log(f"  database.py hatasi: {e}")

def clear_cache():
    """Python cache temizle"""
    for d in glob.glob(os.path.join(BOT_DIR, "__pycache__")):
        shutil.rmtree(d, ignore_errors=True)
    log("✅ Cache temizlendi")

def verify():
    """Dosya dogrulama"""
    log("🔍 Dogrulama yapiliyor...")
    
    bot_path = os.path.join(BOT_DIR, "bot.py")
    if os.path.exists(bot_path):
        c = open(bot_path, "r", encoding="utf-8").read()
        if "_cnt < 120" in c:
            log("  bot.py: 120 ✓")
        else:
            log("  bot.py: ⚠️ 120 bulunamadi")
    
    db_path = os.path.join(BOT_DIR, "database.py")
    if os.path.exists(db_path):
        c = open(db_path, "r", encoding="utf-8").read()
        if "(v9)" in c:
            log("  database.py: v9 ✓")
        else:
            log("  database.py: ⚠️ v9 bulunamadi")
    
    # Syntax kontrol
    try:
        subprocess.run([sys.executable, "-c", "import py_compile; py_compile.compile('bot.py', doraise=True)"],
                       cwd=BOT_DIR, capture_output=True, timeout=30)
        log("  bot.py syntax: ✓")
    except:
        log("  bot.py syntax: ⚠️ Hata var!")
    
    try:
        subprocess.run([sys.executable, "-c", "import py_compile; py_compile.compile('database.py', doraise=True)"],
                       cwd=BOT_DIR, capture_output=True, timeout=30)
        log("  database.py syntax: ✓")
    except:
        log("  database.py syntax: ⚠️ Hata var!")

def check_seed():
    """Seed urun sayisi"""
    try:
        import sqlite3
        conn = sqlite3.connect(os.path.join(BOT_DIR, "techdeals.db"))
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM shop_products WHERE user_id=0 AND currency='SEED' AND is_active=1")
        cnt = c.fetchone()[0]
        log(f"🌱 Seed urun: {cnt}")
        conn.close()
    except Exception as e:
        log(f"🌱 Seed kontrol hatasi: {e}")

def run():
    """Bot'u calistir - ana dongu"""
    log("=" * 50)
    log("🤖 Bot baslatiliyor (Durdur: pkill -f supervisor.py)")
    log("=" * 50)
    
    while True:
        try:
            # HER baslangicta webhook temizle - 409 Conflict onleme
            log("🌐 Webhook temizleniyor...")
            for i in range(3):
                try:
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
                    req = urllib.request.Request(url)
                    urllib.request.urlopen(req, timeout=10)
                except:
                    pass
                time.sleep(1)
            log("  Webhook temizlendi ✓")
            
            # Bot'u baslatmadan once eski bot sureci kaldirsa kaldir
            subprocess.run(["pkill", "-9", "-f", "bot.py"], capture_output=True)
            time.sleep(2)
            
            # Bot'u baslat
            log("🚀 Bot baslatiliyor...")
            proc = subprocess.Popen(
                [sys.executable, "-B", "bot.py"],
                cwd=BOT_DIR, 
                stdout=sys.stdout, 
                stderr=sys.stderr
            )
            
            # PID dosyasina yaz
            with open(PID_FILE, 'w') as f:
                f.write(str(proc.pid))
            
            exit_code = proc.wait()
            log(f"⚠️ Bot durdu (kod: {exit_code}), 15sn sonra yeniden baslatilacak...")
            time.sleep(15)
            
        except KeyboardInterrupt:
            log("⏹️ Kullanici durdurdu")
            try:
                proc.terminate()
            except:
                pass
            clean_lock()
            break
        except Exception as e:
            log(f"❌ Hata: {e}")
            time.sleep(15)

def main():
    log("═══════════════════════════════════════════")
    log("🛡️ ShopSphere Supervisor v2.0")
    log("═══════════════════════════════════════════")
    
    # 1) Lock kontrolu
    check_lock()
    
    try:
        # 2) Eski surecleri oldur
        kill_old()
        
        # 3) bashrc temizle
        clean_bashrc()
        
        # 4) Dosya yamalari
        os.chdir(BOT_DIR)
        clear_cache()
        patch()
        verify()
        check_seed()
        
        # 5) wake-lock
        try:
            subprocess.run(["termux-wake-lock"], capture_output=True)
            log("🔒 wake-lock aktif")
        except:
            pass
        
        # 6) Bot'u calistir
        run()
        
    except Exception as e:
        log(f"❌ Supervisor hatasi: {e}")
    finally:
        clean_lock()

if __name__ == "__main__":
    main()
