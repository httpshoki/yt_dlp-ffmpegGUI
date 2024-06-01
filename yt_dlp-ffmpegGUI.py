import os
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import yt_dlp
import configparser

# Função para salvar as configurações
def save_settings(dest_folder):
    config = configparser.ConfigParser()
    config['Settings'] = {'destination_folder': dest_folder}
    with open('settings.ini', 'w') as configfile:
        config.write(configfile)

# Função para carregar as configurações
def load_settings():
    config = configparser.ConfigParser()
    if os.path.exists('settings.ini'):
        config.read('settings.ini')
        return config['Settings'].get('destination_folder', '')
    return ''

# Função para baixar o vídeo e mostrar o progresso
def download_video():
    video_url = entry_url.get()
    dest_folder = entry_dest.get()
    if not video_url:
        messagebox.showerror("Erro", "Por favor, insira a URL do vídeo.")
        return
    if not dest_folder:
        messagebox.showerror("Erro", "Por favor, escolha a pasta de destino.")
        return

    # Salvar a pasta de destino
    save_settings(dest_folder)

    ydl_opts = {
        'format': 'bestvideo+bestaudio',
        'outtmpl': os.path.join(dest_folder, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'progress_hooks': [update_progress],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(video_url, download=True)
            video_title = info_dict.get('title', None)
            temp_file = os.path.join(dest_folder, f"{video_title}.mp4")
            final_file = os.path.join(dest_folder, f"{video_title}_final.mp4")
        
        subprocess.run(['ffmpeg', '-i', temp_file, '-c:v', 'copy', '-c:a', 'copy', final_file])
        os.remove(temp_file)
        messagebox.showinfo("Sucesso", f"Conversão concluída. O vídeo foi salvo como {final_file}.")
    except Exception as e:
        messagebox.showerror("Erro", str(e))

# Função para atualizar a barra de progresso
def update_progress(d):
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes', 0)
        percent = (downloaded / total) * 100 if total > 0 else 0
        progress_bar['value'] = percent
        progress_bar_label.config(text=f"{percent:.2f}%")
        speed = d.get('speed', 0)
        speed_label.config(text=f"Velocidade: {speed / 1024:.2f} KB/s")
        root.update_idletasks()

# Função para escolher a pasta de destino
def choose_dest_folder():
    folder = filedialog.askdirectory()
    if folder:
        entry_dest.delete(0, tk.END)
        entry_dest.insert(0, folder)

# Configurações da GUI
root = tk.Tk()
root.title("Download de Vídeos")

tk.Label(root, text="Digite a URL:").grid(row=0, column=0, padx=5, pady=5)
entry_url = tk.Entry(root, width=50)
entry_url.grid(row=0, column=1, padx=5, pady=5)

tk.Label(root, text="Escolha a pasta de destino:").grid(row=1, column=0, padx=5, pady=5)
entry_dest = tk.Entry(root, width=50)
entry_dest.grid(row=1, column=1, padx=5, pady=5)
entry_dest.insert(0, load_settings())

btn_browse = tk.Button(root, text="Procurar", command=choose_dest_folder)
btn_browse.grid(row=1, column=2, padx=5, pady=5)

btn_download = tk.Button(root, text="Baixar e Converter", command=download_video)
btn_download.grid(row=2, column=1, padx=5, pady=5)

progress_bar = ttk.Progressbar(root, length=400)
progress_bar.grid(row=3, column=1, padx=5, pady=5)

progress_bar_label = tk.Label(root, text="0.00%")
progress_bar_label.grid(row=3, column=2, padx=5, pady=5)

speed_label = tk.Label(root, text="Velocidade: 0.00 KB/s")
speed_label.grid(row=4, column=1, padx=5, pady=5)

root.mainloop()
