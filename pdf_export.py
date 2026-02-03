import sqlite3, json, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime

# ================= EXPORTAR PDF =================
def exportar_pdf(id_bd):

    # ===== BD =====
    con = sqlite3.connect("data/database.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM registros WHERE id=?", (id_bd,))
    row = cur.fetchone()
    con.close()

    if not row:
        print("Registro no encontrado")
        return

    cliente = row[1]
    ruc = row[2]
    direccion = row[3]
    correo = row[4]
    responsable = row[5]
    telefono = row[6]
    guia = row[7]
    fecha = row[8]
    equipos = json.loads(row[9]) if row[9] else []

    firma_tecnico = row[10]
    firma_cliente = row[11]

    nro_formato = 1000 + id_bd
    filename = f"Formato_CABELAB_{nro_formato}.pdf"

    # ===== ESTILOS =====
    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", fontSize=7)
    small_bold = ParagraphStyle("smallbold", fontSize=7, fontName="Helvetica-Bold")
    title = ParagraphStyle("title", fontSize=11, alignment=TA_CENTER, fontName="Helvetica-Bold")
    right = ParagraphStyle("right", fontSize=7, alignment=TA_LEFT)

    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm)
    elementos = []

    # =====================================================
    # HEADER LOGO + EMPRESA
    # =====================================================
    logo = ""
    if os.path.exists("data/logo_cabelab.png"):
        logo = Image("data/logo_cabelab.png", 6*cm, 1.8*cm)

    empresa_info = Paragraph("""
    <b>CABELAB S.A.C. - SERVICIO AUTORIZADO ESAB</b><br/>
    AV. Venezuela 866 - Urb. Santa Isabel La Perla<br/>
    AREQUIPA - PERÚ<br/>
    ventas@cabelab.com | +51 919007755
    """, right)

    header = Table([[logo, empresa_info]], colWidths=[7*cm, 10*cm])
    header.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))

    elementos.append(header)
    elementos.append(Spacer(1, 5))

    # =====================================================
    # TITULO
    # =====================================================
    elementos.append(Paragraph(f"<b>FORMATO DE RECEPCIÓN N° {nro_formato}</b>", title))
    elementos.append(Spacer(1, 5))

    # =====================================================
    # DATOS CLIENTE
    # =====================================================
    # separar fecha y hora
    fecha_solo, hora_solo = fecha.split(" ")

    datos = f"""
    <b>FECHA:</b> {fecha_solo}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
    <b>HORA:</b> {hora_solo}<br/>

    <b>CLIENTE:</b> {cliente}<br/>
    <b>RUC/DNI:</b> {ruc}<br/>
    <b>DIRECCIÓN:</b> {direccion}<br/>
    <b>CORREO:</b> {correo}<br/>

    <b>RESPONSABLE:</b> {responsable}<br/>
    <b>TELF / CELULAR:</b> {telefono}<br/>
    <b>GUÍA DE REMISIÓN:</b> {guia}<br/>
    """
    elementos.append(Paragraph(datos, small))
    elementos.append(Spacer(1, 6))

    # =====================================================
    # TABLA EQUIPOS
    # =====================================================
    encabezado = ["ITEM","CANT","MARCA","MODELO","DESCRIPCIÓN","N° SERIE","SERVICIO","FALLA"]
    data = [encabezado]

    for i, eq in enumerate(equipos, start=1):
        data.append([
            Paragraph(str(i), small),
            Paragraph(eq["cant"], small),
            Paragraph(eq["marca"], small),
            Paragraph(eq["modelo"], small),
            Paragraph(eq["descripcion"], small),   # ✅ AQUI
            Paragraph(eq["serie"], small),
            Paragraph(eq["servicio"], small),
            Paragraph(eq["falla"], small),
        ])

    tabla = Table(data, repeatRows=1,
        colWidths=[0.8*cm,0.8*cm,2.2*cm,2.5*cm,3.5*cm,2.5*cm,2.2*cm,2.5*cm])

    tabla.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
        ('GRID',(0,0),(-1,-1),0.3,colors.black),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),7),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('ALIGN',(0,0),(-1,0),'CENTER'),
    ]))

    elementos.append(Paragraph("<b>1. EQUIPOS</b>", small_bold))
    elementos.append(tabla)
    elementos.append(Spacer(1, 8))

    # =====================================================
    # TABLA ACCESORIOS
    # =====================================================
    data2 = [["ITEM","ACCESORIOS","OBSERVACIONES"]]

    for i, eq in enumerate(equipos, start=1):
        data2.append([
            Paragraph(str(i), small),
            Paragraph(eq["accesorio"], small),
            Paragraph(eq["obs"], small),
        ])


    tabla2 = Table(data2, repeatRows=1, colWidths=[1*cm,8*cm,8*cm])
    tabla2.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.lightgrey),
        ('GRID',(0,0),(-1,-1),0.3,colors.black),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),7),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))

    elementos.append(Paragraph("<b>2. ACCESORIOS Y OBSERVACIONES</b>", small_bold))
    elementos.append(tabla2)
    elementos.append(Spacer(1, 10))

    # =====================================================
    # NOTA
    # =====================================================
    nota = Paragraph("""
    <b>NOTA:</b> Transcurrido un año desde la fecha de recepción, la empresa no se hace responsable por 
    deterioro o pérdida del equipo. Todo reclamo posterior queda sin efecto.
    """, small)
    elementos.append(nota)
    elementos.append(Spacer(1, 12))

    # =====================================================
    # FIRMAS
    # =====================================================
    # Firma técnico
    if firma_tecnico and os.path.exists(firma_tecnico):
        img_tecnico = Image(firma_tecnico, 4*cm, 1.5*cm)
    else:
        img_tecnico = Paragraph(" ", small)

    # Firma cliente
    if firma_cliente and os.path.exists(firma_cliente):
        img_cliente = Image(firma_cliente, 4*cm, 1.5*cm)
    else:
        img_cliente = Paragraph(" ", small)

    # Tabla firma técnico
    tabla_firma1 = Table([
        [img_tecnico],
        ["Nombre y firma del encargado de recepción"]
    ], colWidths=[8*cm])

    tabla_firma1.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('LINEBELOW',(0,0),(0,0),0.3,colors.black),
        ('FONTSIZE',(0,1),(-1,1),7),
    ]))

    # Tabla firma cliente
    tabla_firma2 = Table([
        [img_cliente],
        ["Nombre y firma del cliente responsable"]
    ], colWidths=[8*cm])

    tabla_firma2.setStyle(TableStyle([
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('LINEBELOW',(0,0),(0,0),0.3,colors.black),
        ('FONTSIZE',(0,1),(-1,1),7),
    ]))

    tabla_firmas = Table([
        [tabla_firma1, "", tabla_firma2]
    ], colWidths=[8*cm, 1*cm, 8*cm])

    elementos.append(tabla_firmas)

    # =====================================================
    doc.build(elementos)
    #print("PDF generado:", filename)
    return filename
