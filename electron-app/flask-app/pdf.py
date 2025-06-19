from fpdf import FPDF
import webbrowser
import os
import unicodedata
from datetime import datetime

class PDFGenerator:
    def __init__(self, offer_details):
        self.offer_details = offer_details

    def normalize_text(self, text):
        """Replace Romanian diacritics with normal letters."""
        if not text:
            return ""
        text = unicodedata.normalize('NFKC', text)
        text = ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        return text

    def safe_format_float(self, value):
        """Safely format a value as a float with 2 decimal places, defaulting to 0.00 if invalid."""
        try:
            return f"{float(value):.2f}"
        except (ValueError, TypeError):
            return "0.00"

    def generate_pdf(self):
        try:
            # Determine the dynamic path for the branding image
            current_dir = os.path.dirname(os.path.abspath(__file__))
            branding_image_path = os.path.join(current_dir, 'resources', 'Branding.jpg')

            # Retrieve vehicle details
            vehicle_details = self.offer_details.get("vehicle_name") or "-"

            # Retrieve client name
            client_name = self.offer_details.get('client_name') or self.offer_details.get('nume', 'Client Necunoscut')

            date = self.offer_details['date']
            observations = self.offer_details['observations']
            categories = self.offer_details['categories']

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # Add branding image as a centered header
            pdf.image(branding_image_path, x=(210 - 50) / 2, y=10, h=25)  # Centered image with height 25px
            pdf.ln(40)  # Add 40px vertical space below the logo

            # Add company title and subtitle
            pdf.set_font('Helvetica', 'B', 18)
            pdf.cell(0, 10, self.normalize_text('AutoSavCar Company'), ln=True, align='C')
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, self.normalize_text(f'Oferta pentru {client_name}'), ln=True, align='C')
            pdf.ln(15)  # Add space below the subtitle

            # Add client and offer details
            pdf.set_font('Helvetica', '', 12)
            pdf.cell(0, 10, self.normalize_text(f'Masina: {vehicle_details}'), ln=True)
            pdf.cell(0, 10, self.normalize_text(f'Data: {date}'), ln=True)
            pdf.cell(0, 10, self.normalize_text(f'Nr. Oferta: {self.offer_details["offer_number"]}'), ln=True)
            pdf.ln(10)  # Add space below the details

            # Add observations
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 10, self.normalize_text('Observatii'), ln=True)
            pdf.set_fill_color(245, 245, 245)  # Light gray background for observations
            pdf.multi_cell(0, 10, self.normalize_text(observations), fill=True)
            pdf.ln(10)  # Add space below observations

            # Add category-specific tables
            for category, data in categories.items():
                # Add category title
                pdf.set_font('Helvetica', 'B', 14)
                total_price = float(data['total_price']) if isinstance(data['total_price'], (int, float, str)) else 0.0
                pdf.cell(0, 10, self.normalize_text(f"Categoria: {category} - Total: {total_price:.2f} RON"), ln=True)
                pdf.ln(15)  # Add 15px spacing before the table

                # Calculate total table width and adjust column widths proportionally
                page_width = 210  # A4 page width in mm
                left_margin = 10  # Default left margin in mm
                right_margin = 10  # Default right margin in mm
                table_width = page_width - left_margin - right_margin  # Available width for the table

                # Adjusted column widths to ensure equal gaps on both sides
                column_widths = {
                    "Produs": 0.3 * table_width,  # 30% of table width
                    "Brand": 0.125 * table_width,  # 12.5% of table width
                    "Cant.": 0.075 * table_width,  # 7.5% of table width
                    "Pret Unit.": 0.125 * table_width,  # 12.5% of table width
                    "Total": 0.125 * table_width,  # 12.5% of table width
                    "Discount": 0.1 * table_width,  # 10% of table width
                    "Pret cu Disc.": 0.15 * table_width,  # 15% of table width
                }

                # Add table headers
                pdf.set_font('Helvetica', 'B', 12)
                pdf.set_fill_color(211, 211, 211)  # Light grey background for headers
                pdf.set_text_color(255, 255, 255)  # White text for headers
                pdf.cell(column_widths["Produs"], 10, self.normalize_text('Produs'), 1, 0, 'C', fill=True)
                pdf.cell(column_widths["Brand"], 10, self.normalize_text('Brand'), 1, 0, 'C', fill=True)
                pdf.cell(column_widths["Cant."], 10, self.normalize_text('Cant.'), 1, 0, 'C', fill=True)
                pdf.cell(column_widths["Pret Unit."], 10, self.normalize_text('Pret Unit.'), 1, 0, 'C', fill=True)
                pdf.cell(column_widths["Total"], 10, self.normalize_text('Total'), 1, 0, 'C', fill=True)
                pdf.cell(column_widths["Discount"], 10, self.normalize_text('Discount'), 1, 0, 'C', fill=True)
                pdf.cell(column_widths["Pret cu Disc."], 10, self.normalize_text('Pret cu Disc.'), 1, 1, 'C', fill=True)

                # Add products
                pdf.set_font('Helvetica', '', 10)
                pdf.set_text_color(0, 0, 0)  # Black text for rows
                fill = False  # Alternating row colors
                for product in data['products']:
                    pdf.set_fill_color(245, 245, 245) if fill else pdf.set_fill_color(255, 255, 255)
                    pdf.cell(column_widths["Produs"], 10, self.normalize_text(product[0]), 1, 0, 'L', fill=True)
                    pdf.cell(column_widths["Brand"], 10, self.normalize_text(product[1]), 1, 0, 'L', fill=True)
                    pdf.cell(column_widths["Cant."], 10, str(product[3]), 1, 0, 'C', fill=True)
                    pdf.cell(column_widths["Pret Unit."], 10, self.safe_format_float(product[4]), 1, 0, 'C', fill=True)
                    pdf.cell(column_widths["Total"], 10, self.safe_format_float(product[5]), 1, 0, 'C', fill=True)
                    pdf.cell(column_widths["Discount"], 10, f"{product[6]}%" if product[6] else "0%", 1, 0, 'C', fill=True)
                    pdf.set_text_color(0, 150, 0)  # Green text for Pret cu Disc.
                    pdf.cell(column_widths["Pret cu Disc."], 10, self.safe_format_float(product[7]), 1, 1, 'C', fill=True)
                    pdf.set_text_color(0, 0, 0)  # Reset text color to black
                    fill = not fill  # Toggle row color

                pdf.ln(10)  # Add space below the table

            # Add call-to-action
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 10, self.normalize_text('Suna-ne sau scrie-ne sa ne anunti legat de decizia ta!'), ln=True, align='C')
            pdf.set_text_color(0, 0, 255)
            pdf.set_font('Helvetica', 'U', 12)
            pdf.cell(0, 10, '+40 727 975 866', ln=True, align='C', link='tel:+40727975866')

            # Save the PDF in the specified folder
            pdf_folder = 'electron-app/flask-app/pdf'
            os.makedirs(pdf_folder, exist_ok=True)
            pdf_file = os.path.join(pdf_folder, f'Oferta_{self.offer_details["offer_number"]}.pdf')
            pdf.output(pdf_file)

            # Open the PDF in the default browser
            webbrowser.open_new(pdf_file)

            # Show success message
            return pdf_file
        except Exception as e:
            print(f"Error generating PDF: {e}")
            raise

class OrderPDFGenerator:
    def __init__(self, order_details):
        self.order_details = order_details

    def normalize_text(self, text):
        return PDFGenerator({}).normalize_text(text)

    def safe_format_float(self, value):
        return PDFGenerator({}).safe_format_float(value)

    def generate_pdf(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            branding_image_path = os.path.join(current_dir, 'resources', 'Branding.jpg')

            client_name = self.order_details.get("client_name", "Client Necunoscut")
            vehicle_details = self.order_details.get("vehicle_name", "-")
            order_number = self.order_details.get("order_number", "CMD-???")
            date = self.order_details.get("date", datetime.now().strftime("%Y-%m-%d"))
            status = self.order_details.get("status", "Comandată")
            amount_paid = self.order_details.get("amount_paid", 0.0)
            observations = self.order_details.get("observations", "")
            products = self.order_details.get("products", [])

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # Header
            pdf.image(branding_image_path, x=(210 - 50) / 2, y=10, h=25)
            pdf.ln(40)

            pdf.set_font('Helvetica', 'B', 18)
            pdf.cell(0, 10, self.normalize_text('AutoSavCar Company'), ln=True, align='C')
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, self.normalize_text(f'Comandă pentru {client_name}'), ln=True, align='C')
            pdf.ln(10)

            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(40, 10, self.normalize_text("Număr comandă:"), ln=0)
            pdf.cell(0, 10, self.normalize_text(order_number), ln=1)

            pdf.cell(40, 10, self.normalize_text("Data:"), ln=0)
            pdf.cell(0, 10, self.normalize_text(date), ln=1)

            pdf.cell(40, 10, self.normalize_text("Status:"), ln=0)
            pdf.cell(0, 10, self.normalize_text(status), ln=1)

            pdf.cell(40, 10, self.normalize_text("Suma plătită:"), ln=0)
            pdf.cell(0, 10, f"{self.safe_format_float(amount_paid)} RON", ln=1)

            pdf.cell(40, 10, self.normalize_text("Vehicul:"), ln=0)
            pdf.cell(0, 10, self.normalize_text(vehicle_details), ln=1)
            pdf.ln(10)

            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 10, self.normalize_text('Observații'), ln=True)
            pdf.set_font('Helvetica', '', 11)
            pdf.set_fill_color(245, 245, 245)
            pdf.multi_cell(0, 10, self.normalize_text(observations), fill=True)
            pdf.ln(10)

            # Table headers
            pdf.set_font('Helvetica', 'B', 11)
            headers = ["Produs", "Brand", "Cant.", "PU", "Total", "Disc.", "Final"]
            widths = [50, 35, 15, 20, 20, 15, 25]

            pdf.set_fill_color(211, 211, 211)
            pdf.set_text_color(255, 255, 255)
            for h, w in zip(headers, widths):
                pdf.cell(w, 10, self.normalize_text(h), 1, 0, 'C', fill=True)
            pdf.ln()

            # Table rows
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(0, 0, 0)
            fill = False
            total_sum = 0

            for row in products:
                product_name, brand, qty, pu, total, discount, final_price = row
                total_sum += float(final_price)
                fill_color = (245, 245, 245) if fill else (255, 255, 255)
                pdf.set_fill_color(*fill_color)
                cells = [
                    product_name, brand, str(qty),
                    self.safe_format_float(pu),
                    self.safe_format_float(total),
                    f"{discount}%",
                    self.safe_format_float(final_price)
                ]
                for val, w in zip(cells, widths):
                    pdf.cell(w, 10, self.normalize_text(val), 1, 0, 'C', fill=True)
                pdf.ln()
                fill = not fill

            # Total
            pdf.ln(5)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 10, self.normalize_text(f"Total Comandă: {total_sum:.2f} RON"), ln=True, align="R")

            # Contact
            pdf.ln(10)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 10, self.normalize_text('Pentru întrebări sau detalii, ne poți contacta:'), ln=True, align='C')
            pdf.set_text_color(0, 0, 255)
            pdf.set_font('Helvetica', 'U', 12)
            pdf.cell(0, 10, '+40 727 975 866', ln=True, align='C', link='tel:+40727975866')

            # Save and open
            pdf_folder = 'electron-app/flask-app/pdf'
            os.makedirs(pdf_folder, exist_ok=True)
            pdf_file = os.path.join(pdf_folder, f'Comanda_{order_number}.pdf')
            pdf.output(pdf_file)
            webbrowser.open_new(pdf_file)

            return pdf_file
        except Exception as e:
            print(f"Error generating Order PDF: {e}")
            raise
