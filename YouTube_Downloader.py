import yt_dlp
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import queue
import time
import math
import re
from tkinter.font import Font

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("800x900")
        self.root.configure(bg="#f0f0f0")
        self.root.resizable(True, True)  # Allow resizing
        self.root.minsize(600, 400)  # Set minimum size

        # Initialize variables
        self.folder_path = tk.StringVar()
        self.quality_var = tk.StringVar(value='High')
        self.media_type_var = tk.StringVar(value='Video')
        self.start_var = tk.StringVar(value='1')
        self.end_var = tk.StringVar(value='1')
        self.progress_var = tk.DoubleVar()
        self.percent_var = tk.StringVar(value="0.00%")
        self.speed_var = tk.StringVar(value="Download Speed: 0 KiB/s")
        self.time_left_var = tk.StringVar(value="Time Left: 00:00")
        self.file_size_var = tk.StringVar(value="File Size: 0 MB")
        self.file_name_var = tk.StringVar(value="File Name: N/A")
        self.cancel_flag = False
        self.pause_flag = False
        self.pause_event = threading.Event()

        # Queue for thread-safe communication
        self.queue = queue.Queue()

        # Apply styles
        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')
        self.configure_styles()

        # Create the UI elements
        self.create_widgets()

        # Configure column and row weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Start the queue processing
        self.process_queue()

    def configure_styles(self):
        # Configure colors
        bg_color = "#f0f0f0"
        fg_color = "#333333"
        accent_color = "#0078D7"  # Blue color for buttons and progress bar

        # Configure fonts
        default_font = Font(family="Segoe UI", size=10)
        header_font = Font(family="Segoe UI", size=14, weight="bold")

        # Configure styles
        self.style.configure("TLabel", font=default_font, background=bg_color, foreground=fg_color)
        self.style.configure("TEntry", font=default_font)
        self.style.configure("TCombobox", font=default_font)
        self.style.configure("TButton",
                             font=default_font,
                             foreground="white",
                             background=accent_color,
                             borderwidth=0,
                             padding=6)
        self.style.map("TButton",
                      background=[('active', '#0058b3')])  # Darker blue on hover
        self.style.configure("Header.TLabel", font=header_font, background=bg_color, foreground=accent_color)

        # Style for Progressbar
        self.style.configure("green.Horizontal.TProgressbar",
                             troughcolor="#d3d3d3",
                             background="#4CAF50")  # Green color

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20 20 20 20", style="Main.TFrame")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)  # Make the progress frame expandable

        # Header
        header_label = ttk.Label(main_frame, text="YouTube Downloader", style="Header.TLabel")
        header_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")

        # YouTube URL
        url_label = ttk.Label(main_frame, text="Enter YouTube URL:")
        url_label.grid(row=1, column=0, sticky="w", pady=(0, 5))
        self.url_entry = ttk.Entry(main_frame)
        self.url_entry.grid(row=2, column=0, columnspan=2, sticky="we", pady=(0, 20))

        # Download Folder
        folder_label = ttk.Label(main_frame, text="Download Folder:")
        folder_label.grid(row=3, column=0, sticky="w", pady=(0, 5))
        self.folder_display = ttk.Entry(main_frame, textvariable=self.folder_path, state='readonly')
        self.folder_display.grid(row=4, column=0, sticky="we", pady=(0, 5))
        self.select_folder_button = ttk.Button(main_frame, text="Browse", command=self.select_folder, width=10)
        self.select_folder_button.grid(row=4, column=1, padx=(10, 0), pady=(0, 5))

        # Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Download Options", padding=(10, 5))
        options_frame.grid(row=5, column=0, columnspan=2, sticky="we", pady=(20, 0))
        options_frame.columnconfigure(1, weight=1)
        options_frame.columnconfigure(3, weight=1)

        # Quality Selection
        quality_label = ttk.Label(options_frame, text="Quality:")
        quality_label.grid(row=0, column=0, sticky="w", pady=5)
        quality_options = ["High", "Medium", "Low"]
        self.quality_combobox = ttk.Combobox(options_frame, textvariable=self.quality_var, values=quality_options, state='readonly')
        self.quality_combobox.grid(row=0, column=1, sticky="we", pady=5)
        self.quality_combobox.current(0)

        # Media Type Selection
        type_label = ttk.Label(options_frame, text="Type:")
        type_label.grid(row=0, column=2, sticky="w", pady=5, padx=(20, 0))
        media_type_options = ["Video", "Audio"]
        self.media_type_combobox = ttk.Combobox(options_frame, textvariable=self.media_type_var, values=media_type_options, state='readonly')
        self.media_type_combobox.grid(row=0, column=3, sticky="we", pady=5)
        self.media_type_combobox.current(0)

        # Playlist Range
        start_label = ttk.Label(options_frame, text="Start:")
        start_label.grid(row=1, column=0, sticky="w", pady=5)
        self.start_entry = ttk.Entry(options_frame, textvariable=self.start_var, width=10)
        self.start_entry.grid(row=1, column=1, sticky="w", pady=5)

        end_label = ttk.Label(options_frame, text="End:")
        end_label.grid(row=1, column=2, sticky="w", pady=5, padx=(20, 0))
        self.end_entry = ttk.Entry(options_frame, textvariable=self.end_var, width=10)
        self.end_entry.grid(row=1, column=3, sticky="w", pady=5)

        # Download Button
        self.download_button = ttk.Button(main_frame, text="Start Download", command=self.start_download)
        self.download_button.grid(row=6, column=0, columnspan=2, pady=(20, 10), sticky="we")

        # Progress Frame
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.grid(row=7, column=0, columnspan=2, sticky="nswe", pady=(10, 0))
        self.progress_frame.columnconfigure(0, weight=1)
        self.progress_frame.rowconfigure(3, weight=1)  # Make file name label expandable

        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100, mode='determinate', style="green.Horizontal.TProgressbar")
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0, 5))

        self.percent_label = ttk.Label(self.progress_frame, textvariable=self.percent_var)
        self.percent_label.grid(row=1, column=0, sticky="w", pady=(0, 5))

        self.speed_label = ttk.Label(self.progress_frame, textvariable=self.speed_var)
        self.speed_label.grid(row=2, column=0, sticky="w", pady=(0, 5))

        self.time_left_label = ttk.Label(self.progress_frame, textvariable=self.time_left_var)
        self.time_left_label.grid(row=2, column=1, sticky="e", pady=(0, 5))

        self.file_name_label = ttk.Label(self.progress_frame, textvariable=self.file_name_var, wraplength=400)
        self.file_name_label.grid(row=3, column=0, columnspan=2, sticky="nswe", pady=(0, 5))

        self.file_size_label = ttk.Label(self.progress_frame, textvariable=self.file_size_var)
        self.file_size_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 5))

        # Control Buttons
        self.control_frame = ttk.Frame(main_frame)
        self.control_frame.grid(row=8, column=0, columnspan=2, sticky="we", pady=(10, 0))
        self.control_frame.columnconfigure(0, weight=1)
        self.control_frame.columnconfigure(1, weight=1)

        self.pause_button = ttk.Button(self.control_frame, text="Pause", command=self.pause_download, state='disabled')
        self.pause_button.grid(row=0, column=0, sticky="we", padx=(0, 5))

        self.cancel_button = ttk.Button(self.control_frame, text="Cancel", command=self.cancel_download, state='disabled')
        self.cancel_button.grid(row=0, column=1, sticky="we", padx=(5, 0))

        # Initially hide progress and control frames
        self.progress_frame.grid_remove()
        self.control_frame.grid_remove()

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
            # Optionally, change the button text to "Change Folder"
            self.select_folder_button.config(text="Change Folder")

    def start_download(self):
        url = self.url_entry.get().strip()
        download_folder = self.folder_path.get().strip()

        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL.")
            return
        if not download_folder:
            messagebox.showerror("Error", "Please select a download folder.")
            return

        # Show progress and control frames
        self.progress_frame.grid()
        self.control_frame.grid()

        # Disable input fields and download button
        self.url_entry.config(state='disabled')
        self.folder_display.config(state='readonly')
        self.select_folder_button.config(state='disabled')
        self.quality_combobox.config(state='disabled')
        self.media_type_combobox.config(state='disabled')
        self.start_entry.config(state='disabled')
        self.end_entry.config(state='disabled')
        self.download_button.config(state='disabled')

        # Enable control buttons
        self.pause_button.config(state='normal')
        self.cancel_button.config(state='normal')

        # Reset progress
        self.progress_var.set(0)
        self.percent_var.set("0.00%")
        self.speed_var.set("Download Speed: 0 KiB/s")
        self.time_left_var.set("Time Left: 00:00")
        self.file_size_var.set("File Size: Calculating...")
        self.file_name_var.set("File Name: Retrieving...")

        # Reset flags
        self.cancel_flag = False
        self.pause_flag = False
        self.pause_event.clear()

        # Start download in a separate thread
        download_thread = threading.Thread(target=self.download_media, daemon=True)
        download_thread.start()

    def pause_download(self):
        if not self.pause_flag:
            self.pause_flag = True
            self.pause_event.set()
            self.pause_button.config(text="Resume")
            self.speed_var.set("Download Paused")
            self.time_left_var.set("Time Left: Paused")
        else:
            self.pause_flag = False
            self.pause_event.clear()
            self.pause_button.config(text="Pause")
            self.speed_var.set("Download Speed: Resuming...")
            self.time_left_var.set("Time Left: Calculating...")

    def cancel_download(self):
        if messagebox.askyesno("Cancel Download", "Are you sure you want to cancel the download?"):
            self.cancel_flag = True
            self.cancel_button.config(state='disabled')
            self.pause_button.config(state='disabled')
            self.pause_button.config(text="Pause")
            self.speed_var.set("Cancelling Download...")
            self.time_left_var.set("Time Left: Cancelling...")

    def download_media(self):
        url = self.url_entry.get().strip()
        download_folder = self.folder_path.get().strip()
        quality = self.quality_var.get()
        media_type = self.media_type_var.get()
        start = self.start_var.get().strip()
        end = self.end_var.get().strip()

        # Set download options based on selected quality and media type
        ydl_opts = {
            'outtmpl': os.path.join(download_folder, '%(playlist_index)s - %(title)s.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'noplaylist': False,  # Allow playlist downloads
            'quiet': True,
            'no_warnings': True,
            'restrictfilenames': True,
            'ignoreerrors': False,
            'continuedl': True,
            'retries': 3,
        }

        if media_type == 'Video':
            ydl_opts['format'] = {
                'High': 'bestvideo+bestaudio/best',
                'Medium': '136+bestaudio/best',
                'Low': 'worstvideo+bestaudio/worst'
            }.get(quality, 'bestvideo+bestaudio/best')
            ydl_opts['merge_output_format'] = 'mp4'
        elif media_type == 'Audio':
            ydl_opts['format'] = 'bestaudio'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        # Handle downloading specific parts of a playlist
        if start.isdigit() and end.isdigit():
            start_num = int(start)
            end_num = int(end)
            if start_num > end_num:
                self.queue.put(("error", "Start index cannot be greater than end index."))
                self.reset_ui()
                return
            ydl_opts['playliststart'] = start_num
            ydl_opts['playlistend'] = end_num

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            if not self.cancel_flag:
                self.queue.put(("success", f"{media_type} downloaded successfully."))
        except yt_dlp.utils.DownloadError as e:
            if self.cancel_flag:
                self.queue.put(("warning", "Download was cancelled."))
            else:
                self.queue.put(("error", f"Download Error: {e}"))
        except Exception as e:
            self.queue.put(("error", f"An unexpected error occurred: {e}"))
        finally:
            self.reset_ui()

    def reset_ui(self):
        # Reset UI elements in the main thread
        self.queue.put(("reset", None))

    def progress_hook(self, d):
        if self.cancel_flag:
            raise yt_dlp.utils.DownloadError("Download cancelled by user.")

        if d['status'] == 'downloading':
            # Clean the strings to remove any ANSI codes
            percent_str = self.strip_ansi_codes(d.get('_percent_str', '0%')).strip('%')
            speed_str = self.strip_ansi_codes(d.get('_speed_str', '0KiB/s')).strip()
            eta_str = self.strip_ansi_codes(d.get('_eta_str', '00:00')).strip()
            filename = os.path.basename(d.get('filename', 'N/A'))
            filesize = d.get('total_bytes', 0)

            # Convert percent to float
            percent = float(percent_str) if self.is_float(percent_str) else 0.0

            while self.pause_flag:
                time.sleep(0.1)
                if self.cancel_flag:
                    break

            # Convert filesize to human-readable format
            human_size = self.format_size(filesize)

            # Put the progress data into the queue
            self.queue.put(("progress", {
                "percent": percent,
                "speed": speed_str,
                "eta": eta_str,
                "filename": filename,
                "filesize": human_size
            }))
        elif d['status'] == 'finished':
            # When finished, set progress to 100%
            self.queue.put(("progress", {
                "percent": 100.0,
                "speed": "0 KiB/s",
                "eta": "00:00",
                "filename": os.path.basename(d.get('filename', 'N/A')),
                "filesize": self.format_size(d.get('total_bytes', 0))
            }))

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                if msg_type == "progress":
                    self.update_progress(data)
                elif msg_type == "success":
                    # Show completion alert
                    messagebox.showinfo("Download Complete", data)
                    self.reset_ui_after_download()
                elif msg_type == "warning":
                    messagebox.showwarning("Cancelled", data)
                    self.reset_ui_after_download()
                elif msg_type == "error":
                    messagebox.showerror("Error", data)
                    self.reset_ui_after_download()
                elif msg_type == "reset":
                    self.reset_ui_after_download()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def update_progress(self, data):
        self.progress_var.set(data["percent"])
        self.percent_var.set(f"{data['percent']:.2f}%")
        self.speed_var.set(f"Download Speed: {data['speed']}")
        self.time_left_var.set(f"Time Left: {data['eta']}")
        self.file_name_var.set(f"File Name: {data['filename']}")
        self.file_size_var.set(f"File Size: {data['filesize']}")

    def reset_ui_after_download(self):
        # Hide progress and control frames
        self.progress_frame.grid_remove()
        self.control_frame.grid_remove()

        # Enable input fields and download button
        self.url_entry.config(state='normal')
        self.folder_display.config(state='readonly')
        self.select_folder_button.config(state='normal')
        self.quality_combobox.config(state='readonly')
        self.media_type_combobox.config(state='readonly')
        self.start_entry.config(state='normal')
        self.end_entry.config(state='normal')
        self.download_button.config(state='normal')

        # Disable control buttons
        self.pause_button.config(state='disabled', text="Pause")
        self.cancel_button.config(state='disabled')

        # Reset progress variables
        self.progress_var.set(0)
        self.percent_var.set("0.00%")
        self.speed_var.set("Download Speed: 0 KiB/s")
        self.time_left_var.set("Time Left: 00:00")
        self.file_size_var.set("File Size: 0 MB")
        self.file_name_var.set("File Name: N/A")

    def strip_ansi_codes(self, s):
        return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', s)

    def is_float(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def format_size(self, size_bytes):
        if size_bytes == 0:
            return "0 MB"
        size_name = ("Bytes", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

def main():
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
