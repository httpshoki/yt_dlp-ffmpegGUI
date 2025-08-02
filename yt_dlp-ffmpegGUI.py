import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import yt_dlp
import configparser
import threading
import queue

class VideoDownloaderApp:
    """
    Uma aplicação GUI para baixar vídeos usando yt-dlp.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("YT-DLP Downloader")
        self.root.geometry("600x250")

        self.download_queue = queue.Queue()
        self.final_filepath = ""

        self.create_widgets()

    def create_widgets(self):
        """Cria e posiciona os widgets na janela."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # URL
        ttk.Label(main_frame, text="URL do Vídeo:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_url = ttk.Entry(main_frame, width=60)
        self.entry_url.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)

        # Pasta de Destino
        ttk.Label(main_frame, text="Salvar em:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.entry_dest = ttk.Entry(main_frame, width=60)
        self.entry_dest.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.entry_dest.insert(0, self.load_settings())

        self.btn_browse = ttk.Button(main_frame, text="Procurar...", command=self.choose_dest_folder)
        self.btn_browse.grid(row=1, column=3, padx=5, pady=5)

        # Botão de Download
        self.btn_download = ttk.Button(main_frame, text="Baixar", command=self.start_download_thread)
        self.btn_download.grid(row=2, column=1, pady=10, columnspan=2)

        # Barra de Progresso
        self.progress_bar = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.progress_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)

        self.progress_label = ttk.Label(main_frame, text="0.00%")
        self.progress_label.grid(row=3, column=3, sticky=tk.W, padx=5, pady=5)

        # Status
        self.status_label = ttk.Label(main_frame, text="Pronto.")
        self.status_label.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), padx=5, pady=5)

        main_frame.columnconfigure(1, weight=1)

    def save_settings(self, dest_folder):
        """Salva a pasta de destino em settings.ini."""
        config = configparser.ConfigParser()
        config['Settings'] = {'destination_folder': dest_folder}
        with open('settings.ini', 'w') as configfile:
            config.write(configfile)

    def load_settings(self):
        """Carrega a pasta de destino de settings.ini."""
        config = configparser.ConfigParser()
        if os.path.exists('settings.ini'):
            config.read('settings.ini')
            return config['Settings'].get('destination_folder', '')
        return ''

    def choose_dest_folder(self):
        """Abre um diálogo para o usuário escolher a pasta de destino."""
        folder = filedialog.askdirectory()
        if folder:
            self.entry_dest.delete(0, tk.END)
            self.entry_dest.insert(0, folder)

    def start_download_thread(self):
        """Inicia o processo de download em uma nova thread."""
        video_url = self.entry_url.get()
        dest_folder = self.entry_dest.get()

        if not video_url:
            messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
            return
        if not dest_folder:
            messagebox.showerror("Erro", "Por favor, escolha a pasta de destino.")
            return

        self.btn_download.config(state=tk.DISABLED)
        self.status_label.config(text="Iniciando download...")
        self.progress_bar['value'] = 0
        self.progress_label.config(text="0.00%")

        self.save_settings(dest_folder)

        download_thread = threading.Thread(
            target=self._execute_download,
            args=(video_url, dest_folder),
            daemon=True
        )
        download_thread.start()
        self.root.after(100, self.process_queue)

    def _progress_hook(self, d):
        """Hook para o yt-dlp. Captura o progresso e o caminho final do arquivo."""
        if d['status'] == 'finished':
            self.final_filepath = d.get('info_dict', {}).get('filepath')
        self.download_queue.put(d)

    def _execute_download(self, video_url, dest_folder):
        """Executa o download usando yt-dlp. Este método roda em uma thread separada."""
        try:
            self.final_filepath = ""

            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': os.path.join(dest_folder, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'progress_hooks': [self._progress_hook],
                'noprogress': True, # Desativa o log de progresso no console
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(video_url, download=True)

            if not self.final_filepath:
                self.download_queue.put({'status': 'error', 'message': 'Não foi possível determinar o caminho do arquivo final.'})
                return

            self.download_queue.put({'status': 'success', 'message': f"Download concluído!\nSalvo em: {self.final_filepath}"})

        except Exception as e:
            error_message = str(e)
            if hasattr(e, 'exc_info') and e.exc_info and e.exc_info[1]:
                error_message = str(e.exc_info[1]).replace('ERROR: ', '')
            self.download_queue.put({'status': 'error', 'message': error_message})

    def process_queue(self):
        try:
            message = self.download_queue.get_nowait()

            if message['status'] == 'downloading':
                total_bytes = message.get('total_bytes') or message.get('total_bytes_estimate')
                if total_bytes:
                    downloaded_bytes = message.get('downloaded_bytes', 0)
                    percent = (downloaded_bytes / total_bytes) * 100
                    self.progress_bar['value'] = percent
                    self.progress_label.config(text=f"{percent:.2f}%")

                speed = message.get('speed')
                if speed:
                    self.status_label.config(text=f"Baixando... {message.get('_percent_str', '')} a {message.get('_speed_str', '')}")

                # Continue checking the queue
                self.root.after(100, self.process_queue)

            elif message['status'] == 'finished':
                self.status_label.config(text="Download concluído. Convertendo, por favor aguarde...")
                # Continue checking the queue for the final status
                self.root.after(100, self.process_queue)

            elif message['status'] == 'success':
                self.status_label.config(text="Pronto.")
                self.progress_bar['value'] = 100
                self.progress_label.config(text="100.00%")
                self.btn_download.config(state=tk.NORMAL)
                self.entry_url.delete(0, tk.END)
                messagebox.showinfo("Sucesso", message['message'])

            elif message['status'] == 'error':
                self.status_label.config(text="Erro.")
                self.progress_bar['value'] = 0
                self.progress_label.config(text="0.00%")
                self.btn_download.config(state=tk.NORMAL)
                messagebox.showerror("Erro no Download", message['message'])

        except queue.Empty:
            # If the queue is empty, check again after a short delay
            # This is necessary to keep polling until a final message ('success' or 'error') is received
            if self.btn_download['state'] == tk.DISABLED:
                self.root.after(100, self.process_queue)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()
