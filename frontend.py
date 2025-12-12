#frontend  

import tkinter as tk #python's standard GUI library (importing it)
from tkinter import ttk, messagebox, simpledialog #import themed widgets and dialogs
import requests #for communicating with the backend server via http
from urllib.parse import quote_plus #for url-safe string encoding

backend = "http://127.0.0.1:5000"  # the base url for the backend api

categories = ["All", "Book", "Film", "Magazine"] #categories available for filtering

class LibraryClient(tk.Tk): #main application class that inherits from Tk window 
    def __init__(self):
        super().__init__() #initializing parent class
        self.title("Online Library") #setting the window title 
        self.geometry("800x500") #setting the default window size
        self.create_widgets() # builing the GUI components
        self.load_all_media() #loading the initial list of media items from the backend

    def create_widgets(self):
        #Top frame containing category selector, search, create button
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=8) #placing frame with padding

        # category selection
        ttk.Label(top, text="Category:").pack(side="left")
        self.category_var = tk.StringVar(value="All") #variable to hold selected category 
        #dropdown to select categories
        self.category_cb = ttk.Combobox(top, values=categories, textvariable=self.category_var, state="readonly", width=12) 
        self.category_cb.pack(side="left", padx=(4,10)) #packing combobox with spacing
        #button to load selected category
        ttk.Button(top, text="Load Category", command=self.load_by_category).pack(side="left") 

        #search by exact name
        ttk.Label(top, text="Name (exact):").pack(side="left", padx=(10,0))
        self.search_var = tk.StringVar() #variable storing search name 
        self.search_entry = ttk.Entry(top, textvariable=self.search_var, width=25) #entry for name input
        self.search_entry.pack(side="left", padx=(4,4))
        ttk.Button(top, text="Search", command=self.search_by_name).pack(side="left", padx=(0,6)) #search button

        # button to create new media 
        ttk.Button(top, text="Create New Media", command=self.open_create_dialog).pack(side="right")

        #middle frame containing the list and metadata display
        mid = ttk.Frame(self)
        mid.pack(fill="both", expand=True, padx=8, pady=8)

        #the left panel for listbox with scrollbar
        left = ttk.Frame(mid)
        left.pack(side="left", fill="both", expand=True)
        ttk.Label(left, text="Media List:").pack(anchor="w") #label above listbox
        self.listbox = tk.Listbox(left) #listbox to display media items
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self.on_list_select) #binding selection event
        scrollbar = ttk.Scrollbar(left, orient="vertical", command=self.listbox.yview) #scrollbar for listbox
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set) #connecting scrollbar to listbox

        # right panel for metadata display and buttons
        right = ttk.Frame(mid)
        right.pack(side="right", fill="both", expand=True)
        ttk.Label(right, text="Metadata:").pack(anchor="w") #metadata label
        self.meta_text = tk.Text(right, height=15, wrap="word") #text widget for metadata display
        self.meta_text.pack(fill="both", expand=True) 
        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill="x", pady=(6,0)) #button frame (under metadata display)
        ttk.Button(btn_frame, text="Refresh All", command=self.load_all_media).pack(side="left") #reload all media list 
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=6) #delete selected items
        ttk.Button(btn_frame, text="View Selected (fetch)", command=self.view_selected_fresh).pack(side="left", padx=6) #view selected item metadata from backend

    def set_list(self, items):
        self.listbox.delete(0, tk.END) #clearing existing listbox entries
        self.items_by_index = [] #reset local storage of metadata
        for m in items: #add each media item to listbox
            title = m.get("name", "(no name)") #get name or default
            display = f"{title} — {m.get('category','?')} — {m.get('author','?')}" #display string
            self.listbox.insert(tk.END, display) #inserting into listbox
            self.items_by_index.append(m) #storing metadata for retrieval later

    def load_all_media(self): 
        try:
            r = requests.get(backend + "/media", timeout=5) #get metadata from backend
            r.raise_for_status() #raise error for bad responses
            items = r.json() #parse json response
            self.set_list(items) #populate listbox with items 
            self.meta_text.delete("1.0", tk.END)
            self.meta_text.insert(tk.END, f"Loaded {len(items)} item(s).\nSelect an item to see metadata.") #show result message
        except Exception as e:
            messagebox.showerror("Error", f"Couldn't load media: {e}") #showing error popup

    def load_by_category(self):
        cat = self.category_var.get() #read selected category
        if cat == "All": #if all selected, load all media
            self.load_all_media()
            return
        try:
            url = f"{backend}/media/category/{quote_plus(cat)}" #encode category and build URL 
            r = requests.get(url, timeout=5) #GET request 
            r.raise_for_status()
            items = r.json() #parse result 
            self.set_list(items) #update listbox
            self.meta_text.delete("1.0", tk.END) #reset metadata 
            self.meta_text.insert(tk.END, f"Loaded {len(items)} item(s) in category '{cat}'.") #show result
        except Exception as e:
            messagebox.showerror("Error", f"Couldn't load category: {e}") #show error popup

    def search_by_name(self):
        name = self.search_var.get().strip() #get search term
        if not name: #ensure user entered something
            messagebox.showinfo("Input", "Enter a name to search (exact match).")
            return
        try:
            url = f"{backend}/media/search?name={quote_plus(name)}" #build url
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            results = r.json() #parse result list
            if not results: #in case of no results
                messagebox.showinfo("Search", "No media found with that exact name.")
                return
            self.set_list(results) #show results
            self.meta_text.delete("1.0", tk.END)
            self.meta_text.insert(tk.END, f"Search returned {len(results)} item(s). Select to view metadata.")
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {e}")

    def on_list_select(self, event):
        sel = self.listbox.curselection() #get selected index tuple 
        if not sel:  #if nothing is selected 
            return
        idx = sel[0] #first selected index
        metadata = self.items_by_index[idx] #retrieve corresponding metadata for that index
        self.display_metadata(metadata) #display metadata 

    def display_metadata(self, metadata):
        self.meta_text.delete("1.0", tk.END)  #clear metadata display
        lines = [
            f"Name: {metadata.get('name')}",  #preparing lines to display (metadata)
            f"Category: {metadata.get('category')}",
            f"Author: {metadata.get('author')}",
            f"Publication date: {metadata.get('publication_date')}",
        ]
        self.meta_text.insert(tk.END, "\n".join(lines)) #inserting formatted metadata

    def view_selected_fresh(self):
        sel = self.listbox.curselection() #check selection
        if not sel:
            messagebox.showinfo("Select", "Please select an item in the list.")
            return
        idx = sel[0]
        name = self.items_by_index[idx].get("name") #get selected item's name
        try:
            url = f"{backend}/media/{quote_plus(name)}" #build url to fetch fresh metadata
            r = requests.get(url, timeout=5)
            if r.status_code == 404: #item missing in backend 
                messagebox.showerror("Not found", "Item not found on server.")
                return
            r.raise_for_status()
            metadata = r.json() #parse fresh metadata
            self.display_metadata(metadata) #display it
        except Exception as e:
            messagebox.showerror("Error", f"Couldn't fetch metadata: {e}")

    def open_create_dialog(self):
        dlg = CreateDialog(self) #launch create dialog window
        self.wait_window(dlg) #pause until dialog is closed
        if dlg.created_metadata: #if creation data returned
            try:
                r = requests.post(backend + "/media", json=dlg.created_metadata, timeout=5) #post new media to backend
                if r.status_code == 201:  #successfully created 
                    messagebox.showinfo("Created", "Media successfully created.")
                    self.load_all_media() #refresh media list 
                else:
                    # show server error message if present
                    try:
                        err = r.json()
                    except:
                        err = r.text #fallback to raw text
                    messagebox.showerror("Server error", f"Could not create: {err}")
            except Exception as e:
                messagebox.showerror("Error", f"Create request failed: {e}")

    def delete_selected(self):
        sel = self.listbox.curselection() #need a selection to delete
        if not sel:
            messagebox.showinfo("Select", "Please select an item to delete.")
            return
        idx = sel[0]
        name = self.items_by_index[idx].get("name") #name of media to delete 
        if not messagebox.askyesno("Confirm", f"Delete '{name}'?"): #confirmation dialog
            return
        try:
            url = f"{backend}/media/{quote_plus(name)}" #build delete url
            r = requests.delete(url, timeout=5)
            if r.status_code == 200: #successfully deleted
                messagebox.showinfo("Deleted", "Item deleted.")
                self.load_all_media() #refresh list 
            elif r.status_code == 404: #item missing
                messagebox.showerror("Not found", "Item not found on server.")
            else:
                messagebox.showerror("Error", f"Server returned status {r.status_code}: {r.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Delete failed: {e}")


class CreateDialog(tk.Toplevel): #dialog window for creating new media items
    def __init__(self, parent):
        super().__init__(parent) #initializing parent Toplevel class
        self.title("Create new media") #window title
        self.resizable(False, False) #disable resizing
        self.created_metadata = None #to store created media metadata
        self.build() #build form widgets 
        self.grab_set() #make dialog modal (block main window)

    def build(self):
        from tkcalendar import DateEntry   # imported here so main program runs even if missing

        frm = ttk.Frame(self, padding=10)  #main fraim inside dialog
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Name:").grid(row=0, column=0, sticky="e") #label for name field
        self.name_var = tk.StringVar()         #variable to hold name input
        ttk.Entry(frm, textvariable=self.name_var, width=40).grid(row=0, column=1, pady=4)

        ttk.Label(frm, text="Publication date:").grid(row=1, column=0, sticky="e") #label for date field
        self.date_entry = DateEntry(frm, date_pattern="yyyy-mm-dd") #date entry widget 
        self.date_entry.grid(row=1, column=1, pady=4)

        ttk.Label(frm, text="Author:").grid(row=2, column=0, sticky="e") #label for author field
        self.author_var = tk.StringVar()   #author input
        ttk.Entry(frm, textvariable=self.author_var).grid(row=2, column=1, pady=4)

        ttk.Label(frm, text="Category:").grid(row=3, column=0, sticky="e") #label for category field
        self.cat_var = tk.StringVar(value="Book")  #default category
        ttk.Combobox(               
            frm,                                             #dropdown for category selection
            values=["Book", "Film", "Magazine"],
            textvariable=self.cat_var,
            state="readonly"
        ).grid(row=3, column=1, pady=4)

        btns = ttk.Frame(frm)          #button row
        btns.grid(row=4, column=0, columnspan=2, pady=(8,0))
        ttk.Button(btns, text="Create", command=self.on_create).pack(side="left", padx=6)   #create button
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side="left") #cancel button to close dialog

    def on_create(self):
        name = self.name_var.get().strip() #get name input
        pub = self.date_entry.get()         #date is always valid yyyy-mm-dd format
        author = self.author_var.get().strip() #getting author input
        cat = self.cat_var.get().strip()  #getting category input 

        if not (name and pub and author and cat):    #validate all fields filled (not empty)
            messagebox.showerror("Missing", "All fields are required.")
            return

        self.created_metadata = {         #constructing metadata dictionary
            "name": name,
            "publication_date": pub,
            "author": author,
            "category": cat
        }
        self.destroy()    #close dialog window

if __name__ == "__main__":        #run only when executed directly
    app = LibraryClient() #create main application instance
    app.mainloop() #start the Tkinter event loop
