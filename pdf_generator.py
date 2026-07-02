import io

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _qr_image_reader(url: str) -> ImageReader:
    qr = qrcode.QRCode(
        version=6,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=3,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1a1a1a", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def _hline(c: canvas.Canvas, x1: float, x2: float, y: float, width: float = 0.5):
    c.setLineWidth(width)
    c.setStrokeColor(colors.black)
    c.line(x1, y, x2, y)


def _two_col_field(
    c: canvas.Canvas,
    label1: str,
    value1: str,
    label2: str,
    value2: str,
    y: float,
    left_x: float,
    mid_x: float,
    right_x: float,
    row_h: float = 28,
):
    """Draw one row with two label/value pairs side by side."""
    c.setFont("Helvetica", 8.5)
    c.setFillColor(colors.black)
    c.drawString(left_x, y + 8, label1)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(left_x, y - 4, value1 or "—")

    if label2:
        c.setFont("Helvetica", 8.5)
        c.setFillColor(colors.black)
        c.drawString(mid_x, y + 8, label2)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(mid_x, y - 4, value2 or "—")


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------


def generate_certificate_pdf(record: dict, record_url: str) -> bytes:
    buf = io.BytesIO()
    W, H = A4  # 595 x 842 pts
    c = canvas.Canvas(buf, pagesize=A4)

    OM = 18  # outer margin
    IM = 25  # inner margin (content starts here)

    # ── Borders ──────────────────────────────────────────────────────────────
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(OM, OM, W - 2 * OM, H - 2 * OM)
    c.setLineWidth(0.6)
    c.rect(OM + 5, OM + 5, W - 2 * (OM + 5), H - 2 * (OM + 5))

    # ── QR code — top left ───────────────────────────────────────────────────
    qr_size = 82
    qr_x = IM + 2
    qr_y = H - IM - 5 - qr_size
    try:
        qr_ir = _qr_image_reader(record_url)
        c.drawImage(qr_ir, qr_x, qr_y, width=qr_size, height=qr_size)
    except Exception:
        c.rect(qr_x, qr_y, qr_size, qr_size)  # fallback empty box

    # ── WDR seal — top right ─────────────────────────────────────────────────
    seal_x = W - IM - 84
    seal_y = qr_y
    c.setLineWidth(1)
    c.setStrokeColor(colors.HexColor("#1a4f8a"))
    c.circle(seal_x + 40, seal_y + 42, 38, stroke=1, fill=0)
    c.circle(seal_x + 40, seal_y + 42, 30, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.HexColor("#1a4f8a"))
    c.drawCentredString(seal_x + 40, seal_y + 46, "WDR")
    c.setFont("Helvetica", 6.5)
    c.drawCentredString(seal_x + 40, seal_y + 36, "OFFICIAL")
    c.drawCentredString(seal_x + 40, seal_y + 27, "REGISTRY")

    # ── Center header text ───────────────────────────────────────────────────
    cx = W / 2
    y = H - IM - 10

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    c.drawCentredString(cx, y, "Form No. WD-1")
    y -= 14

    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(cx, y, "WESTEROS DRAGON REGISTRATION SYSTEM")
    y -= 13

    c.setFont("Helvetica", 9)
    c.drawCentredString(cx, y, "Office of the Master of Dragons")
    y -= 11

    c.drawCentredString(cx, y, "Citadel of Oldtown  —  Records Division")
    y -= 11

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(cx, y, "Registrar - KING'S LANDING DRAGONPIT, WESTEROS")
    y -= 18

    c.setFont("Helvetica", 10)
    c.drawCentredString(cx, y, "Dragon Registration Certificate")
    y -= 16

    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.black)
    c.drawCentredString(cx, y, "DRAGON REGISTRATION CERTIFICATE")
    y -= 12

    # ── Legal subtitle ───────────────────────────────────────────────────────
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.black)
    legal1 = "(Issued under the Westeros Dragon Registration Act, 7AC and"
    legal2 = "the Dragon Registry Rules, 7AC Rule 8/13 of the Records Division)"
    c.drawCentredString(cx, y, legal1)
    y -= 9
    c.drawCentredString(cx, y, legal2)
    y -= 8

    _hline(c, OM + 6, W - OM - 6, y)
    y -= 3

    # ── Certifying paragraph ─────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 8.5)
    cert_para = (
        "This is to certify that the following information has been taken from the official Dragon Registry, "
        "which is the record maintained by the"
    )
    cert_para2 = "Office of the Master of Dragons, Citadel of Oldtown, Westeros."
    c.drawString(IM + 5, y, cert_para)
    y -= 11
    c.drawString(IM + 5, y, cert_para2)
    y -= 8

    _hline(c, OM + 6, W - OM - 6, y)
    y -= 16

    # ── Two-column fields ────────────────────────────────────────────────────
    left_x = IM + 5
    mid_x = W / 2 + 5
    right_x = W - IM - 10

    def fmt_date(d):
        if not d:
            return "—"
        try:
            from datetime import date

            if isinstance(d, str):
                parts = d[:10].split("-")
                return f"{parts[2]}/{parts[1]}/{parts[0]}"
            return d.strftime("%d/%m/%Y")
        except Exception:
            return str(d)

    fields = [
        (
            "नाम/Name",
            record.get("child_name", ""),
            "लिंग/Gender",
            record.get("gender", ""),
        ),
        (
            "जन्म दिनांक/Date of Birth",
            fmt_date(record.get("dob")),
            "राइडर का नाम/Signer's Name",
            record.get("rider_name", ""),
        ),
        (
            "Mother Name/माता का नाम",
            record.get("mother_name", ""),
            "Father Name/पिता का नाम",
            record.get("father_name", ""),
        ),
        (
            "जन्म स्थान/Place of Birth",
            record.get("place_of_birth", ""),
            "Wingspan / पंखों का फैलाव",
            f"{record['wingspan_ft']} ft" if record.get("wingspan_ft") else "—",
        ),
        (
            "Temperament / स्वभाव",
            record.get("temperament") or "—",
            "Verified by / सत्यापित",
            "Maester Aldric, Records Keeper",
        ),
    ]

    row_h = 28
    for lbl1, val1, lbl2, val2 in fields:
        _two_col_field(c, lbl1, val1, lbl2, val2, y, left_x, mid_x, right_x, row_h)
        y -= row_h

    # Address-style wide field
    y -= 4
    _hline(c, OM + 6, W - OM - 6, y + row_h - 2, 0.3)
    y -= 8

    # ── Registration number row ───────────────────────────────────────────────
    _hline(c, OM + 6, W - OM - 6, y + 12, 0.5)
    y -= 6

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.black)
    c.drawString(left_x, y, "Registration No. / रजिस्ट्रेशन संख्या:")
    c.drawString(mid_x, y, "Date of Registration / रजिस्ट्रेशन की तारीख:")
    y -= 14

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#1a4f8a"))
    c.drawString(left_x, y, record.get("token", "—"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(mid_x, y, fmt_date(record.get("created_at", "")))
    y -= 20

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    c.drawString(left_x, y, "Remarks / टिप्पणी If Any:")
    y -= 24

    _hline(c, OM + 6, W - OM - 6, y + 14, 0.5)

    # ── Date of issue + Signature ─────────────────────────────────────────────
    y -= 4
    c.setFont("Helvetica-Bold", 9)
    issue_date = fmt_date(record.get("created_at", ""))
    c.drawString(left_x, y, f"Date of Issue / जारी करने की तारीख :  {issue_date}")

    c.setFont("Helvetica", 8)
    c.drawRightString(right_x, y, "Signed by: Maester Aldric")
    y -= 10
    c.drawRightString(right_x, y, "Location: KING'S LANDING, WESTEROS")
    y -= 10
    c.drawRightString(right_x, y, f"Date: {issue_date}")
    y -= 20

    c.setFont("Helvetica", 8)
    c.drawRightString(
        right_x,
        y,
        "Signature of Issuing Authority / जारी करने वाले प्राधिकारी के हस्ताक्षर",
    )

    _hline(c, OM + 6, W - OM - 6, y - 4, 0.5)
    y -= 18

    # ── Footer notes ─────────────────────────────────────────────────────────
    c.setFont("Helvetica", 6.5)
    c.setFillColor(colors.black)

    notes = [
        "Note: This certificate is issued by the Westeros Dragon Registration System (WDR) "
        "and is valid across all seven kingdoms.",
        "Use of digital records for dragon registration is recognized by the Office of the "
        "Master of Dragons vide circular WDR/7AC/2026.",
        "Records may be verified at dragon.drg.in using the Registration No. / "
        "Software Courtesy: WDR Tech Division, Citadel.",
    ]
    for note in notes:
        c.drawString(IM + 5, y, note)
        y -= 9

    _hline(c, OM + 6, W - OM - 6, y + 2, 0.8)
    y -= 10

    c.setFont("Helvetica-Bold", 7)
    c.drawString(IM + 5, y, "Software Courtesy Westeros Dragon Registry (WDR)")
    c.drawRightString(right_x, y, "Certificate can be tracked on dragon.drg.in")

    c.save()
    return buf.getvalue()
