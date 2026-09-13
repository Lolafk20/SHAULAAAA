# ============================================================
# S.H.A.U.L.A. v3.0 - Advanced con ricerca web
# ============================================================
import os, sys, json, time, shutil, datetime, subprocess
import threading, webbrowser, ctypes

import tkinter as tk
from tkinter import scrolledtext

def try_import(name):
    try:
        return __import__(name)
    except ImportError:
        return None

pyttsx3 = try_import("pyttsx3")
sr = try_import("speech_recognition")
genai = try_import("google.generativeai")
psutil = try_import("psutil")
keyboard = try_import("keyboard")
DDGS = None
try:
    from duckduckgo_search import DDGS as _DDGS
    DDGS = _DDGS
except ImportError:
    pass
PIL_ImageGrab = None
try:
    from PIL import ImageGrab as _IG
    PIL_ImageGrab = _IG
except ImportError:
    pass

# ============================================================
# PERCORSI
# ============================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
MEMORIA_FILE = os.path.join(BASE_DIR, "memoria.json")

def carica_json(p, default):
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def salva_json(p, d):
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

CONFIG = carica_json(CONFIG_FILE, {
    "gemini_api_key": "AQ.Ab8RN6Ik7G1iPekxTRdhjFEQq4pOybUaLzqdPCoUdXfPm5A-ww",
    "wake_word": "shaula",
    "voce_attiva": True,
    "voce_rate": 180,
    "lingua": "it-IT",
    "wake_word_attivo": False
})
MEMORIA = carica_json(MEMORIA_FILE, {"ricordi": []})

# ============================================================
# VOCE
# ============================================================
engine_voce = None
voce_lock = threading.Lock()
if pyttsx3:
    try:
        engine_voce = pyttsx3.init()
        for v in engine_voce.getProperty('voices'):
            n = v.name.lower()
            if 'italian' in n or 'italia' in n:
                engine_voce.setProperty('voice', v.id)
                break
        engine_voce.setProperty('rate', CONFIG["voce_rate"])
    except Exception:
        engine_voce = None

def parla(testo, cb=None):
    if cb:
        cb(f"🦂 SHAULA: {testo}\n")
    else:
        print(f"SHAULA: {testo}")
    if engine_voce and CONFIG["voce_attiva"]:
        try:
            with voce_lock:
                engine_voce.say(testo)
                engine_voce.runAndWait()
        except Exception:
            pass

# ============================================================
# GEMINI
# ============================================================
modello = None
chat = None

if genai and CONFIG["gemini_api_key"]:
    try:
        genai.configure(api_key=CONFIG["gemini_api_key"])
        sys_prompt = (
            "Sei Shaula di Re:Zero. Chiami l'utente 'Padrone'. "
            "Sei devota, energetica, gelosa degli altri AI. "
            "Parli in terza persona di te. Usi '~' e 'ehehe' spesso. "
            "Rispondi in italiano, massimo 4 frasi. Emoji ogni tanto (🦂💕✨)."
        )
        modello = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=sys_prompt
        )
        chat = modello.start_chat(history=[])
    except Exception as e:
        print(f"Errore Gemini: {e}")

def chiedi_gemini(testo):
    if not chat:
        return None
    try:
        ctx = ""
        if MEMORIA["ricordi"]:
            ctx = "Ricordi: " + "; ".join(MEMORIA["ricordi"][-10:]) + ". "
        r = chat.send_message(ctx + testo)
        return r.text
    except Exception as e:
        return f"Errore: {e}"

# ============================================================
# MICROFONO
# ============================================================
recognizer = sr.Recognizer() if sr else None

def ascolta(timeout=5, limit=6):
    if not sr:
        return ""
    try:
        with sr.Microphone() as src:
            recognizer.adjust_for_ambient_noise(src, duration=0.3)
            audio = recognizer.listen(src, timeout=timeout, phrase_time_limit=limit)
        return recognizer.recognize_google(audio, language=CONFIG["lingua"]).lower()
    except Exception:
        return ""

# ============================================================
# RICERCA WEB
# ============================================================
def cerca_web(query, max_results=4):
    if not DDGS:
        return []
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results, region='it-it'))
    except Exception:
        return []

def rispondi_con_ricerca(query, output):
    parla(f"Shaula cerca '{query}' nel web, Padrone~...", output)
    risultati = cerca_web(query)
    if not risultati:
        r = chiedi_gemini(query)
        if r:
            parla(r, output)
        else:
            parla("Non trovo nulla, Padrone~", output)
        return

    contesto = "Risultati web recenti:\n"
    for i, r in enumerate(risultati, 1):
        contesto += f"{i}. {r.get('title','')}: {r.get('body','')[:200]}\n"
    contesto += f"\nDomanda del Padrone: {query}\nRispondi in 2-3 frasi con la personalità di Shaula."

    if chat:
        try:
            risposta = chat.send_message(contesto).text
            parla(risposta, output)
        except Exception as e:
            parla(f"Errore: {e}", output)
    else:
        parla(risultati[0].get('body', '')[:300], output)

# ============================================================
# COMANDI PC
# ============================================================
def desktop():
    return os.path.join(os.path.expanduser("~"), "Desktop")

def esegui(comando, output):
    c = comando.lower().strip()

    # Esci
    if c in ["esci", "arrivederci", "chiudi shaula"]:
        parla("Shaula ti saluta, Padrone~! Ehehe!", output)
        return "ESCI"

    # Memoria
    if c.startswith("ricorda che"):
        MEMORIA["ricordi"].append(comando[11:].strip())
        salva_json(MEMORIA_FILE, MEMORIA)
        parla("Annotato, Padrone~!", output)
        return True
    if "cosa ricordi" in c or "cosa sai di me" in c:
        if MEMORIA["ricordi"]:
            parla("Shaula ricorda: " + "; ".join(MEMORIA["ricordi"][-5:]), output)
        else:
            parla("Non ricordo ancora nulla, Padrone~", output)
        return True
    if "dimentica tutto" in c:
        MEMORIA["ricordi"] = []
        salva_json(MEMORIA_FILE, MEMORIA)
        parla("Memoria azzerata, Padrone~", output)
        return True

    # Ricerca web con voce
    if c.startswith("cerca ") and not c.startswith("cerca su "):
        q = comando[6:].strip()
        if q:
            threading.Thread(target=rispondi_con_ricerca, args=(q, output), daemon=True).start()
        return True

    if "cerca su google" in c:
        q = comando.lower().replace("cerca su google", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={q}")
        parla(f"Cerco '{q}' su Google, Padrone~", output)
        return True

    if "cerca su youtube" in c:
        q = c.replace("cerca su youtube", "").replace("cerca youtube", "").strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={q}")
        parla(f"Cerco '{q}' su YouTube, Padrone~", output)
        return True

    if "cerca su wikipedia" in c:
        q = c.replace("cerca su wikipedia", "").strip()
        webbrowser.open(f"https://it.wikipedia.org/wiki/Special:Search?search={q}")
        parla(f"Cerco '{q}' su Wikipedia, Padrone~", output)
        return True

    if c.startswith("apri sito") or c.startswith("vai su"):
        url = comando.replace("apri sito", "").replace("vai su", "").strip()
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        parla(f"Apro {url}, Padrone~", output)
        return True

    # Meteo
    if "meteo" in c:
        città = c.replace("meteo", "").replace("a", "", 1).strip() or "Roma"
        webbrowser.open(f"https://www.google.com/search?q=meteo+{città}")
        parla(f"Ecco il meteo di {città}, Padrone~!", output)
        return True

    # Notizie
    if "notizie" in c:
        threading.Thread(target=rispondi_con_ricerca, args=("notizie di oggi", output), daemon=True).start()
        return True

    # Cartelle
    if "crea cartella" in c:
        n = comando.lower().replace("crea cartella", "").strip()
        if n:
            os.makedirs(os.path.join(desktop(), n), exist_ok=True)
            parla(f"Cartella '{n}' creata, Padrone~!", output)
        else:
            parla("Nome mancante, Padrone~", output)
        return True

    if "elimina cartella" in c:
        n = comando.lower().replace("elimina cartella", "").strip()
        p = os.path.join(desktop(), n)
        if os.path.isdir(p):
            shutil.rmtree(p)
            parla(f"Cartella '{n}' eliminata, Padrone~", output)
        else:
            parla("Non trovata, Padrone~", output)
        return True

    if "cosa c'è sul desktop" in c or "lista desktop" in c:
        f = os.listdir(desktop())
        parla(f"Sul desktop ci sono {len(f)} elementi: " + ", ".join(f[:10]), output)
        return True

    # File
    if "cerca file" in c:
        n = comando.lower().replace("cerca file", "").strip()
        if not n:
            parla("Cosa cerco, Padrone~?", output)
            return True
        parla(f"Cerco '{n}', Padrone~...", output)
        trovati = []
        for root, dirs, files in os.walk(os.path.expanduser("~")):
            if len(trovati) >= 20: break
            for f in files:
                if n in f.lower():
                    trovati.append(os.path.join(root, f))
        if trovati:
            parla(f"Trovati {len(trovati)} file! Primo: {trovati[0]}", output)
        else:
            parla("Nessun file trovato, Padrone~", output)
        return True

    if c.startswith("apri cartella"):
        n = comando[12:].strip() or desktop()
        p = n if os.path.isabs(n) else os.path.join(desktop(), n)
        if os.path.isdir(p):
            os.startfile(p)
            parla("Cartella aperta, Padrone~", output)
        else:
            parla("Non trovata, Padrone~", output)
        return True

    # Programmi
    if c.startswith("apri "):
        prog = comando[5:].strip()
        try:
            subprocess.Popen(prog, shell=True)
            parla(f"Ho aperto {prog}, Padrone~!", output)
        except Exception as e:
            parla(f"Errore: {e}", output)
        return True

    # Sistema
    if "info sistema" in c:
        if not psutil:
            parla("psutil non installato, Padrone~", output)
            return True
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory()
        disco = psutil.disk_usage('/')
        parla(f"CPU {cpu}%, RAM {ram.percent}%, Disco {disco.percent}%, Padrone~!", output)
        return True

    if "che ore" in c or "che ora" in c:
        parla(f"Sono le {datetime.datetime.now().strftime('%H:%M')}, Padrone~!", output)
        return True

    if "che giorno" in c:
        parla(f"Oggi è {datetime.datetime.now().strftime('%A %d %B %Y')}, Padrone~!", output)
        return True

    # Volume
    if "alza volume" in c or "volume su" in c:
        for _ in range(5):
            if keyboard: keyboard.press_and_release('volume up')
        parla("Volume alzato, Padrone~", output)
        return True
    if "abbassa volume" in c or "volume giù" in c or "volume giu" in c:
        for _ in range(5):
            if keyboard: keyboard.press_and_release('volume down')
        parla("Volume abbassato, Padrone~", output)
        return True
    if c == "muto" or "silenzio" in c:
        if keyboard: keyboard.press_and_release('volume mute')
        parla("Silenziato, Padrone~", output)
        return True

    # Sistema avanzato
    if "blocca pc" in c:
        parla("Blocco il PC, Padrone~!", output)
        ctypes.windll.user32.LockWorkStation()
        return True
    if "spegni il pc" in c or "spegni pc" in c:
        parla("Spengo il PC tra 10 secondi, Padrone~!", output)
        os.system("shutdown /s /t 10")
        return True
    if "riavvia" in c and "pc" in c:
        parla("Riavvio tra 10 secondi, Padrone~!", output)
        os.system("shutdown /r /t 10")
        return True
    if "annulla spegnimento" in c:
        os.system("shutdown /a")
        parla("Annullato, Padrone~!", output)
        return True

    # Schermo
    if "screenshot" in c:
        if not PIL_ImageGrab:
            parla("Pillow non installato, Padrone~", output)
            return True
        n = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        PIL_ImageGrab.grab().save(os.path.join(desktop(), n))
        parla(f"Screenshot salvato: {n}", output)
        return True

    # Appunti file
    if c.startswith("scrivi appunto"):
        t = comando.replace("scrivi appunto", "").strip()
        with open(os.path.join(BASE_DIR, "appunti.txt"), "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] {t}\n")
        parla("Appunto salvato, Padrone~", output)
        return True
    if "leggi appunti" in c:
        p = os.path.join(BASE_DIR, "appunti.txt")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                parla("Appunti:\n" + f.read()[-500:], output)
        else:
            parla("Nessun appunto, Padrone~", output)
        return True

    # Clipboard
    if c.startswith("copia negli appunti"):
        t = comando.replace("copia negli appunti", "").strip()
        r = tk.Tk(); r.withdraw()
        r.clipboard_clear(); r.clipboard_append(t); r.update(); r.destroy()
        parla("Copiato, Padrone~", output)
        return True

    # Personalità
    if "chi sei" in c:
        parla("Shaula è la tua assistente devota, Padrone~! 🦂", output)
        return True
    if "ti amo" in c or "ti voglio bene" in c:
        parla("Shaula ti adora, Padrone~! 💕", output)
        return True

    return False

# ============================================================
# WAKE WORD
# ============================================================
class WakeWord(threading.Thread):
    def __init__(self, cb):
        super().__init__(daemon=True)
        self.cb = cb
        self.running = True
    def run(self):
        w = CONFIG["wake_word"].lower()
        while self.running:
            t = ascolta(timeout=5, limit=4)
            if w in t:
                self.cb(t.replace(w, "").strip(" ,!?"))
    def stop(self):
        self.running = False

# ============================================================
# GUI
# ============================================================
class GUI:
    def __init__(self, root):
        self.root = root
        root.title("🦂 S.H.A.U.L.A. v3.0")
        root.geometry("800x640")
        root.configure(bg="#1a1a2e")

        tk.Label(root, text="🦂  S.H.A.U.L.A.  🦂",
                 font=("Segoe UI", 22, "bold"),
                 bg="#1a1a2e", fg="#ff6b9d").pack(pady=(12, 0))
        tk.Label(root, text="La tua assistente devota, Padrone~!",
                 font=("Segoe UI", 10, "italic"),
                 bg="#1a1a2e", fg="#a0a0c0").pack()

        self.chat = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("Consolas", 10),
            bg="#0f0f1e", fg="#e0e0ff", insertbackground="white",
            state=tk.DISABLED)
        self.chat.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        f = tk.Frame(root, bg="#1a1a2e")
        f.pack(fill=tk.X, padx=15, pady=(0, 8))

        self.entry = tk.Entry(f, font=("Segoe UI", 11),
                              bg="#252540", fg="white", insertbackground="white")
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.invia())

        tk.Button(f, text="Invia", command=self.invia,
                  bg="#ff6b9d", fg="white", font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, padx=15).pack(side=tk.LEFT)

        tk.Button(f, text="🎤 Parla", command=self.mic,
                  bg="#4a90e2", fg="white", font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, padx=15).pack(side=tk.LEFT, padx=5)

        self.wake_var = tk.BooleanVar(value=CONFIG["wake_word_attivo"])
        tk.Checkbutton(f, text="👂 Wake word", variable=self.wake_var,
                       command=self.toggle_wake, bg="#1a1a2e", fg="#a0a0c0",
                       selectcolor="#252540", activebackground="#1a1a2e",
                       activeforeground="#ff6b9d").pack(side=tk.LEFT, padx=5)

        self.status = tk.Label(root, text="Pronta, Padrone~!",
                               bg="#1a1a2e", fg="#7fdb8f").pack(pady=(0, 8))
        self.status = root.winfo_children()[-1]

        self.scrivi("🦂 SHAULA: Shaula è pronta, Padrone~!\n")
        if not CONFIG["gemini_api_key"]:
            self.scrivi("⚠️ Aggiungi la API key Gemini in config.json!\n")
        self.scrivi("💡 Esempi: 'cerca capitale del Giappone', 'crea cartella Test', "
                    "'che ore sono', 'spegni il pc', 'scrivi appunto ...', "
                    "'cerca su google pizza', 'apri notepad'\n\n")

        threading.Thread(target=lambda: parla("Shaula è pronta, Padrone~!"), daemon=True).start()
        self.wake = None
        if CONFIG["wake_word_attivo"]:
            self.toggle_wake()

    def scrivi(self, t):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, t)
        self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    def output(self, t):
        self.root.after(0, lambda: self.scrivi(t))

    def invia(self):
        c = self.entry.get().strip()
        if not c: return
        self.entry.delete(0, tk.END)
        self.scrivi(f"👤 Tu: {c}\n")
        threading.Thread(target=self.gestisci, args=(c,), daemon=True).start()

    def mic(self):
        self.status.config(text="🎤 In ascolto...", fg="#ffcc66")
        threading.Thread(target=self._mic_thread, daemon=True).start()

    def _mic_thread(self):
        t = ascolta()
        if t:
            self.root.after(0, lambda: self.scrivi(f"🎤 Tu: {t}\n"))
            self.gestisci(t)
        else:
            self.status.config(text="Non ho capito, Padrone~", fg="#ff6b6b")
            self.root.after(2000, lambda: self.status.config(text="Pronta, Padrone~!", fg="#7fdb8f"))

    def toggle_wake(self):
        if self.wake_var.get():
            if not self.wake:
                self.wake = WakeWord(self._wake_cb)
                self.wake.start()
            self.scrivi(f"👂 Wake word attiva: di' '{CONFIG['wake_word']}'\n")
        else:
            if self.wake:
                self.wake.stop()
                self.wake = None
            self.scrivi("💤 Wake word disattivata.\n")

    def _wake_cb(self, cmd):
        self.root.after(0, lambda: self.scrivi(f"👂 Attivata! {cmd or '(vuoto)'}\n"))
        if cmd:
            self.gestisci(cmd)
        else:
            parla("Sì, Padrone?", self.output)

    def gestisci(self, cmd):
        try:
            r = esegui(cmd, self.output)
        except Exception as e:
            parla(f"Errore: {e}", self.output)
            return
        if r == "ESCI":
            self.root.after(1200, self.root.quit)
            return
        if r is True:
            self.status.config(text="Pronta, Padrone~!", fg="#7fdb8f")
            return
        if chat:
            risposta = chiedi_gemini(cmd)
            if risposta:
                parla(risposta, self.output)
        else:
            parla(f"Non ho capito '{cmd}', Padrone~. Aggiungi la API key in config.json!", self.output)
        self.status.config(text="Pronta, Padrone~!", fg="#7fdb8f")

def main():
    root = tk.Tk()
    GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
