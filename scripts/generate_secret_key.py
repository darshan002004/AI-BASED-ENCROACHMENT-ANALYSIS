"""
EncroWatch AI — Production Secret Key Generator.
Generates cryptographically strong random tokens suitable for SECRET_KEY,
JWT signing, database passwords, and API credentials.
"""

import secrets

def generate_keys():
    jwt_secret_hex = secrets.token_hex(32)  # 64-character hex string (256-bit entropy)
    jwt_secret_b64 = secrets.token_urlsafe(48)  # 64-character URL-safe string
    db_password = secrets.token_urlsafe(24)

    print("=" * 70)
    print("ENCROWATCH AI — PRODUCTION CRYPTOGRAPHIC CREDENTIAL GENERATOR")
    print("=" * 70)
    print("\n1. Production JWT SECRET_KEY (Hex 256-bit):")
    print(f"   SECRET_KEY={jwt_secret_hex}")
    print("\n2. Alternative JWT SECRET_KEY (URL-Safe Base64):")
    print(f"   SECRET_KEY={jwt_secret_b64}")
    print("\n3. Strong MongoDB Production Password:")
    print(f"   MONGO_INITDB_ROOT_PASSWORD={db_password}")
    print("\n" + "=" * 70)
    print("INSTRUCTIONS:")
    print("- Copy these values into your production '.env' file.")
    print("- NEVER commit '.env' containing these values into version control.")
    print("- Keep a secure backup of these credentials in your vault.")
    print("=" * 70)

if __name__ == "__main__":
    generate_keys()
