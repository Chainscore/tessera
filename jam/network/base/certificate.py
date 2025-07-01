import os
import base64

from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, PublicFormat
from tsrkit_types import U32, Uint

from jam.logging import get_logger
from jam.types.protocol.crypto import Hash

# Module-specific logger
logger = get_logger("network")

ASN1_PREFIX = bytes.fromhex("302e020100300506032b657004220420")
ZERO_SEED = b"\x00" * 32

def base32_encode(data):
    return base64.b32encode(data).decode("utf-8").lower().replace("=", "")

def generate_san(pubkey: bytes) -> str:
    """
    Compute the alternative name N(k) for a 32-byte Ed25519 public key,
    following the SNP specification.

    N(k) = "e" + B(E32⁻¹(k), 52)
    """
    if len(pubkey) != 32:
        raise ValueError("Public key must be exactly 32 bytes")

    def b(n: Uint[256], l: int) -> str:
        if l == 0:
            return ""
        return alphabet[n % 32] + b(Uint[256](n // 32), l - 1)

    alphabet = "abcdefghijklmnopqrstuvwxyz234567"
    n, _ = Uint[256].decode_from(pubkey)
    return "e" + b(n, 52)

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

    # JIP-5 Sync
    ed25519_secret = Hash.blake2b(bytes("jam_val_key_ed25519", 'utf-8') + seed)
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(ed25519_secret))

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

    san = generate_san(decoded_public_key)

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
    )

    certificate = cert_builder.sign(private_key=private_key, algorithm=None)

    with open(f"seeds/{port}/cert.pem", "wb") as f:
        f.write(certificate.public_bytes(Encoding.PEM))

    return san

def verify_certificate(cert: x509.Certificate):
    try:
        now = datetime.now(timezone.utc)

        if cert.not_valid_before_utc > now:
            raise ValueError("Certificate not yet valid.")

        if cert.not_valid_after_utc < now:
            raise ValueError("Certificate expired.")

        pk = cert.public_key()

        if not isinstance(pk, Ed25519PublicKey):
            raise ValueError("Certificate public key must be Ed25519.")

        test_san = generate_san(pk.public_bytes_raw())

        san_extension = cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        san = san_extension.value.get_values_for_type(x509.general_name.DNSName)

        if len(san) != 1:
            raise ValueError("Certificate must have exactly one Subject Alternative Name.")

        if san[0] != test_san:
            raise ValueError("Subject Alternative Name doesn't match with key.")

        if cert.signature_algorithm_oid != x509.SignatureAlgorithmOID.ED25519:
            raise ValueError("Expected Ed25519 signature algorithm.")

        logger.info("Certificate verification successful!", issuer=cert.issuer)

        return True, None

    except Exception as e:
        return False, e