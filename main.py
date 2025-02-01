import tkinter as tk
from tkinter import filedialog, colorchooser, simpledialog, messagebox, font
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
import time
import threading
from PIL import Image, ImageTk
from spellchecker import SpellChecker
import reportlab.lib.pagesizes as ps
from reportlab.pdfgen import canvas

class TextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Text Editor")
        self.root.geometry("800x600")

        self.file_path = None
        self.file_history = []
        self.auto_save_interval = 300  # Auto-save every 5 minutes (300 seconds)
        self.unsaved_changes = False

        self.text_area = tk.Text(self.root, wrap='word', font=("Arial", 12), undo=True)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        self.text_color = "black"
        self.bg_color = "white"
        
        # Set up the menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File Menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open", command=self.open_file)
        self.file_menu.add_command(label="Save", command=self.save_file)
        self.file_menu.add_command(label="Save As", command=self.save_as)
        self.file_menu.add_command(label="Export as PDF", command=self.export_pdf)
        self.file_menu.add_command(label="Recent Files", command=self.show_recent_files)
        self.file_menu.add_command(label="Exit", command=self.quit)

        # Edit Menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Align Left", command=self.align_left)
        self.edit_menu.add_command(label="Align Center", command=self.align_center)
        self.edit_menu.add_command(label="Align Right", command=self.align_right)
        self.edit_menu.add_command(label="Justify", command=self.justify_text)
        self.edit_menu.add_command(label="Highlight Text", command=self.highlight_text)
        self.edit_menu.add_command(label="Undo", command=self.undo_action)
        self.edit_menu.add_command(label="Redo", command=self.redo_action)

        # Search Menu
        self.search_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Search", menu=self.search_menu)
        self.search_menu.add_command(label="Find", command=self.find_text)
        self.search_menu.add_command(label="Replace", command=self.replace_text)

        # View Menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_command(label="Light Theme", command=self.set_light_theme)
        self.view_menu.add_command(label="Dark Theme", command=self.set_dark_theme)

        # Font customization
        self.view_menu.add_command(label="Change Font", command=self.change_font)
        self.view_menu.add_command(label="Change Font Size", command=self.change_font_size)
        self.view_menu.add_command(label="Change Text Color", command=self.change_text_color)
        self.view_menu.add_command(label="Change Background Color", command=self.change_bg_color)

        # Setup the status bar
        self.status_bar = tk.Label(self.root, text="Line: 1 | Column: 1 | Word Count: 0", anchor="w")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Start auto-save in a separate thread
        self.auto_save_thread = threading.Thread(target=self.auto_save, daemon=True)
        self.auto_save_thread.start()

        # Track changes
        self.text_area.bind("<KeyPress>", self.mark_unsaved)

        # SpellChecker initialization
        self.spell_checker = SpellChecker()

        # Multi-Document Interface using ttk.Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Drag-and-Drop Support
        self.root = TkinterDnD.Tk()
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        file_path = event.data
        if file_path.lower().endswith('.txt'):
            self.open_file(file_path)

    def open_file(self):
        if self.unsaved_changes:
            response = messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to save them?")
            if response:
                self.save_file()

        file_path = filedialog.askopenfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            self.file_path = file_path
            self.add_to_recent_files(file_path)
            try:
                with open(file_path, 'r', encoding="utf-8") as file:
                    content = file.read()
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(tk.END, content)
                    self.unsaved_changes = False
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")

    def save_file(self):
        if self.file_path:
            try:
                with open(self.file_path, 'w', encoding="utf-8") as file:
                    content = self.text_area.get(1.0, tk.END)
                    file.write(content)
                    self.unsaved_changes = False
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {e}")
        else:
            self.save_as()

    def save_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            self.file_path = file_path
            self.add_to_recent_files(file_path)
            try:
                with open(file_path, 'w', encoding="utf-8") as file:
                    content = self.text_area.get(1.0, tk.END)
                    file.write(content)
                    self.unsaved_changes = False
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {e}")

    def add_to_recent_files(self, file_path):
        if file_path not in self.file_history:
            self.file_history.insert(0, file_path)
            if len(self.file_history) > 5:
                self.file_history.pop()

    def show_recent_files(self):
        recent_files_menu = tk.Menu(self.root, tearoff=0)
        for file in self.file_history:
            recent_files_menu.add_command(label=file, command=lambda f=file: self.open_recent_file(f))
        recent_files_menu.post(self.root.winfo_rootx(), self.root.winfo_rooty() + 50)

    def open_recent_file(self, file_path):
        self.file_path = file_path
        try:
            with open(file_path, 'r', encoding="utf-8") as file:
                content = file.read()
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, content)
                self.unsaved_changes = False
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

    def auto_save(self):
        while True:
            if self.file_path and self.unsaved_changes:
                self.save_file()
            time.sleep(self.auto_save_interval)

    def mark_unsaved(self, event=None):
        self.unsaved_changes = True

    def highlight_text(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.text_area.tag_add("highlight", "sel.first", "sel.last")
            self.text_area.tag_config("highlight", background=color)

    def align_left(self):
        self.text_area.tag_configure("left", justify='left')
        self.text_area.tag_add("left", "1.0", "end")

    def align_center(self):
        self.text_area.tag_configure("center", justify='center')
        self.text_area.tag_add("center", "1.0", "end")

    def align_right(self):
        self.text_area.tag_configure("right", justify='right')
        self.text_area.tag_add("right", "1.0", "end")

    def justify_text(self):
        self.text_area.tag_configure("justify", justify='justify')
        self.text_area.tag_add("justify", "1.0", "end")

    def find_text(self):
        query = simpledialog.askstring("Find", "Enter text to find:")
        if query:
            start = 1.0
            while True:
                pos = self.text_area.search(query, start, stopindex=tk.END)
                if not pos:
                    break
                self.text_area.tag_add("highlight", pos, f"{pos}+{len(query)}c")
                start = f"{pos}+{len(query)}c"
            self.text_area.tag_config("highlight", background="yellow")

    def redo_action(self):
        """Redo the last undone action in the text area."""
        try:
            self.text_area.edit_redo()
        except Exception as e:
            messagebox.showerror("Redo Error", "No action to redo.")
            
    def undo_action(self):
        """Undo the last action in the text area."""
        try:
            self.text_area.edit_undo()
        except Exception as e:
            messagebox.showerror("Undo Error", "No action to undo.")

    def replace_text(self):
        query = simpledialog.askstring("Find", "Enter text to find:")
        if query:
            replace = simpledialog.askstring("Replace", "Enter replacement text:")
            content = self.text_area.get(1.0, tk.END)
            content = content.replace(query, replace)
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, content)

    def set_light_theme(self):
        self.text_area.config(bg="white", fg="black")
        self.text_color = "black"
        self.bg_color = "white"

    def set_dark_theme(self):
        self.text_area.config(bg="black", fg="white")
        self.text_color = "white"
        self.bg_color = "black"

    def change_font(self):
        font_name = simpledialog.askstring("Font", "Enter font name (e.g., Arial, Times New Roman):")
        if font_name:
            self.text_area.config(font=(font_name, 12))

    def change_font_size(self):
        size = simpledialog.askinteger("Font Size", "Enter font size:")
        if size:
            self.text_area.config(font=("Arial", size))

    def change_text_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.text_area.config(fg=color)

    def change_bg_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.text_area.config(bg=color)

    def export_pdf(self):
        if self.file_path:
            content = self.text_area.get(1.0, tk.END)
            pdf_file = self.file_path.replace(".txt", ".pdf")
            c = canvas.Canvas(pdf_file, pagesize=ps.letter)
            c.drawString(50, 750, content)
            c.save()
            messagebox.showinfo("Export", f"File saved as {pdf_file}")
        else:
            messagebox.showwarning("Warning", "Save the file first before exporting to PDF.")

    def quit(self):
        if self.unsaved_changes:
            response = messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to save them?")
            if response:
                self.save_file()
        self.root.quit()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    editor = TextEditor(root)
    root.mainloop()