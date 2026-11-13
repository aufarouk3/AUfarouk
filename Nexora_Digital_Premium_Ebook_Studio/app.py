import os, re
from io import BytesIO
from xml.sax.saxutils import escape
import streamlit as st
from groq import Groq
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

NAVY = "#111827"
GOLD = "#D6B779"
IVORY = "#F5F1E8"
WHITE = "#FFFFFF"

st.set_page_config(page_title="Nexora Digital | eBook Studio", page_icon="📘", layout="wide")
st.title("📘 Nexora Digital — Premium eBook Studio")
st.caption("Create a branded eBook PDF plus a separate printable worksheet pack.")

def get_api_key():
    try:
        return st.secrets.get("GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    except Exception:
        return os.getenv("GROQ_API_KEY", "")

api_key = get_api_key()
if not api_key:
    st.error("Add GROQ_API_KEY in Streamlit Community Cloud → App settings → Secrets, or as an environment variable.")
    st.markdown("[Get a Groq API key](https://console.groq.com/keys)")
    st.stop()

client = Groq(api_key=api_key)
MODEL = "openai/gpt-oss-20b"

def ask_groq(system, prompt, max_tokens=3500):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role":"system","content":system},{"role":"user","content":prompt}],
        temperature=0.65,
        max_completion_tokens=max_tokens,
    )
    return (response.choices[0].message.content or "").strip()

def safe_name(s):
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", s).strip("_").lower() or "nexora_product"

def styles():
    s = getSampleStyleSheet()
    return {
        "cover": ParagraphStyle("Cover", parent=s["Title"], fontName="Helvetica-Bold",
            fontSize=27, leading=33, alignment=TA_CENTER, textColor=colors.HexColor(NAVY), spaceAfter=18),
        "sub": ParagraphStyle("Sub", parent=s["Normal"], fontSize=13, leading=19,
            alignment=TA_CENTER, textColor=colors.HexColor("#555555")),
        "h": ParagraphStyle("H", parent=s["Heading1"], fontSize=17, leading=22,
            textColor=colors.HexColor(NAVY), spaceBefore=8, spaceAfter=12),
        "body": ParagraphStyle("Body", parent=s["BodyText"], fontSize=10, leading=15,
            alignment=TA_LEFT, spaceAfter=8),
        "small": ParagraphStyle("Small", parent=s["Normal"], fontSize=9,
            alignment=TA_CENTER, textColor=colors.HexColor("#666666")),
    }

def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor(GOLD))
    canvas.setLineWidth(1)
    canvas.line(20*mm, 16*mm, A4[0]-20*mm, 16*mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(20*mm, 10*mm, "NEXORA DIGITAL")
    canvas.drawRightString(A4[0]-20*mm, 10*mm, str(doc.page))
    canvas.restoreState()

def cover_story(title, subtitle, author, stys):
    return [
        Spacer(1, 36*mm),
        Paragraph("NEXORA DIGITAL", ParagraphStyle("Brand", parent=stys["small"],
            fontSize=12, textColor=colors.HexColor(GOLD), spaceAfter=20)),
        Paragraph(escape(title), stys["cover"]),
        Paragraph(escape(subtitle), stys["sub"]),
        Spacer(1, 25*mm),
        Paragraph("SMART IDEAS. DIGITAL POSSIBILITIES.", stys["small"]),
        Spacer(1, 12*mm),
        Paragraph("Prepared by " + escape(author or "Nexora Digital"), stys["small"]),
        PageBreak()
    ]

def make_ebook_pdf(title, subtitle, author, sections):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=23*mm, title=title, author=author)
    stys = styles()
    story = cover_story(title, subtitle, author, stys)
    story.append(Paragraph("CONTENTS", stys["h"]))
    for heading, _ in sections:
        story.append(Paragraph(escape(heading), stys["body"]))
    story.append(PageBreak())
    for idx, (heading, content) in enumerate(sections):
        story.append(Paragraph(escape(heading), stys["h"]))
        for para in re.split(r"\n\s*\n", content.strip()):
            para = para.strip()
            if para:
                story.append(Paragraph(escape(para).replace("\n", "<br/>"), stys["body"]))
        if idx < len(sections)-1:
            story.append(Spacer(1, 7*mm))
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    return buf.getvalue()

def make_worksheet_pdf(title, worksheets, author):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=17*mm, leftMargin=17*mm,
        topMargin=18*mm, bottomMargin=23*mm, title=title + " — Worksheets", author=author)
    stys = styles()
    story = cover_story(title + "\nWORKSHEET PACK", "Printable exercises and planning sheets", author, stys)
    for index, ws in enumerate(worksheets):
        story.append(Paragraph(escape(ws["title"]), stys["h"]))
        story.append(Paragraph(escape(ws["instructions"]), stys["body"]))
        rows = [[Paragraph("<b>"+escape(c)+"</b>", stys["body"]) for c in ws["headers"]]]
        for _ in range(ws["rows"]):
            rows.append([""] * len(ws["headers"]))
        widths = [(A4[0]-34*mm)/len(ws["headers"])] * len(ws["headers"])
        table = Table(rows, colWidths=widths, rowHeights=[10*mm]+[12*mm]*ws["rows"])
        table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor(IVORY)),
            ("TEXTCOLOR",(0,0),(-1,0),colors.HexColor(NAVY)),
            ("GRID",(0,0),(-1,-1),0.6,colors.HexColor(GOLD)),
            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
            ("LEFTPADDING",(0,0),(-1,-1),5),
            ("RIGHTPADDING",(0,0),(-1,-1),5),
        ]))
        story.append(table)
        story.append(Spacer(1, 8*mm))
        if ws.get("reflection"):
            story.append(Paragraph("<b>Reflection:</b> " + escape(ws["reflection"]), stys["body"]))
        if index < len(worksheets)-1:
            story.append(PageBreak())
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
    return buf.getvalue()

SYSTEM = """You are a professional educational eBook editor. Write original, useful, practical material.
Do not invent statistics, citations, URLs, laws, testimonials or guarantees. Mark facts needing checking [VERIFY].
For financial education, avoid personalised investment, tax or legal advice. Explain that examples are illustrative.
Use clear headings and paragraphs. Include realistic examples, exercises, reflection questions and actionable steps."""

with st.sidebar:
    st.header("Brand settings")
    brand = st.text_input("Brand / author", "Nexora Digital")
    tagline = st.text_input("Tagline", "Smart Ideas. Digital Possibilities.")
    st.caption("Brand palette: Midnight navy • Champagne gold • Warm ivory")

with st.form("ebook_setup"):
    title = st.text_input("eBook title", "The Paycheck-to-Paycheck Money Reset")
    subtitle = st.text_input("Subtitle", "A 30-Day Practical Guide to Budgeting, Controlling Spending and Building Savings")
    topic = st.text_area("What should the eBook teach?",
        "Help readers understand their money, plan paychecks, control spending, manage debt and begin saving.", height=90)
    audience = st.text_input("Target readers", "Working adults and young professionals in the United States and United Kingdom")
    edition = st.selectbox("Edition", ["Combined US & UK edition", "United States edition", "United Kingdom edition"])
    tone = st.selectbox("Writing style", ["Premium workbook style", "Professional and educational", "Friendly and simple"])
    chapters = st.slider("Number of chapters", 3, 12, 8)
    include_intro = st.checkbox("Include introduction", True)
    include_conclusion = st.checkbox("Include conclusion", True)
    generate_outline = st.form_submit_button("Generate chapter outline", type="primary")

if generate_outline:
    if len(topic.strip()) < 20:
        st.warning("Please describe the eBook topic in at least 20 characters.")
    else:
        prompt = f"""Create a detailed table of contents for this eBook.
Title: {title}
Topic: {topic}
Audience: {audience}
Edition: {edition}
Style: {tone}
Return exactly {chapters} numbered chapter headings, one per line. No explanations."""
        try:
            with st.spinner("Planning your eBook..."):
                outline = ask_groq(SYSTEM, prompt, 1400)
            headings = [re.sub(r"^\s*(?:chapter\s*)?\d+[\.\):\-]\s*", "", x).strip()
                        for x in outline.splitlines() if x.strip()]
            headings = [x for x in headings if len(x) > 3][:chapters]
            if len(headings) < chapters:
                st.error("The outline was incomplete. Please generate it again.")
            else:
                st.session_state["project"] = dict(title=title, subtitle=subtitle, topic=topic,
                    audience=audience, edition=edition, tone=tone, headings=headings,
                    brand=brand, include_intro=include_intro, include_conclusion=include_conclusion)
                st.session_state.pop("sections", None)
                st.success("Outline ready. Review it, then generate the full draft.")

if "project" in st.session_state:
    p = st.session_state["project"]
    st.subheader("Review your chapter plan")
    for i, heading in enumerate(p["headings"], 1):
        st.write(f"{i}. {heading}")
    if st.button("Generate introduction, chapters and conclusion", type="primary"):
        sections = []
        parts = []
        if p["include_intro"]:
            parts.append(("Introduction", "Write a substantial introduction that explains the reader's problem, what the book will help them do, who it is for, and how to use the guide."))
        parts.extend([(f"Chapter {i}: {h}", f"Write a substantial, premium, practical chapter about: {h}. Include clear explanations, realistic US and UK examples where relevant, step-by-step actions, a worked example, an exercise, reflection questions and key takeaways.") for i,h in enumerate(p["headings"],1)])
        if p["include_conclusion"]:
            parts.append(("Conclusion and Next Steps", "Write a useful conclusion, recap key lessons and provide a sustainable next-step plan."))
        progress = st.progress(0)
        status = st.empty()
        try:
            for i, (heading, instruction) in enumerate(parts):
                status.write(f"Writing {heading}...")
                prompt = f"""Book: {p['title']}
Subtitle: {p['subtitle']}
Topic: {p['topic']}
Audience: {p['audience']}
Edition: {p['edition']}
Style: {p['tone']}
Section: {heading}
Instructions: {instruction}
Write detailed original content. Do not invent statistics or claims. Use $ and £ examples carefully and explain that figures are illustrative.
Do not use markdown tables; use readable headings and lists."""
                content = ask_groq(SYSTEM, prompt, 4200)
                sections.append((heading, content))
                progress.progress((i+1)/len(parts))
            st.session_state["sections"] = sections
            status.success("Draft completed. Review and edit before publishing.")
        except Exception as e:
            st.error(f"Generation stopped: {e}")

if "sections" in st.session_state and "project" in st.session_state:
    p = st.session_state["project"]
    st.divider()
    st.subheader("Review your eBook")
    for heading, content in st.session_state["sections"]:
        with st.expander(heading):
            st.text_area("Edit this section", content, height=260, key="edit_"+safe_name(heading))
    edited_sections = [(h, st.session_state.get("edit_"+safe_name(h), c))
                       for h,c in st.session_state["sections"]]
    st.session_state["sections"] = edited_sections
    st.subheader("Separate printable worksheets")
    st.write("The app creates a separate PDF workbook with reusable blank practice sheets.")
    worksheet_specs = [
        {"title":"Monthly Budget Planner","instructions":"List expected income and plan essential, flexible and savings categories before spending.","headers":["Category","Planned","Actual","Difference"],"rows":12,"reflection":"What is one adjustment you can make next month?"},
        {"title":"Daily Spending Tracker","instructions":"Record each purchase for seven days. Include cash, card and online spending.","headers":["Date","Purchase","Need / Want","Amount"],"rows":14,"reflection":"Which spending pattern surprised you?"},
        {"title":"Debt Payoff Tracker","instructions":"List debts, balances, interest rates and required minimum payments. Verify all lender terms.","headers":["Debt","Balance","Rate","Payment"],"rows":10,"reflection":"Which repayment approach will you discuss or research further?"},
        {"title":"Savings Challenge","instructions":"Choose a realistic goal and record each contribution. Never sacrifice essential bills to meet a challenge.","headers":["Date","Goal","Saved","New total"],"rows":14,"reflection":"What made saving easier this week?"},
        {"title":"Paycheck Planner","instructions":"Allocate each paycheck to bills, essentials, debt minimums, savings and flexible spending.","headers":["Pay date","Category","Allocated","Remaining"],"rows":12,"reflection":"Does this plan cover expenses until your next payday?"},
        {"title":"Weekly Financial Review","instructions":"Review progress, upcoming bills and any changes needed for the next week.","headers":["Review item","Planned","Actual","Next action"],"rows":10,"reflection":"What is one action to take before the next review?"},
    ]
    selected = st.multiselect("Choose worksheets to include", [x["title"] for x in worksheet_specs],
        default=[x["title"] for x in worksheet_specs])
    worksheets = [x for x in worksheet_specs if x["title"] in selected]
    col1, col2 = st.columns(2)
    with col1:
        ebook_pdf = make_ebook_pdf(p["title"], p["subtitle"], p["brand"], edited_sections)
        st.download_button("⬇️ Download eBook PDF", ebook_pdf,
            file_name=safe_name(p["title"])+".pdf", mime="application/pdf", type="primary")
    with col2:
        if worksheets:
            worksheet_pdf = make_worksheet_pdf(p["title"], worksheets, p["brand"])
            st.download_button("⬇️ Download separate worksheet pack", worksheet_pdf,
                file_name=safe_name(p["title"])+"_worksheets.pdf", mime="application/pdf")
        else:
            st.info("Select at least one worksheet to create the printable pack.")
    st.info("Review all content, test calculations, verify financial guidance and proofread both PDFs before selling. Generated content is a draft, not a substitute for professional advice.")

st.divider()
st.caption("Nexora Digital | Smart Ideas. Digital Possibilities. — Review every generated product before publication.")
