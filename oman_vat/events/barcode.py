# your_app/utils.py
import barcode
from barcode.writer import SVGWriter
import io
import base64

def get_barcode_svg(value):
    # Using 'code128' for high-density, high-quality output
    code = barcode.get('code128', value, writer=SVGWriter())
    buffer = io.BytesIO()
    code.write(buffer)
    # Return as data URI string
    return f"data:image/svg+xml;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"