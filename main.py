import sys, sqlite3, json
from PyQt5.QtWidgets import *
from ui_formulario import Formulario
from pdf_export import exportar_pdf
import os

# ================= MAIN WINDOW =================
class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema CABELAB")
        self.setGeometry(100, 100, 1300, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        # ===== BARRA SUPERIOR =====
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar por cliente, modelo, marca...")
        self.search.textChanged.connect(self.cargar)

        btn_add = QPushButton("➕ Agregar Registro")
        btn_add.clicked.connect(self.abrir_formulario)

        top.addWidget(self.search)
        top.addWidget(btn_add)

        # ===== TABLA =====
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Cliente", "RUC", "Dirección", "correo"
            "Marcas", "Modelos", "Fecha", "Editar", "PDF"
        ])

        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 200)
        self.table.setColumnWidth(4, 200)
        self.table.setColumnWidth(5, 150)
        self.table.setColumnWidth(6, 150)
        self.table.setColumnWidth(7, 80)
        self.table.setColumnWidth(8, 80)

        layout.addLayout(top)
        layout.addWidget(self.table)
        central.setLayout(layout)

        self.db()
        self.cargar()

    # ===== DATABASE =====
    def db(self):
        # Crear carpeta data si no existe
        if not os.path.exists("data"):
            os.makedirs("data")

        # Crear DB si no existe        
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
        con.commit()
        con.close()

    # ===== CARGAR DATOS =====
    def cargar(self):
        texto = self.search.text()

        con = sqlite3.connect("data/database.db")
        cur = con.cursor()
        cur.execute("""
        SELECT * FROM registros 
        WHERE cliente LIKE ? OR equipos LIKE ?
        """, (f"%{texto}%", f"%{texto}%"))
        datos = cur.fetchall()
        con.close()

        self.table.setRowCount(len(datos))

        for r, row in enumerate(datos):
            id_bd = row[0]
            cliente = row[1]
            ruc = row[2]
            direccion = row[3]
            fecha = row[5]
            equipos = json.loads(row[9]) if row[9] else []

            marcas = ", ".join(set(e["marca"] for e in equipos))
            modelos = ", ".join(e["modelo"] for e in equipos)

            self.table.setItem(r, 0, QTableWidgetItem(str(id_bd)))
            self.table.setItem(r, 1, QTableWidgetItem(cliente))
            self.table.setItem(r, 2, QTableWidgetItem(ruc))
            self.table.setItem(r, 3, QTableWidgetItem(direccion))
            self.table.setItem(r, 4, QTableWidgetItem(marcas))
            self.table.setItem(r, 5, QTableWidgetItem(modelos))
            self.table.setItem(r, 6, QTableWidgetItem(fecha))

            # ===== BOTON EDITAR =====
            btn_edit = QPushButton("✏️")
            btn_edit.clicked.connect(lambda _, rid=id_bd: self.editar_registro(rid))
            self.table.setCellWidget(r, 7, btn_edit)

            # ===== BOTON PDF =====
            btn_pdf = QPushButton("📄")
            btn_pdf.clicked.connect(lambda _, rid=id_bd: self.exportar_pdf_ui(rid))
            self.table.setCellWidget(r, 8, btn_pdf)

    # ===== FORMULARIO NUEVO =====
    def abrir_formulario(self):
        self.form = Formulario(self)
        self.form.show()

    # ===== FORMULARIO EDITAR =====
    def editar_registro(self, id_bd):
        self.form = Formulario(self, id_bd)
        self.form.show()

    def exportar_pdf_ui(self, id_bd):
        nombre = exportar_pdf(id_bd)

        if nombre:
            QMessageBox.information(
                self,
                "PDF Generado",
                f"El PDF se exportó correctamente:\n\n{nombre}"
            )
            os.startfile(nombre)
        else:
            QMessageBox.warning(self, "Error", "No se pudo generar el PDF")

# ===== RUN =====
app = QApplication(sys.argv)
win = Main()
win.show()
sys.exit(app.exec_())
