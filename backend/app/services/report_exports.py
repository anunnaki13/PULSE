"""Small deterministic report renderers for Phase 4 export endpoints."""

from __future__ import annotations

import csv
import io
from html import escape


def render_csv(headers: list[str], rows: list[list[object]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(["" if value is None else value for value in row])
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def render_word_html(title: str, sections: list[tuple[str, list[list[object]]]]) -> bytes:
    body = [f"<h1>{escape(title)}</h1>"]
    for heading, rows in sections:
        body.append(f"<h2>{escape(heading)}</h2>")
        body.append("<table border='1' cellspacing='0' cellpadding='4'>")
        for row in rows:
            body.append("<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>")
        body.append("</table>")
    html = (
        "<html><head><meta charset='utf-8'>"
        "<style>body{font-family:Arial,sans-serif}table{border-collapse:collapse}td{font-size:10pt}</style>"
        "</head><body>"
        + "".join(body)
        + "</body></html>"
    )
    return html.encode("utf-8")


def render_pdf(title: str, lines: list[str]) -> bytes:
    text_lines = [title, *lines[:42]]
    stream_parts = ["BT", "/F1 16 Tf", "50 790 Td", f"({_pdf_escape(text_lines[0])}) Tj"]
    stream_parts.extend(["/F1 10 Tf"])
    for line in text_lines[1:]:
        stream_parts.append("0 -16 Td")
        stream_parts.append(f"({_pdf_escape(line[:110])}) Tj")
    stream_parts.append("ET")
    stream = "\n".join(stream_parts).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = io.BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(output.tell())
        output.write(f"{index} 0 obj\n".encode())
        output.write(obj)
        output.write(b"\nendobj\n")
    xref = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n".encode())
    output.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode())
    output.write(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return output.getvalue()


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
