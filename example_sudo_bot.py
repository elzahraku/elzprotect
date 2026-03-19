# =============================================================
#  Contoh Penggunaan Sistem Sudo Owner di Hydogram
#  File: example_sudo_bot.py
# =============================================================

from hydrogram import Client, filters
from hydrogram.sudo_guard import owner_only, sudo_only

# ✅ Daftarkan Telegram ID yang diizinkan
# ID pertama = owner (pemilik utama)
# ID lainnya = sudo users (admin)
SUDO_USERS = [
    123456789,   # ← Owner utama (ID Telegram kamu)
    987654321,   # ← Sudo user 1
    111222333,   # ← Sudo user 2
]

app = Client(
    "my_bot",
    api_id=12345,
    api_hash="your_api_hash_here",
    bot_token="your_bot_token_here",
    sudo_users=SUDO_USERS,  # ← Daftarkan di sini
)


# ==============================================================
# CARA 1 — Pakai filters.sudo (filter langsung di handler)
# Hanya sudo users yang terdaftar yang bisa akses
# ==============================================================
@app.on_message(filters.sudo)
async def sudo_command(client, message):
    await message.reply(
        f"✅ Halo sudo user!\n"
        f"ID kamu: `{message.from_user.id}`\n"
        f"Kamu terdaftar sebagai sudo user."
    )


# ==============================================================
# CARA 2 — Pakai filters.owner (hanya owner pertama)
# ==============================================================
@app.on_message(filters.owner & filters.command("shutdown"))
async def shutdown_bot(client, message):
    await message.reply("🔴 Bot dimatikan oleh owner.")
    await client.stop()


# ==============================================================
# CARA 3 — Pakai decorator @sudo_only
# ==============================================================
@app.on_message(filters.command("status"))
@sudo_only
async def bot_status(client, message):
    await message.reply(
        "📊 Status bot:\n"
        "- Running ✅\n"
        f"- Sudo users terdaftar: {len(client.sudo_users)}"
    )


# ==============================================================
# CARA 4 — Pakai decorator @owner_only
# ==============================================================
@app.on_message(filters.command("restart"))
@owner_only
async def restart_bot(client, message):
    await message.reply("🔄 Restarting bot...")
    await client.restart()


# ==============================================================
# Handler untuk user TIDAK TERDAFTAR (opsional)
# Kirim pesan penolakan jika bukan sudo user
# ==============================================================
@app.on_message(filters.private & ~filters.sudo)
async def reject_unauthorized(client, message):
    await message.reply(
        "⛔ Kamu tidak memiliki akses untuk menggunakan bot ini.\n"
        "Hubungi pemilik bot untuk mendapatkan akses."
    )


if __name__ == "__main__":
    app.run()
