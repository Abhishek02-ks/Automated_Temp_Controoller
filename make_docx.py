"""
make_docx.py  –  Convert review_paper.md to review_paper.docx
Uses ONLY Python built-ins (zipfile, xml, textwrap) — no pip required.
"""

import zipfile, os, re, textwrap
from xml.sax.saxutils import escape

OUT = "research_paper.docx"
MD  = "research_paper.md"

# ── helpers ────────────────────────────────────────────────────────────────────

def esc(t): return escape(str(t))

def make_rpr(bold=False, italic=False, size=None, color=None, font=None):
    parts = []
    if bold:   parts.append("<w:b/>")
    if italic: parts.append("<w:i/>")
    if size:   parts.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    if color:  parts.append(f'<w:color w:val="{color}"/>')
    f = font or "Times New Roman"
    parts.insert(0, f'<w:rFonts w:ascii="{f}" w:hAnsi="{f}" w:cs="{f}"/>')
    return "<w:rPr>" + "".join(parts) + "</w:rPr>"

def run(text, bold=False, italic=False, size=None, color=None, font=None):
    rpr = make_rpr(bold, italic, size, color, font)
    return f"<w:r>{rpr}<w:t xml:space=\"preserve\">{esc(text)}</w:t></w:r>"

def inline_runs(text, base_size=24, base_bold=False, base_italic=False):
    """Parse **bold**, *italic*, and `code` inline markers → run XML."""
    pattern = re.compile(r'(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)')
    result, last = [], 0
    for m in pattern.finditer(text):
        if m.start() > last:
            result.append(run(text[last:m.start()], bold=base_bold,
                               italic=base_italic, size=base_size))
        full = m.group(0)
        if full.startswith("**"):
            result.append(run(m.group(2), bold=True, italic=base_italic,
                               size=base_size))
        elif full.startswith("*"):
            result.append(run(m.group(3), bold=base_bold, italic=True,
                               size=base_size))
        else:  # backtick code
            result.append(run(m.group(4), font="Courier New", size=base_size))
        last = m.end()
    if last < len(text):
        result.append(run(text[last:], bold=base_bold, italic=base_italic,
                           size=base_size))
    return "".join(result)

def para(runs_xml, style="Normal", align=None, spacing_before=0,
         spacing_after=160, indent_left=0):
    jc = f'<w:jc w:val="{align}"/>' if align else '<w:jc w:val="both"/>'
    return (
        f'<w:p>'
        f'<w:pPr>'
        f'<w:pStyle w:val="{style}"/>'
        f'<w:spacing w:before="{spacing_before}" w:after="{spacing_after}"/>'
        f'<w:ind w:left="{indent_left}"/>'
        f'{jc}'
        f'</w:pPr>'
        f'{runs_xml}'
        f'</w:p>'
    )

def heading(text, level):
    sizes  = {1: 36, 2: 28, 3: 26}
    colors = {1: "1F3864", 2: "2E4057", 3: "374151"}
    sz  = sizes.get(level, 26)
    col = colors.get(level, "000000")
    r   = run(text, bold=True, size=sz, color=col)
    sp_before = {1: 360, 2: 280, 3: 200}.get(level, 160)
    return para(r, align="left", spacing_before=sp_before, spacing_after=120)

def body_para(text):
    return para(inline_runs(text, base_size=24))

def center_para(text, size=20, bold=False, italic=False, color=None):
    r = run(text, bold=bold, italic=italic, size=size, color=color)
    return para(r, align="center", spacing_before=0, spacing_after=80)

def code_para(text):
    r = run(text, font="Courier New", size=18)
    return para(r, align="left", indent_left=720, spacing_before=0,
                spacing_after=40)

def separator():
    return (
        '<w:p><w:pPr><w:pBdr>'
        '<w:bottom w:val="single" w:sz="4" w:space="1" w:color="CCCCCC"/>'
        '</w:pBdr></w:pPr></w:p>'
    )

def table_xml(rows):
    """rows: list of list of strings. First row = header."""
    def tc(text, header=False):
        bg = '<w:shd w:val="clear" w:color="auto" w:fill="1F3864"/>' if header else \
             '<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/>'
        col = "FFFFFF" if header else "000000"
        r = run(text, bold=header, size=20, color=col)
        return (
            f'<w:tc>'
            f'<w:tcPr>{bg}<w:tcBorders>'
            f'<w:top w:val="single" w:sz="4" w:color="CCCCCC"/>'
            f'<w:bottom w:val="single" w:sz="4" w:color="CCCCCC"/>'
            f'<w:left w:val="single" w:sz="4" w:color="CCCCCC"/>'
            f'<w:right w:val="single" w:sz="4" w:color="CCCCCC"/>'
            f'</w:tcBorders>'
            f'<w:tcMar><w:left w:w="100" w:type="dxa"/>'
            f'<w:right w:w="100" w:type="dxa"/></w:tcMar></w:tcPr>'
            f'<w:p><w:pPr><w:jc w:val="left"/></w:pPr>{r}</w:p>'
            f'</w:tc>'
        )
    xml = '<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/>' \
          '<w:tblBorders>' \
          '<w:insideH w:val="single" w:sz="4" w:color="CCCCCC"/>' \
          '<w:insideV w:val="single" w:sz="4" w:color="CCCCCC"/>' \
          '</w:tblBorders></w:tblPr>'
    for i, row in enumerate(rows):
        cells = "".join(tc(c, header=(i == 0)) for c in row)
        xml += f'<w:tr>{cells}</w:tr>'
    xml += '</w:tbl>'
    return xml

# ── Markdown → docx paragraphs ────────────────────────────────────────────────

def parse_md(md_text):
    lines = md_text.splitlines()
    paras = []
    i = 0
    in_code = False
    code_lines = []
    table_rows = []
    in_table = False

    while i < len(lines):
        line = lines[i]

        # ── fenced code block ──────────────────────────────────────────────
        if line.strip().startswith("```"):
            if not in_code:
                in_code = True
                code_lines = []
            else:
                in_code = False
                # emit each code line as a code paragraph
                for cl in code_lines:
                    paras.append(code_para(cl if cl else " "))
                paras.append(para("", spacing_before=0, spacing_after=80))
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        # ── table ──────────────────────────────────────────────────────────
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # skip separator rows (---|---…)
            if all(re.match(r'^[-:]+$', c) for c in cells if c):
                i += 1
                continue
            table_rows.append(cells)
            in_table = True
            i += 1
            continue
        else:
            if in_table and table_rows:
                paras.append(table_xml(table_rows))
                paras.append(para("", spacing_before=0, spacing_after=80))
                table_rows = []
                in_table = False

        # ── headings ──────────────────────────────────────────────────────
        hm = re.match(r'^(#{1,3})\s+(.*)', line)
        if hm:
            lvl = len(hm.group(1))
            paras.append(heading(hm.group(2), lvl))
            i += 1
            continue

        # ── horizontal rule ───────────────────────────────────────────────
        if re.match(r'^---+$', line.strip()):
            paras.append(separator())
            i += 1
            continue

        # ── block quote (abstract / note) ─────────────────────────────────
        if line.strip().startswith(">"):
            text = re.sub(r'^>\s*', '', line.strip())
            # strip italic markdown wrapper
            text = re.sub(r'^\*(.+)\*\s*—', r'\1 —', text)
            r = inline_runs(text, base_size=22, base_italic=True)
            paras.append(para(r, align="both", indent_left=720,
                               spacing_before=80, spacing_after=80))
            i += 1
            continue

        # ── list items ────────────────────────────────────────────────────
        lm = re.match(r'^(\s*)[-*]\s+(.*)', line)
        if lm:
            indent = 720 + len(lm.group(1)) * 180
            r = run("• ", bold=True, size=24) + inline_runs(lm.group(2))
            paras.append(para(r, align="both", indent_left=indent,
                               spacing_before=0, spacing_after=60))
            i += 1
            continue

        nm = re.match(r'^\d+\.\s+(.*)', line)
        if nm:
            r = inline_runs(nm.group(1))
            paras.append(para(r, align="both", indent_left=720,
                               spacing_before=0, spacing_after=60))
            i += 1
            continue

        # ── blank line ────────────────────────────────────────────────────
        if not line.strip():
            paras.append(para("", spacing_before=0, spacing_after=80))
            i += 1
            continue

        # ── italic-centered lines (Index Terms / submission note) ─────────
        if line.strip().startswith("*") and line.strip().endswith("*") and \
                not line.strip().startswith("**"):
            text = line.strip().strip("*")
            paras.append(center_para(text, italic=True, size=22))
            i += 1
            continue

        # ── default body text ─────────────────────────────────────────────
        paras.append(body_para(line.strip()))
        i += 1

    # flush pending table
    if table_rows:
        paras.append(table_xml(table_rows))

    return paras

# ── assemble document.xml ──────────────────────────────────────────────────────

NSMAP = (
    'xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:o="urn:schemas-microsoft-com:office:office" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
    'xmlns:v="urn:schemas-microsoft-com:vml" '
    'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:w10="urn:schemas-microsoft-com:office:word" '
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
    'xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" '
    'xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" '
    'xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" '
    'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"'
)

def build_document(body_parts):
    body_xml = "\n".join(body_parts)
    sect = (
        '<w:sectPr>'
        '<w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1080" w:bottom="1440" w:left="1080"'
        ' w:header="720" w:footer="720" w:gutter="0"/>'
        '</w:sectPr>'
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document {NSMAP}>'
        f'<w:body>{body_xml}{sect}</w:body>'
        f'</w:document>'
    )

# ── docx ZIP structure ─────────────────────────────────────────────────────────

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/settings.xml"
    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="word/document.xml"/>
</Relationships>"""

WORD_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings"
    Target="settings.xml"/>
</Relationships>"""

SETTINGS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:defaultTabStop w:val="720"/>
  <w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>
</w:settings>"""

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    with open(MD, encoding="utf-8") as f:
        md = f.read()

    body_parts = parse_md(md)
    doc_xml = build_document(body_parts)

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/_rels/document.xml.rels", WORD_RELS)
        z.writestr("word/document.xml", doc_xml)
        z.writestr("word/settings.xml", SETTINGS)

    size_kb = os.path.getsize(OUT) // 1024
    print(f"Created '{OUT}'  ({size_kb} KB)")

if __name__ == "__main__":
    main()
