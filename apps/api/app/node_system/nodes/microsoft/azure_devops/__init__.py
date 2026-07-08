"""Shared brand config for Azure DevOps.

Imported by every manifest (action + trigger + webhook) in this folder
so name/color/icon_slug are defined once. Change here, all variants
pick it up on next backend reload.
"""

NAME = "Azure DevOps"
COLOR = "#ffffff"
ICON_SLUG = "azure_devops"
