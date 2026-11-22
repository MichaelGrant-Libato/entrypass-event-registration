
import base64
from io import BytesIO

import qrcode


def generate_ticket_qr(ticket_code: str) -> str:
    """
    Generate a PNG QR code containing the ticket code.

    Returns a base64 data URI suitable for an HTML image.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )

    qr.add_data(ticket_code)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    encoded_image = base64.b64encode(
        buffer.getvalue()
    ).decode("ascii")

    return f"data:image/png;base64,{encoded_image}"
