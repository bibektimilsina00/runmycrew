"""Shared brand config for Vercel.

Imported by every manifest (action + trigger + webhook) in this folder
so name/color/icon_slug are defined once. Change here, all variants
pick it up on next backend reload.
"""

NAME = "Vercel"
COLOR = "#1c1c1c"
ICON_SLUG = "vercel"
