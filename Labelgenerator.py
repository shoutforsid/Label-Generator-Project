import tkinter as tk
from tkinter import filedialog, messagebox
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
from PIL import Image, ImageTk
import os
import webbrowser

class LabelGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Label Generator (12 per A4)')

        # Data variables
        self.article_no = tk.StringVar()
        self.color = tk.StringVar()
        self.mrp = tk.StringVar()
        self.firm_name = tk.StringVar()
        self.address = tk.StringVar()
        self.market_by = tk.StringVar()
        self.contact = tk.StringVar()
        self.website = tk.StringVar()
        self.image_path = None

        self.setup_ui()

    def setup_ui(self):
        fields = [
            ('Article No', self.article_no),
            ('Color', self.color),
            ('MRP', self.mrp),
            ('Firm Name', self.firm_name),
            ('Address', self.address),
            ('Marketed By', self.market_by),
            ('Contact', self.contact),
            ('Website', self.website)
        ]
        for i, (label_text, var) in enumerate(fields):
            tk.Label(self.root, text=label_text+':').grid(row=i, column=0, sticky='e', padx=4, pady=2)
            tk.Entry(self.root, textvariable=var, width=40).grid(row=i, column=1, padx=4, pady=2)

        # Sizes area
        self.size_frame = tk.LabelFrame(self.root, text='Sizes and Quantities (enter integer qty)')
        self.size_frame.grid(row=len(fields), column=0, columnspan=2, pady=8, padx=4, sticky='we')

        self.sizes = ['6uk', '7uk', '8uk', '9uk', '10uk', '11uk']
        self.size_vars = {}
        for idx, s in enumerate(self.sizes):
            tk.Label(self.size_frame, text=s+':').grid(row=idx, column=0, sticky='e', padx=2, pady=2)
            v = tk.StringVar(value='0')
            tk.Entry(self.size_frame, textvariable=v, width=8).grid(row=idx, column=1, sticky='w')
            self.size_vars[s] = v

        # Image upload + preview
        tk.Button(self.root, text='Upload Image', command=self.upload_image).grid(row=100, column=0, pady=6)
        self.image_preview = tk.Label(self.root)
        self.image_preview.grid(row=100, column=1, sticky='w')

        # Actions
        tk.Button(self.root, text='Print Preview', command=self.print_preview).grid(row=200, column=0, pady=8)
        tk.Button(self.root, text='Generate PDF', command=self.generate_pdf).grid(row=200, column=1, pady=8, sticky='w')

    def upload_image(self):
        path = filedialog.askopenfilename(filetypes=[('Image files', '*.png;*.jpg;*.jpeg;*.bmp')])
        if not path:
            return
        self.image_path = path
        try:
            im = Image.open(path)
            im.thumbnail((120, 120))
            tkimg = ImageTk.PhotoImage(im)
            self.image_preview.config(image=tkimg)
            self.image_preview.image = tkimg
        except Exception as e:
            messagebox.showerror('Image error', f'Could not load image: {e}')
            self.image_path = None

    def print_preview(self):
        preview = tk.Toplevel(self.root)
        preview.title('Print Preview (approx)')
        canvas_w = tk.Canvas(preview, width=900, height=600, bg='white')
        vs = tk.Scrollbar(preview, orient='vertical', command=canvas_w.yview)
        frame = tk.Frame(canvas_w)
        frame.bind("<Configure>", lambda e: canvas_w.configure(scrollregion=canvas_w.bbox("all")))
        canvas_w.create_window((0,0), window=frame, anchor='nw')
        canvas_w.configure(yscrollcommand=vs.set)
        canvas_w.pack(side='left', fill='both', expand=True)
        vs.pack(side='right', fill='y')

        tk.Label(frame, text='--- Print Preview (visual, not exact print scale) ---', font=('Arial', 12, 'bold')).pack(pady=6)

        per_row = 3
        card_w, card_h = 260, 150
        row_frame = None
        idx = 0

        for size in self.sizes:
            qty = self.size_vars[size].get().strip()
            if not qty.isdigit() or int(qty) <= 0:
                continue
            for _ in range(int(qty)):
                if idx % per_row == 0:
                    row_frame = tk.Frame(frame)
                    row_frame.pack(fill='x', pady=6)
                card = tk.Frame(row_frame, width=card_w, height=card_h, relief='solid', borderwidth=1)
                card.pack(side='left', padx=6)
                card.pack_propagate(False)

                # left: image
                if self.image_path:
                    try:
                        im = Image.open(self.image_path)
                        im.thumbnail((80, 80))
                        tkimg = ImageTk.PhotoImage(im)
                        lbl = tk.Label(card, image=tkimg)
                        lbl.image = tkimg
                        lbl.pack(side='left', padx=6, pady=6)
                    except Exception:
                        pass

                # right: text
                txt = (f"Article: {self.article_no.get()}\nColor: {self.color.get()}\nSize: {size}\n"
                       f"MRP: ₹{self.mrp.get()}\nMarketed by: {self.market_by.get()}\nContact: {self.contact.get()}\n"
                       f"Web: {self.website.get()}\n{self.firm_name.get()} | {self.address.get()}")
                tk.Label(card, text=txt, justify='left', anchor='w', font=('Helvetica', 8)).pack(side='left', padx=6)
                idx += 1

    def generate_pdf(self):
        if not self.article_no.get().strip():
            messagebox.showerror('Missing', 'Article No is required.')
            return

        clean_name = "".join(c for c in self.article_no.get() if c.isalnum() or c in ('-', '_')).strip() or 'labels'
        pdf_file = f'labels_{clean_name}.pdf'
        c = canvas.Canvas(pdf_file, pagesize=A4)
        page_w, page_h = A4

        cols = 3
        rows = 4
        margin_x = 10 * mm
        margin_y = 12 * mm
        gap_x = 5 * mm
        gap_y = 6 * mm

        label_w = (page_w - 2*margin_x - (cols-1)*gap_x) / cols
        label_h = (page_h - 2*margin_y - (rows-1)*gap_y) / rows

        count = 0
        for size in self.sizes:
            qty = self.size_vars[size].get().strip()
            if not qty.isdigit() or int(qty) <= 0:
                continue
            for _ in range(int(qty)):
                if count > 0 and count % (cols*rows) == 0:
                    c.showPage()
                col = count % cols
                row = (count // cols) % rows

                x = margin_x + col * (label_w + gap_x)
                y_top = page_h - (margin_y + row * (label_h + gap_y))
                c.rect(x, y_top - label_h, label_w, label_h)

                pad = 4 * mm
                img_w = 18 * mm
                img_h = 18 * mm
                img_x = x + pad
                img_y = y_top - pad - img_h

                if self.image_path and os.path.isfile(self.image_path):
                    try:
                        c.drawImage(self.image_path, img_x, img_y, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
                    except Exception as e:
                        print("Image draw error:", e)

                text_x = img_x + img_w + (4 * mm)
                text_y_start = y_top - pad - 2

                lines = [
                    f"Article No: {self.article_no.get()}",
                    f"Color: {self.color.get()}",
                    f"Size: {size}",
                    f"MRP: ₹{self.mrp.get()}",
                    f"Marketed by: {self.market_by.get()}",
                    f"Contact: {self.contact.get()} | {self.website.get()}",
                ]

                c.setFont("Helvetica-Bold", 8)
                c.drawString(text_x, text_y_start, lines[0])
                c.setFont("Helvetica", 8)
                line_gap = 10
                for i, ln in enumerate(lines[1:], start=1):
                    c.drawString(text_x, text_y_start - i*line_gap, ln)

                firm_txt = f"{self.firm_name.get()} | {self.address.get()}"
                c.setFont("Helvetica-Oblique", 7)
                firm_y = y_top - label_h + pad + 4
                c.drawString(text_x, firm_y, firm_txt)

                try:
                    barcode_value = f"{self.article_no.get()}-{size}"
                    barcode = code128.Code128(barcode_value, barHeight=9*mm, humanReadable=False)
                    barcode_width = barcode.width
                    barcode_x = x + (label_w - barcode_width) / 2
                    barcode_y = firm_y + 8
                    if barcode_x < x + pad:
                        barcode_x = x + pad
                    barcode.drawOn(c, barcode_x, barcode_y)
                except Exception as e:
                    print("Barcode error:", e)

                count += 1

        c.save()
        messagebox.showinfo('Done', f'PDF saved: {pdf_file}')
        try:
            webbrowser.open_new(os.path.abspath(pdf_file))
        except Exception:
            pass

if __name__ == '__main__':
    root = tk.Tk()
    app = LabelGeneratorApp(root)
    root.mainloop()
