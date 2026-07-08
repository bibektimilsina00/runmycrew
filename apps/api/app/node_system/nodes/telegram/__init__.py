"""Shared brand config for Telegram.

Imported by every manifest (action + trigger + webhook) in this folder
so name/color/icon_slug are defined once. Change here, all variants
pick it up on next backend reload.
"""

NAME = "Telegram"
COLOR = "#ffffff"
ICON_SLUG = "telegram"
