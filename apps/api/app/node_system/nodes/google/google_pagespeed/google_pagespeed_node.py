"""Google PageSpeed Insights action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.google.google_pagespeed.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GooglePageSpeedNode = build_rest_node(MANIFEST)
