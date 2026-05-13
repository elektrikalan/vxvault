import sys
import os
import threading
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from PIL import Image

# Projenin kök dizinini sys.path'e ekleyelim
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.http_client import HTTPClient
from collectors.vxvault import VXVaultCollector
from parsers.vxvault_parser import parse, parse_details
from storage.sqlite import SQLiteStore
from storage.csv_export import export_to_csv
from config import BASE_URL

# İkon yolları
ICON_ICO = r"C:\Users\ahmtg\Desktop\Denemeler-scriptler\Python\Düzenlenenler\mail-analyzer\assets\icon.ico"
ICON_PNG = r"C:\Users\ahmtg\Desktop\Denemeler-scriptler\Python\Düzenlenenler\mail-analyzer\assets\icon.png"

class LoggerRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, str):
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", str)
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass

class VXVaultGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("VXVault Collector - Professional Edition")
        self.geometry("1200x800")
        
        # İkon Ayarla
        if os.path.exists(ICON_ICO):
            self.after(200, lambda: self.iconbitmap(ICON_ICO))

        # Tema Ayarları
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Grid Yapısı
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Yan Menü (Sidebar)
        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(8, weight=1) # Esneklik için alt satır

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="VX VAULT\nCOLLECTOR", font=ctk.CTkFont(size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.fetch_all_button = ctk.CTkButton(self.sidebar_frame, text="Tüm Verileri Çek", command=self.start_fetch_all)
        self.fetch_all_button.grid(row=1, column=0, padx=10, pady=10)

        self.fetch_recent_button = ctk.CTkButton(self.sidebar_frame, text="Son Kayıtları Çek", command=self.start_fetch_recent)
        self.fetch_recent_button.grid(row=2, column=0, padx=10, pady=10)

        self.deep_scrape_var = ctk.BooleanVar(value=False)
        self.deep_scrape_checkbox = ctk.CTkCheckBox(self.sidebar_frame, text="Derin Tarama", variable=self.deep_scrape_var, font=ctk.CTkFont(size=11))
        self.deep_scrape_checkbox.grid(row=3, column=0, padx=10, pady=10)

        self.auto_download_var = ctk.BooleanVar(value=False)
        self.auto_download_checkbox = ctk.CTkCheckBox(self.sidebar_frame, text="Otomatik İndir", variable=self.auto_download_var, font=ctk.CTkFont(size=11))
        self.auto_download_checkbox.grid(row=4, column=0, padx=10, pady=10)

        # Progress Bar - Sidebar'ın en altına yakın
        self.progress_bar = ctk.CTkProgressBar(self.sidebar_frame)
        self.progress_bar.grid(row=9, column=0, padx=20, pady=(10, 5), sticky="ew")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Hazır", text_color="gray", font=ctk.CTkFont(size=11))
        self.status_label.grid(row=10, column=0, padx=20, pady=(0, 20))

        # Ana Panel - Tabview yapısı
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        self.tab_logs = self.tabview.add("İşlem Kayıtları")
        self.tab_explorer = self.tabview.add("Veri Gezgini")
        self.tab_batch = self.tabview.add("Toplu İşlemler")

        # --- LOG TAB ---
        self.tab_logs.grid_columnconfigure(0, weight=1)
        self.tab_logs.grid_rowconfigure(0, weight=1)

        self.log_textbox = ctk.CTkTextbox(self.tab_logs, state="disabled", font=("Consolas", 12))
        self.log_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # --- EXPLORER TAB ---
        self.tab_explorer.grid_columnconfigure(0, weight=1)
        self.tab_explorer.grid_rowconfigure(1, weight=1)

        # Search Frame
        self.search_frame = ctk.CTkFrame(self.tab_explorer, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.search_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Hash veya IP adresi girin...")
        self.search_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.search_button = ctk.CTkButton(self.search_frame, text="Sorgula", width=80, command=self.search_data)
        self.search_button.grid(row=0, column=1, padx=2)

        self.refresh_button = ctk.CTkButton(self.search_frame, text="Yenile", width=80, command=self.load_all_data)
        self.refresh_button.grid(row=0, column=2, padx=2)

        self.export_button = ctk.CTkButton(self.search_frame, text="Excel", width=80, fg_color="#27ae60", hover_color="#1e8449", command=self.export_current_view)
        self.export_button.grid(row=0, column=3, padx=2)

        self.download_listed_button = ctk.CTkButton(self.search_frame, text="İndir", width=80, fg_color="#e67e22", hover_color="#d35400", command=self.download_listed_records)
        self.download_listed_button.grid(row=0, column=4, padx=2)

        # Treeview için Stil Güncelleme
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", 
                             background="#1d1d1d", 
                             foreground="#dcdcdc", 
                             fieldbackground="#1d1d1d", 
                             rowheight=45,
                             borderwidth=0,
                             font=("Segoe UI", 10))
        self.style.map("Treeview", background=[('selected', '#3498db')])
        self.style.configure("Treeview.Heading", 
                             background="#333333", 
                             foreground="white", 
                             relief="flat",
                             padding=5,
                             font=("Segoe UI", 10, "bold"))

        # Treeview (Table)
        columns = ("date", "filename", "md5", "sha256", "ip", "size", "url", "tools")
        self.tree = ttk.Treeview(self.tab_explorer, columns=columns, show="headings", selectmode="browse")
        
        # Column Headings
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
        
        self.tree.heading("date", text="Tarih")
        self.tree.heading("filename", text="Dosya Adı")
        self.tree.heading("md5", text="MD5 Hash")
        self.tree.heading("sha256", text="SHA256 Hash")
        self.tree.heading("ip", text="IP Adresi")
        self.tree.heading("size", text="Boyut")
        self.tree.heading("url", text="Kaynak URL")
        self.tree.heading("tools", text="Araçlar")

        # Column Widths & Alignment
        self.tree.column("date", width=80, anchor="center")
        self.tree.column("filename", width=150, anchor="w")
        self.tree.column("md5", width=250, anchor="center")
        self.tree.column("sha256", width=250, anchor="center")
        self.tree.column("ip", width=120, anchor="center")
        self.tree.column("size", width=80, anchor="center")
        self.tree.column("url", width=260, anchor="w")
        self.tree.column("tools", width=220, anchor="w")

        self.tree.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # Scrollbar for Treeview
        self.tree_scroll = ctk.CTkScrollbar(self.tab_explorer, orientation="vertical", command=self.tree.yview)
        self.tree_scroll.grid(row=1, column=1, sticky="ns", pady=(0, 10))
        self.tree.configure(yscrollcommand=self.tree_scroll.set)

        # Event Bindings
        self.tree.bind("<Button-3>", self.show_context_menu)

        # Context Menu
        self.context_menu = tk.Menu(self, tearoff=0, bg="#333333", fg="white", activebackground="#3498db")
        self.context_menu.add_command(label="Kaynağı Aç (URL)", command=self.open_selected_url)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="VirusTotal'de Ara", command=self.open_vt)
        self.context_menu.add_command(label="Triage'da Ara", command=self.open_triage)

        # --- BATCH TAB ---
        self.tab_batch.grid_columnconfigure(0, weight=1)
        self.tab_batch.grid_rowconfigure(1, weight=1)

        self.batch_label = ctk.CTkLabel(self.tab_batch, text="Hash Listesini Yapıştırın (Her satıra bir tane):")
        self.batch_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")

        self.batch_textbox = ctk.CTkTextbox(self.tab_batch, font=("Consolas", 12))
        self.batch_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.batch_button_frame = ctk.CTkFrame(self.tab_batch, fg_color="transparent")
        self.batch_button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.batch_search_button = ctk.CTkButton(self.batch_button_frame, text="Toplu Sorgula ve Kaydet", command=self.start_batch_search)
        self.batch_search_button.grid(row=0, column=0, padx=5)

        self.batch_download_button = ctk.CTkButton(self.batch_button_frame, text="Listedekileri İndir", fg_color="#e67e22", command=self.start_batch_download)
        self.batch_download_button.grid(row=0, column=1, padx=5)

        # Konsol çıktısını GUI'ye yönlendir
        sys.stdout = LoggerRedirector(self.log_textbox)

        self.is_running = False

    def start_fetch_all(self):
        if self.is_running: return
        self.status_label.configure(text="Durum: Tüm Veriler Çekiliyor...", text_color="#3498db")
        threading.Thread(target=self.run_collector, args=(None,), daemon=True).start()

    def start_fetch_recent(self):
        if self.is_running: return
        self.status_label.configure(text="Durum: Son Veriler Çekiliyor...", text_color="#3498db")
        threading.Thread(target=self.run_collector, args=(3,), daemon=True).start()

    def run_collector(self, max_pages=None):
        self.is_running = True
        self.progress_bar.set(0)
        
        try:
            client = HTTPClient()
            if not client.login():
                print("[-] Giriş başarısız, işlem durduruldu.")
                self.status_label.configure(text="Durum: Giriş Hatası", text_color="red")
                self.is_running = False
                return

            collector = VXVaultCollector(client)
            storage = SQLiteStore()

            page = 0
            total_items = 0
            
            while True:
                if max_pages and page >= max_pages:
                    break

                print(f"[*] Sayfa {page + 1} çekiliyor...")
                html = collector.fetch(page * 40)
                
                if not html:
                    print(f"[-] Sayfa {page + 1} veri çekilemedi.")
                    break

                items = parse(html)
                if not items:
                    print("[+] Daha fazla kayıt bulunamadı.")
                    break

                for item in items:
                    if self.deep_scrape_var.get() and item.details_id:
                        print(f"[*] Detaylar aliniyor: {item.md5}")
                        detail_html = collector.fetch_details(item.details_id)
                        if detail_html:
                            item = parse_details(detail_html, item)

                    if item.md5:
                        if self.auto_download_var.get():
                            download_url = f"{BASE_URL}/files/{item.md5}.zip"
                            client.download_file(download_url, f"{item.md5}.zip")
                        else:
                            print(f"[*] Otomatik indirme kapalı, atlanıyor: {item.md5}")

                storage.insert_many(items)
                total_items += len(items)

                print(f"[✓] Sayfa {page + 1} tamamlandı. ({len(items)} kayıt)")
                
                if max_pages:
                    self.progress_bar.set((page + 1) / max_pages)
                else:
                    self.progress_bar.set(((page + 1) % 100) / 100)

                page += 1

            print(f"\n[DONE] İşlem tamamlandı. Toplam çekilen kayıt: {total_items}")
            self.status_label.configure(text="Durum: Tamamlandı", text_color="green")
            
        except Exception as e:
            print(f"[-] Kritik Hata: {e}")
            self.status_label.configure(text="Durum: Hata Oluştu", text_color="red")
        
        self.is_running = False
        self.progress_bar.set(1)

    def search_data(self):
        query = self.search_entry.get().strip()
        if not query: return
        
        self.status_label.configure(text="Durum: Sorgulanıyor...", text_color="#3498db")
        
        storage = SQLiteStore()
        results = storage.search(query)
        
        if not results and (len(query) == 32 or len(query) == 64):
            print(f"[*] DB'de bulunamadı, online sorgulanıyor: {query}")
            threading.Thread(target=self.online_search, args=(query,), daemon=True).start()
        else:
            self.display_records(results)
            self.status_label.configure(text="Durum: Hazır", text_color="gray")

    def online_search(self, query):
        try:
            client = HTTPClient()
            client.login()
            collector = VXVaultCollector(client)
            storage = SQLiteStore()
            
            print(f"[*] Hash/IP aratılıyor: {query}")
            
            # 1. Aşama: Doğrudan MD5 veya genel arama (Sitenin kendi motoru)
            search_html = collector.search_hash(query)
            items = parse(search_html)
            
            if items:
                record = items[0]
                print(f"[+] Kayıt listede bulundu, detaylar çekiliyor: {record.md5}")
                if record.details_id:
                    detail_html = collector.fetch_details(record.details_id)
                    if detail_html:
                        record = parse_details(detail_html, record)
                storage.insert_many([record])
                self.display_records([record])
                return

            # 2. Aşama: Eğer SHA256 ise ve motor bulamadıysa, son sayfalarda brute-force ara
            # VXVault'un arama motoru SHA256'yı her zaman doğru indexlemiyor olabilir.
            if len(query) == 64:
                print(f"[*] SHA256 motor araması sonuç vermedi, son 5 sayfada derin tarama yapılıyor...")
                for p in range(5):
                    print(f"[*] Sayfa {p+1} kontrol ediliyor...")
                    html = collector.fetch(p * 40)
                    page_items = parse(html)
                    for item in page_items:
                        # Her kaydın içine girip SHA256 kontrol et
                            if not item.details_id:
                                continue
                            detail_html = collector.fetch_details(item.details_id)
                            record = parse_details(detail_html, item)
                            storage.insert_many([record])
                            self.display_records([record])
                            return
            
            print(f"[-] Online sonuç bulunamadı: {query}")
            self.display_records([])
            
        except Exception as e:
            print(f"[-] Online sorgu hatası: {e}")
        
        self.status_label.configure(text="Durum: Hazır", text_color="gray")

    def load_all_data(self):
        storage = SQLiteStore()
        results = storage.get_all(limit=500)
        self.display_records(results)

    def display_records(self, records):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if records:
            for r in records:
                if hasattr(r, 'date'):
                    d, u, m, i, t, s1, s2, sz, fn, tl = r.date, r.url, r.md5, r.ip, r.tools, r.sha1, r.sha256, r.size, r.filename, r.tools_links
                else:
                    d = r[0]
                    u = r[1]
                    m = r[2]
                    i = r[3]
                    t = r[4]
                    s1 = r[6] if len(r) > 6 else ""
                    s2 = r[7] if len(r) > 7 else ""
                    sz = r[8] if len(r) > 8 else ""
                    fn = r[9] if len(r) > 9 else ""
                    tl = r[10] if len(r) > 10 else ""
                # Araçlar sütununu çok satırlı göster
                tools_multiline = (tl or t or "").replace("\\n", "\n") if tl else (t or "")
                self.tree.insert("", "end", values=(d, fn, m, s2, i, sz, u, tools_multiline))
                
        self.tabview.set("Veri Gezgini")
        self.last_results = records

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.delete(0, 'end')
            self.context_menu.add_command(label="Kaynağı Aç (URL)", command=self.open_selected_url)
            self.context_menu.add_separator()

            links = self.get_selected_tools_links()
            if links:
                for idx, (label, url) in enumerate(links, start=1):
                    self.context_menu.add_command(
                        label=f"Link {idx}: {label}",
                        command=lambda url=url: self.open_link(url)
                    )
                self.context_menu.add_separator()

            self.context_menu.add_command(label="VirusTotal'de Ara", command=self.open_vt)
            self.context_menu.add_command(label="Triage'da Ara", command=self.open_triage)
            self.context_menu.post(event.x_root, event.y_root)

    def open_selected_url(self):
        selected = self.tree.selection()
        if not selected: return
        url = self.tree.item(selected[0], "values")[6]
        if url and url != "Unknown":
            import webbrowser
            webbrowser.open(url.replace("hxxp", "http"))

    def open_vt(self):
        selected = self.tree.selection()
        if not selected: return
        md5 = self.tree.item(selected[0], "values")[2]
        import webbrowser
        webbrowser.open(f"https://www.virustotal.com/gui/file/{md5}")

    def open_triage(self):
        selected = self.tree.selection()
        if not selected: return
        md5 = self.tree.item(selected[0], "values")[2]
        import webbrowser
        webbrowser.open(f"https://tria.ge/s?q={md5}")

    def get_selected_tools_links(self):
        selected = self.tree.selection()
        if not selected or not hasattr(self, 'last_results'):
            return []
        idx = self.tree.index(selected[0])
        if idx >= len(self.last_results):
            return []
        record = self.last_results[idx]
        tools_links = ""
        if hasattr(record, 'tools_links'):
            tools_links = record.tools_links or ""
        else:
            if len(record) > 10:
                tools_links = record[10] or ""
        links = []
        for line in tools_links.splitlines():
            if not line.strip():
                continue
            if ':' in line:
                label, url = line.split(':', 1)
                links.append((label.strip(), url.strip()))
            else:
                links.append((line.strip(), line.strip()))
        return links

    def open_link(self, url):
        import webbrowser
        if url and not url.startswith('http'):
            if url.startswith('/'):
                url = BASE_URL + url
        webbrowser.open(url)

    def download_listed_records(self):
        if hasattr(self, 'last_results') and self.last_results:
            threading.Thread(target=self.run_selective_download, args=(self.last_results,), daemon=True).start()
        else:
            print("[-] Indirilecek kayit bulunamadi.")

    def run_selective_download(self, records):
        self.status_label.configure(text="Durum: Seçilenler İndiriliyor...", text_color="#e67e22")
        client = HTTPClient()
        client.login()
        
        for r in records:
            md5 = r.md5 if hasattr(r, 'md5') else r[2]
            if md5:
                download_url = f"{BASE_URL}/files/{md5}.zip"
                client.download_file(download_url, f"{md5}.zip")
        
        self.status_label.configure(text="Durum: İndirme Tamamlandı", text_color="green")

    def start_batch_search(self):
        if self.is_running: return
        hashes = self.batch_textbox.get("1.0", "end-1c").splitlines()
        hashes = [h.strip() for h in hashes if h.strip()]
        if not hashes: return
        
        self.status_label.configure(text=f"Durum: {len(hashes)} Hash Sorgulanıyor...", text_color="#3498db")
        threading.Thread(target=self.run_batch_search, args=(hashes,), daemon=True).start()

    def run_batch_search(self, hashes):
        self.is_running = True
        client = HTTPClient()
        client.login()
        collector = VXVaultCollector(client)
        storage = SQLiteStore()
        
        from models.ioc import IOCRecord
        count = 0
        found_records = []
        
        for h in hashes:
            # Önce DB kontrol
            db_res = storage.search(h)
            if db_res:
                print(f"[*] DB'de mevcut: {h}")
                found_records.append(db_res[0])
                continue
            
            # Online sorgu
            search_html = collector.search_hash(h)
            items = parse(search_html) if search_html else []
            if items:
                record = items[0]
                if record.details_id:
                    detail_html = collector.fetch_details(record.details_id)
                    if detail_html:
                        record = parse_details(detail_html, record)
            
        print(f"\n[DONE] Toplu sorgu bitti. {count} yeni kayit eklendi.")
        self.status_label.configure(text="Durum: Toplu Sorgu Tamam", text_color="green")
        
        # Sonuçları tabloda göster
        if found_records:
            self.display_records(found_records)
            
        self.is_running = False

    def start_batch_download(self):
        if self.is_running: return
        hashes = self.batch_textbox.get("1.0", "end-1c").splitlines()
        hashes = [h.strip() for h in hashes if h.strip()]
        if not hashes: return
        
        self.status_label.configure(text=f"Durum: {len(hashes)} Dosya İndiriliyor...", text_color="#e67e22")
        threading.Thread(target=self.run_batch_download, args=(hashes,), daemon=True).start()

    def run_batch_download(self, hashes):
        self.is_running = True
        client = HTTPClient()
        client.login()
        
        for h in hashes:
            if h:
                download_url = f"{BASE_URL}/files/{h}.zip"
                client.download_file(download_url, f"{h}.zip")
            self.progress_bar.set((hashes.index(h) + 1) / len(hashes))
            
        self.status_label.configure(text="Durum: Toplu İndirme Tamam", text_color="green")
        self.is_running = False

    def export_current_view(self):
        if hasattr(self, 'last_results') and self.last_results:
            path = export_to_csv(self.last_results)
            print(f"[+] Veriler disara aktarildi: {path}")
            self.status_label.configure(text=f"Durum: Aktarıldı ({os.path.basename(path)})", text_color="green")
        else:
            print("[-] Aktarilacak veri bulunamadi.")

if __name__ == "__main__":
    app = VXVaultGUI()
    app.mainloop()
