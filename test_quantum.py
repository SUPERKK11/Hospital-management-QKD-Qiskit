from backend.utils.quantum import simulate_qkd_exchange
from backend.utils.encryption import encrypt_data, decrypt_data

print("--- ⚛️ STARTING QUANTUM SIMULATION ⚛️ ---")

# 1. Run QKD
result = simulate_qkd_exchange()
secret_key = result['final_key']
print(f"✅ Key Generated: {secret_key[:10]}... (hidden)")

# 2. Test Encryption
original_msg = "Patient has infinite energy."
print(f"📄 Original: {original_msg}")

encrypted = encrypt_data(original_msg, secret_key)
print(f"🔒 Encrypted: {encrypted}")

decrypted = decrypt_data(encrypted, secret_key)
print(f"🔓 Decrypted: {decrypted}")

if original_msg == decrypted:
    print("--- ✅ SUCCESS: QUANTUM SECURE ---")
else:
    print("--- ❌ FAILURE ---")