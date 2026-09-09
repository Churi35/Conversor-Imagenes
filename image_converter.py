import sys
import os
import subprocess
from pathlib import Path


# ============================================================
# Bootstrap automático del entorno virtual
# ============================================================

REQUIRED_PACKAGES = {
    "PyQt6": "PyQt6",
    "PIL": "Pillow",
}


def ensure_virtual_environment():
    """
    Crea un entorno virtual local y ejecuta nuevamente
    este programa utilizando el Python del entorno.

    Esto evita modificar el Python del sistema y evita
    problemas con PEP 668 / externally-managed-environment.
    """

    # Ya estamos dentro del entorno virtual.
    if sys.prefix != sys.base_prefix:
        return

    base_dir = Path(__file__).resolve().parent
    venv_dir = base_dir / ".venv"

    if os.name == "nt":
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:
        venv_python = venv_dir / "bin" / "python"

    # Crear el entorno virtual si todavía no existe.
    if not venv_python.exists():
        print("Creando entorno virtual .venv...")

        try:
            subprocess.check_call([
                sys.executable,
                "-m",
                "venv",
                str(venv_dir),
            ])
        except subprocess.CalledProcessError:
            print()
            print("No fue posible crear el entorno virtual.")
            print()
            print("En Ubuntu/Debian puedes instalar python3-venv con:")
            print()
            print("    sudo apt install python3-venv")
            print()
            sys.exit(1)

    # Comprobar e instalar las dependencias.
    for import_name, package_name in REQUIRED_PACKAGES.items():

        try:
            subprocess.check_call(
                [
                    str(venv_python),
                    "-c",
                    f"import {import_name}",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        except subprocess.CalledProcessError:

            print(f"Instalando {package_name}...")

            try:
                subprocess.check_call([
                    str(venv_python),
                    "-m",
                    "pip",
                    "install",
                    package_name,
                ])
            except subprocess.CalledProcessError:
                print(f"No fue posible instalar {package_name}.")
                sys.exit(1)

    # Reiniciar el programa utilizando el Python del .venv.
    print("Iniciando aplicación...")

    os.execv(
        str(venv_python),
        [str(venv_python)] + sys.argv,
    )


ensure_virtual_environment()


# ============================================================
# Imports de la aplicación
# ============================================================

from PIL import Image

from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)


FORMATS = {
    "PNG": "PNG",
    "JPEG": "JPEG",
    "WEBP": "WEBP",
    "BMP": "BMP",
    "TIFF": "TIFF",
}

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}


# ============================================================
# Aplicación
# ============================================================

class ImageConverter(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Image Converter")
        self.resize(760, 430)

        self.input_path = None
        self.output_dir = None

        self.build_ui()
        self.update_mode_ui()

    # --------------------------------------------------------
    # Interfaz
    # --------------------------------------------------------

    def build_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        title = QLabel("Conversor de imágenes")
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )
        main_layout.addWidget(title)

        # -------------------------
        # Modo de operación
        # -------------------------

        mode_group = QGroupBox("Modo de operación")
        mode_layout = QHBoxLayout(mode_group)

        self.normal_radio = QRadioButton(
            "Convertir una imagen"
        )
        self.normal_radio.setChecked(True)

        self.batch_radio = QRadioButton(
            "Convertir una carpeta"
        )

        self.normal_radio.toggled.connect(
            self.update_mode_ui
        )

        mode_layout.addWidget(self.normal_radio)
        mode_layout.addWidget(self.batch_radio)
        mode_layout.addStretch()

        main_layout.addWidget(mode_group)

        # -------------------------
        # Entrada
        # -------------------------

        input_group = QGroupBox("Entrada")
        input_layout = QGridLayout(input_group)

        self.input_label = QLabel("Imagen:")
        input_layout.addWidget(
            self.input_label,
            0,
            0,
        )

        self.input_edit = QLineEdit()
        self.input_edit.setReadOnly(True)

        self.input_button = QPushButton(
            "Seleccionar imagen"
        )

        self.input_button.clicked.connect(
            self.select_input
        )

        input_layout.addWidget(
            self.input_edit,
            0,
            1,
        )

        input_layout.addWidget(
            self.input_button,
            0,
            2,
        )

        main_layout.addWidget(input_group)

        # -------------------------
        # Conversión
        # -------------------------

        conversion_group = QGroupBox("Conversión")
        conversion_layout = QGridLayout(
            conversion_group
        )

        conversion_layout.addWidget(
            QLabel("Formato destino:"),
            0,
            0,
        )

        self.format_combo = QComboBox()

        self.format_combo.addItems(
            FORMATS.keys()
        )

        self.format_combo.setCurrentText(
            "PNG"
        )

        conversion_layout.addWidget(
            self.format_combo,
            0,
            1,
        )

        conversion_layout.addWidget(
            QLabel("Directorio destino:"),
            1,
            0,
        )

        self.output_edit = QLineEdit()
        self.output_edit.setReadOnly(True)

        output_button = QPushButton(
            "Seleccionar carpeta"
        )

        output_button.clicked.connect(
            self.select_output
        )

        conversion_layout.addWidget(
            self.output_edit,
            1,
            1,
        )

        conversion_layout.addWidget(
            output_button,
            1,
            2,
        )

        main_layout.addWidget(
            conversion_group
        )

        # -------------------------
        # Botón
        # -------------------------

        buttons = QHBoxLayout()

        self.convert_button = QPushButton(
            "Convertir imagen"
        )

        self.convert_button.clicked.connect(
            self.start_conversion
        )

        buttons.addWidget(
            self.convert_button
        )

        buttons.addStretch()

        main_layout.addLayout(buttons)

        # -------------------------
        # Progreso
        # -------------------------

        self.progress = QProgressBar()
        self.progress.setValue(0)

        main_layout.addWidget(
            self.progress
        )

        self.status = QLabel("Listo.")

        main_layout.addWidget(
            self.status
        )

    # --------------------------------------------------------
    # Cambio de modo
    # --------------------------------------------------------

    def update_mode_ui(self):

        is_single = self.normal_radio.isChecked()

        self.input_path = None
        self.input_edit.clear()

        self.progress.setValue(0)
        self.status.setText("Listo.")

        if is_single:

            self.input_label.setText(
                "Imagen:"
            )

            self.input_button.setText(
                "Seleccionar imagen"
            )

            self.convert_button.setText(
                "Convertir imagen"
            )

        else:

            self.input_label.setText(
                "Carpeta:"
            )

            self.input_button.setText(
                "Seleccionar carpeta"
            )

            self.convert_button.setText(
                "Convertir carpeta"
            )

    # --------------------------------------------------------
    # Seleccionar entrada
    # --------------------------------------------------------

    def select_input(self):

        # Modo imagen
        if self.normal_radio.isChecked():

            path, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar imagen",
                "",
                (
                    "Imágenes "
                    "(*.png *.jpg *.jpeg *.webp "
                    "*.bmp *.tif *.tiff)"
                ),
            )

            if path:

                self.input_path = Path(path)

                self.input_edit.setText(
                    str(self.input_path)
                )

                if not self.output_dir:

                    self.output_dir = (
                        self.input_path.parent
                    )

                    self.output_edit.setText(
                        str(self.output_dir)
                    )

        # Modo carpeta
        else:

            directory = (
                QFileDialog.getExistingDirectory(
                    self,
                    "Seleccionar carpeta con imágenes",
                )
            )

            if directory:

                self.input_path = Path(
                    directory
                )

                self.input_edit.setText(
                    str(self.input_path)
                )

                if not self.output_dir:

                    self.output_dir = (
                        self.input_path
                    )

                    self.output_edit.setText(
                        str(self.output_dir)
                    )

    # --------------------------------------------------------
    # Seleccionar destino
    # --------------------------------------------------------

    def select_output(self):

        directory = (
            QFileDialog.getExistingDirectory(
                self,
                "Seleccionar directorio destino",
            )
        )

        if directory:

            self.output_dir = Path(
                directory
            )

            self.output_edit.setText(
                str(self.output_dir)
            )

    # --------------------------------------------------------
    # Generar nombre de salida
    # --------------------------------------------------------

    def get_output_path(self, source):

        extension = (
            self.format_combo.currentText()
            .lower()
        )

        if extension == "jpeg":
            suffix = ".jpg"
        else:
            suffix = "." + extension

        return (
            self.output_dir
            / f"{source.stem}_converted{suffix}"
        )

    # --------------------------------------------------------
    # Iniciar conversión
    # --------------------------------------------------------

    def start_conversion(self):

        if self.normal_radio.isChecked():

            self.convert_image()

        else:

            self.convert_folder()

    # --------------------------------------------------------
    # Convertir una imagen
    # --------------------------------------------------------

    def convert_image(self):

        if not self.input_path:

            QMessageBox.warning(
                self,
                "Falta imagen",
                "Selecciona una imagen.",
            )

            return

        if not self.output_dir:

            QMessageBox.warning(
                self,
                "Falta directorio",
                "Selecciona un directorio destino.",
            )

            return

        try:

            self.progress.setValue(10)

            self.status.setText(
                "Leyendo imagen..."
            )

            with Image.open(
                self.input_path
            ) as image:

                if (
                    self.format_combo.currentText()
                    == "JPEG"
                ):

                    image = image.convert(
                        "RGB"
                    )

                output_path = (
                    self.get_output_path(
                        self.input_path
                    )
                )

                self.status.setText(
                    "Escribiendo imagen..."
                )

                image.save(
                    output_path,
                    format=FORMATS[
                        self.format_combo.currentText()
                    ],
                )

            self.progress.setValue(100)

            self.status.setText(
                f"Conversión terminada: "
                f"{output_path.name}"
            )

            QMessageBox.information(
                self,
                "Conversión terminada",
                (
                    "Imagen guardada en:\n"
                    f"{output_path}"
                ),
            )

        except Exception as exc:

            self.progress.setValue(0)

            self.status.setText(
                "Error durante la conversión."
            )

            QMessageBox.critical(
                self,
                "Error",
                (
                    "No fue posible convertir "
                    f"la imagen:\n\n{exc}"
                ),
            )

    # --------------------------------------------------------
    # Convertir carpeta
    # --------------------------------------------------------

    def convert_folder(self):

        if not self.input_path:

            QMessageBox.warning(
                self,
                "Falta carpeta",
                "Selecciona una carpeta con imágenes.",
            )

            return

        if not self.output_dir:

            QMessageBox.warning(
                self,
                "Falta directorio",
                "Selecciona un directorio destino.",
            )

            return

        source_dir = self.input_path

        if not source_dir.is_dir():

            QMessageBox.warning(
                self,
                "Carpeta inválida",
                (
                    "La entrada seleccionada "
                    "no es una carpeta."
                ),
            )

            return

        images = [
            p
            for p in source_dir.iterdir()
            if (
                p.is_file()
                and p.suffix.lower()
                in IMAGE_EXTENSIONS
            )
        ]

        if not images:

            QMessageBox.information(
                self,
                "Sin imágenes",
                (
                    "No se encontraron imágenes "
                    "compatibles en la carpeta."
                ),
            )

            return

        converted = 0
        errors = 0

        self.progress.setValue(0)

        for index, source in enumerate(
            images,
            start=1,
        ):

            try:

                self.status.setText(
                    (
                        f"Procesando {index}/"
                        f"{len(images)}: "
                        f"{source.name}"
                    )
                )

                with Image.open(
                    source
                ) as image:

                    if (
                        self.format_combo.currentText()
                        == "JPEG"
                    ):

                        image = image.convert(
                            "RGB"
                        )

                    output_path = (
                        self.get_output_path(
                            source
                        )
                    )

                    image.save(
                        output_path,
                        format=FORMATS[
                            self.format_combo.currentText()
                        ],
                    )

                converted += 1

            except Exception:

                errors += 1

            percent = int(
                index * 100 / len(images)
            )

            self.progress.setValue(
                percent
            )

            # Permite actualizar la interfaz
            # durante el procesamiento.
            QApplication.processEvents()

        self.status.setText(
            (
                "Proceso terminado. "
                f"Convertidas: {converted}. "
                f"Errores: {errors}."
            )
        )

        QMessageBox.information(
            self,
            "Conversión terminada",
            (
                f"Imágenes procesadas: {len(images)}\n"
                f"Convertidas: {converted}\n"
                f"Errores: {errors}"
            ),
        )


# ============================================================
# Inicio
# ============================================================

def main():

    app = QApplication(sys.argv)

    window = ImageConverter()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()