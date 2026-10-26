
import tkinter as tk
from tkinter import ttk
import serial
import serial.tools.list_ports
import threading
import queue
import time
import re
from datetime import datetime

BG = "#080d0b"
PANEL = "#101a15"
GREEN = "#39ff88"
DIM = "#80a995"
WHITE = "#d7fbe5"
RED = "#ff5c70"
YELLOW = "#ffd166"

COMMANDS = ["help", "status", "uptime", "memory", "chip", "scan"]


class CyberTerminal:
    def __init__(self, root):
        self.root = root
        self.root.title("POCKET CYBER // ESP32 CONTROL")
        self.root.geometry("1100x760")
        self.root.minsize(820, 620)
        self.root.configure(bg=BG)

        self.ser = None
        self.reader_thread = None
        self.stop_reader = threading.Event()
        self.rx_queue = queue.Queue()
        self.connected = False
        self.started_at = time.time()

        self.port_var = tk.StringVar()
        self.status_var = tk.StringVar(value="DISCONNECTED")
        self.input_var = tk.StringVar()

        self.build_ui()
        self.refresh_ports()
        self.root.after(100, self.process_rx)
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

        self.log("POCKET CYBER TERMINAL v2.0", GREEN)
        self.log("Live Cyber Dashboard initialized.", GREEN)
        self.log("Select your COM port and click CONNECT.", DIM)
        self.log("System ready.", GREEN)

    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=20, pady=(18, 10))

        tk.Label(
            header,
            text="▣ POCKET CYBER",
            font=("Consolas", 22, "bold"),
            fg=GREEN,
            bg=BG
        ).pack(side="left")

        tk.Label(
            header,
            text="ESP32-C3 // LIVE CYBER DASHBOARD",
            font=("Consolas", 10),
            fg=DIM,
            bg=BG
        ).pack(side="right", pady=8)

        tk.Frame(
            self.root, bg=GREEN, height=1
        ).pack(fill="x", padx=20, pady=(0, 14))

        # Connection controls
        connection = tk.Frame(self.root, bg=PANEL)
        connection.pack(fill="x", padx=20, pady=(0, 12))

        tk.Label(
            connection,
            text="DEVICE PORT",
            fg=DIM,
            bg=PANEL,
            font=("Consolas", 10)
        ).pack(side="left", padx=(12, 6), pady=12)

        self.port_box = ttk.Combobox(
            connection,
            textvariable=self.port_var,
            width=12,
            state="readonly",
            font=("Consolas", 10)
        )
        self.port_box.pack(side="left", padx=4, pady=10)

        tk.Button(
            connection,
            text="↻",
            command=self.refresh_ports,
            bg=PANEL,
            fg=GREEN,
            activebackground=BG,
            activeforeground=GREEN,
            relief="flat",
            font=("Consolas", 13),
            cursor="hand2"
        ).pack(side="left", padx=3)

        self.connect_btn = tk.Button(
            connection,
            text="CONNECT",
            command=self.toggle_connection,
            bg=GREEN,
            fg=BG,
            activebackground=WHITE,
            relief="flat",
            font=("Consolas", 10, "bold"),
            padx=15,
            pady=6,
            cursor="hand2"
        )
        self.connect_btn.pack(side="left", padx=8, pady=7)

        self.status_label = tk.Label(
            connection,
            textvariable=self.status_var,
            fg=YELLOW,
            bg=PANEL,
            font=("Consolas", 10, "bold")
        )
        self.status_label.pack(side="right", padx=14)

        # Dashboard row 1
        cards = tk.Frame(self.root, bg=BG)
        cards.pack(fill="x", padx=20, pady=(0, 8))

        self.uptime_card = self.make_card(
            cards, "HOST SESSION", "00:00:00"
        )
        self.link_card = self.make_card(
            cards, "SERIAL LINK", "OFFLINE"
        )
        self.device_uptime_card = self.make_card(
            cards, "DEVICE UPTIME", "--"
        )

        # Dashboard row 2
        metrics = tk.Frame(self.root, bg=BG)
        metrics.pack(fill="x", padx=20, pady=(0, 12))

        self.heap_card = self.make_card(
            metrics, "FREE HEAP", "--"
        )
        self.cpu_card = self.make_card(
            metrics, "CPU FREQUENCY", "--"
        )
        self.chip_card = self.make_card(
            metrics, "CHIP MODEL", "--"
        )

        # Terminal area
        terminal_frame = tk.Frame(self.root, bg=PANEL)
        terminal_frame.pack(
            fill="both", expand=True, padx=20, pady=(0, 12)
        )

        tk.Label(
            terminal_frame,
            text="  LIVE CONSOLE",
            fg=GREEN,
            bg=PANEL,
            anchor="w",
            font=("Consolas", 11, "bold")
        ).pack(fill="x", pady=(9, 4))

        self.output = tk.Text(
            terminal_frame,
            bg=BG,
            fg=WHITE,
            insertbackground=GREEN,
            selectbackground="#214b35",
            font=("Consolas", 10),
            relief="flat",
            wrap="word",
            padx=12,
            pady=10,
            state="disabled"
        )
        self.output.pack(
            fill="both", expand=True, padx=8, pady=(0, 8)
        )

        self.output.tag_config("green", foreground=GREEN)
        self.output.tag_config("dim", foreground=DIM)
        self.output.tag_config("red", foreground=RED)
        self.output.tag_config("yellow", foreground=YELLOW)
        self.output.tag_config("white", foreground=WHITE)

        # Quick command buttons
        command_frame = tk.Frame(self.root, bg=BG)
        command_frame.pack(fill="x", padx=20, pady=(0, 8))

        tk.Label(
            command_frame,
            text="QUICK COMMANDS",
            fg=DIM,
            bg=BG,
            font=("Consolas", 9)
        ).pack(anchor="w", pady=(0, 6))

        buttons = tk.Frame(command_frame, bg=BG)
        buttons.pack(fill="x")

        for command in COMMANDS:
            tk.Button(
                buttons,
                text=command.upper(),
                command=lambda c=command: self.send_command(c),
                bg=PANEL,
                fg=GREEN,
                activebackground="#214b35",
                activeforeground=WHITE,
                relief="flat",
                font=("Consolas", 9),
                padx=9,
                pady=6,
                cursor="hand2"
            ).pack(side="left", padx=(0, 6))

        # Input bar
        input_frame = tk.Frame(self.root, bg=PANEL)
        input_frame.pack(fill="x", padx=20, pady=(0, 18))

        tk.Label(
            input_frame,
            text=">",
            fg=GREEN,
            bg=PANEL,
            font=("Consolas", 14, "bold")
        ).pack(side="left", padx=(12, 7), pady=8)

        self.entry = tk.Entry(
            input_frame,
            textvariable=self.input_var,
            bg=PANEL,
            fg=WHITE,
            insertbackground=GREEN,
            relief="flat",
            font=("Consolas", 11)
        )
        self.entry.pack(
            side="left", fill="x", expand=True, pady=10
        )
        self.entry.bind(
            "<Return>", lambda event: self.send_input()
        )

        tk.Button(
            input_frame,
            text="SEND",
            command=self.send_input,
            bg=GREEN,
            fg=BG,
            activebackground=WHITE,
            relief="flat",
            font=("Consolas", 10, "bold"),
            padx=16,
            pady=6,
            cursor="hand2"
        ).pack(side="right", padx=8, pady=6)

        self.update_host_clock()

    def make_card(self, parent, title, value):
        card = tk.Frame(
            parent, bg=PANEL, padx=12, pady=10
        )
        card.pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )

        tk.Label(
            card,
            text=title,
            bg=PANEL,
            fg=DIM,
            font=("Consolas", 9)
        ).pack(anchor="w")

        value_label = tk.Label(
            card,
            text=value,
            bg=PANEL,
            fg=GREEN,
            font=("Consolas", 13, "bold"),
            anchor="w"
        )
        value_label.pack(anchor="w", pady=(5, 0))

        return value_label

    def log(self, message, tag="white"):
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.output.configure(state="normal")
        self.output.insert("end", f"[{timestamp}] ", "dim")
        self.output.insert("end", str(message) + "\n", tag)
        self.output.see("end")
        self.output.configure(state="disabled")

    @staticmethod
    def format_bytes(value):
        if value >= 1024 * 1024:
            return f"{value / (1024 * 1024):.2f} MB"
        if value >= 1024:
            return f"{value / 1024:.1f} KB"
        return f"{value} B"

    def update_telemetry(self, message):
        # Device uptime
        match = re.search(
            r"Uptime:\s*(\d+)\s*days?,\s*(\d+)\s*hours?,\s*"
            r"(\d+)\s*minutes?,\s*(\d+)\s*seconds?",
            message,
            re.IGNORECASE
        )
        if match:
            days, hours, minutes, seconds = map(
                int, match.groups()
            )
            self.device_uptime_card.configure(
                text=f"{days}d {hours}h {minutes}m {seconds}s"
            )

        # Free heap memory
        match = re.search(
            r"Free heap:\s*(\d+)\s*bytes",
            message,
            re.IGNORECASE
        )
        if match:
            self.heap_card.configure(
                text=self.format_bytes(int(match.group(1)))
            )

        # CPU frequency
        match = re.search(
            r"CPU:\s*(\d+)\s*MHz",
            message,
            re.IGNORECASE
        )
        if match:
            self.cpu_card.configure(
                text=f"{match.group(1)} MHz"
            )

        # Chip model
        match = re.search(
            r"Model:\s*(.+)",
            message,
            re.IGNORECASE
        )
        if match:
            self.chip_card.configure(
                text=match.group(1).strip()
            )

    def refresh_ports(self):
        ports = list(serial.tools.list_ports.comports())
        names = [port.device for port in ports]
        self.port_box["values"] = names

        if names and self.port_var.get() not in names:
            self.port_var.set(names[0])
        elif not names:
            self.port_var.set("")
            if hasattr(self, "output"):
                self.log(
                    "No serial ports detected. Check USB.",
                    "yellow"
                )

    def toggle_connection(self):
        if self.connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        port = self.port_var.get()

        if not port:
            self.log("Select a COM port first.", "yellow")
            self.refresh_ports()
            return

        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=115200,
                timeout=0.2,
                write_timeout=1
            )

            self.stop_reader.clear()
            self.connected = True

            self.status_var.set("CONNECTED")
            self.status_label.configure(fg=GREEN)
            self.connect_btn.configure(text="DISCONNECT")
            self.link_card.configure(text=port, fg=GREEN)

            self.log(
                f"Serial connection opened on {port}.",
                "green"
            )
            self.log(
                "Waiting for device startup output...",
                "dim"
            )

            self.reader_thread = threading.Thread(
                target=self.read_serial,
                daemon=True
            )
            self.reader_thread.start()

            # Allow the ESP32 time to restart before requesting data.
            self.root.after(
                3500, self.request_device_info
            )

        except (serial.SerialException, OSError) as exc:
            self.ser = None
            self.connected = False
            self.status_var.set("DISCONNECTED")
            self.status_label.configure(fg=YELLOW)
            self.connect_btn.configure(text="CONNECT")
            self.log(f"Connection failed: {exc}", "red")

    def read_serial(self):
        while not self.stop_reader.is_set():
            try:
                current_serial = self.ser

                if current_serial and current_serial.is_open:
                    data = current_serial.readline()

                    if data:
                        text = data.decode(
                            "utf-8", errors="replace"
                        ).rstrip()
                        self.rx_queue.put(("device", text))
                else:
                    break

            except (serial.SerialException, OSError) as exc:
                if not self.stop_reader.is_set():
                    self.rx_queue.put(("error", str(exc)))
                break

    def process_rx(self):
        try:
            while True:
                kind, message = self.rx_queue.get_nowait()

                if kind == "device":
                    if message:
                        self.update_telemetry(message)
                        self.log(message, "green")

                elif kind == "error":
                    self.log(f"Serial error: {message}", "red")
                    self.disconnect()

        except queue.Empty:
            pass

        if self.root.winfo_exists():
            self.root.after(100, self.process_rx)

    def send_command(self, command):
        if not self.connected or not self.ser:
            self.log(
                "Connect to the ESP32 before sending commands.",
                "yellow"
            )
            return

        try:
            self.ser.write(
                (command + "\n").encode("utf-8")
            )
            self.log("> " + command, "yellow")

        except (serial.SerialException, OSError) as exc:
            self.log(f"Send failed: {exc}", "red")

    def request_device_info(self):
        if not self.connected:
            return

        for command in ("status", "uptime", "memory", "chip"):
            self.send_command(command)

    def send_input(self):
        command = self.input_var.get().strip()

        if not command:
            return

        self.input_var.set("")
        self.send_command(command)

    def disconnect(self):
        self.stop_reader.set()

        old_ser = self.ser
        self.ser = None
        self.connected = False

        if old_ser:
            try:
                old_ser.close()
            except (serial.SerialException, OSError):
                pass

        self.status_var.set("DISCONNECTED")
        self.status_label.configure(fg=YELLOW)
        self.connect_btn.configure(text="CONNECT")
        self.link_card.configure(text="OFFLINE", fg=YELLOW)

        self.device_uptime_card.configure(text="--", fg=YELLOW)
        self.heap_card.configure(text="--", fg=YELLOW)
        self.cpu_card.configure(text="--", fg=YELLOW)
        self.chip_card.configure(text="--", fg=YELLOW)

        self.log("Serial connection closed.", "dim")

    def update_host_clock(self):
        elapsed = int(time.time() - self.started_at)
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.uptime_card.configure(
            text=f"{hours:02}:{minutes:02}:{seconds:02}"
        )

        self.root.after(1000, self.update_host_clock)

    def close_app(self):
        if self.connected:
            self.disconnect()

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = CyberTerminal(root)
    root.mainloop()
