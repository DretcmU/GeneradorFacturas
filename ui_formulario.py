from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPainter, QPen, QPixmap
from PyQt5.QtCore import Qt, QPoint
import sqlite3
from datetime import datetime
import os
import json

# ================= LISTAS =================
DESCRIPCIONES = ["",
"MAQUINA DE SOLDAR","ALIMENTADOR","MOTOSOLDADORA","TARJETAS ELECTRÓNICAS","ANTORCHA",
"CABLE DE CONTROL","MALETA","TRACTOR COMPACTO UNIVERSAL","CORTE PLASMA",
"OXICORTE CNC","EXTRACTOR DE HUMOS","CARETA DE SOLDAR"
]

MARCAS = ["",
"ESAB","MILLER","LINCOLN E.","BOSCH","KEMPPI","DAF","ALIENWELD","RONCH",
"HYPERTHERM","CABELAB","HOBART","CEMONT","HUGONG","KENDE","OERLIKON",
"TRUPER","OKAYAMA","WELDECK","SOLANDINAS","STAYER WELDING"
]

SERVICIOS = ["",
"Revisión General",
"Garantía ESAB",
"Garantía CABELAB"
]

# ================= FIRMA DIGITAL =================
class Firma(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400,150)
        self.pix = QPixmap(self.size())
        self.pix.fill(Qt.white)
        self.last = QPoint()

    def paintEvent(self, e):
        p = QPainter(self)
        p.drawPixmap(0,0,self.pix)

    def mousePressEvent(self, e):
        self.last = e.pos()

    def mouseMoveEvent(self, e):
        p = QPainter(self.pix)
        pen = QPen(Qt.black, 2)
        p.setPen(pen)
        p.drawLine(self.last, e.pos())
        self.last = e.pos()
        self.update()

    def guardar(self, ruta):
        self.pix.save(ruta)

# ================= FORMULARIO =================
class Formulario(QWidget):
    def __init__(self, main, id_bd=None):
        super().__init__()
        self.main = main
        self.id_bd = id_bd

        self.setWindowTitle("Formato de Recepción CABELAB")
        self.setGeometry(50,50,1400,900)

        layout = QVBoxLayout()

        # ===== DATOS CLIENTE =====
        grid = QGridLayout()
        self.cliente = QLineEdit()
        self.ruc = QLineEdit()
        self.direccion = QLineEdit()
        self.correo = QLineEdit()

        grid.addWidget(QLabel("Cliente"),0,0)
        grid.addWidget(self.cliente,0,1)
        grid.addWidget(QLabel("RUC/DNI"),0,2)
        grid.addWidget(self.ruc,0,3)
        grid.addWidget(QLabel("Dirección"),1,0)
        grid.addWidget(self.direccion,1,1)
        grid.addWidget(QLabel("Correo"),1,2)
        grid.addWidget(self.correo,1,3)

        self.responsable = QLineEdit()
        self.telefono = QLineEdit()
        self.guia = QLineEdit()

        # NUEVA FILA SUPERIOR
        grid.addWidget(QLabel("Responsable"), 2, 0)
        grid.addWidget(self.responsable, 2, 1)
        grid.addWidget(QLabel("Teléfono/Celular"), 2, 2)
        grid.addWidget(self.telefono, 2, 3)

        grid.addWidget(QLabel("Guía de Remisión"), 3, 0)
        grid.addWidget(self.guia, 3, 1)

        layout.addLayout(grid)

        # ===== TABLA EQUIPOS =====
        self.equipos = QTableWidget()
        self.equipos.setColumnCount(8)
        self.equipos.setHorizontalHeaderLabels(
            ["Item","Cant","Marca","Modelo","Descripción","Serie","Servicio","Falla"]
        )
        self.equipos.setRowCount(0)

        layout.addWidget(QLabel("EQUIPOS"))
        layout.addWidget(self.equipos)

        # ===== BOTONES =====
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Agregar Equipo")
        btn_del = QPushButton("➖ Quitar Equipo")

        btn_add.clicked.connect(self.agregar_equipo)
        btn_del.clicked.connect(self.quitar_equipo)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_del)
        layout.addLayout(btn_layout)

        # ===== ACCESORIOS =====
        self.acc = QTableWidget()
        self.acc.setColumnCount(3)
        self.acc.setHorizontalHeaderLabels(["Item","Accesorio","Observación"])
        self.acc.setRowCount(0)

        layout.addWidget(QLabel("ACCESORIOS DEL EQUIPO"))
        layout.addWidget(self.acc)

        # agregar primera fila
        self.agregar_equipo()

        # ===== FIRMAS =====
        firmas_layout = QHBoxLayout()
        self.firma_tecnico = Firma()
        self.firma_cliente = Firma()

        firmas_layout.addWidget(QLabel("Firma Recepción"))
        firmas_layout.addWidget(self.firma_tecnico)
        firmas_layout.addWidget(QLabel("Firma Cliente"))
        firmas_layout.addWidget(self.firma_cliente)

        layout.addLayout(firmas_layout)

        # ===== BOTON GUARDAR =====
        btn_guardar = QPushButton("💾 Guardar Registro")
        btn_guardar.clicked.connect(self.guardar)
        layout.addWidget(btn_guardar)

        self.setLayout(layout)
        
        self.cargar_registro()


    # ================= GUARDAR =================
    def guardar(self):
        os.makedirs("data/firmas", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        firma1 = f"data/firmas/firma_recepcion_{ts}.png"
        firma2 = f"data/firmas/firma_cliente_{ts}.png"

        if not self.cliente.text():
            QMessageBox.warning(self,"Error","Ingrese cliente")
            return
            
        # ===== GUARDAR EQUIPOS + ACCESORIOS =====
        lista_equipos = []

        for row in range(self.equipos.rowCount()):
            cant = self.get_item(self.equipos, row,1)
            modelo = self.get_item(self.equipos, row,3)
            serie = self.get_item(self.equipos, row,5)
            falla = self.get_item(self.equipos, row,7)

            marca = self.equipos.cellWidget(row,2).currentText()
            desc  = self.equipos.cellWidget(row,4).currentText()
            serv  = self.equipos.cellWidget(row,6).currentText()

            accesorio = self.get_item(self.acc, row,1)
            obs = self.get_item(self.acc, row,2)

            if modelo == "" and serie == "":
                continue

            lista_equipos.append({
                "cant": cant,
                "marca": marca,
                "modelo": modelo,
                "descripcion": desc,
                "serie": serie,
                "servicio": serv,
                "falla": falla,
                "accesorio": accesorio,
                "obs": obs
            })

        equipos_json = json.dumps(lista_equipos, ensure_ascii=False)

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ===== SQLITE =====
        con = sqlite3.connect("data/database.db")
        cur = con.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS registros(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            ruc TEXT,
            direccion TEXT,
            correo TEXT,
            responsable TEXT,
            telefono TEXT,
            guia TEXT,
            fecha TEXT,
            equipos TEXT,
            firma_tecnico TEXT,
            firma_cliente TEXT
        )
        """)

        if self.id_bd:  # EDITAR
            cur.execute("""
            UPDATE registros 
            SET cliente=?, ruc=?, direccion=?, correo=?, responsable=?, telefono=?, guia=?, equipos=? 
            WHERE id=?
            """, (
                self.cliente.text(),
                self.ruc.text(),
                self.direccion.text(),
                self.correo.text(),
                self.responsable.text(),
                self.telefono.text(),
                self.guia.text(),
                equipos_json,
                self.id_bd
            ))
        else:  # NUEVO
            cur.execute("""
            INSERT INTO registros(cliente,ruc,direccion,correo,responsable,telefono,guia,fecha,equipos,firma_tecnico,firma_cliente)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,(
                self.cliente.text(),
                self.ruc.text(),
                self.direccion.text(),
                self.correo.text(),
                self.responsable.text(),
                self.telefono.text(),
                self.guia.text(),
                fecha,
                equipos_json,
                firma1,
                firma2
            ))
            
            self.firma_tecnico.guardar(firma1)
            self.firma_cliente.guardar(firma2)

        con.commit()
        con.close()

        self.main.cargar()
        QMessageBox.information(self, "OK", "Registro guardado correctamente")
        self.close()

    # ===== HELPER =====
    def get_item(self, table, row, col):
        item = table.item(row, col)
        return item.text() if item else ""

    # ================= AGREGAR EQUIPO =================
    def agregar_equipo(self):
        row = self.equipos.rowCount()
        self.equipos.insertRow(row)

        self.equipos.setItem(row,0,QTableWidgetItem(str(row+1)))
        self.equipos.setItem(row,1,QTableWidgetItem("1"))

        combo_marca = QComboBox()
        combo_marca.addItems(MARCAS)
        self.equipos.setCellWidget(row,2,combo_marca)

        self.equipos.setItem(row,3,QTableWidgetItem(""))

        combo_desc = QComboBox()
        combo_desc.addItems(DESCRIPCIONES)
        self.equipos.setCellWidget(row,4,combo_desc)

        self.equipos.setItem(row,5,QTableWidgetItem(""))

        combo_serv = QComboBox()
        combo_serv.addItems(SERVICIOS)
        self.equipos.setCellWidget(row,6,combo_serv)

        self.equipos.setItem(row,7,QTableWidgetItem(""))

        # ACCESORIOS
        self.acc.insertRow(row)
        self.acc.setItem(row,0,QTableWidgetItem(str(row+1)))
        self.acc.setItem(row,1,QTableWidgetItem(""))
        self.acc.setItem(row,2,QTableWidgetItem(""))

        self.actualizar_items()

    def quitar_equipo(self):
        row = self.equipos.rowCount()
        if row > 1:
            self.equipos.removeRow(row-1)
            self.acc.removeRow(row-1)
        self.actualizar_items()

    def actualizar_items(self):
        for i in range(self.equipos.rowCount()):
            self.equipos.setItem(i,0,QTableWidgetItem(str(i+1)))
            self.acc.setItem(i,0,QTableWidgetItem(str(i+1)))

    def cargar_registro(self):
        if not self.id_bd:
            return

        con = sqlite3.connect("data/database.db")
        cur = con.cursor()
        cur.execute("SELECT * FROM registros WHERE id=?", (self.id_bd,))
        row = cur.fetchone()
        con.close()

        if not row:
            return

        self.cliente.setText(row[1])
        self.ruc.setText(row[2])
        self.direccion.setText(row[3])
        self.correo.setText(row[4])
        self.responsable.setText(row[5])
        self.telefono.setText(row[6])
        self.guia.setText(row[7])

        equipos = json.loads(row[9]) if row[9] else []

        self.equipos.setRowCount(0)
        self.acc.setRowCount(0)

        for eq in equipos:
            self.agregar_equipo()
            r = self.equipos.rowCount()-1

            self.equipos.setItem(r,1,QTableWidgetItem(eq["cant"]))
            self.equipos.setItem(r,3,QTableWidgetItem(eq["modelo"]))
            self.equipos.setItem(r,5,QTableWidgetItem(eq["serie"]))
            self.equipos.setItem(r,7,QTableWidgetItem(eq["falla"]))

            self.equipos.cellWidget(r,2).setCurrentText(eq["marca"])
            self.equipos.cellWidget(r,4).setCurrentText(eq["descripcion"])
            self.equipos.cellWidget(r,6).setCurrentText(eq["servicio"])

            self.acc.setItem(r,1,QTableWidgetItem(eq["accesorio"]))
            self.acc.setItem(r,2,QTableWidgetItem(eq["obs"]))
