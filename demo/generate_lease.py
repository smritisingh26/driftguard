"""Generate a synthetic residential lease agreement PDF for demo purposes."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

def generate():
    doc = SimpleDocTemplate(
        "lease_agreement.pdf",
        pagesize=letter,
        leftMargin=1.2*inch, rightMargin=1.2*inch,
        topMargin=1.0*inch, bottomMargin=1.0*inch
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=16,
        alignment=TA_CENTER, spaceAfter=6)
    subtitle_style = ParagraphStyle('subtitle', fontName='Helvetica', fontSize=11,
        alignment=TA_CENTER, spaceAfter=16, textColor=colors.HexColor("#555555"))
    heading_style = ParagraphStyle('heading', fontName='Helvetica-Bold', fontSize=11,
        spaceBefore=14, spaceAfter=4)
    body_style = ParagraphStyle('body', fontName='Helvetica', fontSize=10,
        leading=15, spaceAfter=6, alignment=TA_JUSTIFY)
    bold_style = ParagraphStyle('bold', fontName='Helvetica-Bold', fontSize=10,
        leading=15, spaceAfter=4)

    story = []

    story.append(Paragraph("RESIDENTIAL LEASE AGREEMENT", title_style))
    story.append(Paragraph("State of California", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=16))

    # Parties table
    party_data = [
        ["LANDLORD:", "Margaret H. Thornton"],
        ["ADDRESS:", "4821 Elmwood Drive, San Jose, CA 95128"],
        ["TENANT(S):", "Jordan A. Reeves"],
        ["PROPERTY:", "Unit 4B, 220 Crestview Lane, Mountain View, CA 94040"],
        ["LEASE TERM:", "12 months, commencing August 1, 2025, ending July 31, 2026"],
        ["MONTHLY RENT:", "$3,200.00 (Three Thousand Two Hundred Dollars)"],
        ["SECURITY DEPOSIT:", "$6,400.00 (Two months' rent)"],
    ]
    t = Table(party_data, colWidths=[1.6*inch, 4.8*inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    sections = [
        ("1. RENT PAYMENT",
         "Tenant agrees to pay the monthly rent of $3,200.00 on or before the FIRST (1st) day of "
         "each calendar month. Rent shall be paid by bank transfer or certified check to Landlord "
         "at the address listed above. A late fee of $150.00 will be assessed for any rent received "
         "after the 5th day of the month. Landlord reserves the right to increase rent upon 60 days "
         "written notice in accordance with California Civil Code Section 1945.5. Rent increases "
         "shall not exceed 5% plus local CPI or 10% of the lowest rent charged in the prior 12 months, "
         "whichever is lower, per California AB 1482."),

        ("2. SECURITY DEPOSIT",
         "Upon execution of this Agreement, Tenant shall deposit the sum of $6,400.00 as a security "
         "deposit. This deposit is held to secure Tenant's performance of obligations under this "
         "Agreement. Landlord may withhold from the deposit amounts sufficient to remedy defaults in "
         "rent payment, repair damages beyond normal wear and tear, and clean the premises if left "
         "unclean. Landlord shall return the deposit within 21 days of Tenant vacating the property, "
         "along with an itemized statement of any deductions. Failure to return the deposit within "
         "this period may entitle Tenant to statutory damages of twice the withheld amount under "
         "California Civil Code Section 1950.5."),

        ("3. OCCUPANCY AND USE",
         "The premises shall be occupied solely as a private residential dwelling by the named Tenant "
         "and no other persons without prior written consent of Landlord. Tenant shall not use or "
         "permit the premises to be used for any unlawful purpose. Tenant shall comply with all "
         "applicable laws, ordinances, and regulations. Subletting or assignment of this lease is "
         "strictly prohibited without prior written consent of Landlord. Violation of this clause "
         "constitutes material breach and grounds for immediate termination."),

        ("4. MAINTENANCE AND REPAIRS",
         "Tenant shall maintain the premises in a clean and sanitary condition and shall not permit "
         "any waste or nuisance. Tenant is responsible for minor repairs under $150.00. Tenant must "
         "promptly notify Landlord in writing of any defects or conditions requiring repair. Landlord "
         "shall complete repairs within a reasonable time, not to exceed 30 days for non-emergency "
         "items. Tenant shall be liable for damages caused by Tenant's negligence or misuse. "
         "Unauthorized alterations, modifications, or improvements are strictly prohibited and "
         "Tenant may be required to restore the premises at Tenant's expense upon vacating."),

        ("5. ENTRY BY LANDLORD",
         "Landlord or Landlord's agents may enter the premises with 24-hour advance written notice "
         "for inspection, repairs, or to show the unit to prospective tenants or buyers. In the event "
         "of emergency, Landlord may enter without prior notice. Repeated or unreasonable entries "
         "without notice may constitute constructive eviction under California law. Tenant shall not "
         "change or add locks without prior written consent. Landlord retains the right to a duplicate "
         "key at all times."),

        ("6. PETS",
         "No pets of any kind shall be permitted on the premises without prior written consent of "
         "Landlord. Unauthorized pets constitute a material breach of this Agreement. If Landlord "
         "consents to a pet, Tenant shall pay an additional non-refundable pet fee of $500.00 and an "
         "additional monthly pet rent of $75.00. Tenant shall be fully liable for any damage caused "
         "by authorized or unauthorized pets."),

        ("7. UTILITIES AND SERVICES",
         "Tenant is responsible for establishing and paying all utility accounts including electricity, "
         "gas, internet, and cable. Water, trash, and sewer services are included in the monthly rent. "
         "Failure to maintain required utilities shall constitute a material breach of this Agreement. "
         "Landlord makes no warranty regarding the quality or continuity of utility services provided "
         "by third-party providers."),

        ("8. TERMINATION AND DEFAULT",
         "This lease shall terminate on July 31, 2026. Tenant must provide 30 days written notice "
         "prior to vacating. Early termination by Tenant without cause shall result in forfeiture of "
         "the security deposit and liability for rent through the end of the lease term or until the "
         "unit is re-let, whichever occurs first. Landlord may terminate this Agreement upon 3-day "
         "written notice for non-payment of rent, and upon 3-day notice to cure or quit for material "
         "breach of any other provision. Habitual late payment (3 or more occurrences) constitutes "
         "grounds for non-renewal."),

        ("9. INDEMNIFICATION AND LIABILITY",
         "Tenant agrees to indemnify, defend, and hold harmless Landlord from any claims, damages, "
         "losses, or expenses arising from Tenant's use of the premises or Tenant's breach of this "
         "Agreement. Landlord shall not be liable for loss of or damage to Tenant's personal property "
         "except where caused by Landlord's gross negligence or willful misconduct. Tenant is strongly "
         "advised to obtain renter's insurance. Landlord's liability for any breach of the implied "
         "warranty of habitability shall be limited to rent abatement for the period of uninhabitability."),

        ("10. GOVERNING LAW AND DISPUTES",
         "This Agreement shall be governed by the laws of the State of California. Any disputes "
         "arising under this Agreement shall be resolved in the courts of Santa Clara County. In any "
         "action to enforce this Agreement, the prevailing party shall be entitled to reasonable "
         "attorney's fees and costs. This Agreement constitutes the entire understanding between "
         "the parties and supersedes all prior negotiations, representations, or agreements. Any "
         "modification must be in writing and signed by both parties."),
    ]

    for heading, text in sections:
        story.append(Paragraph(heading, heading_style))
        story.append(Paragraph(text, body_style))

    story.append(Spacer(1, 24))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceAfter=16))
    story.append(Paragraph("SIGNATURES", heading_style))

    sig_data = [
        ["Landlord Signature:", "______________________________", "Date:", "____________"],
        ["Tenant Signature:", "______________________________", "Date:", "____________"],
    ]
    sig_t = Table(sig_data, colWidths=[1.5*inch, 2.5*inch, 0.6*inch, 1.4*inch])
    sig_t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(sig_t)

    doc.build(story)
    print("Lease agreement generated: lease_agreement.pdf")

if __name__ == "__main__":
    generate()
