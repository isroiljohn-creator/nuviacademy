"""Utility helpers."""
import hashlib


def hash_phone(phone: str) -> str:
    """Create SHA-256 hash of phone number for dedup."""
    return hashlib.sha256(phone.strip().encode()).hexdigest()


def format_price(amount: int) -> str:
    """Format UZS price: 97000 → '97 000'"""
    return f"{amount:,}".replace(",", " ")
