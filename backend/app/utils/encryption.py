from cryptography.fernet import Fernet
import base64

def get_fernet(key_hex):
    """
    Convert our Quantum Hex Key into a format Fernet (AES) accepts.
    Fernet needs a 32-byte base64 encoded key.
    """
    # Take first 32 bytes of the hex key
    key_bytes = bytes.fromhex(key_hex[:64]) 
    return Fernet(base64.urlsafe_b64encode(key_bytes))

def encrypt_data(data: str, key_hex: str) -> str:
    """Locks the data using the Quantum Key"""
    f = get_fernet(key_hex)
    return f.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str, key_hex: str) -> str:
    """Unlocks the data using the Quantum Key"""
    f = get_fernet(key_hex)
    return f.decrypt(encrypted_data.encode()).decode()