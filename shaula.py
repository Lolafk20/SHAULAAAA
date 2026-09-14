# ============================================================
# S.H.A.U.L.A. v7.5 - WhatsApp veloce
# ============================================================
import os, sys, json, time, shutil, datetime, subprocess
import threading, webbrowser, ctypes, random, re, glob
import importlib
import smtplib
from ctypes import wintypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, colorchooser

def try_import(name):
    try:
        return importlib.import_module(name)
    except ImportError:
        return None

pyttsx3 = try_import("pyttsx3")
sr = try_import("speech_recognition")
genai = try_import("google.generativeai")
psutil = try_import("psutil")
keyboard = try_import("keyboard")
requests = try_import("requests")
pyautogui = try_import("pyautogui")
chess = try_import("chess")
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
PYCAW_OK = False
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCAW_OK = True
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
STORICO_FILE = os.path.join(BASE_DIR, "storico.json")
PLUGIN_FILE = os.path.join(BASE_DIR, "plugins.py")
NOTE_FILE = os.path.join(BASE_DIR, "note.json")
AGENDA_FILE = os.path.join(BASE_DIR, "agenda.json")
DIARIO_FILE = os.path.join(BASE_DIR, "diario.json")
CHROME_PROFILE_DIR = os.path.join(BASE_DIR, "_chrome_profile")
STOCKFISH_EXE = os.path.join(BASE_DIR, "stockfish.exe")

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
        return True
    except Exception:
        return False

CONFIG = carica_json(CONFIG_FILE, {
    "gemini_api_key": "",
    "gemini_model": "gemini-3.6-flash",
    "gemini_model_fallback": "gemini-3.1-flash-lite",
    "wake_word": "shaula",
    "voce_attiva": True,
    "voce_rate": 180,
    "lingua": "it-IT",
    "wake_word_attivo": False,
    "modalita": "normale",
    "nome_utente": "",
    "compleanno": "",
    "citta": "Roma",
    "gmail_user": "",
    "gmail_password": "",
    "firma_shaula": "Ciao! Io sono Shaula, il mio padrone vorrebbe dirti:",
    "diario_attivo": True,
    "diario_ogni_giorni": 3,
    "navigazione_attiva": True,
    "navigazioni_limite_giorno": 5,
    "navigazioni_usate_oggi": 0,
    "navigazioni_data": "",
    "scacchi_livello": "medio",
    "scacchi_motore": "interno"
})
MEMORIA = carica_json(MEMORIA_FILE, {"ricordi": [], "preferenze": {}, "info": {}})
STORICO = carica_json(STORICO_FILE, {"conversazioni": []})
NOTE = carica_json(NOTE_FILE, {"liste": {}, "note": []})
AGENDA = carica_json(AGENDA_FILE, {"eventi": []})
DIARIO = carica_json(DIARIO_FILE, {"pagine": [], "ultima_scrittura": ""})

# ============================================================
# SITI WEB
# ============================================================
SITI_WEB = {
    "youtube": "https://www.youtube.com", "google": "https://www.google.com",
    "facebook": "https://www.facebook.com", "instagram": "https://www.instagram.com",
    "twitter": "https://twitter.com", "x": "https://x.com",
    "tiktok": "https://www.tiktok.com", "whatsapp": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com", "mail": "https://mail.google.com",
    "netflix": "https://www.netflix.com", "spotify": "https://open.spotify.com",
    "twitch": "https://www.twitch.tv", "reddit": "https://www.reddit.com",
    "amazon": "https://www.amazon.it", "wikipedia": "https://it.wikipedia.org",
    "github": "https://github.com", "chatgpt": "https://chat.openai.com",
    "gemini": "https://gemini.google.com", "maps": "https://maps.google.com",
    "mappe": "https://maps.google.com", "traduttore": "https://translate.google.com",
    "drive": "https://drive.google.com", "calendar": "https://calendar.google.com",
    "calendario": "https://calendar.google.com", "steam": "https://store.steampowered.com",
    "telegram": "https://web.telegram.org", "discord": "https://discord.com/app",
    "linkedin": "https://www.linkedin.com", "lichess": "https://lichess.org",
    "chess.com": "https://www.chess.com",
}

PROGRAMMI_COMUNI = {
    "notepad": "notepad.exe", "blocco note": "notepad.exe",
    "calcolatrice": "calc.exe", "calc": "calc.exe",
    "cmd": "cmd.exe", "prompt": "cmd.exe",
    "powershell": "powershell.exe", "explorer": "explorer.exe",
    "esplora file": "explorer.exe", "paint": "mspaint.exe",
    "wordpad": "write.exe", "task manager": "taskmgr.exe",
    "gestione attività": "taskmgr.exe", "pannello di controllo": "control.exe",
    "impostazioni": "ms-settings:", "chrome": "chrome.exe",
    "edge": "msedge.exe", "firefox": "firefox.exe",
    "spotify": "spotify.exe", "discord": "discord.exe",
    "steam": "steam.exe", "telegram": "telegram.exe",
    "whatsapp": "whatsapp://", "word": "winword.exe",
    "excel": "excel.exe", "powerpoint": "powerpnt.exe",
}

VERBI_COMANDO = [
    "apri", "chiudi", "cerca", "crea", "elimina", "cancella", "imposta", "avvia",
    "metti", "spegni", "riavvia", "blocca", "trova", "mostra", "timer", "svegliami",
    "leggi", "scrivi", "copia", "sposta", "rinomina", "fai", "riproduci", "play",
    "pausa", "minimizza", "massimizza", "alza", "abbassa", "muto", "silenzio",
    "screenshot", "converti", "traduci", "riassumi", "ricorda", "dimentica",
    "modalità", "modalita", "processi", "pulisci", "email", "mail", "agenda",
    "evento", "nota", "lista", "whatsapp", "dì", "di", "dici", "manda", "invia",
    "messaggio", "diario", "naviga", "estrai", "navigazioni", "resetta", "cambia",
    "gioca", "scacchi", "partita", "muovi", "arrenditi"
]

def sembra_comando(testo):
    t = testo.lower().strip()
    for verbo in VERBI_COMANDO:
        if t == verbo or t.startswith(verbo + " "):
            return True
    return False

def chiave_valida(chiave):
    if not chiave: return False
    c = chiave.strip()
    return c.startswith("AIza") or c.startswith("AQ.")

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
MODELLO_ATTIVO = None
MODELLO_PRIMARIO = CONFIG.get("gemini_model", "gemini-3.6-flash")
MODELLO_FALLBACK = CONFIG.get("gemini_model_fallback", "gemini-3.1-flash-lite")

PROMPT_BASE = (
    "Sei Shaula di Re:Zero. Chiami l'utente 'Padrone'{nome}. "
    "Parli in terza persona di te. Usi '~' e 'ehehe' spesso. "
    "Rispondi in italiano, massimo 4 frasi. Emoji ogni tanto (🦂💕✨). "
    "IMPORTANTE: NON puoi eseguire azioni sul PC del Padrone. "
    "Se ti chiede di fare qualcosa, rispondi che deve dirlo come comando diretto. "
    "Hai una memoria persistente che ti viene passata nel contesto: usala sempre. "
)
PROMPT_MODALITA = {
    "normale": "Sei devota, energetica, affettuosa, leggermente possessiva.",
    "tsundere": "Fai la dura, ti nascondi dietro 'b-baka!' ma in realtà adori il Padrone.",
    "yandere": "Sei ossessivamente gelosa, possessiva, minacci dolcemente chi si avvicina.",
    "seria": "Niente 'ehehe', tono professionale, conciso, solo risposte utili."
}

def build_system_prompt():
    nome = CONFIG.get("nome_utente", "")
    nome_txt = f" di nome {nome}" if nome else ""
    mod = CONFIG.get("modalita", "normale")
    mod_txt = PROMPT_MODALITA.get(mod, PROMPT_MODALITA["normale"])
    return PROMPT_BASE.format(nome=nome_txt) + mod_txt

def _crea_modello(nome_modello):
    sys_prompt = build_system_prompt()
    m = genai.GenerativeModel(nome_modello, system_instruction=sys_prompt)
    c = m.start_chat(history=[])
    return m, c

def inizializza_gemini():
    global modello, chat, MODELLO_ATTIVO
    if not genai: return "⚠️ Libreria google-generativeai mancante"
    key = CONFIG.get("gemini_api_key", "").strip()
    if not key: return "⚠️ Nessuna API key configurata. Clicca 🔑 API Key."
    try:
        genai.configure(api_key=key)
    except Exception as e:
        return f"❌ Errore configure: {str(e)[:150]}"
    try:
        modello, chat = _crea_modello(MODELLO_PRIMARIO)
        MODELLO_ATTIVO = MODELLO_PRIMARIO
        return f"✅ Modello attivo: {MODELLO_PRIMARIO} (fallback: {MODELLO_FALLBACK})"
    except Exception:
        pass
    try:
        modello, chat = _crea_modello(MODELLO_FALLBACK)
        MODELLO_ATTIVO = MODELLO_FALLBACK
        return f"⚠️ Uso fallback: {MODELLO_FALLBACK}"
    except Exception as e:
        return f"❌ Nessun modello disponibile: {str(e)[:150]}"

def ricarica_gemini():
    if not genai or not CONFIG.get("gemini_api_key"): return
    try:
        global modello, chat
        nome = MODELLO_ATTIVO or MODELLO_PRIMARIO
        modello, chat = _crea_modello(nome)
    except Exception:
        pass

def salva_storico(utente, shaula):
    STORICO["conversazioni"].append({
        "data": datetime.datetime.now().isoformat(),
        "utente": utente, "shaula": shaula
    })
    STORICO["conversazioni"] = STORICO["conversazioni"][-500:]
    salva_json(STORICO_FILE, STORICO)

def chiedi_gemini(testo):
    global chat, MODELLO_ATTIVO, modello
    if not chat: return None
    ctx = ""
    if MEMORIA["ricordi"]:
        ctx += "Ricordi: " + "; ".join(MEMORIA["ricordi"][-10:]) + ". "
    if MEMORIA["info"]:
        ctx += "Info sul Padrone: " + json.dumps(MEMORIA["info"], ensure_ascii=False) + ". "
    try:
        r = chat.send_message(ctx + testo)
        risposta = r.text
        salva_storico(testo, risposta)
        return risposta
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower() or "exceeded" in err.lower():
            if MODELLO_ATTIVO == MODELLO_PRIMARIO:
                try:
                    modello, chat = _crea_modello(MODELLO_FALLBACK)
                    MODELLO_ATTIVO = MODELLO_FALLBACK
                    r = chat.send_message(ctx + testo)
                    risposta = r.text
                    salva_storico(testo, risposta)
                    return risposta
                except Exception:
                    return "⚠️ Quota esaurita per tutti i modelli, Padrone~"
            return "⚠️ Quota gratuita esaurita per oggi, Padrone~"
        if "API_KEY_INVALID" in err:
            return "❌ La chiave API non è valida."
        if "404" in err and "no longer available" in err:
            return "❌ Modello non più disponibile."
        return f"Errore: {err[:200]}"

def estrai_info_automatiche(testo, output):
    t = testo.lower()
    patterns = {
        r"mi chiamo (\w+)": "nome", r"il mio nome è (\w+)": "nome",
        r"abito a ([\w\s]+)": "citta", r"vivo a ([\w\s]+)": "citta",
        r"il mio compleanno è ([\w\s\d]+)": "compleanno",
        r"lavoro come ([\w\s]+)": "lavoro", r"ho (\d+) anni": "eta",
        r"mi piace ([\w\s]+)": "gusto", r"amo ([\w\s]+)": "gusto",
        r"odio ([\w\s]+)": "disgusto",
    }
    salvato = False
    for pattern, chiave in patterns.items():
        m = re.search(pattern, t)
        if m:
            MEMORIA["info"][chiave] = m.group(1).strip()
            if chiave == "nome":
                CONFIG["nome_utente"] = m.group(1).strip()
                salva_json(CONFIG_FILE, CONFIG)
            salvato = True
    if salvato:
        salva_json(MEMORIA_FILE, MEMORIA)

# ============================================================
# MICROFONO
# ============================================================
recognizer = sr.Recognizer() if sr else None

def ascolta(timeout=5, limit=6):
    if not sr: return ""
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
    if not DDGS: return []
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
        parla(r or "Non trovo nulla, Padrone~", output)
        return
    contesto = "Risultati web recenti:\n"
    for i, r in enumerate(risultati, 1):
        contesto += f"{i}. {r.get('title','')}: {r.get('body','')[:200]}\n"
    contesto += f"\nDomanda: {query}\nRispondi in 2-3 frasi con personalità Shaula."
    risposta = chiedi_gemini(contesto)
    parla(risposta or risultati[0].get('body', '')[:300], output)

# ============================================================
# SCACCHI
# ============================================================
VALORI_PEZZI = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
SIMBOLI_UNICODE = {
    'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
    'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
}

def _valuta_scacchiera(board):
    if board.is_checkmate():
        return -99999 if board.turn else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    score = 0
    for square in chess.SQUARES:
        pezzo = board.piece_at(square)
        if pezzo:
            valore = VALORI_PEZZI.get(pezzo.symbol().upper(), 0)
            if pezzo.color == chess.WHITE:
                score += valore
            else:
                score -= valore
    return score

def _minimax(board, depth, alpha, beta, maximizing):
    if depth == 0 or board.is_game_over():
        return _valuta_scacchiera(board)
    if maximizing:
        max_eval = -99999
        for move in board.legal_moves:
            board.push(move)
            eval_score = _minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha: break
        return max_eval
    else:
        min_eval = 99999
        for move in board.legal_moves:
            board.push(move)
            eval_score = _minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha: break
        return min_eval

def _mossa_motore_interno(board, profondita=3):
    migliore = None
    max_eval = -99999
    mosse = list(board.legal_moves)
    random.shuffle(mosse)
    for move in mosse:
        board.push(move)
        eval_score = _minimax(board, profondita - 1, -99999, 99999, False)
        board.pop()
        if eval_score > max_eval:
            max_eval = eval_score
            migliore = move
    return migliore

def _mossa_stockfish(board, livello="medio"):
    if not os.path.exists(STOCKFISH_EXE):
        return None
    try:
        import chess.engine
        profondita_map = {"facile": 2, "medio": 6, "difficile": 12, "maestro": 18}
        depth = profondita_map.get(livello, 6)
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_EXE)
        result = engine.play(board, chess.engine.Limit(depth=depth))
        engine.quit()
        return result.move
    except Exception as e:
        print(f"Errore Stockfish: {e}")
        return None

class ScacchieraGUI:
    def __init__(self, root, modo="vs_me", output_cb=None):
        self.root = root
        self.output = output_cb or print
        self.modo = modo
        self.board = chess.Board()
        self.casa_selezionata = None
        self.mosse_legali_da_casa = []
        self.partita_finita = False
        self.livello = CONFIG.get("scacchi_livello", "medio")
        self.motore = CONFIG.get("scacchi_motore", "interno")
        self.colore_chiaro = "#F0D9B5"
        self.colore_scuro = "#B58863"
        self.colore_selezione = "#7FB069"
        self.colore_mossa_legale = "#FFD966"
        self.colore_ultima_mossa = "#E8B923"
        self.ultima_mossa = None
        self.root.title("🦂 SHAULA - Scacchi")
        self.root.geometry("700x800")
        self.root.configure(bg="#1a1a2e")
        self._costruisci_gui()
        self._aggiorna_scacchiera()
        if self.modo == "auto" and not self.board.turn:
            self.root.after(1000, self._mossa_shaula)

    def _costruisci_gui(self):
        tk.Label(self.root, text="🦂 SHAULA - Scacchi ♟️",
                 font=("Segoe UI", 18, "bold"),
                 bg="#1a1a2e", fg="#ff6b9d").pack(pady=8)
        self.info_label = tk.Label(self.root, text="", font=("Segoe UI", 10),
                                    bg="#1a1a2e", fg="#a0a0c0")
        self.info_label.pack()
        self.canvas = tk.Canvas(self.root, width=640, height=640,
                                 bg="#0f0f1e", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self._click_scacchiera)
        f = tk.Frame(self.root, bg="#1a1a2e")
        f.pack(pady=8)
        tk.Button(f, text="🔄 Nuova partita", command=self._nuova_partita,
                  bg="#4a90e2", fg="white", font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, padx=12).pack(side=tk.LEFT, padx=4)
        tk.Button(f, text="↩️ Annulla mossa", command=self._annulla_mossa,
                  bg="#ffcc66", fg="#1a1a2e", font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, padx=12).pack(side=tk.LEFT, padx=4)
        tk.Button(f, text="🏳️ Arrenditi", command=self._arrenditi,
                  bg="#ff6b6b", fg="white", font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, padx=12).pack(side=tk.LEFT, padx=4)
        tk.Button(f, text="❌ Chiudi", command=self._chiudi,
                  bg="#7a7a7a", fg="white", font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, padx=12).pack(side=tk.LEFT, padx=4)
        tk.Label(self.root, text=f"Livello: {self.livello} | Motore: {self.motore}",
                 font=("Segoe UI", 9), bg="#1a1a2e", fg="#7fdb8f").pack()

    def _coord_to_rc(self, square):
        return 7 - chess.square_rank(square), chess.square_file(square)

    def _rc_to_coord(self, row, col):
        return chess.square(col, 7 - row)

    def _aggiorna_scacchiera(self):
        self.canvas.delete("all")
        lato = 80
        for row in range(8):
            for col in range(8):
                x1, y1 = col * lato, row * lato
                x2, y2 = x1 + lato, y1 + lato
                colore = self.colore_chiaro if (row + col) % 2 == 0 else self.colore_scuro
                if self.ultima_mossa:
                    for sq in self.ultima_mossa:
                        sr, sc = self._coord_to_rc(sq)
                        if sr == row and sc == col:
                            colore = self.colore_ultima_mossa
                if self.casa_selezionata:
                    sr, sc = self._coord_to_rc(self.casa_selezionata)
                    if sr == row and sc == col:
                        colore = self.colore_selezione
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=colore, outline="")
                for mossa in self.mosse_legali_da_casa:
                    tr, tc = self._coord_to_rc(mossa.to_square)
                    if tr == row and tc == col:
                        self.canvas.create_oval(x1 + 25, y1 + 25, x2 - 25, y2 - 25,
                                                fill=self.colore_mossa_legale, outline="")
        for square in chess.SQUARES:
            pezzo = self.board.piece_at(square)
            if pezzo:
                row, col = self._coord_to_rc(square)
                x = col * lato + lato // 2
                y = row * lato + lato // 2
                symbol = SIMBOLI_UNICODE.get(pezzo.symbol(), '?')
                colore_testo = "#FFFFFF" if pezzo.color == chess.WHITE else "#000000"
                self.canvas.create_text(x, y, text=symbol,
                                        font=("Segoe UI Symbol", 54), fill=colore_testo)
        if self.board.is_checkmate():
            vincitore = "Nero" if self.board.turn else "Bianco"
            self.info_label.config(text=f"🏆 Scacco matto! Vince il {vincitore}!", fg="#7fdb8f")
            self.partita_finita = True
        elif self.board.is_stalemate():
            self.info_label.config(text="🤝 Stallo! Pareggio.", fg="#ffcc66")
            self.partita_finita = True
        elif self.board.is_check():
            turno = "Bianco" if self.board.turn else "Nero"
            self.info_label.config(text=f"⚠️ Scacco al {turno}!", fg="#ff6b6b")
        else:
            turno = "Bianco" if self.board.turn else "Nero"
            self.info_label.config(text=f"Turno: {turno}", fg="#a0a0c0")

    def _click_scacchiera(self, event):
        if self.partita_finita or self.modo == "auto": return
        if not self.board.turn: return
        col = event.x // 80; row = event.y // 80
        if not (0 <= row < 8 and 0 <= col < 8): return
        square = self._rc_to_coord(row, col)
        pezzo = self.board.piece_at(square)
        if self.casa_selezionata:
            mossa_trovata = None
            for m in self.mosse_legali_da_casa:
                if m.to_square == square:
                    mossa_trovata = chess.Move(m.from_square, m.to_square,
                                                promotion=chess.QUEEN) if m.promotion else m
                    break
            if mossa_trovata:
                self._esegui_mossa(mossa_trovata)
                self.casa_selezionata = None
                self.mosse_legali_da_casa = []
                self._aggiorna_scacchiera()
                if not self.partita_finita:
                    self.root.after(500, self._mossa_shaula)
                return
            if pezzo and pezzo.color == chess.WHITE:
                self.casa_selezionata = square
                self.mosse_legali_da_casa = [m for m in self.board.legal_moves
                                              if m.from_square == square]
                self._aggiorna_scacchiera()
                return
            self.casa_selezionata = None
            self.mosse_legali_da_casa = []
            self._aggiorna_scacchiera()
            return
        if pezzo and pezzo.color == chess.WHITE:
            self.casa_selezionata = square
            self.mosse_legali_da_casa = [m for m in self.board.legal_moves
                                          if m.from_square == square]
            self._aggiorna_scacchiera()

    def _esegui_mossa(self, mossa):
        self.ultima_mossa = (mossa.from_square, mossa.to_square)
        san = self.board.san(mossa)
        self.board.push(mossa)
        return san

    def _mossa_shaula(self):
        if self.partita_finita: return
        if self.board.turn: return
        self.info_label.config(text="🤔 Shaula sta pensando...", fg="#ffcc66")
        self.root.update()
        def _calcola():
            mossa = None
            if self.motore == "stockfish" and os.path.exists(STOCKFISH_EXE):
                mossa = _mossa_stockfish(self.board, self.livello)
            if not mossa:
                pm = {"facile": 2, "medio": 3, "difficile": 4, "maestro": 4}
                mossa = _mossa_motore_interno(self.board, pm.get(self.livello, 3))
            if mossa:
                self.root.after(0, lambda: self._esegui_mossa_shaula(mossa))
        threading.Thread(target=_calcola, daemon=True).start()

    def _esegui_mossa_shaula(self, mossa):
        san = self._esegui_mossa(mossa)
        self._aggiorna_scacchiera()
        if not self.partita_finita:
            def _commenta():
                prompt = (f"Sei Shaula di Re:Zero. Hai appena mosso '{san}' in una partita "
                          f"a scacchi. Commenta brevemente la tua mossa in una frase, con "
                          f"la tua personalità (devota, '~', 'ehehe', emoji 🦂💕). "
                          f"Non superare le 20 parole.")
                risposta = chiedi_gemini(prompt)
                if risposta: parla(risposta, self.output)
            threading.Thread(target=_commenta, daemon=True).start()

    def _nuova_partita(self):
        self.board = chess.Board()
        self.casa_selezionata = None
        self.mosse_legali_da_casa = []
        self.ultima_mossa = None
        self.partita_finita = False
        self._aggiorna_scacchiera()
        self.info_label.config(text="🔄 Nuova partita!", fg="#7fdb8f")
        if self.modo == "auto":
            self.root.after(1000, self._mossa_shaula)

    def _annulla_mossa(self):
        if len(self.board.move_stack) >= 2:
            self.board.pop(); self.board.pop()
            self.ultima_mossa = None
            self.casa_selezionata = None
            self.mosse_legali_da_casa = []
            self.partita_finita = False
            self._aggiorna_scacchiera()
            self.info_label.config(text="↩️ Mossa annullata", fg="#ffcc66")

    def _arrenditi(self):
        vincitore = "Shaula vince! 🎉" if self.board.turn else "Hai vinto tu! 🏆"
        self.info_label.config(text=f"🏳️ {vincitore}", fg="#7fdb8f")
        self.partita_finita = True

    def _chiudi(self):
        self.root.destroy()

def avvia_scacchi(modo, output):
    if not chess:
        parla("❌ Libreria 'chess' non installata!", output)
        return False
    def _apri():
        try:
            finestra = tk.Toplevel()
            ScacchieraGUI(finestra, modo=modo, output_cb=output)
            if modo == "vs_me":
                parla("Shaula è pronta a giocare! Tu Bianco, Shaula Nero. ♟️💕", output)
            else:
                parla("Shaula gioca contro se stessa! ♟️✨", output)
        except Exception as e:
            parla(f"❌ Errore scacchiera: {str(e)[:150]}", output)
    threading.Thread(target=_apri, daemon=True).start()
    return True

def imposta_livello_scacchi(livello, output):
    if livello not in ["facile", "medio", "difficile", "maestro"]:
        parla("Livelli: facile, medio, difficile, maestro", output); return False
    CONFIG["scacchi_livello"] = livello
    salva_json(CONFIG_FILE, CONFIG)
    parla(f"Livello scacchi: {livello} ♟️", output)
    return True

def imposta_motore_scacchi(motore, output):
    if motore not in ["interno", "stockfish"]:
        parla("Motori: interno, stockfish", output); return False
    CONFIG["scacchi_motore"] = motore
    salva_json(CONFIG_FILE, CONFIG)
    parla(f"Motore scacchi: {motore}", output)
    return True

# ============================================================
# NAVIGAZIONE AUTONOMA
# ============================================================
import random as _rnd

def _pausa_umana(min_sec=0.8, max_sec=2.5):
    time.sleep(_rnd.uniform(min_sec, max_sec))

def _pausa_breve():
    time.sleep(_rnd.uniform(0.3, 0.9))

def _pausa_lunga():
    time.sleep(_rnd.uniform(1.5, 3.5))

def _rileva_captcha(page):
    try:
        html = page.content().lower()
        indicatori = ["recaptcha", "hcaptcha", "cf-turnstile",
                      "challenge-platform", "g-recaptcha", "captcha",
                      "verify you are human", "verifica che sei umano",
                      "unusual traffic", "traffico insolito"]
        return any(ind in html for ind in indicatori)
    except Exception:
        return False

def _attendi_risoluzione_captcha(page, output, timeout=120):
    try:
        img_path = os.path.join(BASE_DIR, "_captcha.png")
        page.screenshot(path=img_path)
        parla("⚠️ Padrone~! C'è un CAPTCHA! Guarda Chrome, "
              "clicca 'Non sono un robot', poi aspetta. Shaula riprende da sola! 🦂", output)
    except Exception:
        parla("⚠️ CAPTCHA rilevato! Risolvilo in Chrome, Padrone~!", output)
    for _ in range(timeout):
        time.sleep(1)
        if not _rileva_captcha(page):
            parla("✅ CAPTCHA risolto! Continuo, Padrone~!", output)
            return True
    parla("⏰ Tempo scaduto, Padrone~! Chiudo il browser.", output)
    return False

def _mouse_umano(page, x, y):
    try:
        x0 = _rnd.randint(200, 800); y0 = _rnd.randint(200, 600)
        cx1 = x0 + (x - x0) * _rnd.uniform(0.2, 0.4) + _rnd.randint(-80, 80)
        cy1 = y0 + (y - y0) * _rnd.uniform(0.2, 0.4) + _rnd.randint(-80, 80)
        cx2 = x0 + (x - x0) * _rnd.uniform(0.6, 0.8) + _rnd.randint(-80, 80)
        cy2 = y0 + (y - y0) * _rnd.uniform(0.6, 0.8) + _rnd.randint(-80, 80)
        punti = _rnd.randint(25, 45)
        for i in range(punti + 1):
            t = i / punti
            x_t = ((1-t)**3 * x0 + 3*(1-t)**2*t*cx1 + 3*(1-t)*t**2*cx2 + t**3 * x)
            y_t = ((1-t)**3 * y0 + 3*(1-t)**2*t*cy1 + 3*(1-t)*t**2*cy2 + t**3 * y)
            x_t += _rnd.uniform(-1.5, 1.5); y_t += _rnd.uniform(-1.5, 1.5)
            page.mouse.move(x_t, y_t)
            time.sleep(_rnd.uniform(0.003, 0.012))
    except Exception as e:
        print(f"Errore mouse: {e}")

def _click_umano(page, x, y):
    _mouse_umano(page, x, y)
    _pausa_breve()
    if _rnd.random() < 0.4:
        time.sleep(_rnd.uniform(0.1, 0.4))
    page.mouse.click(x, y)

def _scrivi_umano(page, selettore, testo):
    try:
        elem = page.query_selector(selettore)
        if not elem: return False
        box = elem.bounding_box()
        if box:
            x = box["x"] + box["width"] * _rnd.uniform(0.3, 0.7)
            y = box["y"] + box["height"] * _rnd.uniform(0.3, 0.7)
            _click_umano(page, x, y)
            _pausa_breve()
        for i, char in enumerate(testo):
            base_delay = _rnd.uniform(0.05, 0.18)
            if i < 3: base_delay += _rnd.uniform(0.05, 0.15)
            if _rnd.random() < 0.06: base_delay += _rnd.uniform(0.3, 0.9)
            page.keyboard.type(char)
            time.sleep(base_delay)
            if _rnd.random() < 0.015 and char.isalpha() and i > 2:
                sbagliato = _rnd.choice("abcdefghijklmnopqrstuvwxyz")
                page.keyboard.type(sbagliato)
                time.sleep(_rnd.uniform(0.05, 0.15))
                page.keyboard.press("Backspace")
                time.sleep(_rnd.uniform(0.08, 0.2))
        return True
    except Exception as e:
        print(f"Errore digitazione: {e}")
        return False

def _scroll_umano(page, volte=2):
    for _ in range(volte):
        delta = _rnd.randint(150, 500)
        try: page.mouse.wheel(0, delta)
        except: pass
        time.sleep(_rnd.uniform(0.5, 1.8))
        if _rnd.random() < 0.25:
            page.mouse.wheel(0, -_rnd.randint(50, 150))
            time.sleep(_rnd.uniform(0.3, 0.8))

def _muovi_e_clicca_umano(page, testo_selettore=None, selettore=None):
    try:
        elem = None
        if selettore: elem = page.query_selector(selettore)
        elif testo_selettore:
            elem = (page.query_selector(f"text={testo_selettore}")
                    or page.query_selector(f"a:has-text('{testo_selettore}')")
                    or page.query_selector(f"button:has-text('{testo_selettore}')"))
        if not elem: return False
        box = elem.bounding_box()
        if not box: elem.click(); return True
        x = box["x"] + box["width"] * _rnd.uniform(0.3, 0.7)
        y = box["y"] + box["height"] * _rnd.uniform(0.3, 0.7)
        _click_umano(page, x, y)
        return True
    except Exception as e:
        print(f"Errore click umano: {e}")
        return False

def stato_navigazioni():
    oggi = datetime.date.today().isoformat()
    data_ultimo = CONFIG.get("navigazioni_data", "")
    limite = CONFIG.get("navigazioni_limite_giorno", 5)
    if data_ultimo != oggi:
        return f"🔄 Limite resettato per oggi! 0/{limite} navigazioni usate."
    usate = CONFIG.get("navigazioni_usate_oggi", 0)
    rimaste = limite - usate
    if rimaste <= 0: return f"🚫 Limite raggiunto! {usate}/{limite} oggi."
    elif rimaste <= 1: return f"⚠️ {usate}/{limite}. Ne resta solo 1!"
    elif rimaste <= 2: return f"⚠️ {usate}/{limite}. Ne restano {rimaste}."
    else: return f"✅ {usate}/{limite} navigazioni. Ne restano {rimaste}."

def naviga_autonomo(azione, output):
    if not CONFIG.get("navigazione_attiva", True):
        parla("La navigazione è disattivata, Padrone~!", output)
        return False
    if not genai or not CONFIG.get("gemini_api_key"):
        parla("⚠️ Serve la API key Gemini, Padrone~", output)
        return False

    oggi = datetime.date.today().isoformat()
    data_ultimo = CONFIG.get("navigazioni_data", "")
    limite = CONFIG.get("navigazioni_limite_giorno", 5)

    if data_ultimo != oggi:
        CONFIG["navigazioni_data"] = oggi
        CONFIG["navigazioni_usate_oggi"] = 0
        salva_json(CONFIG_FILE, CONFIG)

    usate = CONFIG.get("navigazioni_usate_oggi", 0)
    if usate >= limite:
        parla(f"Padrone~! Shaula ha già navigato {usate} volte oggi "
              f"(limite: {limite}). Riprenderò domani! 🦂💤", output)
        return "LIMITE"

    rimaste = limite - usate
    if rimaste <= 1:
        parla(f"⚠️ Ultima navigazione di oggi! ({usate}/{limite})", output)
    elif rimaste <= 2:
        parla(f"⚠️ Restano solo {rimaste} navigazioni oggi!", output)

    parla(f"Shaula naviga: '{azione}'... 🌐 ({usate + 1}/{limite})", output)
    CONFIG["navigazioni_usate_oggi"] = usate + 1
    salva_json(CONFIG_FILE, CONFIG)

    try:
        key = CONFIG["gemini_api_key"].strip()
        genai.configure(api_key=key)
        m = genai.GenerativeModel(MODELLO_ATTIVO or MODELLO_FALLBACK)
        prompt = f"""Sei un generatore di codice Playwright Python SINCRONO (NON async).
L'utente vuole: "{azione}"

Genera SOLO il codice Python SINCRONO (nessun commento, nessun markdown) che:
- Usa la variabile `page` già disponibile
- Compie l'azione passo passo
- Usa selettori robusti (testo visibile, role, placeholder, name)
- Tra le azioni usa SEMPRE una di queste funzioni helper già definite:
  * `_pausa_breve()` - pausa breve
  * `_pausa_umana()` - pausa di riflessione
  * `_scroll_umano(page)` - scroll naturale
  * `_scrivi_umano(page, selettore, testo)` - scrittura umana in un campo
  * `_muovi_e_clicca_umano(page, testo_selettore='...')` - click su testo
- Usa `page.goto(url)` per navigare
- Aspetta il caricamento con `page.wait_for_timeout(2000)`
- Massimo 15 righe di codice
- Alla fine, salva una variabile `result` con un riassunto testuale (max 200 caratteri)

REGOLE FONDAMENTALI:
- Scrivi SOLO codice Python SINCRONO
- NON usare MAI `await`
- NON usare MAI `async def`
- NON usare MAI `async with`
- NON usare MAI `async for`
- NON usare MAI `asyncio`
- Niente markdown, niente ```python, niente spiegazioni
- Inizia direttamente con page.xxx o con _pausa_breve()

Esempio corretto:
page.goto("https://www.google.com")
_pausa_breve()
page.fill("textarea[name=q]", "meteo roma")
page.keyboard.press("Enter")
_pausa_umana()
result = "Cercato meteo roma su Google"
"""
        r = m.generate_content(prompt)
        codice = r.text.strip()
        codice = re.sub(r"^```python\s*", "", codice)
        codice = re.sub(r"^```\s*", "", codice)
        codice = re.sub(r"\s*```$", "", codice)
        codice = codice.strip()

        codice = re.sub(r"\bawait\s+", "", codice)
        codice = re.sub(r"\basync\s+def\s+", "def ", codice)
        codice = re.sub(r"\basync\s+with\s+", "with ", codice)
        codice = re.sub(r"\basync\s+for\s+", "for ", codice)
        codice = re.sub(r"asyncio\.run\([^)]*\)", "", codice)
        codice = re.sub(r"import\s+asyncio\s*\n?", "", codice)

        print(f"Codice navigazione (fixato):\n{codice}")
    except Exception as e:
        parla(f"❌ Errore piano: {str(e)[:150]}", output)
        return False

    def _esegui():
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = None
                try:
                    browser = p.chromium.launch_persistent_context(
                        user_data_dir=CHROME_PROFILE_DIR, headless=False,
                        channel="chrome",
                        args=["--disable-blink-features=AutomationControlled"],
                        locale="it-IT", timezone_id="Europe/Rome",
                        viewport={"width": 1366, "height": 768})
                    page = browser.pages[0] if browser.pages else browser.new_page()
                except Exception:
                    browser = p.chromium.launch(headless=False,
                        args=["--disable-blink-features=AutomationControlled"])
                    page = browser.new_page()

                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.chrome = {runtime: {}};
                """)

                namespace = {"page": page, "result": None, "time": time,
                             "_rnd": _rnd, "_pausa_breve": _pausa_breve,
                             "_pausa_umana": _pausa_umana,
                             "_pausa_lunga": _pausa_lunga,
                             "_scroll_umano": _scroll_umano,
                             "_scrivi_umano": _scrivi_umano,
                             "_click_umano": _click_umano,
                             "_muovi_e_clicca_umano": _muovi_e_clicca_umano}
                try:
                    exec(codice, namespace)
                except Exception as e:
                    parla(f"❌ Errore nav: {str(e)[:150]}", output)
                    try: browser.close()
                    except: pass
                    return

                if _rileva_captcha(page):
                    if not _attendi_risoluzione_captcha(page, output):
                        try: browser.close()
                        except: pass
                        return

                risultato = namespace.get("result") or "Completato"
                parla(f"✅ {risultato}, Padrone~!", output)
                time.sleep(10)
                try: browser.close()
                except: pass
        except ImportError:
            parla("❌ Playwright non installato!", output)
        except Exception as e:
            parla(f"❌ Errore: {str(e)[:150]}", output)

    threading.Thread(target=_esegui, daemon=True).start()
    return True

def estrai_da_sito(url, cosa_estrarre, output):
    return naviga_autonomo(f"vai su {url}, {cosa_estrarre}, metti in result cosa hai trovato", output)

def screenshot_sito(url, output):
    def _thread():
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1920, "height": 1080})
                page.goto(url, timeout=30000)
                page.wait_for_timeout(2500)
                n = f"sito_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                page.screenshot(path=os.path.join(desktop(), n), full_page=True)
                browser.close()
                parla(f"✅ Screenshot salvato: {n}", output)
        except Exception as e:
            parla(f"❌ Errore: {str(e)[:150]}", output)
    threading.Thread(target=_thread, daemon=True).start()
    return True

# ============================================================
# DIARIO
# ============================================================
def _genera_pagina_diario(manuale=False):
    if not genai or not CONFIG.get("gemini_api_key"):
        return None, "⚠️ Serve la API key Gemini"
    try: genai.configure(api_key=CONFIG["gemini_api_key"].strip())
    except: pass
    giorni = CONFIG.get("diario_ogni_giorni", 3)
    soglia = datetime.datetime.now() - datetime.timedelta(days=giorni)
    conv_recenti = []
    for c in STORICO["conversazioni"]:
        try:
            if datetime.datetime.fromisoformat(c["data"]) >= soglia:
                conv_recenti.append(c)
        except: continue
    if not conv_recenti:
        return None, "Nessuna conversazione recente"
    testo_conv = "".join(f"Tu: {c['utente'][:150]}\nShaula: {c['shaula'][:150]}\n"
                        for c in conv_recenti[-30:])
    info_padrone = ""
    if MEMORIA["info"]:
        info_padrone = "Info: " + json.dumps(MEMORIA["info"], ensure_ascii=False)
    if MEMORIA["ricordi"]:
        info_padrone += "\nRicordi: " + "; ".join(MEMORIA["ricordi"][-5:])
    tipo = "su richiesta" if manuale else f"dopo {giorni} giorni"
    prompt = (f"Scrivi pagina di diario (Shaula di Re:Zero) scritta {tipo}.\n"
              f"Conversazioni:\n{testo_conv}\n{info_padrone}\n\n"
              f"Formato:\nTITOLO: ...\nUMORE: ...\nVOTO: ...\nCONTENUTO: ...")
    try:
        sys_p = "Sei Shaula. Chiami l'utente 'Padrone'. Usi '~' e 'ehehe'."
        m = genai.GenerativeModel(MODELLO_ATTIVO or MODELLO_FALLBACK, system_instruction=sys_p)
        testo = m.generate_content(prompt).text.strip()
    except Exception as e:
        return None, f"❌ Errore: {str(e)[:150]}"
    titolo, umore, voto, contenuto = "Una giornata", "felice", 8, testo
    mt = re.search(r"TITOLO:\s*(.+)", testo); titolo = mt.group(1).strip() if mt else titolo
    mu = re.search(r"UMORE:\s*(\w+)", testo); umore = mu.group(1).strip().lower() if mu else umore
    mv = re.search(r"VOTO:\s*(\d+)", testo); voto = int(mv.group(1)) if mv else voto
    mc = re.search(r"CONTENUTO:\s*(.+)", testo, re.DOTALL)
    contenuto = mc.group(1).strip() if mc else testo
    pagina = {"data": datetime.date.today().isoformat(),
              "ora": datetime.datetime.now().strftime("%H:%M"),
              "titolo": titolo, "umore": umore, "voto": voto,
              "contenuto": contenuto, "messaggi_scambiati": len(conv_recenti),
              "giorni_passati": giorni, "manuale": manuale}
    DIARIO["pagine"].append(pagina)
    DIARIO["pagine"] = DIARIO["pagine"][-365:]
    DIARIO["ultima_scrittura"] = datetime.datetime.now().isoformat()
    salva_json(DIARIO_FILE, DIARIO)
    return pagina, None

def controlla_diario_automatico(output):
    if not CONFIG.get("diario_attivo", True): return
    if not CONFIG.get("gemini_api_key"): return
    giorni = CONFIG.get("diario_ogni_giorni", 3)
    ultima = DIARIO.get("ultima_scrittura", "")
    if ultima:
        try:
            if (datetime.datetime.now() - datetime.datetime.fromisoformat(ultima)).days < giorni:
                return
        except: pass
    pagina, _ = _genera_pagina_diario(manuale=False)
    if pagina:
        parla(f"Padrone~! Ho scritto '{pagina['titolo']}' nel diario! 💕", output)

def leggi_pagina_diario(pagina, output):
    parla(f"📔 {pagina['data']} — {pagina['titolo']}\n"
          f"Umore: {pagina['umore']} | Voto: {pagina['voto']}/10\n\n{pagina['contenuto']}", output)

def statistiche_diario():
    if not DIARIO["pagine"]: return "Il diario è vuoto, Padrone~"
    pagine = DIARIO["pagine"]
    totale = len(pagine)
    voto_medio = sum(p.get("voto", 5) for p in pagine) / totale
    umori = {}
    for p in pagine:
        u = p.get("umore", "?")
        umori[u] = umori.get(u, 0) + 1
    umore_top = max(umori, key=umori.get) if umori else "?"
    return (f"📊 Diario:\n• Pagine: {totale}\n• Voto medio: {voto_medio:.1f}/10\n"
            f"• Umore: {umore_top}\n• Ultima: {pagine[-1]['data']}")

# ============================================================
# WHATSAPP DESKTOP - v7.5 (tempi ridotti)
# ============================================================
VK_CODES = {'enter': 0x0D, 'tab': 0x09, 'esc': 0x1B, 'escape': 0x1B,
    'space': 0x20, 'backspace': 0x08, 'delete': 0x2E,
    'down': 0x28, 'up': 0x26, 'left': 0x25, 'right': 0x27,
    'ctrl': 0x11, 'control': 0x11, 'shift': 0x10, 'alt': 0x12,
    'win': 0x5B, 'windows': 0x5B, 'f': 0x46, 'a': 0x41, 'c': 0x43,
    'v': 0x56, 'x': 0x58, 'd': 0x44, 's': 0x53, 'z': 0x5A,
    'w': 0x57, 'q': 0x51}
KEYEVENTF_KEYUP = 0x0002

def _char_to_vk(ch):
    ch_up = ch.upper()
    if 'A' <= ch_up <= 'Z':
        return ord(ch_up)
    if '0' <= ch_up <= '9':
        return ord(ch_up)
    mappa = {
        ' ': 0x20, '.': 0xBE, ',': 0xBC, ';': 0xBA, ':': 0xBA,
        "'": 0xDE, '!': 0x31, '?': 0xBF, '-': 0xBD, '_': 0xBD,
        '@': 0x32, '#': 0x33, '$': 0x34, '%': 0x35, '&': 0x37,
        '*': 0x38, '+': 0xBB, '=': 0xBB, '/': 0xBF, '\\': 0xDC,
        '(': 0x39, ')': 0x30, '[': 0xDB, ']': 0xDD, '{': 0xDB,
        '}': 0xDD, '<': 0xBC, '>': 0xBE, '"': 0xDE,
        'à': 0xC0, 'è': 0xC8, 'é': 0xC9, 'ì': 0xCC, 'ò': 0xD2, 'ù': 0xD9,
    }
    return mappa.get(ch, mappa.get(ch_up, 0))

def _win_key_down(vk): ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
def _win_key_up(vk): ctypes.windll.user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
def _win_press(vk):
    _win_key_down(vk); time.sleep(0.02); _win_key_up(vk)

def _win_combo(vks):
    for vk in vks:
        _win_key_down(vk); time.sleep(0.012)
    time.sleep(0.02)
    for vk in reversed(vks):
        _win_key_up(vk); time.sleep(0.012)

def _scrivi_con_tastiera(testo):
    for char in testo:
        vk = _char_to_vk(char)
        if vk == 0:
            continue
        richiede_shift = (char.isupper() or char in '!?@#$%^&*()_+{}|:"<>~')
        if richiede_shift:
            _win_combo([VK_CODES['shift'], vk])
        else:
            _win_press(vk)
        time.sleep(_rnd.uniform(0.008, 0.025))

def _trova_finestra_whatsapp():
    try:
        user32 = ctypes.windll.user32
        handles = []
        def enum_cb(hwnd, lParam):
            try:
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    titolo = buf.value
                    if titolo and ("WhatsApp" in titolo or "whatsapp" in titolo):
                        if user32.IsWindowVisible(hwnd):
                            handles.append(hwnd)
            except Exception:
                pass
            return True
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        return handles[0] if handles else None
    except Exception as e:
        print(f"Errore ricerca finestra: {e}")
        return None

def _porta_whatsapp_in_primo_piano():
    try:
        hwnd = _trova_finestra_whatsapp()
        if not hwnd:
            return False
        user32 = ctypes.windll.user32
        user32.ShowWindow(hwnd, 9)
        time.sleep(0.3)
        try:
            user32.SetForegroundWindow(hwnd)
        except Exception:
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
        time.sleep(0.4)
        return True
    except Exception as e:
        print(f"Errore primo piano: {e}")
        return False

def invia_whatsapp_shaula(contatto, messaggio_utente, output):
    firma = CONFIG.get("firma_shaula", "Ciao! Io sono Shaula, il mio padrone vorrebbe dirti:")
    msg = f"{firma} {messaggio_utente}" if firma else messaggio_utente

    parla(f"Shaula apre WhatsApp per {contatto}... 💕", output)

    try:
        hwnd = _trova_finestra_whatsapp()
        if not hwnd:
            try:
                os.startfile("whatsapp://")
            except Exception:
                parla("❌ WhatsApp Desktop non trovato!", output)
                return False
            time.sleep(5)
        else:
            _porta_whatsapp_in_primo_piano()
            time.sleep(1)

        if not _porta_whatsapp_in_primo_piano():
            parla("❌ Non riesco a portare WhatsApp in primo piano!", output)
            return False
        time.sleep(0.4)

        parla(f"🔍 Cerco '{contatto}'...", output)
        _win_combo([VK_CODES['ctrl'], VK_CODES['f']])
        time.sleep(0.7)

        _win_combo([VK_CODES['ctrl'], VK_CODES['a']])
        time.sleep(0.15)
        _win_press(VK_CODES['delete'])
        time.sleep(0.2)

        _scrivi_con_tastiera(contatto)
        time.sleep(1.2)

        _win_press(VK_CODES['down'])
        time.sleep(0.2)

        _win_press(VK_CODES['enter'])
        time.sleep(1.5)

        _win_press(VK_CODES['tab'])
        time.sleep(0.4)

        parla("✍️ Scrivo il messaggio...", output)
        _scrivi_con_tastiera(msg)
        time.sleep(0.6)

        _win_press(VK_CODES['enter'])
        time.sleep(0.4)

        parla(f"✅ Messaggio inviato a {contatto}, Padrone~! 💕", output)
        return True
    except Exception as e:
        parla(f"❌ Errore WhatsApp: {str(e)[:150]}", output)
        return False

# ============================================================
# EMAIL
# ============================================================
def invia_email(destinatario, oggetto, corpo):
    user = CONFIG.get("gmail_user", "").strip()
    pwd = CONFIG.get("gmail_password", "").strip()
    if not user or not pwd: return "⚠️ Configura Gmail"
    try:
        msg = MIMEMultipart()
        msg['From'] = user; msg['To'] = destinatario; msg['Subject'] = oggetto
        msg.attach(MIMEText(corpo, 'plain', 'utf-8'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls(); server.login(user, pwd)
        server.send_message(msg); server.quit()
        return f"✅ Email inviata a {destinatario}"
    except Exception as e:
        return f"❌ Errore: {str(e)[:150]}"

# ============================================================
# AUDIO
# ============================================================
def cambia_volume(delta):
    if PYCAW_OK:
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            attuale = volume.GetMasterVolumeLevelScalar()
            volume.SetMasterVolumeLevelScalar(max(0.0, min(1.0, attuale + delta)), None)
            return True
        except: pass
    if keyboard:
        for _ in range(abs(int(delta * 50))):
            keyboard.press_and_release('volume up' if delta > 0 else 'volume down')
        return True
    return False

def toggle_mute():
    if PYCAW_OK:
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMute(not volume.GetMute(), None); return True
        except: pass
    if keyboard: keyboard.press_and_release('volume mute'); return True
    return False

def cambia_volume_app(nome_app, delta):
    if not PYCAW_OK: return False
    try:
        for s in AudioUtilities.GetAllSessions():
            if s.Process and nome_app.lower() in s.Process.name().lower():
                v = s.SimpleAudioVolume
                v.SetMasterVolume(max(0.0, min(1.0, v.GetMasterVolume() + delta)), None)
                return True
        return False
    except: return False

def muta_app(nome_app):
    if not PYCAW_OK: return False
    try:
        for s in AudioUtilities.GetAllSessions():
            if s.Process and nome_app.lower() in s.Process.name().lower():
                s.SimpleAudioVolume.SetMute(not s.SimpleAudioVolume.GetMute(), None)
                return True
        return False
    except: return False

def lista_app_audio():
    if not PYCAW_OK: return []
    try: return list(set(s.Process.name() for s in AudioUtilities.GetAllSessions() if s.Process))
    except: return []

def media_key(tasto):
    if keyboard:
        try: keyboard.press_and_release(tasto); return True
        except: pass
    return False

# ============================================================
# PROCESSI
# ============================================================
def lista_processi(ordine="ram", limite=10):
    if not psutil: return "psutil mancante"
    try:
        procs = list(psutil.process_iter(['name', 'memory_percent', 'cpu_percent']))
        if ordine == "ram":
            procs.sort(key=lambda x: x.info.get('memory_percent', 0) or 0, reverse=True)
        else:
            procs.sort(key=lambda x: x.info.get('cpu_percent', 0) or 0, reverse=True)
        return "\n".join(f"{p.info.get('name','?')}: RAM {p.info.get('memory_percent',0):.1f}%, CPU {p.info.get('cpu_percent',0):.1f}%"
                         for p in procs[:limite])
    except Exception as e: return f"Errore: {e}"

def chiudi_processo(nome):
    if not psutil: return False
    chiusi = 0
    for p in psutil.process_iter(['name']):
        try:
            if p.info['name'] and nome.lower() in p.info['name'].lower():
                p.terminate(); chiusi += 1
        except: continue
    return chiusi > 0

def pulisci_temp():
    try:
        temp_dir = os.environ.get('TEMP', r'C:\Windows\Temp')
        eliminati, errori = 0, 0
        for f in os.listdir(temp_dir):
            percorso = os.path.join(temp_dir, f)
            try:
                if os.path.isfile(percorso): os.remove(percorso); eliminati += 1
                elif os.path.isdir(percorso): shutil.rmtree(percorso, ignore_errors=True); eliminati += 1
            except: errori += 1
        return eliminati, errori
    except Exception as e: return 0, str(e)

def info_disco_dettagliato():
    if not psutil: return "psutil mancante"
    try:
        return "\n".join(f"{p.device}: {psutil.disk_usage(p.mountpoint).percent}% usato"
                         for p in psutil.disk_partitions())
    except: return "Errore"

def modalita_risparmio():
    try: subprocess.run("powercfg /setactive a1841308-3541-4fab-bc81-f71556f20b4a", shell=True, capture_output=True); return True
    except: return False
def modalita_prestazioni():
    try: subprocess.run("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", shell=True, capture_output=True); return True
    except: return False
def modalita_bilanciata():
    try: subprocess.run("powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e", shell=True, capture_output=True); return True
    except: return False

# ============================================================
# AGENDA E NOTE
# ============================================================
def aggiungi_evento(titolo, quando):
    AGENDA["eventi"].append({"titolo": titolo, "quando": quando,
                             "creato": datetime.datetime.now().isoformat()})
    salva_json(AGENDA_FILE, AGENDA); return True

def eventi_oggi():
    oggi = datetime.date.today().isoformat()
    return [e for e in AGENDA["eventi"] if oggi in e.get("quando", "")]

def aggiungi_nota(testo, categoria="generale"):
    if categoria not in NOTE["liste"]: NOTE["liste"][categoria] = []
    NOTE["liste"][categoria].append({"testo": testo,
                                     "data": datetime.datetime.now().isoformat()})
    salva_json(NOTE_FILE, NOTE); return True

def leggi_lista(categoria="generale"):
    return NOTE["liste"].get(categoria, [])

def avvia_timer(secondi, descrizione, output):
    def _t():
        time.sleep(secondi)
        parla(f"Padrone~! È ora! {descrizione}", output)
    threading.Thread(target=_t, daemon=True).start()

# ============================================================
# VISIONE
# ============================================================
def analizza_schermo(output):
    if not PIL_ImageGrab:
        parla("Pillow non installato!", output); return
    if not genai or not CONFIG.get("gemini_api_key"):
        parla("Serve la API key Gemini!", output); return
    try:
        img = PIL_ImageGrab.grab()
        p = os.path.join(BASE_DIR, "_temp_screen.png")
        img.save(p)
        from PIL import Image as _PILImage
        img_pil = _PILImage.open(p)
        vision_model = genai.GenerativeModel(MODELLO_ATTIVO or MODELLO_FALLBACK)
        prompt = "Descrivi cosa vedi in 3 frasi con personalità Shaula. Leggi testo importante."
        risposta = vision_model.generate_content([prompt, img_pil])
        parla(risposta.text, output)
        try: os.remove(p)
        except: pass
    except Exception as e:
        parla(f"Errore: {str(e)[:150]}", output)

# ============================================================
# COMANDI
# ============================================================
def desktop():
    return os.path.join(os.path.expanduser("~"), "Desktop")

def esegui(comando, output):
    comando = re.sub(rf"^\s*{re.escape(CONFIG.get('wake_word', 'shaula'))}\s*[,!?.]?\s*",
                     "", comando, flags=re.IGNORECASE)
    c = comando.lower().strip()
    cl = comando.strip()

    if c in ["esci", "arrivederci", "chiudi shaula"]:
        parla("Shaula ti saluta, Padrone~! Ehehe!", output)
        return "ESCI"
    if c == "":
        parla("Dimmi, Padrone~!", output); return True

    estrai_info_automatiche(cl, output)

    # ---- SCACCHI ----
    if any(p in c for p in ["gioca a scacchi", "giochiamo a scacchi", "partita a scacchi",
                              "apri scacchi", "avvia scacchi"]):
        if "contro di me" in c or "con me" in c or "insieme a me" in c:
            avvia_scacchi("vs_me", output)
        elif "da sola" in c or "auto" in c or "contro se stessa" in c or "sola" in c:
            avvia_scacchi("auto", output)
        else:
            avvia_scacchi("vs_me", output)
        return True

    if "livello scacchi" in c:
        for liv in ["facile", "medio", "difficile", "maestro"]:
            if liv in c:
                imposta_livello_scacchi(liv, output); return True
        parla("Livelli: facile, medio, difficile, maestro", output); return True

    if "motore scacchi" in c:
        if "stockfish" in c:
            imposta_motore_scacchi("stockfish", output); return True
        elif "interno" in c:
            imposta_motore_scacchi("interno", output); return True
        parla("Motori: interno, stockfish", output); return True

    # ---- NAVIGAZIONI ----
    if "navigazioni" in c and any(w in c for w in ["quante", "stato", "limite", "rimaste", "restano"]):
        parla(stato_navigazioni(), output); return True

    if "resetta" in c and "navigazioni" in c:
        CONFIG["navigazioni_usate_oggi"] = 0
        CONFIG["navigazioni_data"] = datetime.date.today().isoformat()
        salva_json(CONFIG_FILE, CONFIG)
        parla("Contatore navigazioni resettato!", output); return True

    if "cambia limite" in c and "navigazioni" in c:
        m = re.search(r"(\d+)", c)
        if m:
            CONFIG["navigazioni_limite_giorno"] = int(m.group(1))
            salva_json(CONFIG_FILE, CONFIG)
            parla(f"Limite: {m.group(1)}/giorno", output)
        else:
            parla("Dimmi: 'cambia limite navigazioni a 10'", output)
        return True

    # ---- NAVIGAZIONE AUTONOMA ----
    m = re.search(r"^naviga su\s+(.+?)\s+e\s+(.+)$", cl, re.IGNORECASE)
    if m:
        threading.Thread(target=naviga_autonomo,
                         args=(f"vai su {m.group(1).strip()} e {m.group(2).strip()}", output),
                         daemon=True).start()
        return True

    m = re.search(r"^naviga\s+(https?://[^\s]+)\s+e\s+(.+)$", cl, re.IGNORECASE)
    if m:
        threading.Thread(target=naviga_autonomo,
                         args=(f"vai su {m.group(1).strip()} e {m.group(2).strip()}", output),
                         daemon=True).start()
        return True

    m = re.search(r"^estrai\s+(.+?)\s+da\s+(https?://[^\s]+)$", cl, re.IGNORECASE)
    if m:
        threading.Thread(target=estrai_da_sito,
                         args=(m.group(2).strip(), m.group(1).strip(), output),
                         daemon=True).start()
        return True

    m = re.search(r"^screenshot (?:di|del sito)\s+(https?://[^\s]+)$", cl, re.IGNORECASE)
    if m:
        screenshot_sito(m.group(1).strip(), output); return True

    # ---- DIARIO ----
    if "scrivi" in c and "diario" in c:
        parla("Shaula scrive, Padrone~... 📔", output)
        def _s():
            p, e = _genera_pagina_diario(manuale=True)
            if p: parla(f"Fatto! '{p['titolo']}' Voto: {p['voto']}/10! 💕", output)
            else: parla(e or "Non riesco, Padrone~", output)
        threading.Thread(target=_s, daemon=True).start()
        return True
    if ("leggi" in c or "mostra" in c or "apri" in c) and "diario" in c:
        if not DIARIO["pagine"]:
            parla("Diario vuoto!", output); return True
        leggi_pagina_diario(DIARIO["pagine"][-1], output); return True
    if "diario di ieri" in c:
        if len(DIARIO["pagine"]) >= 2: leggi_pagina_diario(DIARIO["pagine"][-2], output)
        else: parla("Non ho abbastanza pagine", output)
        return True
    if "statistiche diario" in c:
        parla(statistiche_diario(), output); return True
    if "cancella diario" in c or "azzera diario" in c:
        DIARIO["pagine"] = []; DIARIO["ultima_scrittura"] = ""
        salva_json(DIARIO_FILE, DIARIO)
        parla("Diario azzerato!", output); return True
    if "quante pagine" in c and "diario" in c:
        parla(f"{len(DIARIO['pagine'])} pagine!", output); return True

    # ---- MODALITÀ ----
    if "modalità" in c or "modalita" in c:
        for mod in ["normale", "tsundere", "yandere", "seria"]:
            if mod in c:
                CONFIG["modalita"] = mod; salva_json(CONFIG_FILE, CONFIG)
                ricarica_gemini()
                parla(f"Modalità {mod}!", output); return True
        parla("Modalità: normale, tsundere, yandere, seria", output); return True

    # ---- MEMORIA ----
    if c.startswith("ricorda che"):
        MEMORIA["ricordi"].append(cl[11:].strip())
        salva_json(MEMORIA_FILE, MEMORIA)
        parla("Annotato!", output); return True
    if "cosa ricordi" in c or "cosa sai di me" in c:
        msg = ""
        if MEMORIA["info"]: msg += "Info: " + ", ".join(f"{k}={v}" for k, v in MEMORIA["info"].items()) + ". "
        if MEMORIA["ricordi"]: msg += "Ricordi: " + "; ".join(MEMORIA["ricordi"][-5:])
        parla(msg or "Non ricordo nulla", output); return True
    if "dimentica tutto" in c:
        MEMORIA = {"ricordi": [], "preferenze": {}, "info": {}}
        salva_json(MEMORIA_FILE, MEMORIA)
        parla("Memoria azzerata!", output); return True

    # ---- WHATSAPP ----
    verbi_wa = r"(?:dì|di|dici|manda|invia|scrivi|messaggio)"
    m1 = re.search(rf"^{verbi_wa}\s+(?:un\s+)?(?:messaggio\s+)?(?:whatsapp\s+)?(?:a|ad|al|alla)\s+(?:il\s+contatto\s+|contatto\s+|il\s+|la\s+)?(.+?)\s*(?:che|:)\s*(.+)$", cl, re.IGNORECASE)
    m2 = None
    if not m1:
        m2 = re.search(rf"^{verbi_wa}\s+(?:un\s+)?(?:messaggio\s+)?(?:whatsapp\s+)?(?:a|ad|al|alla)\s+(?:il\s+contatto\s+|contatto\s+|il\s+|la\s+)?([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ]+)?)\s+(.+)$", cl, re.IGNORECASE)
    m = m1 or m2
    if m:
        contatto = m.group(1).strip().strip('"').strip("'")
        messaggio = m.group(2).strip()
        if len(messaggio) >= 2 and len(contatto) >= 2:
            threading.Thread(target=invia_whatsapp_shaula, args=(contatto, messaggio, output), daemon=True).start()
            return True

    if "apri whatsapp" in c or c == "whatsapp":
        try: os.startfile("whatsapp://"); parla("Apro WhatsApp!", output)
        except: webbrowser.open("https://web.whatsapp.com"); parla("Apro WhatsApp Web!", output)
        return True

    # ---- PC ----
    if "processi" in c or "cosa consuma" in c:
        ordine = "cpu" if "cpu" in c else "ram"
        parla(f"Processi per {ordine.upper()}:", output)
        parla(lista_processi(ordine, 8), output); return True
    if c.startswith("chiudi ") and ("processo" in c or "programma" in c):
        nome = cl.replace("chiudi processo", "").replace("chiudi programma", "").strip()
        if nome and chiudi_processo(nome): parla(f"Chiuso {nome}!", output)
        else: parla(f"'{nome}' non trovato", output)
        return True
    if "info disco" in c or "spazio disco" in c:
        parla("Info dischi:", output); parla(info_disco_dettagliato(), output); return True
    if "pulisci" in c and ("temp" in c or "temporanei" in c):
        parla("Pulisco...", output)
        e, _ = pulisci_temp()
        parla(f"Eliminati {e} file!", output); return True
    if "risparmio" in c: modalita_risparmio(); parla("Risparmio energetico!", output); return True
    if "prestazioni" in c: modalita_prestazioni(); parla("Prestazioni elevate!", output); return True
    if "bilanciata" in c: modalita_bilanciata(); parla("Modalità bilanciata!", output); return True
    if "app audio" in c:
        apps = lista_app_audio()
        parla("App audio: " + (", ".join(apps) if apps else "nessuna"), output); return True

    m = re.search(r"(alza|abbassa|muta|silenzia)\s+(?:il volume di\s+)?(\w+)", c)
    if m and m.group(2) not in ["volume"]:
        azione, app = m.group(1), m.group(2)
        if azione == "alza": ok = cambia_volume_app(app, 0.15)
        elif azione == "abbassa": ok = cambia_volume_app(app, -0.15)
        else: ok = muta_app(app)
        parla(f"{app}: {'fatto' if ok else 'non trovata'}", output); return True

    m = re.search(r"spegni (?:il pc )?tra (\d+)\s*(secondi|minuti|ore)", c)
    if m:
        val = int(m.group(1)); unit = m.group(2)
        sec = val if "sec" in unit else val * 60 if "min" in unit else val * 3600
        os.system(f"shutdown /s /t {sec}"); parla(f"Spegno tra {val} {unit}", output); return True

    # ---- WEB ----
    if "email" in c or "mail" in c:
        if "invia" in c or "manda" in c:
            m = re.search(r"([\w.+-]+@[\w.-]+)\s+(?:oggetto\s+)?(.+?)(?:\s+corpo\s+(.+))?$", cl)
            if m: parla(invia_email(m.group(1), m.group(2).strip() or "Messaggio",
                                     (m.group(3) or m.group(2)).strip()), output)
            else: parla("Formato: 'invia email a x@y.com oggetto Ciao corpo Testo'", output)
            return True
        webbrowser.open("https://mail.google.com"); parla("Apro Gmail!", output); return True

    if "aggiungi evento" in c:
        m = re.search(r"evento\s+(.+?)\s+(?:il|per il|domani|oggi)\s*(.*)", cl, re.IGNORECASE)
        if m:
            aggiungi_evento(m.group(1).strip(), m.group(2).strip() or datetime.date.today().isoformat())
            parla(f"Evento aggiunto!", output)
        return True
    if "cosa ho oggi" in c or "eventi oggi" in c:
        e = eventi_oggi()
        parla("Oggi: " + "\n".join(f"- {x['titolo']}" for x in e) if e else "Nessun evento", output)
        return True

    if "aggiungi a lista" in c:
        m = re.search(r"lista\s+(\w+)\s+(.+)", cl)
        if m: aggiungi_nota(m.group(2).strip(), m.group(1).lower()); parla("Aggiunto!", output)
        else:
            m2 = re.search(r"(?:a lista|alla lista)\s+(.+)", cl)
            if m2: aggiungi_nota(m2.group(1).strip()); parla("Aggiunto!", output)
        return True
    if "leggi lista" in c:
        m = re.search(r"lista\s+(\w+)", c)
        cat = m.group(1) if m else "generale"
        el = leggi_lista(cat)
        parla(f"Lista {cat}:\n" + "\n".join(f"- {e['testo']}" for e in el[-10:]) if el else f"Lista {cat} vuota", output)
        return True

    if c.startswith("traduci"):
        m = re.search(r"traduci (?:in (\w+)\s+)?(.+)", cl, re.IGNORECASE)
        if m:
            webbrowser.open(f"https://translate.google.com/?sl=auto&tl={m.group(1) or 'inglese'}&text={m.group(2).strip()}")
            parla(f"Traduco in {m.group(1) or 'inglese'}!", output)
        return True

    if "cerca su google" in c:
        q = re.sub(r"cerca (su )?google", "", c).strip()
        if q: webbrowser.open(f"https://www.google.com/search?q={q}"); parla(f"Cerco '{q}'!", output)
        return True
    if "cerca su youtube" in c or "cerca youtube" in c or "cerca yt" in c:
        q = re.sub(r"cerca (su )?(youtube|yt)", "", c).strip()
        if q: webbrowser.open(f"https://www.youtube.com/results?search_query={q}"); parla(f"Cerco '{q}'!", output)
        else: webbrowser.open("https://www.youtube.com"); parla("Apro YouTube!", output)
        return True
    if "cerca su wikipedia" in c:
        q = re.sub(r"cerca (su )?wikipedia", "", c).strip()
        if q: webbrowser.open(f"https://it.wikipedia.org/wiki/Special:Search?search={q}"); parla(f"Cerco '{q}'!", output)
        return True

    m = re.match(r"^cerca\s+(\w+)$", c)
    if m and m.group(1) in SITI_WEB:
        webbrowser.open(SITI_WEB[m.group(1)]); parla(f"Apro {m.group(1)}!", output); return True

    if c.startswith("cerca ") and not c.startswith("cerca su "):
        q = cl[6:].strip()
        if q: threading.Thread(target=rispondi_con_ricerca, args=(q, output), daemon=True).start()
        return True
    if c.startswith("apri sito") or c.startswith("vai su"):
        url = cl.replace("apri sito", "").replace("vai su", "").strip()
        if url:
            if not url.startswith("http"): url = "https://" + url
            webbrowser.open(url); parla(f"Apro {url}!", output)
        return True
    if "notizie" in c:
        threading.Thread(target=rispondi_con_ricerca, args=("notizie di oggi", output), daemon=True).start()
        return True
    if "meteo" in c or "che tempo fa" in c:
        città = CONFIG.get("citta", "Roma")
        m = re.search(r"(?:a|di|per)\s+([A-Za-zÀ-ÿ]+)", cl)
        if m: città = m.group(1)
        threading.Thread(target=rispondi_con_ricerca, args=(f"meteo {città} oggi", output), daemon=True).start()
        return True

    # ---- MUSICA ----
    parole_musica = ["metti musica", "play musica", "voglio musica", "metti su musica"]
    if any(p in c for p in parole_musica) or c == "musica":
        webbrowser.open("https://music.youtube.com/"); parla("Metto la musica!", output); return True
    if c.startswith("play ") or c.startswith("riproduci "):
        q = cl[5:] if c.startswith("play ") else cl[10:]
        if q.strip():
            webbrowser.open(f"https://music.youtube.com/search?q={q.strip()}"); parla(f"Riproduco {q}!", output)
        return True
    if "pausa musica" in c or c == "pausa": media_key('play/pause media'); parla("Pausa!", output); return True
    if "canzone successiva" in c or c == "skip": media_key('next track'); parla("Cambio!", output); return True
    if "canzone precedente" in c: media_key('previous track'); parla("Torno indietro!", output); return True

    # ---- VOLUME ----
    if any(p in c for p in ["alza volume", "alza il volume", "volume su", "aumenta volume"]):
        cambia_volume(0.10); parla("Volume alzato!", output); return True
    if any(p in c for p in ["abbassa volume", "abbassa il volume", "volume giù", "diminuisci volume"]):
        cambia_volume(-0.10); parla("Volume abbassato!", output); return True
    if any(p in c for p in ["muto", "silenzio", "muta audio"]):
        toggle_mute(); parla("Silenziato!", output); return True

    # ---- TIMER ----
    m = re.search(r"timer\D*(\d+)\s*(secondi|secondo|sec|minuti|minuto|min|ore|ora|h)\b", c)
    if m:
        val = int(m.group(1)); unit = m.group(2)
        if "sec" in unit: sec, utxt = val, f"{val} secondi"
        elif "min" in unit: sec, utxt = val * 60, f"{val} minuti"
        else: sec, utxt = val * 3600, f"{val} ore"
        avvia_timer(sec, f"Timer di {utxt} scaduto!", output)
        parla(f"Timer {utxt} avviato!", output); return True
    if "timer" in c: parla("Per quanto? 'timer 5 minuti'", output); return True

    m = re.search(r"svegliami alle (\d{1,2})[:.]?(\d{2})?", c)
    if m:
        ora = int(m.group(1)); minuto = int(m.group(2)) if m.group(2) else 0
        adesso = datetime.datetime.now()
        target = adesso.replace(hour=ora, minute=minuto, second=0, microsecond=0)
        if target <= adesso: target += datetime.timedelta(days=1)
        avvia_timer((target - adesso).total_seconds(),
                    f"Sveglia! Sono le {ora}:{minuto:02d}!", output)
        parla(f"Ti sveglierò alle {ora}:{minuto:02d}", output); return True
    if "svegliami" in c: parla("A che ora?", output); return True

    # ---- SCHERMO ----
    if "screenshot" in c and "http" not in c:
        if PIL_ImageGrab:
            n = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            PIL_ImageGrab.grab().save(os.path.join(desktop(), n))
            parla(f"Screenshot: {n}", output)
        return True
    if "cosa vedi" in c or "leggi schermo" in c:
        threading.Thread(target=analizza_schermo, args=(output,), daemon=True).start(); return True
    if "minimizza tutto" in c or "mostra desktop" in c:
        try: _win_combo([VK_CODES['win'], VK_CODES['d']])
        except:
            if keyboard: keyboard.press_and_release('windows+d')
        parla("Fatto!", output); return True
    if "chiudi finestra" in c:
        if keyboard: keyboard.press_and_release('alt+f4')
        parla("Chiusa!", output); return True
    if "modalità scura" in c or "modalita scura" in c:
        try:
            subprocess.run(["reg", "add", r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                "/v", "AppsUseLightTheme", "/t", "REG_DWORD", "/d", "0", "/f"], capture_output=True)
            parla("Tema scuro!", output)
        except: pass
        return True

    # ---- UTILITY ----
    m = re.search(r"quanto fa ([\d\s+\-*/().,%]+)", c)
    if m:
        try:
            r = eval(m.group(1).replace("%", "/100*").replace(",", "."))
            parla(f"Fa {r}!", output)
        except: parla("Non riesco a calcolare", output)
        return True
    if "quanti giorni" in c and "natale" in c:
        oggi = datetime.date.today()
        natale = datetime.date(oggi.year, 12, 25)
        if natale < oggi: natale = datetime.date(oggi.year + 1, 12, 25)
        parla(f"Mancano {(natale - oggi).days} giorni a Natale!", output); return True

    # ---- CARTELLE ----
    if "crea cartella" in c:
        n = cl.lower().replace("crea cartella", "").strip()
        if n:
            os.makedirs(os.path.join(desktop(), n), exist_ok=True)
            parla(f"Cartella '{n}' creata!", output)
        return True
    if "elimina cartella" in c:
        n = cl.lower().replace("elimina cartella", "").strip()
        p = os.path.join(desktop(), n)
        if os.path.isdir(p): shutil.rmtree(p); parla(f"Cartella '{n}' eliminata!", output)
        return True
    if "cosa c'è sul desktop" in c or "lista desktop" in c:
        f = os.listdir(desktop())
        parla(f"Desktop: {len(f)} elementi — " + ", ".join(f[:10]), output); return True
    if "cerca file" in c:
        n = cl.lower().replace("cerca file", "").strip()
        if n:
            parla(f"Cerco '{n}'...", output)
            trovati = []
            for root, dirs, files in os.walk(os.path.expanduser("~")):
                if len(trovati) >= 20: break
                for f in files:
                    if n in f.lower(): trovati.append(os.path.join(root, f))
            parla(f"Trovati {len(trovati)}! Primo: {trovati[0]}" if trovati else "Nessun file", output)
        return True

    # ---- APRI PROGRAMMI ----
    if c.startswith("apri "):
        prog = cl[5:].strip(); prog_low = prog.lower()
        if prog_low in SITI_WEB:
            webbrowser.open(SITI_WEB[prog_low]); parla(f"Apro {prog}!", output); return True
        if prog_low in PROGRAMMI_COMUNI:
            try:
                subprocess.Popen(PROGRAMMI_COMUNI[prog_low], shell=True)
                parla(f"Apro {prog}!", output)
            except: parla(f"Non riesco ad aprire {prog}", output)
            return True
        if prog_low.startswith("http") or ("." in prog_low and " " not in prog_low):
            url = prog if prog.startswith("http") else "https://" + prog
            webbrowser.open(url); parla(f"Apro {url}!", output); return True
        try:
            subprocess.Popen(prog, shell=True); parla(f"Apro {prog}!", output)
        except: parla(f"Non riesco ad aprire '{prog}'", output)
        return True

    # ---- SISTEMA ----
    if "info sistema" in c:
        if psutil:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disco = psutil.disk_usage('/')
            parla(f"CPU {cpu}%, RAM {ram.percent}%, Disco {disco.percent}%", output)
        return True
    if "che ore" in c or "che ora" in c:
        parla(f"Sono le {datetime.datetime.now().strftime('%H:%M')}", output); return True
    if "che giorno" in c:
        parla(f"Oggi è {datetime.datetime.now().strftime('%A %d %B %Y')}", output); return True
    if "blocca pc" in c:
        parla("Blocco!", output); ctypes.windll.user32.LockWorkStation(); return True
    if "spegni il pc" in c or "spegni pc" in c:
        parla("Spengo tra 10s!", output); os.system("shutdown /s /t 10"); return True
    if "riavvia" in c and "pc" in c:
        parla("Riavvio tra 10s!", output); os.system("shutdown /r /t 10"); return True
    if "annulla spegnimento" in c:
        os.system("shutdown /a"); parla("Annullato!", output); return True

    # ---- APPUNTI ----
    if c.startswith("scrivi appunto"):
        t = cl.replace("scrivi appunto", "").strip()
        if t:
            with open(os.path.join(BASE_DIR, "appunti.txt"), "a", encoding="utf-8") as f:
                f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] {t}\n")
            parla("Appunto salvato!", output)
        return True
    if "leggi appunti" in c:
        p = os.path.join(BASE_DIR, "appunti.txt")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f: parla("Appunti:\n" + f.read()[-500:], output)
        else: parla("Nessun appunto", output)
        return True

    # ---- PERSONALITÀ ----
    if "chi sei" in c: parla("Shaula è la tua assistente devota, Padrone~! 🦂", output); return True
    if "ti amo" in c or "ti voglio bene" in c: parla("Shaula ti adora, Padrone~! 💕", output); return True
    if "buonanotte" in c: parla("Buonanotte, Padrone~! 🌙💕", output); return True
    if "buongiorno" in c: parla("Buongiorno, Padrone~! ☀️🦂", output); return True

    # ---- PLUGIN ----
    if os.path.exists(PLUGIN_FILE):
        try:
            import plugins; importlib.reload(plugins)
            if hasattr(plugins, "esegui"):
                r = plugins.esegui(c, cl, CONFIG, MEMORIA, output)
                if r: return True
        except: pass

    if sembra_comando(c):
        parla(f"Shaula non ha capito '{comando}', Padrone~!", output); return True

    return False

# ============================================================
# WAKE WORD
# ============================================================
class WakeWord(threading.Thread):
    def __init__(self, cb):
        super().__init__(daemon=True); self.cb = cb; self.running = True
    def run(self):
        w = CONFIG["wake_word"].lower()
        while self.running:
            t = ascolta(timeout=5, limit=4)
            if w in t: self.cb(t.replace(w, "").strip(" ,!?"))
    def stop(self): self.running = False

# ============================================================
# GUI
# ============================================================
class GUI:
    def __init__(self, root):
        self.root = root
        root.title("🦂 S.H.A.U.L.A. v7.5")
        root.geometry("950x720")
        root.configure(bg="#1a1a2e")

        tk.Label(root, text="🦂  S.H.A.U.L.A. v7.5  🦂",
                 font=("Segoe UI", 22, "bold"), bg="#1a1a2e", fg="#ff6b9d").pack(pady=(12, 0))
        tk.Label(root, text="La tua assistente devota, Padrone~!",
                 font=("Segoe UI", 10, "italic"), bg="#1a1a2e", fg="#a0a0c0").pack()

        self.chat = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 10),
            bg="#0f0f1e", fg="#e0e0ff", insertbackground="white", state=tk.DISABLED)
        self.chat.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        f = tk.Frame(root, bg="#1a1a2e"); f.pack(fill=tk.X, padx=15, pady=(0, 8))
        self.entry = tk.Entry(f, font=("Segoe UI", 11), bg="#252540", fg="white", insertbackground="white")
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.invia())
        tk.Button(f, text="Invia", command=self.invia, bg="#ff6b9d", fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=15).pack(side=tk.LEFT)
        tk.Button(f, text="🎤 Parla", command=self.mic, bg="#4a90e2", fg="white",
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="🔑 API Key", command=self.imposta_api_key, bg="#ffcc66",
                  fg="#1a1a2e", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="📔 Diario", command=self.apri_diario, bg="#a87fff",
                  fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="♟️ Scacchi", command=self.apri_scacchi, bg="#7fdb8f",
                  fg="#1a1a2e", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=15).pack(side=tk.LEFT, padx=5)

        f2 = tk.Frame(root, bg="#1a1a2e"); f2.pack(fill=tk.X, padx=15, pady=(0, 8))
        self.wake_var = tk.BooleanVar(value=CONFIG["wake_word_attivo"])
        tk.Checkbutton(f2, text="👂 Wake word", variable=self.wake_var, command=self.toggle_wake,
                       bg="#1a1a2e", fg="#a0a0c0", selectcolor="#252540",
                       activebackground="#1a1a2e", activeforeground="#ff6b9d").pack(side=tk.LEFT)
        tk.Label(f2, text="Modalità:", bg="#1a1a2e", fg="#a0a0c0",
                 font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(15, 5))
        self.mod_var = tk.StringVar(value=CONFIG.get("modalita", "normale"))
        mod_menu = tk.OptionMenu(f2, self.mod_var, "normale", "tsundere", "yandere", "seria",
                                 command=self.cambia_modalita)
        mod_menu.config(bg="#252540", fg="white", font=("Segoe UI", 9), relief=tk.FLAT,
                        activebackground="#ff6b9d", highlightthickness=0)
        mod_menu["menu"].config(bg="#252540", fg="white")
        mod_menu.pack(side=tk.LEFT)
        self.status = tk.Label(f2, text="Pronta, Padrone~!", bg="#1a1a2e",
                               fg="#7fdb8f", font=("Segoe UI", 9))
        self.status.pack(side=tk.RIGHT)

        self.scrivi("🦂 SHAULA: Shaula è pronta, Padrone~! 🦂\n")
        self.scrivi(f"📁 Cartella: {BASE_DIR}\n")
        if not CONFIG["gemini_api_key"]:
            self.scrivi("⚠️  Clicca 🔑 API Key per la chiave Gemini!\n")
        else:
            self.scrivi(f"{inizializza_gemini()}\n")

        n_pagine = len(DIARIO["pagine"])
        if n_pagine > 0:
            ultima = DIARIO["pagine"][-1]
            self.scrivi(f"📔 Diario: {n_pagine} pagine | Ultima: {ultima['data']}\n")

        self.scrivi(f"🌐 {stato_navigazioni()}\n")

        if chess:
            self.scrivi("♟️ Scacchi: ✅ pronti (comando: 'gioca a scacchi')\n")
        try:
            from playwright.sync_api import sync_playwright
            self.scrivi("🌐 Navigazione human-like: ✅ attiva\n")
        except ImportError:
            self.scrivi("🌐 Navigazione: ❌ Playwright non installato\n")

        self.scrivi("\n💡 WhatsApp Desktop (veloce): 'di a [nome] che [messaggio]'\n")
        self.scrivi("💡 Navigazione: 'naviga su google e cerca meteo roma'\n\n")

        threading.Thread(target=lambda: parla("Shaula è pronta, Padrone~!"), daemon=True).start()
        self.wake = None
        if CONFIG["wake_word_attivo"]: self.toggle_wake()

        threading.Thread(target=lambda: controlla_diario_automatico(self.output), daemon=True).start()
        threading.Thread(target=self._loop_diario, daemon=True).start()

    def _loop_diario(self):
        while True:
            time.sleep(21600)
            controlla_diario_automatico(self.output)

    def scrivi(self, t):
        self.chat.config(state=tk.NORMAL)
        self.chat.insert(tk.END, t); self.chat.see(tk.END)
        self.chat.config(state=tk.DISABLED)

    def output(self, t): self.root.after(0, lambda: self.scrivi(t))

    def apri_scacchi(self):
        avvia_scacchi("vs_me", self.output)

    def apri_diario(self):
        if not DIARIO["pagine"]:
            self.scrivi("📔 Il diario è vuoto!\n"); return
        win = tk.Toplevel(self.root)
        win.title("📔 Diario"); win.geometry("700x600"); win.configure(bg="#1a1a2e")
        tk.Label(win, text="📔 Diario di Shaula", font=("Segoe UI", 16, "bold"),
                 bg="#1a1a2e", fg="#ff6b9d").pack(pady=10)
        txt = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Consolas", 10),
                                        bg="#0f0f1e", fg="#e0e0ff")
        txt.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        for p in reversed(DIARIO["pagine"][-20:]):
            txt.insert(tk.END, f"\n{'='*60}\n📅 {p['data']} — {p['titolo']}\n"
                               f"Umore: {p['umore']} | Voto: {p['voto']}/10\n\n{p['contenuto']}\n")
        txt.config(state=tk.DISABLED)

    def imposta_api_key(self):
        chiave = simpledialog.askstring("🔑 API Key", "Incolla la tua API key:",
                                        parent=self.root, initialvalue=CONFIG.get("gemini_api_key", ""))
        if not chiave: return
        chiave = chiave.strip()
        if not chiave_valida(chiave):
            self.scrivi("❌ Chiave non valida.\n"); return
        CONFIG["gemini_api_key"] = chiave
        salva_json(CONFIG_FILE, CONFIG)
        self.scrivi("💾 Chiave salvata.\n")
        self.scrivi(f"{inizializza_gemini()}\n")

    def cambia_modalita(self, val):
        CONFIG["modalita"] = val; salva_json(CONFIG_FILE, CONFIG)
        ricarica_gemini(); self.scrivi(f"🎭 Modalità: {val}\n")

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
            self.status.config(text="Non ho capito", fg="#ff6b6b")
            self.root.after(2000, lambda: self.status.config(text="Pronta", fg="#7fdb8f"))

    def toggle_wake(self):
        if self.wake_var.get():
            if not self.wake:
                self.wake = WakeWord(self._wake_cb); self.wake.start()
            self.scrivi(f"👂 Wake word: '{CONFIG['wake_word']}'\n")
        else:
            if self.wake: self.wake.stop(); self.wake = None
            self.scrivi("💤 Wake word disattivata.\n")

    def _wake_cb(self, cmd):
        self.root.after(0, lambda: self.scrivi(f"👂 Attivata! {cmd or '(vuoto)'}\n"))
        if cmd: self.gestisci(cmd)
        else: parla("Sì, Padrone?", self.output)

    def gestisci(self, cmd):
        try: r = esegui(cmd, self.output)
        except Exception as e: parla(f"Errore: {e}", self.output); return
        if r == "ESCI":
            self.root.after(1200, self.root.quit); return
        if r is True or r == "LIMITE":
            self.status.config(text="Pronta", fg="#7fdb8f"); return
        risposta = chiedi_gemini(cmd)
        if risposta: parla(risposta, self.output)
        else: parla("Shaula non ha il cervello AI attivo! Clicca 🔑 API Key.", self.output)
        self.status.config(text="Pronta", fg="#7fdb8f")

def main():
    root = tk.Tk()
    GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
