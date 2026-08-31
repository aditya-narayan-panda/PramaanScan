from io import BytesIO
from urllib.parse import quote

import qrcode
from qrcode.constants import ERROR_CORRECT_M


def build_verification_url(
    communication_id: str,
    base_url: str = "http://localhost:5173",
) -> str:
    """
    Build the public verification URL encoded inside the QR code.
    Points to the FRONTEND verification page, not the raw API.
    """

    if not communication_id:
        raise ValueError("communication_id is required")

    base_url = base_url.rstrip("/")

    return (
        f"{base_url}/verify/communication/{quote(communication_id, safe='')}"
    )


def generate_qr_bytes(
    communication_id: str,
    base_url: str = "http://127.0.0.1:8000",
) -> bytes:
    """
    Generate a PNG QR code containing the communication verification URL.
    """

    verification_url = build_verification_url(
        communication_id=communication_id,
        base_url=base_url,
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )

    qr.add_data(verification_url)
    qr.make(fit=True)

    image = qr.make_image()

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    return buffer.getvalue()


def generate_qr_data(
    communication_id: str,
    base_url: str = "http://127.0.0.1:8000",
) -> dict:
    """
    Return QR metadata without generating the image.
    Useful for frontend/API responses.
    """

    verification_url = build_verification_url(
        communication_id=communication_id,
        base_url=base_url,
    )

    return {
        "communication_id": communication_id,
        "verification_url": verification_url,
        "format": "PNG",
        "purpose": "Public communication verification",
    }
