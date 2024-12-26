from pdf2image import convert_from_bytes
from PIL import Image
import io
import os

# Get the PDF file name
pdf_path = 'data/pdf/example2.pdf'
pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

# Create the output directory if it doesn't exist
output_dir = 'data/png/'
os.makedirs(output_dir, exist_ok=True)

# Read the PDF file
with open(pdf_path, 'rb') as file:
    pdf_data = file.read()

# Convert PDF to images
images = convert_from_bytes(pdf_data, dpi=300)

# Save each image as PNG
for i, image in enumerate(images):
    output_file = f"{output_dir}{pdf_name}-{i + 1}.png"
    image.save(output_file, 'PNG')

print(f"Converted {len(images)} pages to PNG files in {output_dir}")