import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)

print("=== Step 1: Generate RSA key ===")
rsa_private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
rsa_public = rsa_private.public_key()
print("RSA key generated OK")

print("\n=== Step 2: Generate X25519 (DH) key ===")
dh_private = X25519PrivateKey.generate()
dh_public_bytes = dh_private.public_key().public_bytes_raw()
print(f"DH public key bytes ({len(dh_public_bytes)} bytes): {dh_public_bytes.hex()}")

print("\n=== Step 3: Sign DH key with RSA private key ===")
signature = rsa_private.sign(
    dh_public_bytes,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH,
    ),
    hashes.SHA256(),
)
print(f"Signature OK ({len(signature)} bytes)")

print(
    "\n=== Step 4: Export RSA public key and DH key as base64 (simulating wire format) ==="
)
rsa_pub_b64 = base64.b64encode(
    rsa_public.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
).decode()
dh_pub_b64 = base64.b64encode(dh_public_bytes).decode()
sig_b64 = base64.b64encode(signature).decode()
print(f"RSA public key (b64, first 40 chars): {rsa_pub_b64[:40]}...")
print(f"DH  public key (b64): {dh_pub_b64}")
print(f"Signature      (b64, first 40 chars): {sig_b64[:40]}...")

print("\n=== Step 5: Simulate receiving side — decode and verify ===")
recv_rsa_key = serialization.load_pem_public_key(base64.b64decode(rsa_pub_b64))
recv_dh_bytes = base64.b64decode(dh_pub_b64)
recv_signature = base64.b64decode(sig_b64)

recv_rsa_key.verify(
    recv_signature,
    recv_dh_bytes,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH,
    ),
    hashes.SHA256(),
)
print("✓ Signature verified successfully — the pipeline works end to end")
