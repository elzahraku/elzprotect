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


def elz_protect(
    owner_id: int,
    sudo_owners: list[int] | None = None,
    devs: list[int] | None = None,
) -> None:
    """
    Validasi ID sebelum bot bisa berjalan.

    Bot diizinkan jalan jika minimal SATU ID yang terdaftar
    di ``ELZ_AUTHORIZED_IDS`` ditemukan di salah satu dari:
    - ``owner_id``
    - ``sudo_owners``
    - ``devs``

    Jika tidak ada satupun yang cocok, proses dihentikan dengan sys.exit(1).

    Args:
        owner_id:     Nilai ``OWNER_ID`` dari config.
        sudo_owners:  List ID dari variabel ``SUDO_OWNERS`` di config.
        devs:         List ID dari variabel ``DEVS`` di config.

    Example:
        .. code-block:: python

            from hydrogram.sudo_guard import elz_protect
            from config import OWNER_ID, SUDO_OWNERS, DEVS

            elz_protect(
                owner_id=OWNER_ID,
                sudo_owners=SUDO_OWNERS,
                devs=DEVS,
            )
    """
    if not ELZ_AUTHORIZED_IDS:
        log.critical(
            "🔒 [ELZ PROTECT] ELZ_AUTHORIZED_IDS kosong! "
            "Tambahkan ID Anda di hydrogram/sudo_guard.py"
        )
        sys.exit(1)

    # Kumpulkan ID dari OWNER_ID, SUDO_OWNERS, DEVS
    all_ids: set[int] = set()
    all_ids.add(owner_id)
    if sudo_owners:
        all_ids.update(sudo_owners)
    if devs:
        all_ids.update(devs)

    # Cek apakah ada minimal satu ID authorized
    matched = all_ids & set(ELZ_AUTHORIZED_IDS)
    if not matched:
        log.critical(
            "🚫 [ELZ PROTECT] Tidak ada ID yang diizinkan ditemukan di config! "
            "Deploy dibatalkan. (Dicek: OWNER_ID, SUDO_OWNERS, DEVS)"
        )
        sys.exit(1)

    log.info(
        "✅ [ELZ PROTECT] ID terverifikasi dari config. Bot diizinkan berjalan."
    )
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
