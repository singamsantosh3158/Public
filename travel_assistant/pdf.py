import io
import re

import requests
from fpdf import FPDF
from PIL import Image

_MAX_IMAGE_WIDTH_PX = 1000

_IMAGE_LINE = re.compile(r"^!\[([^\]]*)\]\((https?://\S+?)\)\s*$")
_BOLD_RUN = re.compile(r"(\*\*[^*]+\*\*)")

# The core PDF fonts are Latin-1 only; LLM output commonly uses typographic
# characters outside that range, so normalize the common ones instead of
# bundling a Unicode font just for this.
_UNICODE_REPLACEMENTS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", "•": "-",
    " ": " ",
}


def _latin1_safe(text: str) -> str:
    for source, replacement in _UNICODE_REPLACEMENTS.items():
        text = text.replace(source, replacement)
    return text.encode("latin-1", "replace").decode("latin-1")


def _load_capped_image(content: bytes) -> io.BytesIO:
    """Downscale/recompress so one photo can't blow up the PDF size, whatever the source sent."""
    image = Image.open(io.BytesIO(content))
    image = image.convert("RGB")
    if image.width > _MAX_IMAGE_WIDTH_PX:
        ratio = _MAX_IMAGE_WIDTH_PX / image.width
        image = image.resize((_MAX_IMAGE_WIDTH_PX, round(image.height * ratio)))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=82)
    buffer.seek(0)
    return buffer


def _write_inline(pdf: FPDF, text: str, line_height: float) -> None:
    for part in _BOLD_RUN.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            pdf.set_font(style="B")
            pdf.write(line_height, _latin1_safe(part[2:-2]))
            pdf.set_font(style="")
        else:
            pdf.write(line_height, _latin1_safe(part))


def markdown_to_pdf(markdown_text: str, title: str) -> bytes:
    """Render the simple Markdown subset used by this app's itineraries into a PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_title(_latin1_safe(title))
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()

        if not line:
            pdf.ln(4)
            continue

        image_match = _IMAGE_LINE.match(line)
        if image_match:
            try:
                response = requests.get(
                    image_match.group(2),
                    timeout=10,
                    headers={"User-Agent": "travel-assistant-agent (personal project)"},
                )
                response.raise_for_status()
                pdf.image(_load_capped_image(response.content), w=170)
                pdf.ln(4)
            except Exception:
                pass  # a broken/unsupported photo shouldn't block the rest of the PDF
            continue

        if line in ("---", "***"):
            pdf.ln(2)
            continue

        heading_level = len(line) - len(line.lstrip("#"))
        if 1 <= heading_level <= 3 and line[heading_level : heading_level + 1] == " ":
            size = {1: 18, 2: 15, 3: 13}[heading_level]
            pdf.set_font("Helvetica", "B", size)
            pdf.multi_cell(0, size * 0.7, _latin1_safe(line[heading_level + 1 :]))
            pdf.set_font("Helvetica", size=11)
            continue

        prefix = ""
        if line.startswith("- ") or line.startswith("* "):
            prefix = "- "
            line = line[2:]

        if prefix:
            pdf.write(6, prefix)
        _write_inline(pdf, line, line_height=6)
        pdf.ln(7)

    return bytes(pdf.output())
