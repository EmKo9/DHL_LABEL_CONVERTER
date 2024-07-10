from flask import Flask, request, send_file, render_template
import fitz  # PyMuPDF
from PIL import Image
import io

app = Flask(__name__)

def process_label(pdf_path, output_pdf_path):
    # PDF öffnen und die erste Seite extrahieren
    pdf_document = fitz.open(pdf_path)
    page = pdf_document.load_page(0)

    # Erhöhen der Pixmap-Auflösung
    zoom = 3  # Erhöhung der Auflösung um den Faktor 3
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    # Bild aus der PDF-Seite extrahieren
    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Label ins Querformat drehen (90 Grad im Uhrzeigersinn)
    rotated_image = image.rotate(-90, expand=True)

    # Label in der Mitte teilen (rechte Hälfte für Barcodes)
    width, height = rotated_image.size
    right_box = (width // 2, 0, width, height)
    right_image = rotated_image.crop(right_box)

    # DIN A6 Maße (105 mm x 148 mm), konvertiert in Pixel (300 DPI)
    a6_width, a6_height = 1240, 1748

    # Neue A6 Bilder erstellen und das geteilte Label darauf setzen
    new_right_image = Image.new('RGB', (a6_width, a6_height), (255, 255, 255))

    # Rechts gesetztes Bild zentrieren
    right_offset = ((a6_width - right_image.width) // 2, (a6_height - right_image.height) // 2)
    new_right_image.paste(right_image, right_offset)

    # 10 Pixel von der linken Seite abschneiden
    cropped_image = new_right_image.crop((10, 0, a6_width, a6_height))

    # Konvertiere das PIL-Image in Bytes
    img_byte_arr = io.BytesIO()
    cropped_image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()

    # Erstelle einen Pixmap aus den Bytes
    right_pix = fitz.Pixmap(fitz.csRGB, fitz.open("pdf", img_byte_arr).load_page(0).get_pixmap())

    # Neue PDFs erstellen und speichern
    new_pdf_document = fitz.open()
    right_pdf_page = new_pdf_document.new_page(width=a6_width, height=a6_height)

    # Füge den Pixmap in das PDF-Dokument ein
    right_pdf_page.insert_image(right_pdf_page.rect, pixmap=right_pix)
    
    new_pdf_document.save(output_pdf_path)
    new_pdf_document.close()

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    file_path = 'uploaded_label.pdf'
    file.save(file_path)
    
    output_path = 'processed_label.pdf'
    process_label(file_path, output_path)
    
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=False)
