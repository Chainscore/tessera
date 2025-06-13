import base64

from datetime import datetime, timedelta, timezone
import json
import os

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, PublicFormat
from tsrkit_types import Bytes, U32

ASN1_PREFIX = bytes.fromhex("302e020100300506032b657004220420")
ZERO_SEED = b"\x00" * 32

def base32_encode(data):
    return base64.b32encode(data).decode("utf-8").lower().replace("=", "")

def generate_keys(port: int):
    """
    Generate keys for a node running on a given port
        - Goes to /seeds/keys.json to read the secret key
        - Generates the certificate in /seeds/{port}/cert.pem and the public key in /seeds/{port}/pub_key.pem
    Args:
        port (int): Port number

    Raises:
        ValueError: If the seed is not 32 bytes long

    Returns:
        str: SAN of the certificate
    """

    seed = b"".join([U32(int(os.environ["SEED"])).encode()] * 8)
    if len(seed) != 32:
        raise ValueError("Seed must be exactly 32 bytes long.")

    # Create the private key from seed and 
    # Store private key in /seeds/{port}/key.pem
    # And public key in /seeds/{port}/pub_key.pem
    # Private_key_base = ASN1_PREFIX + seed
    private_key = Ed25519PrivateKey.from_private_bytes(seed)
    private_key_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption()
    )
    # If seeds/{port} doesn't exist, create it
    if not os.path.exists(f"seeds/{port}"):
        os.makedirs(f"seeds/{port}")

    with open(f"seeds/{port}/key.pem", "wb") as f:
        f.write(private_key_pem)

    public_key = private_key.public_key()

    public_key_pem = public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo
    )


    # If seeds/{port}/pub_key.pem doesn't exist, create it
    with open(f"seeds/{port}/pub_key.pem", "wb") as f:
        f.write(public_key_pem)

    # Create the certificate
    # Store it in /seeds/{port}/cert.pem
    public_key_der = base64.b64decode(public_key_pem.split(b"\n")[1])
    decoded_public_key = public_key_der[-32:]

    san = "e" + base32_encode(decoded_public_key)

    valid_from = datetime.now(timezone.utc)
    valid_to = valid_from + timedelta(days=365)

    subject = issuer = x509.Name([
        x509.NameAttribute(x509.NameOID.COMMON_NAME, "JAM Client Ed25519 Cert")
    ])

    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(valid_from)
        .not_valid_after(valid_to)
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(san)]),
            critical=False
        )
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True
        )
        .add_extension(
            x509.KeyUsage(digital_signature=True, key_cert_sign=True,
                          key_encipherment=False, data_encipherment=False,
                          key_agreement=False, content_commitment=False,
                          crl_sign=False, encipher_only=False, decipher_only=False),
            critical=True
        )
    )

    certificate = cert_builder.sign(private_key=private_key, algorithm=None)

    with open(f"seeds/{port}/cert.pem", "wb") as f:
        f.write(certificate.public_bytes(Encoding.PEM))

    return san
