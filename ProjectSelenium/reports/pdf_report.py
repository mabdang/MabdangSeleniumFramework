from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, Flowable
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from PIL import Image as PILImage
import os

# --------- Header / Footer dengan Page X of Y ---------
def _header_footer(canvas, doc, meta_info):
    """
    Header dengan tabel kecil + Footer Page X of Y
    header_text: dict berisi 'project', 'author', 'tools'
    """
    canvas.saveState()
    width, height = A4
    canvas.setFont("Helvetica", 9)
    #canvas.drawString(30, height - 30)
    
    # Ambil info dari dict
    project = meta_info.get("project", "")
    author  = meta_info.get("author", "")
    tools   = meta_info.get("tools", "")

    # -------- Header --------
    header_data = [[f"Project: {project}", f"Author: {author}", f"Tools: {tools}"]]
    table = Table(header_data, colWidths=[width/3-20]*3)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#D9E1F2")),  # light blue
        ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('BOX', (0,0), (-1,-1), 0.5, colors.grey)
    ]))

    # Tentukan posisi header
    w, h = table.wrap(0,0)
    table.drawOn(canvas, doc.leftMargin, height - h - 10)

    # -------- Footer --------
    footer_y = 30
    # Garis melintang
    canvas.setLineWidth(0.5)
    canvas.setStrokeColor(colors.grey)
    canvas.line(36, footer_y + 12, width - 36, footer_y + 12)

    # Kiri: Confidential
    canvas.setFont("Helvetica-Oblique", 8)
    canvas.drawString(36, footer_y, "Confidential")

    # Tengah: Project Name
    canvas.setFont("Helvetica", 8)
    w_center = canvas.stringWidth(project, "Helvetica", 8)
    canvas.drawString((width - w_center)/2, footer_y, project)

    # Kanan: Page X of Y
    page_num = canvas.getPageNumber()
    page_text = f"Page {page_num}"
    w_right = canvas.stringWidth(page_text, "Helvetica", 8)
    canvas.drawString(width - 36 - w_right, footer_y, page_text)

    canvas.restoreState()

def _cover_page(canvas, doc):
    pass

def _scale_image(img_path, max_w=460, max_h=360):
    with PILImage.open(img_path) as im:
        w, h = im.size
    ratio = min(max_w / w, max_h / h)
    return int(w*ratio), int(h*ratio)

# TOC Entry Helper
class TOCEntry(Flowable):
    def __init__(self, text, level, style):
        super().__init__()
        self.text = text
        self.level = level
        self.style = style
    def wrap(self, availWidth, availHeight):
        return (0,0)
    def draw(self):
        self.canv.bookmarkPage(self.text)
        self.canv.addOutlineEntry(self.text, self.text, level=self.level, closed=False)

# ---------------- Main PDF ----------------
def generate_pdf_report(output_path: str, snapshot: dict):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    meta = snapshot["meta"]
    cases = snapshot["cases"]
    totals = snapshot["totals"]

    project_name = meta["project_name"]
    website      = meta["website"]
    author       = meta["author"]
    tools        = meta["tools"]

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CoverTitle", fontSize=24, alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor("#0B5394"), fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="CoverMeta", fontSize=12, alignment=TA_CENTER, spaceAfter=6, textColor=colors.grey))
    styles.add(ParagraphStyle(name="H1", parent=styles["Heading1"], spaceBefore=12, spaceAfter=6))
    styles.add(ParagraphStyle(name="H2", parent=styles["Heading2"], spaceBefore=8, spaceAfter=4))
    styles.add(ParagraphStyle(name="StepTitle", fontSize=12, leading=14, spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#333333")))
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=12, textColor=colors.grey))

    doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=48, bottomMargin=36)
    flow = []

    # ---------------- Cover Page ----------------
    #flow.append(PageBreak())  # start new page for cover
    flow.append(Spacer(1, 120))

    # Project Title (besar, bold)
    flow.append(Paragraph(
        f"{project_name} - {website}", 
        ParagraphStyle(
            'CoverTitle',
            fontSize=24,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.HexColor("#0B5394"),  # navy color
            fontName="Helvetica-Bold"
        )
    ))

    # Subtitle / environment info (italic)
    flow.append(Paragraph(
        f"Environment: {meta.get('environment', 'QA')}",
        ParagraphStyle(
            'CoverEnv',
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=colors.HexColor("#333333"),
            fontName="Helvetica-Oblique"
        )
    ))

    # Author
    flow.append(Paragraph(
        f"Author: {author}",
        ParagraphStyle(
            'CoverMeta',
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=6,
            textColor=colors.grey
        )
    ))

    # Tools used
    flow.append(Paragraph(
        f"Tools: {tools}",
        ParagraphStyle(
            'CoverMetaTools',
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=6,
            textColor=colors.grey
        )
    ))

    # Test Case ID / feature
    flow.append(Paragraph(
        f"Test Case ID: {meta.get('test_case_id', 'N/A')}",
        ParagraphStyle(
            'CoverMetaTC',
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=colors.grey
        )
    ))

    # Optional: add a horizontal line
    flow.append(Spacer(1, 12))
    line = Table([[""]], colWidths=[doc.width])
    line.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#0B5394"))
    ]))
    flow.append(line)

    flow.append(PageBreak())  # next page starts TOC
    # ---------------- Table of Contents ----------------
    toc = TableOfContents()
    toc_rows = []
    toc_rows.append(["Table of Content", "2"])  # bisa hardcode page 2 cover/TOC
    toc_rows.append(["Document Summary", "3"])

    toc.levelStyles = [
        ParagraphStyle(name='TOCHeading1', fontName='Helvetica-Bold', leftIndent=20, firstLineIndent=-10, leading=12),
        ParagraphStyle(name='TOCHeading2', fontName='Helvetica', leftIndent=40, firstLineIndent=-10, leading=11),
    ]

    #Tambahkan setiap test case dan steps
    page_counter = 4  # mulai halaman konten setelah summary (sesuaikan nanti)
    for c in cases:
        case_name = f"{c['title']} - {c['scenario_type']}"
        toc_rows.append([case_name, str(page_counter)])
        for s in c["steps"]:
            step_line = f"{s['step_id']}. {s['title']}"
            toc_rows.append(["   " + step_line, str(page_counter)])  # indent step
            page_counter += 1  # asumsi 1 halaman per step, bisa adjust

    # Buat Table TOC
    toc_table = Table(toc_rows, colWidths=[400, 60])
    toc_table.setStyle(TableStyle([
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("TOPPADDING", (0,0), (-1,-1), 2)
    ]))
    flow.append(toc_table)
    flow.append(PageBreak())

    # ---------------- Document Summary ----------------
    flow.append(Paragraph("Document Summary", styles["H1"]))
    total_table = Table(
        [["Total Passed", totals.get("passed",0)],
         ["Total Failed", totals.get("failed",0)],
         ["Total Warning", totals.get("warning",0)],
         ["Total Done", totals.get("done",0)],
         ["Total Steps", totals.get("total",0)]],
        colWidths=[240,100]
    )
    total_table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.25,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.whitesmoke),("ALIGN",(1,0),(1,-1),"RIGHT")]))
    flow.append(total_table)
    flow.append(Spacer(1,12))

    summary_rows = [["Case - ID","Steps","Status"]]
    for c in cases:
        name = f"{c['title']} - {c['case_id']} - {c['scenario_type']}"
        steps_title = "\n".join(f"{s['step_id']}. {s['title']}" for s in c["steps"])
        steps_status = "\n".join(f"{s['step_id']}. {s['status']}" for s in c["steps"])
        summary_rows.append([name,steps_title,steps_status])
    sum_table = Table(summary_rows, colWidths=[240,180,120])
    sum_table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.25,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#F5F5F5")),("VALIGN",(0,0),(-1,-1),"TOP")]))
    flow.append(sum_table)
    flow.append(PageBreak())

    # ---------------- Step Details with TOC ----------------
    for c in cases:
        case_heading = f"{c['title']} - {c['case_id']} - {c['scenario_type']}"
        flow.append(Paragraph(case_heading, styles["H1"]))
        flow.append(TOCEntry(case_heading, 0, styles["H1"]))
        flow.append(Spacer(1,4))
        for s in c["steps"]:
            step_heading = f"{s['step_id']}. {s['title']}"
            flow.append(Paragraph(step_heading, styles["H2"]))
            flow.append(TOCEntry(step_heading, 1, styles["H2"]))
 
            flow.append(Spacer(1,6))
            if s.get("image") and os.path.exists(s["image"]):
                try:
                    w,h = _scale_image(s["image"])
                    flow.append(Image(s["image"], width=w, height=h))
                except:
                    flow.append(Paragraph("[Gambar gagal dimuat]", styles["Small"]))
            if s.get("description"):
                flow.append(Paragraph(s["description"], styles["Normal"]))        
            #st = s.get("status","unknown").upper()
            #err = s.get("error","")
            #flow.append(Paragraph(f"Status: <b>{st}</b>" + (f" — Error: {err}" if err else ""), styles["Small"]))
            #flow.append(Spacer(1,12))
            flow.append(PageBreak())

    # ---------------- Build PDF ----------------
    meta_info = {"project": project_name, "author": author, "tools": tools}

    doc.build(
        flow,
        onFirstPage=lambda c,d: _header_footer(c, d, meta_info),   # onFirstPage sudah menghitung page_num
        onLaterPages=lambda c,d: _header_footer(c, d, meta_info)
    )

