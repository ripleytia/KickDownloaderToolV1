import customtkinter as ctk
import yt_dlp
import threading
import os
import sys
from tkinter import filedialog, messagebox
from PIL import Image

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# Ripleytia Tema Renkleri (Gelişmiş)
BG_COLOR = "#050505"      # Ekstra koyu siyah arka plan
FG_COLOR = "#121212"      # Panel arka planı
PURPLE_ACCENT = "#8A2BE2" # Parlak Ripleytia Moru
PURPLE_HOVER = "#A233FF"
PURPLE_BORDER = "#4B0082"
TEXT_COLOR = "#FFFFFF"
TEXT_MUTED = "#A0A0A0"

class DownloaderLogic:
    @staticmethod
    def resolve_kick_url(url):
        if "kick.com" in url:
            import urllib.request
            import re
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
                # Try to find a master.m3u8 first (usually VODs)
                matches = re.findall(r'(https://[^\s"\'<>]*?master\.m3u8)', html)
                if not matches:
                    # Fallback to any m3u8
                    matches = re.findall(r'(https://[^\s"\'<>]*?\.m3u8)', html)
                if matches:
                    return matches[-1] # Son bulunan m3u8 genellikle en sağlıklısı
            except Exception as e:
                print("URL Resolve Error:", e)
        return url

    @staticmethod
    def get_info(url):
        resolved_url = DownloaderLogic.resolve_kick_url(url)
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(resolved_url, download=False)
            return info

    @staticmethod
    def download(url, format_id, output_path, progress_hook):
        resolved_url = DownloaderLogic.resolve_kick_url(url)
        
        # Eğer m3u8 kullanırsak title 'master' olabiliyor, bu yüzden linkten ID'yi çekiyoruz
        video_id = url.split('/')[-1]
        if '?' in video_id:
            video_id = video_id.split('?')[0]
            
        ydl_opts = {
            'format': format_id,
            'outtmpl': os.path.join(output_path, f'{video_id}.%(ext)s'),
            'progress_hooks': [progress_hook],
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([resolved_url])


class KickDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ripleytia Kick Downloader Pro")
        self.geometry("900x750")
        self.configure(fg_color=BG_COLOR)
        
        # Pencere ikonu
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
            
        self.download_path = os.path.expanduser("~/Downloads")

        # Grid configuration
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Üst Banner (Ripleytia Logosu)
        banner_path = resource_path("banner.jpg")
        if os.path.exists(banner_path):
            banner_img = Image.open(banner_path)
            # Resize image maintaining aspect ratio
            width = 900
            height = int((width / banner_img.width) * banner_img.height)
            if height > 200:
                height = 200
                width = int((height / banner_img.height) * banner_img.width)
                
            self.banner_image = ctk.CTkImage(light_image=banner_img, dark_image=banner_img, size=(width, height))
            self.banner_label = ctk.CTkLabel(self, image=self.banner_image, text="")
            self.banner_label.grid(row=0, column=0, pady=(0, 10), sticky="n")

        # Ana İçerik Tabları
        self.tabview = ctk.CTkTabview(self, 
                                      fg_color=FG_COLOR,
                                      border_width=2,
                                      border_color=PURPLE_BORDER,
                                      segmented_button_fg_color=BG_COLOR,
                                      segmented_button_selected_color=PURPLE_ACCENT,
                                      segmented_button_selected_hover_color=PURPLE_HOVER,
                                      segmented_button_unselected_color=BG_COLOR,
                                      text_color=TEXT_COLOR,
                                      corner_radius=15)
        self.tabview.grid(row=1, column=0, padx=30, pady=(0, 20), sticky="nsew")

        self.tabview.add("Klip İndir")
        self.tabview.add("Yayın Tekrarı İndir")
        self.tabview.add("Toplu Klip İndir")
        
        # Kayıt Yeri Seçici
        self.path_frame = ctk.CTkFrame(self, fg_color=FG_COLOR, corner_radius=10, border_width=1, border_color=PURPLE_BORDER)
        self.path_frame.grid(row=2, column=0, padx=30, pady=(0, 20), sticky="ew")
        
        self.path_label = ctk.CTkLabel(self.path_frame, text=f"Kayıt Klasörü: {self.download_path}", text_color=TEXT_COLOR, font=ctk.CTkFont(weight="bold"))
        self.path_label.pack(side="left", padx=20, pady=15)
        
        self.btn_change_path = ctk.CTkButton(self.path_frame, text="Değiştir", 
                                             fg_color=PURPLE_ACCENT, hover_color=PURPLE_HOVER, 
                                             font=ctk.CTkFont(weight="bold"),
                                             width=120, height=35, command=self.change_download_path)
        self.btn_change_path.pack(side="right", padx=20, pady=15)

        self.setup_clip_tab()
        self.setup_vod_tab()
        self.setup_batch_tab()

    def change_download_path(self):
        path = filedialog.askdirectory(initialdir=self.download_path)
        if path:
            self.download_path = path
            self.path_label.configure(text=f"Kayıt Klasörü: {self.download_path}")

    def create_ui_elements(self, tab, placeholder, fetch_cmd, download_cmd, is_batch=False):
        tab.grid_columnconfigure(0, weight=1)
        
        if is_batch:
            tab.grid_rowconfigure(1, weight=1)
            lbl = ctk.CTkLabel(tab, text="Linkleri alt alta yapıştırın:", text_color=TEXT_COLOR, font=ctk.CTkFont(size=14, weight="bold"))
            lbl.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
            
            entry = ctk.CTkTextbox(tab, border_color=PURPLE_ACCENT, border_width=2, fg_color=BG_COLOR, 
                                   font=ctk.CTkFont(size=13), corner_radius=10)
            entry.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        else:
            entry = ctk.CTkEntry(tab, placeholder_text=placeholder, height=45,
                                border_color=PURPLE_ACCENT, border_width=2, fg_color=BG_COLOR,
                                font=ctk.CTkFont(size=14), corner_radius=10)
            entry.grid(row=0, column=0, padx=20, pady=(30, 15), sticky="ew")

        btn_fetch = None
        if not is_batch:
            btn_fetch = ctk.CTkButton(tab, text="Kaliteleri Getir", height=40,
                                      fg_color="transparent", border_width=2, border_color=PURPLE_ACCENT, 
                                      hover_color=PURPLE_BORDER, text_color=TEXT_COLOR,
                                      font=ctk.CTkFont(weight="bold", size=14),
                                      command=fetch_cmd)
            btn_fetch.grid(row=1, column=0, padx=20, pady=10)

        format_var = ctk.StringVar(value="Kalite Seçin")
        format_menu = ctk.CTkOptionMenu(tab, variable=format_var, values=["Önce Linki Getir"] if not is_batch else ["En İyi Kalite", "1080p (Mümkünse)", "720p (Mümkünse)"],
                                        height=40, width=250,
                                        fg_color=PURPLE_ACCENT, button_color=PURPLE_BORDER, button_hover_color=PURPLE_HOVER,
                                        font=ctk.CTkFont(weight="bold", size=13))
        format_menu.grid(row=2, column=0, padx=20, pady=15)
        if not is_batch:
            format_menu.configure(state="disabled")

        btn_download = ctk.CTkButton(tab, text="İndir" if not is_batch else "Tümünü İndir", height=50, width=200,
                                     fg_color=PURPLE_ACCENT, hover_color=PURPLE_HOVER,
                                     font=ctk.CTkFont(weight="bold", size=16),
                                     command=download_cmd)
        btn_download.grid(row=3, column=0, padx=20, pady=(15, 10))
        if not is_batch:
            btn_download.configure(state="disabled")

        progress = ctk.CTkProgressBar(tab, progress_color=PURPLE_ACCENT, height=12, corner_radius=6)
        progress.grid(row=4, column=0, padx=40, pady=15, sticky="ew")
        progress.set(0)

        status = ctk.CTkLabel(tab, text="Hazır", text_color=TEXT_MUTED, font=ctk.CTkFont(size=12))
        status.grid(row=5, column=0, padx=20, pady=5)
        
        return entry, btn_fetch, format_var, format_menu, btn_download, progress, status

    # --- KLİP İNDİR SEKMESİ ---
    def setup_clip_tab(self):
        tab = self.tabview.tab("Klip İndir")
        elements = self.create_ui_elements(tab, "Kick Klip URL'sini buraya yapıştırın...", 
                                           self.fetch_clip_qualities, self.download_clip)
        self.clip_url_entry, self.btn_fetch_clip, self.clip_format_var, self.clip_format_menu, self.btn_download_clip, self.clip_progress, self.clip_status = elements
        self.clip_formats = {}

    def fetch_clip_qualities(self):
        url = self.clip_url_entry.get().strip()
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen bir URL girin.")
            return

        self.btn_fetch_clip.configure(state="disabled", text="Aranıyor...")
        self.clip_status.configure(text="Video bilgileri alınıyor...")
        
        def fetch_thread():
            try:
                info = DownloaderLogic.get_info(url)
                formats = info.get('formats', [])
                video_formats = [f for f in formats if f.get('vcodec') != 'none']
                
                options = []
                self.clip_formats.clear()
                
                for f in video_formats:
                    res = f.get('resolution') or f.get('format_note') or "Bilinmiyor"
                    fps = f.get('fps')
                    fps_str = f"{fps}fps" if fps else ""
                    ext = f.get('ext', 'mp4')
                    format_id = f.get('format_id')
                    
                    title = f"{res} {fps_str} ({ext})".strip()
                    if title not in options:
                        options.append(title)
                        self.clip_formats[title] = format_id

                options.insert(0, "En İyi Kalite (Best)")
                self.clip_formats["En İyi Kalite (Best)"] = "bestvideo+bestaudio/best"

                self.clip_format_menu.configure(values=options, state="normal")
                self.clip_format_var.set(options[0])
                self.btn_download_clip.configure(state="normal")
                self.clip_status.configure(text="Kaliteler başarıyla getirildi.", text_color="#00FF00")
                
            except Exception as e:
                self.clip_status.configure(text=f"Hata: {str(e)}", text_color="#FF4444")
            finally:
                self.btn_fetch_clip.configure(state="normal", text="Kaliteleri Getir")

        threading.Thread(target=fetch_thread, daemon=True).start()

    def download_clip(self):
        url = self.clip_url_entry.get().strip()
        selected_format_title = self.clip_format_var.get()
        format_id = self.clip_formats.get(selected_format_title, "best")

        self.btn_download_clip.configure(state="disabled")
        self.clip_progress.set(0)
        self.clip_status.configure(text_color=TEXT_COLOR)
        
        def hook(d):
            if d['status'] == 'downloading':
                p = d.get('_percent_str', '0%').replace('%', '').replace('\x1b[0;94m', '').replace('\x1b[0m', '').strip()
                try:
                    perc = float(p) / 100.0
                    self.clip_progress.set(perc)
                    self.clip_status.configure(text=f"İndiriliyor... {d.get('_percent_str', '')} (Hız: {d.get('_speed_str', '')})")
                except:
                    pass
            elif d['status'] == 'finished':
                self.clip_progress.set(1.0)
                self.clip_status.configure(text="İndirme Tamamlandı!", text_color="#00FF00")
                self.btn_download_clip.configure(state="normal")

        def dl_thread():
            try:
                DownloaderLogic.download(url, format_id, self.download_path, hook)
            except Exception as e:
                self.clip_status.configure(text=f"İndirme Hatası: {str(e)}", text_color="#FF4444")
                self.btn_download_clip.configure(state="normal")

        threading.Thread(target=dl_thread, daemon=True).start()

    # --- YAYIN TEKRARI (VOD) SEKMESİ ---
    def setup_vod_tab(self):
        tab = self.tabview.tab("Yayın Tekrarı İndir")
        elements = self.create_ui_elements(tab, "Kick Yayın Tekrarı (VOD) URL'sini buraya yapıştırın...", 
                                           self.fetch_vod_qualities, self.download_vod)
        self.vod_url_entry, self.btn_fetch_vod, self.vod_format_var, self.vod_format_menu, self.btn_download_vod, self.vod_progress, self.vod_status = elements
        self.vod_formats = {} 

    def fetch_vod_qualities(self):
        url = self.vod_url_entry.get().strip()
        if not url:
            messagebox.showwarning("Uyarı", "Lütfen bir URL girin.")
            return

        self.btn_fetch_vod.configure(state="disabled", text="Aranıyor...")
        self.vod_status.configure(text="Video bilgileri alınıyor...")
        
        def fetch_thread():
            try:
                info = DownloaderLogic.get_info(url)
                formats = info.get('formats', [])
                video_formats = [f for f in formats if f.get('vcodec') != 'none']
                
                options = []
                self.vod_formats.clear()
                
                for f in video_formats:
                    res = f.get('resolution') or f.get('format_note') or "Bilinmiyor"
                    fps = f.get('fps')
                    fps_str = f"{fps}fps" if fps else ""
                    ext = f.get('ext', 'mp4')
                    format_id = f.get('format_id')
                    
                    title = f"{res} {fps_str} ({ext})".strip()
                    if title not in options:
                        options.append(title)
                        self.vod_formats[title] = format_id

                options.insert(0, "En İyi Kalite (Best)")
                self.vod_formats["En İyi Kalite (Best)"] = "bestvideo+bestaudio/best"

                self.vod_format_menu.configure(values=options, state="normal")
                self.vod_format_var.set(options[0])
                self.btn_download_vod.configure(state="normal")
                self.vod_status.configure(text="Kaliteler başarıyla getirildi.", text_color="#00FF00")
                
            except Exception as e:
                self.vod_status.configure(text=f"Hata: {str(e)}", text_color="#FF4444")
            finally:
                self.btn_fetch_vod.configure(state="normal", text="Kaliteleri Getir")

        threading.Thread(target=fetch_thread, daemon=True).start()

    def download_vod(self):
        url = self.vod_url_entry.get().strip()
        selected_format_title = self.vod_format_var.get()
        format_id = self.vod_formats.get(selected_format_title, "best")

        self.btn_download_vod.configure(state="disabled")
        self.vod_progress.set(0)
        self.vod_status.configure(text_color=TEXT_COLOR)
        
        def hook(d):
            if d['status'] == 'downloading':
                p = d.get('_percent_str', '0%').replace('%', '').replace('\x1b[0;94m', '').replace('\x1b[0m', '').strip()
                try:
                    perc = float(p) / 100.0
                    self.vod_progress.set(perc)
                    self.vod_status.configure(text=f"İndiriliyor... {d.get('_percent_str', '')} (Hız: {d.get('_speed_str', '')})")
                except:
                    pass
            elif d['status'] == 'finished':
                self.vod_progress.set(1.0)
                self.vod_status.configure(text="İndirme Tamamlandı!", text_color="#00FF00")
                self.btn_download_vod.configure(state="normal")

        def dl_thread():
            try:
                DownloaderLogic.download(url, format_id, self.download_path, hook)
            except Exception as e:
                self.vod_status.configure(text=f"İndirme Hatası: {str(e)}", text_color="#FF4444")
                self.btn_download_vod.configure(state="normal")

        threading.Thread(target=dl_thread, daemon=True).start()

    # --- TOPLU KLİP İNDİR SEKMESİ ---
    def setup_batch_tab(self):
        tab = self.tabview.tab("Toplu Klip İndir")
        elements = self.create_ui_elements(tab, "", None, self.download_batch, is_batch=True)
        self.batch_textbox, _, self.batch_format_var, self.batch_format_menu, self.btn_download_batch, self.batch_progress, self.batch_status = elements

    def download_batch(self):
        urls = self.batch_textbox.get("1.0", "end-1c").strip().split('\n')
        urls = [url.strip() for url in urls if url.strip()]
        
        if not urls:
            messagebox.showwarning("Uyarı", "Lütfen en az bir URL girin.")
            return

        selected_pref = self.batch_format_var.get()
        format_id = "best"
        if selected_pref == "1080p (Mümkünse)":
            format_id = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
        elif selected_pref == "720p (Mümkünse)":
            format_id = "bestvideo[height<=720]+bestaudio/best[height<=720]"

        self.btn_download_batch.configure(state="disabled")
        self.batch_progress.set(0)
        self.batch_status.configure(text_color=TEXT_COLOR)
        total_urls = len(urls)
        
        def batch_dl_thread():
            for i, url in enumerate(urls):
                self.batch_status.configure(text=f"İndiriliyor: {i+1}/{total_urls} ({url[:30]}...)")
                
                def hook(d):
                    if d['status'] == 'downloading':
                        p = d.get('_percent_str', '0%').replace('%', '').replace('\x1b[0;94m', '').replace('\x1b[0m', '').strip()
                        try:
                            perc = float(p) / 100.0
                            overall = (i + perc) / total_urls
                            self.batch_progress.set(overall)
                            self.batch_status.configure(text=f"İndiriliyor: {i+1}/{total_urls} - {d.get('_percent_str', '')} (Hız: {d.get('_speed_str', '')})")
                        except:
                            pass
                try:
                    DownloaderLogic.download(url, format_id, self.download_path, hook)
                except Exception as e:
                    print(f"Error downloading {url}: {e}")
                    
            self.batch_progress.set(1.0)
            self.batch_status.configure(text=f"Tüm {total_urls} işlem tamamlandı!", text_color="#00FF00")
            self.btn_download_batch.configure(state="normal")

        threading.Thread(target=batch_dl_thread, daemon=True).start()

if __name__ == "__main__":
    app = KickDownloaderApp()
    app.mainloop()
