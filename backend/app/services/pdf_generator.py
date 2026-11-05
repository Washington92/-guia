import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_work_order_pdf(work_order, client, technician=None, items=None) -> bytes:
    """Gera o documento formal em PDF de uma Ordem de Serviço com campo para assinatura."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    brand_title_style = ParagraphStyle(
        "BrandTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
    )
    doc_id_style = ParagraphStyle(
        "DocId",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        alignment=2,
        textColor=colors.HexColor("#0284c7"),
    )
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1e293b"),
    )
    cell_bold_style = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )
    cell_text_style = ParagraphStyle(
        "CellText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
    )
    sign_label_style = ParagraphStyle(
        "SignLabel",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=1,
        textColor=colors.HexColor("#475569"),
    )

    story = []

    header_data = [
        [
            Paragraph("<b>ÁGUIA GESTÃO CRM</b><br/><font size=8 color='#64748b'>OPERATIONS WORKSPACE & SUPORTE TÉCNICO</font>", brand_title_style),
            Paragraph(f"<b>ORDEM DE SERVIÇO</b><br/><font size=10 color='#64748b'>Nº #{work_order.id:05d}</font>", doc_id_style),
        ]
    ]
    header_table = Table(header_data, colWidths=[110 * mm, 70 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=12))

    client_name = getattr(client, "name", "N/A") if client else "N/A"
    client_doc = getattr(client, "document", "N/A") if client else "N/A"
    client_contact = getattr(client, "contact_email", getattr(client, "email", "N/A")) if client else "N/A"
    client_phone = getattr(client, "phone", "N/A") if client else "N/A"

    tech_name = getattr(technician, "name", "Não atribuído") if technician else "Não atribuído"

    sched_str = "Não agendado"
    if getattr(work_order, "scheduled_at", None):
        sched_dt = work_order.scheduled_at
        if isinstance(sched_dt, datetime):
            sched_str = sched_dt.strftime("%d/%m/%Y %H:%M")
        else:
            sched_str = str(sched_dt)

    status_labels = {
        "pending": "Pendente",
        "in_progress": "Em Andamento",
        "completed": "Concluída",
        "cancelled": "Cancelada",
    }
    status_display = status_labels.get(work_order.status, work_order.status.upper())

    info_data = [
        [
            Paragraph("<b>CLIENTE / LOCAL:</b>", cell_bold_style),
            Paragraph(client_name, cell_text_style),
            Paragraph("<b>STATUS:</b>", cell_bold_style),
            Paragraph(status_display, cell_text_style),
        ],
        [
            Paragraph("<b>DOCUMENTO / CNPJ:</b>", cell_bold_style),
            Paragraph(client_doc, cell_text_style),
            Paragraph("<b>PRIORIDADE:</b>", cell_bold_style),
            Paragraph(getattr(work_order, "priority", "Média").capitalize(), cell_text_style),
        ],
        [
            Paragraph("<b>CONTATO / TELEFONE:</b>", cell_bold_style),
            Paragraph(f"{client_contact} | {client_phone}", cell_text_style),
            Paragraph("<b>TÉCNICO RESPONSÁVEL:</b>", cell_bold_style),
            Paragraph(tech_name, cell_text_style),
        ],
        [
            Paragraph("<b>EMISSÃO:</b>", cell_bold_style),
            Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), cell_text_style),
            Paragraph("<b>DATA/HORA AGENDADA:</b>", cell_bold_style),
            Paragraph(sched_str, cell_text_style),
        ],
    ]
    info_table = Table(info_data, colWidths=[40 * mm, 50 * mm, 42 * mm, 48 * mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>DESCRIÇÃO DO SERVIÇO / ESCOPO</b>", section_title_style))
    story.append(Spacer(1, 4))
    desc_content = [
        [Paragraph(f"<b>Título:</b> {work_order.title}", cell_bold_style)],
        [Paragraph(work_order.description or "Sem descrição detalhada.", cell_text_style)],
    ]
    desc_table = Table(desc_content, colWidths=[180 * mm])
    desc_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(desc_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>PEÇAS, MATERIAIS E SERVIÇOS APLICADOS</b>", section_title_style))
    story.append(Spacer(1, 4))
    items = items or []
    items_rows = [
        [
            Paragraph("<b>Item / Descrição</b>", cell_bold_style),
            Paragraph("<b>Qtd</b>", cell_bold_style),
            Paragraph("<b>Vlr Unit. (R$)</b>", cell_bold_style),
            Paragraph("<b>Subtotal (R$)</b>", cell_bold_style),
        ]
    ]
    if items:
        for it in items:
            desc = it.description or "Item"
            qty = it.quantity or 1
            unit = float(it.unit_price or 0.0)
            sub = float(it.total_price or (qty * unit))
            items_rows.append([
                Paragraph(desc, cell_text_style),
                Paragraph(str(qty), cell_text_style),
                Paragraph(f"R$ {unit:,.2f}", cell_text_style),
                Paragraph(f"R$ {sub:,.2f}", cell_text_style),
            ])
    else:
        items_rows.append([
            Paragraph("Nenhuma peça ou material registrado.", cell_text_style),
            Paragraph("-", cell_text_style),
            Paragraph("-", cell_text_style),
            Paragraph("R$ 0,00", cell_text_style),
        ])

    items_table = Table(items_rows, colWidths=[95 * mm, 20 * mm, 32 * mm, 33 * mm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 8))

    labor_val = float(getattr(work_order, "labor_cost", 0.0) or 0.0)
    parts_val = float(getattr(work_order, "parts_cost", 0.0) or 0.0)
    total_val = float(getattr(work_order, "total_cost", 0.0) or (labor_val + parts_val))

    totals_data = [
        [
            Paragraph("<b>Mão de Obra:</b>", cell_bold_style),
            Paragraph(f"R$ {labor_val:,.2f}", cell_text_style),
            Paragraph("<b>Peças/Materiais:</b>", cell_bold_style),
            Paragraph(f"R$ {parts_val:,.2f}", cell_text_style),
            Paragraph("<b>TOTAL GERAL:</b>", cell_bold_style),
            Paragraph(f"<b>R$ {total_val:,.2f}</b>", cell_bold_style),
        ]
    ]
    totals_table = Table(totals_data, colWidths=[28 * mm, 32 * mm, 32 * mm, 32 * mm, 28 * mm, 28 * mm])
    totals_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#0284c7")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 14))

    disclaimer_text = (
        "Declaramos que os serviços acima descritos foram realizados e inspecionados em conformidade com as "
        "especificações técnicas, normas de segurança e exigências operacionais acordadas. O cliente declara "
        "estar de acordo com o escopo executado, peças aplicadas e valores discriminados nesta Ordem de Serviço."
    )
    story.append(Paragraph(disclaimer_text, disclaimer_style))
    story.append(Spacer(1, 24))

    sign_data = [
        [
            Paragraph("____________________________________________<br/><b>TÉCNICO RESPONSÁVEL</b><br/>" + tech_name, sign_label_style),
            Paragraph("____________________________________________<br/><b>CLIENTE / RESPONSÁVEL LOCAL</b><br/>" + client_name, sign_label_style),
        ],
        [
            Paragraph("Data: ____/____/________", sign_label_style),
            Paragraph("Data: ____/____/________", sign_label_style),
        ]
    ]
    sign_table = Table(sign_data, colWidths=[90 * mm, 90 * mm])
    sign_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ]))
    story.append(sign_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_sla_report_pdf(metrics, client_name, start_date=None, end_date=None, sample_tickets=None, client_names=None) -> bytes:
    """Create a PDF operational summary, explicitly distinguishing it from SLA compliance."""
    from xml.sax.saxutils import escape
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("ReportTitle", parent=styles["Title"], textColor=colors.HexColor("#0f172a"), alignment=0)
    h2 = ParagraphStyle("ReportH2", parent=styles["Heading2"], textColor=colors.HexColor("#1e293b"))
    body = ParagraphStyle("ReportBody", parent=styles["BodyText"], fontSize=8, leading=11)
    story = [Paragraph("Relatório operacional de chamados e SLA", title), Spacer(1, 5 * mm)]
    period = f"{start_date or 'Início'} a {end_date or 'Hoje'}"
    story.append(Paragraph(f"Unidade/cliente: {escape(str(client_name))} &nbsp;&nbsp; | &nbsp;&nbsp; Período: {escape(period)}", body))
    story.append(Paragraph("Indicadores operacionais. Não representam cumprimento contratual de SLA: políticas e prazos não estão configurados no sistema.", body))
    story.append(Spacer(1, 5 * mm))
    tickets = metrics.get("tickets", {})
    orders = metrics.get("work_orders", {})
    assets = metrics.get("assets", {})
    rows = [["Indicador", "Total"], ["Chamados", str(tickets.get("total", 0))], ["Chamados ativos", str(tickets.get("active", 0))], ["Chamados urgentes ativos", str(tickets.get("urgent_active", 0))], ["OS", str(orders.get("total", 0))], ["OS pendentes/em execução", str(orders.get("pending_or_running", 0))], ["Ativos cadastrados", str(assets.get("total", 0))]]
    table = Table(rows, colWidths=[120 * mm, 40 * mm], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0,0),(-1,0), colors.HexColor("#e2e8f0")), ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"), ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cbd5e1")), ("PADDING",(0,0),(-1,-1),6)]))
    story.extend([table, Spacer(1, 5 * mm), Paragraph("Chamados por prioridade", h2)])
    pri = metrics.get("tickets", {}).get("by_priority", {})
    story.append(Paragraph(" &nbsp; | &nbsp; ".join(f"{escape(k)}: {v}" for k,v in pri.items()) or "Sem registros", body))
    story.append(Paragraph("Carga de trabalho por técnico", h2))
    tech_rows = [["Técnico", "Ativos", "Resolvidos"]] + [[t.get("name", ""), str(t.get("active_tickets", 0)), str(t.get("completed_tickets", 0))] for t in metrics.get("technician_workload", [])]
    tt = Table(tech_rows, colWidths=[90 * mm, 35 * mm, 35 * mm], repeatRows=1)
    tt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e2e8f0")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cbd5e1")),("PADDING",(0,0),(-1,-1),5)]))
    story.append(tt)
    story.extend([Spacer(1, 5 * mm), Paragraph("Amostra de chamados recentes", h2)])
    sample_rows = [["ID / título", "Unidade", "Prioridade", "Status"]]
    for t in sample_tickets or []:
        sample_rows.append([f"#{t.id} {t.title[:48]}", (client_names or {}).get(t.client_id, ""), t.priority, t.status])
    if len(sample_rows) == 1:
        sample_rows.append(["Sem chamados no período", "", "", ""])
    sample_table = Table(sample_rows, colWidths=[72 * mm, 43 * mm, 23 * mm, 22 * mm], repeatRows=1)
    sample_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e2e8f0")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cbd5e1")),("PADDING",(0,0),(-1,-1),4)]))
    story.append(sample_table)
    doc.build(story)
    return buffer.getvalue()
