"""Zadarma telephony routes."""

from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/zadarma")

# Custom zadarma routes can be added here
