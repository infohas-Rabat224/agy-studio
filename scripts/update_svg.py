import base64
from pathlib import Path

png_path = Path(r"C:\Agy Studio\data\media\image_till_assistant___qatar_du_1791538274.png")
if png_path.exists():
    b64_data = base64.b64encode(png_path.read_bytes()).decode("ascii")
    svg_body = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1080" width="100%" height="100%">\n'
        f'  <image width="1080" height="1080" href="data:image/png;base64,{b64_data}"/>\n'
        '</svg>'
    )
    Path(r"C:\Agy Studio\data\media\image_till_assistant___qatar_du_1791538274.svg").write_text(svg_body, encoding="utf-8")
    Path(r"C:\Agy Studio\Test Workspace\image_till_assistant___qatar_du_1791538274.svg").write_text(svg_body, encoding="utf-8")
    print("SVG successfully updated with full photographic image!")
