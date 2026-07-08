"""Shared brand config for Postmark.

Imported by every manifest (action + trigger + webhook) in this folder
so name/color/icon_slug are defined once. Change here, all variants
pick it up on next backend reload.
"""

NAME = "Postmark"
COLOR = "#ffffff"
ICON_SLUG = "postmark"
