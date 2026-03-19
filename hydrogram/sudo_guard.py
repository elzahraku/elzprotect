#  Hydrogram - Telegram MTProto API Client Library for Python
#  Sudo Guard — Whitelist protection based on Telegram user ID
#
#  Usage:
#      from hydrogram.sudo_guard import sudo_only, owner_only, elz_protect

from __future__ import annotations

import functools
import logging
import sys
from typing import Callable

log = logging.getLogger(__name__)


# ============================================================
# 🔒 ELZ PROTECT — Proteksi deploy di level library
# ============================================================
# Daftar ID Telegram yang diizinkan menjalankan bot.
# Tambahkan ID Anda di sini. Jika kosong atau tidak cocok,
# bot akan langsung berhenti saat dijalankan.
#
# Cara pakai di src.py / main bot:
#   from hydrogram.sudo_guard import elz_protect
#   elz_protect(owner_id=OWNER_ID, elz_ids=ELZ)
# ============================================================

# ✅ GANTI DENGAN ID TELEGRAM ANDA
ELZ_AUTHORIZED_IDS: list[int] = [
    # Contoh: 123456789,
    # Bisa lebih dari satu jika ada ID cadangan
]


def elz_protect(owner_id: int, elz_ids: list[int]) -> None:
    """
    Validasi ID sebelum bot bisa berjalan.

    Dipanggil sekali saat startup di src.py.
    Jika ``owner_id`` atau semua ID di ``elz_ids`` tidak terdaftar
    dalam ``ELZ_AUTHORIZED_IDS``, proses langsung dihentikan
    dengan ``sys.exit(1)``.

    Args:
        owner_id: Nilai ``OWNER_ID`` dari config.
        elz_ids:  List ID dari variabel ``ELZ`` di config.

    Example:
        .. code-block:: python

            from hydrogram.sudo_guard import elz_protect
            from config import OWNER_ID, ELZ

            elz_protect(owner_id=OWNER_ID, elz_ids=ELZ)
    """
    if not ELZ_AUTHORIZED_IDS:
        log.critical(
            "🔒 [ELZ PROTECT] ELZ_AUTHORIZED_IDS kosong! "
            "Tambahkan ID Anda di hydrogram/sudo_guard.py"
        )
        sys.exit(1)

    if owner_id not in ELZ_AUTHORIZED_IDS:
        log.critical(
            "🚫 [ELZ PROTECT] OWNER_ID '%s' tidak diizinkan! "
            "Deploy dibatalkan.",
            owner_id,
        )
        sys.exit(1)

    if not any(uid in ELZ_AUTHORIZED_IDS for uid in elz_ids):
        log.critical(
            "🚫 [ELZ PROTECT] ID ELZ %s tidak ada yang diizinkan! "
            "Deploy dibatalkan.",
            elz_ids,
        )
        sys.exit(1)

    log.info("✅ [ELZ PROTECT] ID terverifikasi. Bot diizinkan berjalan.")
# ============================================================


def sudo_only(func: Callable) -> Callable:
    """Decorator to restrict a handler to sudo users only.

    Sudo users are defined in Client(sudo_users=[...]).
    If the sender is not in the list, the update is silently ignored.

    Example:
        .. code-block:: python

            from hydrogram import Client
            from hydrogram.sudo_guard import sudo_only

            app = Client("bot", sudo_users=[123456789])

            @app.on_message()
            @sudo_only
            async def handler(client, message):
                await message.reply("Only sudo users see this!")
    """

    @functools.wraps(func)
    async def wrapper(client, update, *args, **kwargs):
        user = getattr(update, "from_user", None)
        if user is None or user.id not in client.sudo_users:
            log.warning(
                "Unauthorized access attempt by user_id=%s",
                getattr(user, "id", "unknown"),
            )
            return  # Silently reject
        return await func(client, update, *args, **kwargs)

    return wrapper


def owner_only(func: Callable) -> Callable:
    """Decorator to restrict a handler to the primary owner only.

    The owner is the **first** user ID in Client(sudo_users=[owner_id, ...]).
    If the sender is not the owner, the update is silently ignored.

    Example:
        .. code-block:: python

            from hydrogram import Client
            from hydrogram.sudo_guard import owner_only

            app = Client("bot", sudo_users=[123456789])

            @app.on_message()
            @owner_only
            async def shutdown(client, message):
                await message.reply("Shutting down...")
    """

    @functools.wraps(func)
    async def wrapper(client, update, *args, **kwargs):
        if not client.sudo_users:
            log.warning("owner_only: sudo_users is empty, rejecting all.")
            return
        primary_owner = client.sudo_users[0]
        user = getattr(update, "from_user", None)
        if user is None or user.id != primary_owner:
            log.warning(
                "Non-owner access attempt by user_id=%s",
                getattr(user, "id", "unknown"),
            )
            return  # Silently reject
        return await func(client, update, *args, **kwargs)

    return wrapper
