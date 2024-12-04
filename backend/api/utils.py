import io

from fpdf import FPDF


def generate_pdf(ingredients):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.add_font(
        'ComicSansMS', '',
        'recipes/fonts/ComicSansMS.ttf', uni=True
    )
    pdf.add_font(
        'ComicSansMSB', '',
        'recipes/fonts/ComicSansMSB.ttf', uni=True
    )
    pdf.set_text_color(0, 181, 134)
    pdf.set_font("ComicSansMSB", size=25)
    pdf.cell(0, 10, "К закупкам!", ln=True, align='C')
    pdf.set_text_color(0, 45, 143)
    pdf.set_font("ComicSansMS", size=14)
    for index, ingredient in enumerate(ingredients):
        name = ingredient['ingredient__name']
        unit = ingredient['ingredient__measurement_unit']
        amount = ingredient['amount']
        line_text = f"{index + 1}. {name} ({unit}) — {amount}"
        pdf.cell(0, 10, line_text, ln=True)

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    return pdf_output
