# utils/pdf_generator.py

from fpdf import FPDF
import os

class VoyagePDF(FPDF):
    def header(self):
        # Top branding ribbon header bar
        self.set_fill_color(15, 23, 42)  # Dark slate blue
        self.rect(0, 0, 210, 15, 'F')
        
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_y(5)
        self.cell(0, 5, "VoyageOS -- Intelligent Multi-Agent Itinerary Archive", align="L")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="R")


class PDFGenerator:
    @staticmethod
    def sanitize_for_pdf(text: str) -> str:
        """
        Strips markdown notation, normalizes currency indicators, and flushes out 
        unmappable Unicode symbols/emojis to avoid FPDF character rendering exceptions.
        """
        if not text:
            return ""
            
        # 1. Clean standard structure elements
        text = text.replace("## ", "\n").replace("### ", "\n").replace("**", "")
        text = text.replace("₹", "INR ").replace("Rs.", "INR ")
        
        # 2. Encode to latin-1 while discarding emojis or unrecognized characters safely
        encoded_text = text.encode('latin-1', errors='ignore')
        return encoded_text.decode('latin-1')

    @staticmethod
    def create_itinerary_pdf(state_data: dict, file_path: str = "downloads/itinerary.pdf") -> str:
        """
        Takes raw dictionaries structured from VoyageOS state mapping 
        and renders them cleanly into printable PDF files.
        """
        # Ensure target file generation folder exists on local disk storage
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        trip = state_data.get("trip_details", {})
        budget = state_data.get("tool_results", {}).get("budget", {})
        itinerary_text = state_data.get("message", "")

        pdf = VoyagePDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # --- TITLE ---
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(15, 23, 42)
        dest_name = PDFGenerator.sanitize_for_pdf(trip.get('destination', 'Your Destination'))
        pdf.cell(0, 12, f"Travel Plan: {dest_name}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, "Synthesized dynamically via VoyageOS Multi-Agent Framework", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)

        # --- PROFILE SPECIFICATION DETAILS ---
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(3, 105, 161) # Slate Blue Highlight Hex
        pdf.cell(0, 8, "1. Executive Trip Profile", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(51, 65, 85)
        
        params = [
            ("Origin / Departure Point", PDFGenerator.sanitize_for_pdf(str(trip.get("origin", "N/A")))),
            ("Travelers / Party Count", f"{trip.get('travelers', 1)} Person(s)"),
            ("Trip Profile & Intent", PDFGenerator.sanitize_for_pdf(str(trip.get("trip_type", "Standard"))).title()),
            ("Duration Timeline", f"{trip.get('duration', 0)} Days"),
            ("Configured Budget Limit", f"INR {trip.get('budget', 0):,}")
        ]
        
        for label, val in params:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(55, 7, label, border=1)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 7, val, border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)

        # --- FINANCIAL ALLOCATION MATRIX ---
        if budget and "allocation" in budget:
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(3, 105, 161)
            pdf.cell(0, 8, "2. Algorithmic Budget Allocation", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            
            # Draw Table Header Layout
            pdf.set_fill_color(30, 41, 59)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(60, 8, "Expense Category", border=1, fill=True)
            pdf.cell(40, 8, "Percentage Split", border=1, fill=True)
            pdf.cell(0, 8, "Allocated Amount", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
            
            pdf.set_text_color(51, 65, 85)
            pdf.set_font("Helvetica", "", 10)
            for cat, details in budget["allocation"].items():
                pdf.cell(60, 7, PDFGenerator.sanitize_for_pdf(cat).title(), border=1)
                pdf.cell(40, 7, f"{details.get('percentage')}%", border=1)
                pdf.cell(0, 7, f"INR {details.get('amount'):,}", border=1, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)

        # --- CORE PLAN RENDER BLOCK ---
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(3, 105, 161)
        pdf.cell(0, 8, "3. Fully Verified Core Itinerary", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(15, 23, 42)
        
        # Apply character-purging sanitizer to the entire long-form text block
        clean_text = PDFGenerator.sanitize_for_pdf(itinerary_text)
        pdf.multi_cell(0, 6, clean_text)
        
        pdf.output(file_path)
        return file_path