import os
import socket
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from urllib.request import urlopen

try:
    import psutil
except ImportError:
    psutil = None


class SystemMonitorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Monitor di Sistema")
        self.root.geometry("520x420")
        self.root.configure(bg="#1f1f1f")

        self.bg = "#1f1f1f"
        self.card = "#2a2a2a"
        self.text = "#eaeaea"
        self.accent = "#4aa3ff"

        self._build_ui()
        self._refresh_stats()

    def _build_ui(self) -> None:
        header = tk.Label(
            self.root,
            text="Monitor di Sistema",
            font=("Helvetica", 16, "bold"),
            bg=self.bg,
            fg=self.text,
            pady=10,
        )
        header.pack()

        button_frame = tk.Frame(self.root, bg=self.bg)
        button_frame.pack(pady=10)

        net_button = ttk.Button(
            button_frame,
            text="Schede di rete Windows",
            command=self._open_network_adapters,
        )
        net_button.grid(row=0, column=0, padx=8)

        ip_button = ttk.Button(
            button_frame,
            text="Mostra IP pubblico/privato",
            command=self._show_ip_info,
        )
        ip_button.grid(row=0, column=1, padx=8)

        stats_frame = tk.Frame(self.root, bg=self.bg)
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=10)

        self.cpu_label, self.cpu_bar = self._create_stat_card(stats_frame, "CPU")
        self.net_label, self.net_bar = self._create_stat_card(stats_frame, "Rete")
        self.disk_label, self.disk_bar = self._create_stat_card(stats_frame, "Disco")

    def _create_stat_card(self, parent: tk.Frame, title: str):
        card = tk.Frame(parent, bg=self.card, padx=12, pady=10)
        card.pack(fill=tk.X, pady=8)

        label = tk.Label(
            card,
            text=title,
            font=("Helvetica", 12, "bold"),
            bg=self.card,
            fg=self.text,
        )
        label.pack(anchor="w")

        value = tk.Label(
            card,
            text="--",
            font=("Helvetica", 11),
            bg=self.card,
            fg=self.text,
        )
        value.pack(anchor="w", pady=(4, 6))

        bar = ttk.Progressbar(card, maximum=100)
        bar.pack(fill=tk.X)

        return value, bar

    def _open_network_adapters(self) -> None:
        try:
            subprocess.Popen(["control", "ncpa.cpl"], shell=True)
        except OSError as exc:
            messagebox.showerror("Errore", f"Impossibile aprire le schede di rete: {exc}")

    def _show_ip_info(self) -> None:
        private_ip = self._get_private_ip()
        public_ip = self._get_public_ip()
        messagebox.showinfo(
            "IP pubblico/privato",
            f"IP privato: {private_ip}\nIP pubblico: {public_ip}",
        )

    def _get_private_ip(self) -> str:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except OSError:
            return "Non disponibile"

    def _get_public_ip(self) -> str:
        try:
            with urlopen("https://api.ipify.org", timeout=4) as response:
                return response.read().decode("utf-8")
        except OSError:
            return "Non disponibile"

    def _refresh_stats(self) -> None:
        if psutil is None:
            self.cpu_label.configure(text="psutil non installato")
            self.net_label.configure(text="psutil non installato")
            self.disk_label.configure(text="psutil non installato")
            self.cpu_bar["value"] = 0
            self.net_bar["value"] = 0
            self.disk_bar["value"] = 0
            return

        cpu_percent = psutil.cpu_percent(interval=None)
        net_io = psutil.net_io_counters()
        disk_usage = psutil.disk_usage(os.path.abspath(os.sep))

        net_percent = min((net_io.bytes_sent + net_io.bytes_recv) / (1024 ** 2), 100)

        self.cpu_label.configure(text=f"Utilizzo CPU: {cpu_percent:.0f}%")
        self.net_label.configure(text=f"Traffico rete: {net_percent:.1f} MB")
        self.disk_label.configure(text=f"Utilizzo disco: {disk_usage.percent:.0f}%")

        self.cpu_bar["value"] = cpu_percent
        self.net_bar["value"] = net_percent
        self.disk_bar["value"] = disk_usage.percent

        self.root.after(1000, self._refresh_stats)


if __name__ == "__main__":
    app_root = tk.Tk()
    app = SystemMonitorApp(app_root)
    app_root.mainloop()
