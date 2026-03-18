import os
import base64
import structlog
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PrivateFormat,
    NoEncryption,
    PublicFormat,
)

from typing import TYPE_CHECKING

from cryptography.x509.verification import VerificationError

from tsrkit_types import Uint


if TYPE_CHECKING:
    from jam.settings import Settings

ASN1_PREFIX = bytes.fromhex("302e020100300506032b657004220420")
ZERO_SEED = b"\x00" * 32

logger = structlog.get_logger("network")

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
    n = Uint[256].decode(pubkey)
    return "e" + b(n, 52)


def generate_keys(settings: "Settings") -> str:
    """
    Generate keys for a node running on a given port
        - Goes to /seeds/keys.json to read the secret key
        - Generates the certificate in /seeds/{port}/cert.pem and the public key in /seeds/{port}/pub_key.pem
    Args:
        settings (Settings): Node Settings

    Raises:
        ValueError: If the seed is not 32 bytes long

    Returns:
        str: SAN of the certificate
    """
    port = settings.port

    if port == 0:
        return ""

    seed_dir = f"seeds/{port}"
    key_path = f"{seed_dir}/key.pem"
    pub_path = f"{seed_dir}/pub_key.pem"
    cert_path = f"{seed_dir}/cert.pem"

    # Validate Existing Files
    if os.path.exists(seed_dir) and all(os.path.exists(p) for p in [key_path, pub_path, cert_path]):
        try:
            with open(cert_path, "rb") as f:
                cert = x509.load_pem_x509_certificate(f.read())

            # Validate certificate
            is_valid = verify_certificate(cert)

            # Verify Certificate Public Key matches Settings Public Key
            cert_pub_bytes = cert.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
            matches_settings = (cert_pub_bytes == bytes(settings.ed25519_public))

            if is_valid and matches_settings:
                san_ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
                return san_ext.value.get_values_for_type(x509.DNSName)[0]

        except Exception:
            # Any failure in validation (IO, parsing, or mismatch) triggers regeneration
            pass

    # Regeneration Logic
    # Store private key in /seeds/{port}/key.pem
    # And public key in /seeds/{port}/pub_key.pem

    # If seeds/{port} doesn't exist, create it
    os.makedirs(seed_dir, exist_ok=True)

    # Use pre-computed keys from settings
    private_key = Ed25519PrivateKey.from_private_bytes(bytes(settings.ed25519_private))
    public_key = private_key.public_key()

    private_key_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )

    with open(f"seeds/{port}/key.pem", "wb") as f:
        f.write(private_key_pem)

    public_key_pem = public_key.public_bytes(
        encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo
    )

    with open(f"seeds/{port}/pub_key.pem", "wb") as f:
        f.write(public_key_pem)

    # Create the certificate
    # Store it in /seeds/{port}/cert.pem
    san = generate_san(settings.ed25519_public)
    valid_from = datetime.now(timezone.utc)
    valid_to = valid_from + timedelta(days=365)

    subject = issuer = x509.Name(
        [x509.NameAttribute(x509.NameOID.COMMON_NAME, "TesseraJAM Node Ed25519 Cert")]
    )

    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(valid_from)
        .not_valid_after(valid_to)
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(san)]), critical=False)
    )

    certificate = cert_builder.sign(private_key=private_key, algorithm=None)
    with open(f"seeds/{port}/cert.pem", "wb") as f:
        f.write(certificate.public_bytes(Encoding.PEM))

    return san


def verify_certificate(cert: x509.Certificate):
    try:
        now = datetime.now(timezone.utc)

        if cert.not_valid_before_utc > now:
            raise VerificationError("Certificate not yet valid.")

        if cert.not_valid_after_utc < now:
            raise VerificationError("Certificate expired.")

        pk = cert.public_key()

        if not isinstance(pk, Ed25519PublicKey):
            raise VerificationError("Certificate public key must be Ed25519.")

        test_san = generate_san(pk.public_bytes_raw())

        san_extension = cert.extensions.get_extension_for_oid(
            x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
        )
        san = san_extension.value.get_values_for_type(x509.general_name.DNSName)

        if len(san) != 1:
            raise VerificationError(
                "Certificate must have exactly one Subject Alternative Name."
            )

        if san[0] != test_san:
            raise VerificationError("Subject Alternative Name doesn't match with key.")

        if cert.signature_algorithm_oid != x509.SignatureAlgorithmOID.ED25519:
            raise VerificationError("Expected Ed25519 signature algorithm.")

        logger.debug("Certificate verification successful!", issuer=cert.issuer)

        return True, None

    except Exception as e:
        return False, e
