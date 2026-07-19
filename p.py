import sqlite3, datetime, os
os.chdir(os.path.expanduser("~/techdeals-bot"))

# Patch bot.py
with open("bot.py", "r") as f:
    b = f.read()
b = b.replace("_cnt < 50", "_cnt < 120")
with open("bot.py", "w") as f:
    f.write(b)
print("bot.py patched!")

# Patch database.py
with open("database.py", "r") as f:
    d = f.read()
d = d.replace("(v8)", "(v9)")
with open("database.py", "w") as f:
    f.write(d)
print("database.py patched!")

# Delete cache
import shutil, glob
for d2 in glob.glob("__pycache__"):
    shutil.rmtree(d2)
print("cache cleared!")

# Verify
with open("bot.py", "r") as f:
    assert "_cnt < 120" in f.read(), "bot.py patch FAILED!"
with open("database.py", "r") as f:
    assert "(v9)" in f.read(), "database.py patch FAILED!"
print("PATCH VERIFIED!")
