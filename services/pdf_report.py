from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

def generate_pdf_report(title: str, columns: list, rows: list) -> bytes:
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, height - 50, title)

    p.setFont("Helvetica", 10)
    y = height - 80

    # Заголовки таблицы
    for i, col in enumerate(columns):
        p.drawString(40 + i * 120, y, str(col))

    y -= 20

    for row in rows:
        for i, value in enumerate(row):
            p.drawString(40 + i * 120, y, str(value))
        y -= 18
        if y < 50:
            p.showPage()
            y = height - 80

    p.setFont("Helvetica-Oblique", 8)
    p.drawString(40, 20, f"Сформировано: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

    p.save()
    buffer.seek(0)
    return buffer.read()
