"""Voicelink telephony routes."""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voicelink")

# Custom voicelink routes can be added here
