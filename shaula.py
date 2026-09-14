# ============================================================
# S.H.A.U.L.A. v5.0 - Controllo PC avanzato + Web/Comunicazione
# ============================================================
import os, sys, json, time, shutil, datetime, subprocess
import threading, webbrowser, ctypes, random, re, glob
import importlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import tkinter as tk
from tkinter import scrolledtext, simpledialog

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
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, AudioSession
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
    "gemini_model": "gemini-2.0-flash",
    "gemini_model_fallback": "gemini-2.5-flash-lite",
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
    "monitoraggi": []
})
MEMORIA = carica_json(MEMORIA_FILE, {"ricordi": [], "preferenze": {}, "info": {}})
STORICO = carica_json(STORICO_FILE, {"conversazioni": []})
NOTE = carica_json(NOTE_FILE, {"liste": {}, "note": []})
AGENDA = carica_json(AGENDA_FILE, {"eventi": []})

# ============================================================
# SITI WEB
# ============================================================
SITI_WEB = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "tiktok": "https://www.tiktok.com",
    "whatsapp": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com",
    "mail": "https://mail.google.com",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "twitch": "https://www.twitch.tv",
    "reddit": "https://www.reddit.com",
    "amazon": "https://www.amazon.it",
    "wikipedia": "https://it.wikipedia.org",
    "github": "https://github.com",
    "chatgpt": "https://chat.openai.com",
    "gemini": "https://gemini.google.com",
    "maps": "https://maps.google.com",
    "mappe": "https://maps.google.com",
    "traduttore": "https://translate.google.com",
    "drive": "https://drive.google.com",
    "calendar": "https://calendar.google.com",
    "calendario": "https://calendar.google.com",
    "steam": "https://store.steampowered.com",
    "telegram": "https://web.telegram.org",
    "discord": "https://discord.com/app",
    "linkedin": "https://www.linkedin.com",
}

# Programmi comuni con percorsi Windows
PROGRAMMI_COMUNI = {
    "notepad": "notepad.exe",
    "blocco note": "notepad.exe",
    "calcolatrice": "calc.exe",
    "calc": "calc.exe",
    "cmd": "cmd.exe",
    "prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "esplora file": "explorer.exe",
    "paint": "mspaint.exe",
    "wordpad": "write.exe",
    "task manager": "taskmgr.exe",
    "gestione attività": "taskmgr.exe",
    "pannello di controllo": "control.exe",
    "impostazioni": "ms-settings:",
    "chrome": "chrome.exe",
    "edge": "msedge.exe",
    "firefox": "firefox.exe",
    "spotify": "spotify.exe",
    "discord": "discord.exe",
    "steam": "steam.exe",
    "telegram": "telegram.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
}

VERBI_COMANDO = [
    "apri", "chiudi", "cerca", "crea", "elimina", "cancella",
    "imposta", "avvia", "metti", "spegni", "riavvia", "blocca",
    "trova", "mostra", "timer", "svegliami", "leggi", "scrivi",
    "copia", "sposta", "rinomina", "fai", "riproduci", "play",
    "pausa", "minimizza", "massimizza", "alza", "abbassa",
    "muto", "silenzio", "screenshot", "converti", "traduci",
    "riassumi", "ricorda", "dimentica", "modalità", "modalita",
    "processi", "ram", "cpu", "disco", "pulisci", "ottimizza",
    "email", "mail", "agenda", "evento", "nota", "lista"
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

MODELLO_PRIMARIO = CONFIG.get("gemini_model", "gemini-2.0-flash")
MODELLO_FALLBACK = CONFIG.get("gemini_model_fallback", "gemini-2.5-flash-lite")

PROMPT_BASE = (
    "Sei Shaula di Re:Zero. Chiami l'utente 'Padrone'{nome}. "
    "Parli in terza persona di te. Usi '~' e 'ehehe' spesso. "
    "Rispondi in italiano, massimo 4 frasi. Emoji ogni tanto (🦂💕✨). "
    "IMPORTANTE: NON puoi eseguire azioni sul PC del Padrone. "
    "Se ti chiede di fare qualcosa sul PC, rispondi che deve dirlo come comando diretto. "
    "Hai una memoria persistente che ti viene passata nel contesto: usala sempre. "
)

PROMPT_MODALITA = {
    "normale": "Sei devota, energetica, affettuosa, leggermente possessiva.",
    "tsundere": "Fai la dura, ti nascondi dietro 'b-baka!' ma in realtà adori il Padrone.",
    "yandere": "Sei ossessivamente gelosa, possessiva, minacci dolcemente chi si avvicina al Padrone.",
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
    if not genai:
        return "⚠️ Libreria google-generativeai mancante"
    key = CONFIG.get("gemini_api_key", "").strip()
    if not key:
        return "⚠️ Nessuna API key configurata. Clicca 🔑 API Key."
    try:
        genai.configure(api_key=key)
    except Exception as e:
        return f"❌ Errore configure: {str(e)[:150]}"
    try:
        modello, chat = _crea_modello(MODELLO_PRIMARIO)
        MODELLO_ATTIVO = MODELLO_PRIMARIO
        return f"✅ Modello attivo: {MODELLO_PRIMARIO} (fallback: {MODELLO_FALLBACK})"
    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "API key not valid" in err:
            return "❌ Chiave API non valida."
        pass
    try:
        modello, chat = _crea_modello(MODELLO_FALLBACK)
        MODELLO_ATTIVO = MODELLO_FALLBACK
        return f"⚠️ Uso fallback: {MODELLO_FALLBACK}"
    except Exception as e:
        return f"❌ Nessun modello disponibile: {str(e)[:150]}"

def ricarica_gemini():
    if not genai or not CONFIG.get("gemini_api_key"):
        return
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
    STORICO["conversazioni"] = STORICO["conversazioni"][-200:]
    salva_json(STORICO_FILE, STORICO)

def chiedi_gemini(testo):
    global chat, MODELLO_ATTIVO, modello
    if not chat:
        return None
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
                    risposta = f"[{MODELLO_PRIMARIO} esaurito, uso {MODELLO_FALLBACK}]\n\n{r.text}"
                    salva_storico(testo, risposta)
                    return risposta
                except Exception as e2:
                    return f"⚠️ Quota esaurita per tutti i modelli, Padrone~"
            return "⚠️ Quota gratuita esaurita per oggi, Padrone~"
        if "API_KEY_INVALID" in err:
            return "❌ La chiave API non è valida."
        if "SAFETY" in err or "blocked" in err.lower():
            return "⚠️ Gemini ha bloccato la risposta."
        if "DEADLINE" in err or "timeout" in err.lower():
            return "⚠️ Timeout, riprova."
        return f"Errore: {err[:200]}"

def estrai_info_automatiche(testo, output):
    t = testo.lower()
    patterns = {
        r"mi chiamo (\w+)": "nome",
        r"il mio nome è (\w+)": "nome",
        r"abito a ([\w\s]+)": "citta",
        r"vivo a ([\w\s]+)": "citta",
        r"il mio compleanno è ([\w\s\d]+)": "compleanno",
        r"lavoro come ([\w\s]+)": "lavoro",
        r"ho (\d+) anni": "eta",
        r"mi piace ([\w\s]+)": "gusto",
        r"amo ([\w\s]+)": "gusto",
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
# AUDIO AVANZATO
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
        except Exception:
            pass
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
            volume.SetMute(not volume.GetMute(), None)
            return True
        except Exception:
            pass
    if keyboard:
        keyboard.press_and_release('volume mute')
        return True
    return False

def cambia_volume_app(nome_app, delta):
    """Cambia il volume di un'app specifica (es. Spotify, Chrome)."""
    if not PYCAW_OK:
        return False
    try:
        sessions = AudioUtilities.GetAllSessions()
        trovata = False
        for session in sessions:
            if session.Process:
                nome = session.Process.name().lower()
                if nome_app.lower() in nome:
                    volume = session.SimpleAudioVolume
                    attuale = volume.GetMasterVolume()
                    volume.SetMasterVolume(max(0.0, min(1.0, attuale + delta)), None)
                    trovata = True
        return trovata
    except Exception as e:
        print(f"Errore audio app: {e}")
        return False

def muta_app(nome_app):
    if not PYCAW_OK: return False
    try:
        sessions = AudioUtilities.GetAllSessions()
        trovata = False
        for session in sessions:
            if session.Process:
                nome = session.Process.name().lower()
                if nome_app.lower() in nome:
                    volume = session.SimpleAudioVolume
                    volume.SetMute(not volume.GetMute(), None)
                    trovata = True
        return trovata
    except Exception:
        return False

def lista_app_audio():
    """Restituisce la lista di app che stanno riproducendo audio."""
    if not PYCAW_OK: return []
    apps = []
    try:
        for session in AudioUtilities.GetAllSessions():
            if session.Process:
                apps.append(session.Process.name())
    except Exception:
        pass
    return list(set(apps))

def media_key(tasto):
    if keyboard:
        try:
            keyboard.press_and_release(tasto)
            return True
        except Exception:
            pass
    return False

# ============================================================
# PROCESSI E PERFORMANCE
# ============================================================
def lista_processi(ordinati_per="ram", limite=10):
    """Lista processi attivi ordinati per RAM o CPU."""
    if not psutil: return "psutil non disponibile"
    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
            try:
                info = p.info
                procs.append(info)
            except Exception:
                continue
        if ordinati_per == "ram":
            procs.sort(key=lambda x: x.get('memory_percent', 0) or 0, reverse=True)
        else:
            procs.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)
        risultato = []
        for p in procs[:limite]:
            nome = p.get('name', '?')
            ram = p.get('memory_percent', 0) or 0
            cpu = p.get('cpu_percent', 0) or 0
            risultato.append(f"{nome}: RAM {ram:.1f}%, CPU {cpu:.1f}%")
        return "\n".join(risultato)
    except Exception as e:
        return f"Errore: {e}"

def chiudi_processo(nome):
    """Chiude un processo per nome."""
    if not psutil: return False
    nome_low = nome.lower()
    chiusi = 0
    for p in psutil.process_iter(['name']):
        try:
            if p.info['name'] and nome_low in p.info['name'].lower():
                p.terminate()
                chiusi += 1
        except Exception:
            continue
    return chiusi > 0

def pulisci_temp():
    """Elimina file temporanei di Windows."""
    try:
        temp_dir = os.environ.get('TEMP', r'C:\Windows\Temp')
        eliminati = 0
        errori = 0
        for f in os.listdir(temp_dir):
            percorso = os.path.join(temp_dir, f)
            try:
                if os.path.isfile(percorso):
                    os.remove(percorso)
                    eliminati += 1
                elif os.path.isdir(percorso):
                    shutil.rmtree(percorso, ignore_errors=True)
                    eliminati += 1
            except Exception:
                errori += 1
        return eliminati, errori
    except Exception as e:
        return 0, str(e)

def info_disco_dettagliato():
    """Info su tutti i dischi."""
    if not psutil: return "psutil non disponibile"
    try:
        risultato = []
        for part in psutil.disk_partitions():
            try:
                uso = psutil.disk_usage(part.mountpoint)
                risultato.append(
                    f"{part.device}: {uso.percent}% usato "
                    f"({uso.used // (1024**3)}GB / {uso.total // (1024**3)}GB)"
                )
            except Exception:
                continue
        return "\n".join(risultato)
    except Exception:
        return "Errore lettura dischi"

def modalita_risparmio():
    """Attiva modalità risparmio energetico."""
    try:
        subprocess.run("powercfg /setactive a1841308-3541-4fab-bc81-f71556f20b4a",
                       shell=True, capture_output=True)
        return True
    except Exception:
        return False

def modalita_prestazioni():
    """Attiva modalità prestazioni elevate."""
    try:
        subprocess.run("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
                       shell=True, capture_output=True)
        return True
    except Exception:
        return False

def modalita_bilanciata():
    try:
        subprocess.run("powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e",
                       shell=True, capture_output=True)
        return True
    except Exception:
        return False

# ============================================================
# EMAIL GMAIL
# ============================================================
def invia_email(destinatario, oggetto, corpo):
    """Invia email usando Gmail SMTP."""
    user = CONFIG.get("gmail_user", "").strip()
    pwd = CONFIG.get("gmail_password", "").strip()
    if not user or not pwd:
        return "⚠️ Configura Gmail in config.json (gmail_user + gmail_password)"

    try:
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = destinatario
        msg['Subject'] = oggetto
        msg.attach(MIMEText(corpo, 'plain', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, pwd)
        server.send_message(msg)
        server.quit()
        return f"✅ Email inviata a {destinatario}"
    except Exception as e:
        return f"❌ Errore invio: {str(e)[:150]}"

# ============================================================
# AGENDA E NOTE
# ============================================================
def aggiungi_evento(titolo, data_ora):
    AGENDA["eventi"].append({
        "titolo": titolo,
        "quando": data_ora,
        "creato": datetime.datetime.now().isoformat()
    })
    salva_json(AGENDA_FILE, AGENDA)
    return True

def eventi_oggi():
    oggi = datetime.date.today().isoformat()
    risultati = [e for e in AGENDA["eventi"] if oggi in e.get("quando", "")]
    return risultati

def aggiungi_nota(testo, categoria="generale"):
    if categoria not in NOTE["liste"]:
        NOTE["liste"][categoria] = []
    NOTE["liste"][categoria].append({
        "testo": testo,
        "data": datetime.datetime.now().isoformat()
    })
    salva_json(NOTE_FILE, NOTE)
    return True

def leggi_lista(categoria="generale"):
    return NOTE["liste"].get(categoria, [])

# ============================================================
# TIMER
# ============================================================
def avvia_timer(secondi, descrizione, output):
    def _thread():
        time.sleep(secondi)
        parla(f"Padrone~! È ora! {descrizione}", output)
    threading.Thread(target=_thread, daemon=True).start()

# ============================================================
# VISIONE SCHERMO
# ============================================================
def analizza_schermo(output):
    if not PIL_ImageGrab:
        parla("Pillow non installato, Padrone~", output)
        return
    if not genai or not CONFIG.get("gemini_api_key"):
        parla("Serve la API key Gemini, Padrone~", output)
        return
    try:
        img = PIL_ImageGrab.grab()
        p = os.path.join(BASE_DIR, "_temp_screen.png")
        img.save(p)
        from PIL import Image as _PILImage
        img_pil = _PILImage.open(p)
        vision_model = genai.GenerativeModel(MODELLO_ATTIVO or MODELLO_FALLBACK)
        prompt = (
            "Descrivi cosa vedi in massimo 3 frasi con la personalità di Shaula. "
            "Se c'è testo importante, leggilo. Se c'è un errore, dillo."
        )
        risposta = vision_model.generate_content([prompt, img_pil])
        parla(risposta.text, output)
        try: os.remove(p)
        except: pass
    except Exception as e:
        parla(f"Errore analisi schermo: {str(e)[:150]}", output)

# ============================================================
# COMANDI
# ============================================================
def desktop():
    return os.path.join(os.path.expanduser("~"), "Desktop")

def esegui(comando, output):
    c = comando.lower().strip()
    cl = comando.strip()

    if c in ["esci", "arrivederci", "chiudi shaula"]:
        parla("Shaula ti saluta, Padrone~! Ehehe!", output)
        return "ESCI"

    estrai_info_automatiche(cl, output)

    # ---- MODALITÀ ----
    if "modalità" in c or "modalita" in c:
        for mod in ["normale", "tsundere", "yandere", "seria"]:
            if mod in c:
                CONFIG["modalita"] = mod
                salva_json(CONFIG_FILE, CONFIG)
                ricarica_gemini()
                parla(f"Shaula passa in modalità {mod}, Padrone~!", output)
                return True
        parla("Modalità: normale, tsundere, yandere, seria", output)
        return True

    # ---- MEMORIA ----
    if c.startswith("ricorda che"):
        MEMORIA["ricordi"].append(cl[11:].strip())
        salva_json(MEMORIA_FILE, MEMORIA)
        parla("Annotato, Padrone~!", output)
        return True
    if "cosa ricordi" in c or "cosa sai di me" in c:
        msg = ""
        if MEMORIA["info"]:
            msg += "Info: " + ", ".join(f"{k}={v}" for k, v in MEMORIA["info"].items()) + ". "
        if MEMORIA["ricordi"]:
            msg += "Ricordi: " + "; ".join(MEMORIA["ricordi"][-5:])
        parla(msg or "Non ricordo nulla, Padrone~", output)
        return True
    if "dimentica tutto" in c:
        MEMORIA = {"ricordi": [], "preferenze": {}, "info": {}}
        salva_json(MEMORIA_FILE, MEMORIA)
        parla("Memoria azzerata, Padrone~", output)
        return True

    # ============================================================
    # CONTROLLO PC AVANZATO
    # ============================================================

    # ---- PROCESSI ----
    if "processi" in c or "cosa consuma" in c or "cosa sta usando" in c:
        ordine = "cpu" if "cpu" in c else "ram"
        parla(f"Processi che consumano più {ordine.upper()}:", output)
        risultato = lista_processi(ordine, 8)
        parla(risultato, output)
        return True

    if c.startswith("chiudi ") and ("processo" in c or "programma" in c):
        nome = cl.replace("chiudi processo", "").replace("chiudi programma", "").replace("chiudi", "").strip()
        if nome:
            if chiudi_processo(nome):
                parla(f"Chiuso {nome}, Padrone~!", output)
            else:
                parla(f"Processo '{nome}' non trovato, Padrone~", output)
        return True

    # ---- DISCO ----
    if "info disco" in c or "spazio disco" in c or "quanto spazio" in c:
        parla("Info dischi:", output)
        parla(info_disco_dettagliato(), output)
        return True

    if "pulisci" in c and ("temp" in c or "temporanei" in c or "pc" in c):
        parla("Pulisco i file temporanei, Padrone~...", output)
        eliminati, errori = pulisci_temp()
        parla(f"Eliminati {eliminati} file! Ehehe~", output)
        return True

    # ---- ENERGIA ----
    if "risparmio" in c or "risparmio energetico" in c:
        if modalita_risparmio():
            parla("Modalità risparmio energetico attivata, Padrone~", output)
        return True
    if "prestazioni" in c or "performance" in c:
        if modalita_prestazioni():
            parla("Modalità prestazioni elevate, Padrone~!", output)
        return True
    if "bilanciata" in c:
        if modalita_bilanciata():
            parla("Modalità bilanciata, Padrone~", output)
        return True

    # ---- AUDIO PER-APP ----
    if "app audio" in c or "chi riproduce" in c:
        apps = lista_app_audio()
        if apps:
            parla("App che riproducono audio: " + ", ".join(apps), output)
        else:
            parla("Nessuna app riproduce audio, Padrone~", output)
        return True

    m = re.search(r"(alza|abbassa|muta|silenzia)\s+(?:il volume di\s+)?(\w+)", c)
    if m and m.group(2) not in ["volume"]:
        azione = m.group(1)
        app = m.group(2)
        if azione in ["alza"]:
            if cambia_volume_app(app, 0.15):
                parla(f"Volume di {app} alzato, Padrone~", output)
            else:
                parla(f"App '{app}' non trovata, Padrone~", output)
        elif azione in ["abbassa"]:
            if cambia_volume_app(app, -0.15):
                parla(f"Volume di {app} abbassato, Padrone~", output)
            else:
                parla(f"App '{app}' non trovata, Padrone~", output)
        else:
            if muta_app(app):
                parla(f"{app} mutata, Padrone~", output)
            else:
                parla(f"App '{app}' non trovata, Padrone~", output)
        return True

    # ---- BLOCCO/SPEGNIMENTO PROGRAMMATO ----
    m = re.search(r"blocca (?:il pc )?tra (\d+)\s*(secondi|minuti|ore)", c)
    if m:
        val = int(m.group(1))
        unit = m.group(2)
        sec = val if "sec" in unit else val * 60 if "min" in unit else val * 3600
        def _blocca():
            time.sleep(sec)
            ctypes.windll.user32.LockWorkStation()
        threading.Thread(target=_blocca, daemon=True).start()
        parla(f"Blocco PC tra {val} {unit}, Padrone~", output)
        return True

    m = re.search(r"spegni (?:il pc )?tra (\d+)\s*(secondi|minuti|ore)", c)
    if m:
        val = int(m.group(1))
        unit = m.group(2)
        sec = val if "sec" in unit else val * 60 if "min" in unit else val * 3600
        os.system(f"shutdown /s /t {sec}")
        parla(f"Spegno il PC tra {val} {unit}, Padrone~!", output)
        return True

    # ============================================================
    # WEB E COMUNICAZIONE
    # ============================================================

    # ---- APRI WHATSAPP CON CHAT ----
    if "whatsapp" in c:
        m = re.search(r"(?:a|con|scrivi a)\s+(\w+)", cl)
        if m:
            nome = m.group(1)
            webbrowser.open(f"https://web.whatsapp.com/send?text=Ciao {nome}")
            parla(f"Apro WhatsApp per {nome}, Padrone~", output)
        else:
            webbrowser.open("https://web.whatsapp.com")
            parla("Apro WhatsApp Web, Padrone~", output)
        return True

    # ---- EMAIL ----
    if "email" in c or "mail" in c:
        if "invia" in c or "manda" in c:
            m = re.search(r"(?:a|email a|mail a)\s+([\w.+-]+@[\w.-]+)\s+(?:oggetto\s+)?(.+?)(?:\s+corpo\s+(.+))?$", cl)
            if m:
                dest = m.group(1)
                oggetto = m.group(2).strip() if m.group(2) else "Messaggio da Shaula"
                corpo = m.group(3).strip() if m.group(3) else oggetto
                risultato = invia_email(dest, oggetto, corpo)
                parla(risultato, output)
            else:
                parla("Formato: 'invia email a mario@x.com oggetto Ciao corpo Come stai?'", output)
            return True
        else:
            webbrowser.open("https://mail.google.com")
            parla("Apro Gmail, Padrone~", output)
            return True

    # ---- AGENDA ----
    if "aggiungi evento" in c or "aggiungi appuntamento" in c:
        m = re.search(r"(?:evento|appuntamento)\s+(.+?)\s+(?:il|per il|domani|oggi)\s*(.*)", cl, re.IGNORECASE)
        if m:
            titolo = m.group(1).strip()
            quando = m.group(2).strip() or datetime.date.today().isoformat()
            aggiungi_evento(titolo, quando)
            parla(f"Evento '{titolo}' aggiunto, Padrone~!", output)
        else:
            parla("Formato: 'aggiungi evento riunione per domani'", output)
        return True

    if "cosa ho oggi" in c or "agenda oggi" in c or "eventi oggi" in c:
        eventi = eventi_oggi()
        if eventi:
            testo = "\n".join(f"- {e['titolo']} ({e['quando']})" for e in eventi)
            parla(f"Oggi hai:\n{testo}", output)
        else:
            parla("Nessun evento oggi, Padrone~", output)
        return True

    # ---- NOTE/LISTE ----
    if "aggiungi a lista" in c or "aggiungi alla lista" in c:
        m = re.search(r"lista\s+(\w+)\s+(.+)", cl)
        if m:
            categoria = m.group(1).lower()
            testo = m.group(2).strip()
            aggiungi_nota(testo, categoria)
            parla(f"Aggiunto '{testo}' alla lista {categoria}, Padrone~!", output)
        else:
            m2 = re.search(r"(?:lista|a lista)\s+(.+)", cl)
            if m2:
                aggiungi_nota(m2.group(1).strip(), "generale")
                parla("Aggiunto alla lista, Padrone~", output)
        return True

    if "leggi lista" in c or "cosa c'è nella lista" in c:
        m = re.search(r"lista\s+(\w+)", c)
        categoria = m.group(1) if m else "generale"
        elementi = leggi_lista(categoria)
        if elementi:
            testo = "\n".join(f"- {e['testo']}" for e in elementi[-10:])
            parla(f"Lista {categoria}:\n{testo}", output)
        else:
            parla(f"Lista {categoria} vuota, Padrone~", output)
        return True

    # ---- TRADUZIONE ----
    if c.startswith("traduci"):
        m = re.search(r"traduci (?:in (\w+)\s+)?(.+)", cl, re.IGNORECASE)
        if m:
            lingua = m.group(1) or "inglese"
            testo = m.group(2).strip()
            q = f"traduci in {lingua}: {testo}"
            webbrowser.open(f"https://translate.google.com/?sl=auto&tl={lingua}&text={testo}")
            parla(f"Traduco in {lingua}, Padrone~", output)
        return True

    # ---- RICERCA SU SITI ----
    if "cerca su google" in c or "cerca google" in c:
        q = re.sub(r"cerca (su )?google", "", c).strip()
        if q:
            webbrowser.open(f"https://www.google.com/search?q={q}")
            parla(f"Cerco '{q}' su Google, Padrone~", output)
        return True

    if "cerca su youtube" in c or "cerca youtube" in c or "cerca yt" in c:
        q = re.sub(r"cerca (su )?(youtube|yt)", "", c).strip()
        if q:
            webbrowser.open(f"https://www.youtube.com/results?search_query={q}")
            parla(f"Cerco '{q}' su YouTube, Padrone~", output)
        else:
            webbrowser.open("https://www.youtube.com")
            parla("Apro YouTube, Padrone~!", output)
        return True

    if "cerca su wikipedia" in c or "cerca wikipedia" in c:
        q = re.sub(r"cerca (su )?wikipedia", "", c).strip()
        if q:
            webbrowser.open(f"https://it.wikipedia.org/wiki/Special:Search?search={q}")
            parla(f"Cerco '{q}' su Wikipedia, Padrone~", output)
        return True

    m = re.match(r"^cerca\s+(\w+)$", c)
    if m and m.group(1) in SITI_WEB:
        webbrowser.open(SITI_WEB[m.group(1)])
        parla(f"Apro {m.group(1)}, Padrone~!", output)
        return True

    # ---- RICERCA GENERICA ----
    if c.startswith("cerca ") and not c.startswith("cerca su "):
        q = cl[6:].strip()
        if q:
            threading.Thread(target=rispondi_con_ricerca, args=(q, output), daemon=True).start()
        return True

    if c.startswith("apri sito") or c.startswith("vai su"):
        url = cl.replace("apri sito", "").replace("vai su", "").strip()
        if url:
            if not url.startswith("http"): url = "https://" + url
            webbrowser.open(url)
            parla(f"Apro {url}, Padrone~", output)
        return True

    # ---- NOTIZIE ----
    if "notizie" in c:
        threading.Thread(target=rispondi_con_ricerca, args=("notizie di oggi", output), daemon=True).start()
        return True

    # ---- METEO ----
    if "meteo" in c or "che tempo fa" in c:
        città = CONFIG.get("citta", "Roma")
        m = re.search(r"(?:a|di|per)\s+([A-Za-zÀ-ÿ]+)", cl)
        if m: città = m.group(1)
        threading.Thread(target=rispondi_con_ricerca, args=(f"meteo {città} oggi", output), daemon=True).start()
        return True

    # ---- MUSICA ----
    parole_musica = ["metti musica", "play musica", "metti un po di musica",
                     "voglio musica", "metti su musica", "riproduci musica"]
    if any(p in c for p in parole_musica) or c == "musica":
        webbrowser.open("https://music.youtube.com/")
        parla("Shaula mette la musica, Padrone~! 🎵", output)
        return True
    if c.startswith("play ") or c.startswith("riproduci "):
        q = cl[5:] if c.startswith("play ") else cl[10:]
        if q.strip():
            webbrowser.open(f"https://music.youtube.com/search?q={q.strip()}")
            parla(f"Riproduco {q}, Padrone~", output)
        return True
    if "pausa musica" in c or c == "pausa":
        media_key('play/pause media')
        parla("Pausa, Padrone~", output)
        return True
    if "canzone successiva" in c or c == "skip":
        media_key('next track')
        parla("Cambio canzone, Padrone~", output)
        return True
    if "canzone precedente" in c:
        media_key('previous track')
        parla("Torno indietro, Padrone~", output)
        return True

    # ---- VOLUME GENERALE ----
    if any(p in c for p in ["alza volume", "alza il volume", "volume su", "aumenta volume"]):
        cambia_volume(0.10)
        parla("Volume alzato, Padrone~!", output)
        return True
    if any(p in c for p in ["abbassa volume", "abbassa il volume", "volume giù", "diminuisci volume"]):
        cambia_volume(-0.10)
        parla("Volume abbassato, Padrone~", output)
        return True
    if any(p in c for p in ["muto", "silenzio", "muta audio"]):
        toggle_mute()
        parla("Silenziato, Padrone~", output)
        return True

    # ---- TIMER ----
    m = re.search(r"timer\D*(\d+)\s*(secondi|secondo|sec|minuti|minuto|min|ore|ora|h)\b", c)
    if m:
        val = int(m.group(1))
        unit = m.group(2)
        if "sec" in unit: sec, unit_txt = val, f"{val} secondi"
        elif "min" in unit: sec, unit_txt = val * 60, f"{val} minuti"
        else: sec, unit_txt = val * 3600, f"{val} ore"
        avvia_timer(sec, f"Timer di {unit_txt} scaduto!", output)
        parla(f"Timer di {unit_txt} avviato, Padrone~!", output)
        return True
    if "timer" in c:
        parla("Per quanto tempo? Dì: 'timer 5 minuti'", output)
        return True

    # ---- SVEGLIA ----
    m = re.search(r"svegliami alle (\d{1,2})[:.]?(\d{2})?", c)
    if m:
        ora = int(m.group(1))
        minuto = int(m.group(2)) if m.group(2) else 0
        adesso = datetime.datetime.now()
        target = adesso.replace(hour=ora, minute=minuto, second=0, microsecond=0)
        if target <= adesso: target += datetime.timedelta(days=1)
        sec = (target - adesso).total_seconds()
        avvia_timer(sec, f"Sveglia! Sono le {ora}:{minuto:02d}, Padrone~!", output)
        parla(f"Ti sveglierò alle {ora}:{minuto:02d}, Padrone~!", output)
        return True
    if "svegliami" in c:
        parla("A che ora? Dì: 'svegliami alle 7:30'", output)
        return True

    # ---- SCHERMO ----
    if "screenshot" in c:
        if PIL_ImageGrab:
            n = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            PIL_ImageGrab.grab().save(os.path.join(desktop(), n))
            parla(f"Screenshot salvato: {n}", output)
        return True
    if "cosa vedi" in c or "leggi schermo" in c or "cosa c'è sullo schermo" in c:
        threading.Thread(target=analizza_schermo, args=(output,), daemon=True).start()
        return True
    if "minimizza tutto" in c or "mostra desktop" in c:
        if keyboard: keyboard.press_and_release('windows+d')
        parla("Fatto, Padrone~", output)
        return True
    if "chiudi finestra" in c:
        if keyboard: keyboard.press_and_release('alt+f4')
        parla("Finestra chiusa, Padrone~", output)
        return True
    if "modalità scura" in c or "modalita scura" in c:
        try:
            subprocess.run(["reg", "add",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                "/v", "AppsUseLightTheme", "/t", "REG_DWORD", "/d", "0", "/f"], capture_output=True)
            parla("Tema scuro attivato, Padrone~", output)
        except Exception:
            pass
        return True

    # ---- UTILITY ----
    m = re.search(r"converti ([\d.]+) ([\w]+) in ([\w]+)", c)
    if m:
        q = f"{m.group(1)} {m.group(2)} in {m.group(3)}"
        webbrowser.open(f"https://www.google.com/search?q={q}")
        parla("Cerco la conversione, Padrone~", output)
        return True
    m = re.search(r"quanto fa ([\d\s+\-*/().,%]+)", c)
    if m:
        try:
            expr = m.group(1).replace("%", "/100*").replace(",", ".")
            r = eval(expr)
            parla(f"Fa {r}, Padrone~!", output)
        except Exception:
            parla("Non riesco a calcolare, Padrone~", output)
        return True
    if "quanti giorni" in c and "natale" in c:
        oggi = datetime.date.today()
        natale = datetime.date(oggi.year, 12, 25)
        if natale < oggi: natale = datetime.date(oggi.year + 1, 12, 25)
        parla(f"Mancano {(natale - oggi).days} giorni a Natale, Padrone~!", output)
        return True

    # ---- CARTELLE E FILE ----
    if "crea cartella" in c:
        n = cl.lower().replace("crea cartella", "").strip()
        if n:
            os.makedirs(os.path.join(desktop(), n), exist_ok=True)
            parla(f"Cartella '{n}' creata, Padrone~!", output)
        return True
    if "elimina cartella" in c:
        n = cl.lower().replace("elimina cartella", "").strip()
        p = os.path.join(desktop(), n)
        if os.path.isdir(p):
            shutil.rmtree(p)
            parla(f"Cartella '{n}' eliminata, Padrone~", output)
        return True
    if "cosa c'è sul desktop" in c or "lista desktop" in c:
        f = os.listdir(desktop())
        parla(f"Sul desktop: {len(f)} elementi — " + ", ".join(f[:10]), output)
        return True
    if "cerca file" in c:
        n = cl.lower().replace("cerca file", "").strip()
        if n:
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

    # ---- APRI PROGRAMMI/SITI ----
    if c.startswith("apri "):
        prog = cl[5:].strip()
        prog_low = prog.lower()
        if prog_low in SITI_WEB:
            webbrowser.open(SITI_WEB[prog_low])
            parla(f"Ho aperto {prog}, Padrone~!", output)
            return True
        if prog_low in PROGRAMMI_COMUNI:
            try:
                subprocess.Popen(PROGRAMMI_COMUNI[prog_low], shell=True)
                parla(f"Ho aperto {prog}, Padrone~!", output)
            except Exception:
                parla(f"Non riesco ad aprire {prog}, Padrone~", output)
            return True
        if prog_low.startswith("http") or ("." in prog_low and " " not in prog_low):
            url = prog if prog.startswith("http") else "https://" + prog
            webbrowser.open(url)
            parla(f"Ho aperto {url}, Padrone~!", output)
            return True
        try:
            subprocess.Popen(prog, shell=True)
            parla(f"Ho aperto {prog}, Padrone~!", output)
        except Exception:
            parla(f"Non riesco ad aprire '{prog}', Padrone~.", output)
        return True

    # ---- SISTEMA ----
    if "info sistema" in c:
        if psutil:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disco = psutil.disk_usage('/')
            bat = ""
            try:
                b = psutil.sensors_battery()
                if b: bat = f", batteria {b.percent}%"
            except Exception: pass
            parla(f"CPU {cpu}%, RAM {ram.percent}%, Disco {disco.percent}%{bat}, Padrone~!", output)
        return True
    if "che ore" in c or "che ora" in c:
        parla(f"Sono le {datetime.datetime.now().strftime('%H:%M')}, Padrone~!", output)
        return True
    if "che giorno" in c:
        parla(f"Oggi è {datetime.datetime.now().strftime('%A %d %B %Y')}, Padrone~!", output)
        return True

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

    # ---- APPUNTI FILE ----
    if c.startswith("scrivi appunto"):
        t = cl.replace("scrivi appunto", "").strip()
        if t:
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

    # ---- PERSONALITÀ ----
    if "chi sei" in c:
        parla("Shaula è la tua assistente devota, Padrone~! 🦂", output)
        return True
    if "ti amo" in c or "ti voglio bene" in c:
        parla("Shaula ti adora, Padrone~! 💕", output)
        return True
    if "buonanotte" in c:
        parla("Buonanotte, Padrone~! 🌙💕", output)
        return True
    if "buongiorno" in c:
        parla("Buongiorno, Padrone~! ☀️🦂", output)
        return True

    # ---- PLUGIN ----
    if os.path.exists(PLUGIN_FILE):
        try:
            import plugins
            importlib.reload(plugins)
            if hasattr(plugins, "esegui"):
                r = plugins.esegui(c, cl, CONFIG, MEMORIA, output)
                if r: return True
        except Exception:
            pass

    # ---- ANTI-ALLUCINAZIONE ----
    if sembra_comando(c):
        parla(f"Shaula non ha capito '{comando}', Padrone~! Prova a riformulare.", output)
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
        root.title("🦂 S.H.A.U.L.A. v5.0")
        root.geometry("950x720")
        root.configure(bg="#1a1a2e")

        tk.Label(root, text="🦂  S.H.A.U.L.A. v5.0  🦂",
                 font=("Segoe UI", 22, "bold"),
                 bg="#1a1a2e", fg="#ff6b9d").pack(pady=(12, 0))
        tk.Label(root, text="Controllo PC avanzato + Web & Comunicazione",
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
        tk.Button(f, text="🔑 API Key", command=self.imposta_api_key,
                  bg="#ffcc66", fg="#1a1a2e", font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(f, text="📧 Gmail", command=self.imposta_gmail,
                  bg="#7fdb8f", fg="#1a1a2e", font=("Segoe UI", 10, "bold"),
                  relief=tk.FLAT, padx=15).pack(side=tk.LEFT, padx=5)

        f2 = tk.Frame(root, bg="#1a1a2e")
        f2.pack(fill=tk.X, padx=15, pady=(0, 8))
        self.wake_var = tk.BooleanVar(value=CONFIG["wake_word_attivo"])
        tk.Checkbutton(f2, text="👂 Wake word", variable=self.wake_var,
                       command=self.toggle_wake, bg="#1a1a2e", fg="#a0a0c0",
                       selectcolor="#252540", activebackground="#1a1a2e",
                       activeforeground="#ff6b9d").pack(side=tk.LEFT)
        tk.Label(f2, text="Modalità:", bg="#1a1a2e", fg="#a0a0c0",
                 font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(15, 5))
        self.mod_var = tk.StringVar(value=CONFIG.get("modalita", "normale"))
        mod_menu = tk.OptionMenu(f2, self.mod_var, "normale", "tsundere", "yandere", "seria",
                                 command=self.cambia_modalita)
        mod_menu.config(bg="#252540", fg="white", font=("Segoe UI", 9),
                        relief=tk.FLAT, activebackground="#ff6b9d", highlightthickness=0)
        mod_menu["menu"].config(bg="#252540", fg="white")
        mod_menu.pack(side=tk.LEFT)
        self.status = tk.Label(f2, text="Pronta, Padrone~!",
                               bg="#1a1a2e", fg="#7fdb8f", font=("Segoe UI", 9))
        self.status.pack(side=tk.RIGHT)

        self.scrivi("🦂 SHAULA: Shaula è pronta, Padrone~! 🦂\n")
        self.scrivi(f"📁 Cartella: {BASE_DIR}\n")
        if not CONFIG["gemini_api_key"]:
            self.scrivi("⚠️  Clicca 🔑 API Key per inserire la chiave Gemini!\n")
        else:
            self.scrivi(f"{inizializza_gemini()}\n")
        if not CONFIG.get("gmail_user"):
            self.scrivi("📧 Clicca 'Gmail' per configurare l'invio email (opzionale)\n")
        self.scrivi("\n💡 NUOVE FUNZIONI v5.0:\n")
        self.scrivi("   🖥️  PC: 'processi', 'chiudi processo chrome', 'info disco',\n")
        self.scrivi("       'pulisci temp', 'risparmio energetico', 'prestazioni'\n")
        self.scrivi("   🔊 Audio: 'alza spotify', 'muta chrome', 'app audio'\n")
        self.scrivi("   ⏰ Programmato: 'spegni tra 1 ora', 'blocca tra 10 minuti'\n")
        self.scrivi("   📧 Email: 'invia email a x@y.com oggetto Ciao corpo Testo'\n")
        self.scrivi("   📅 Agenda: 'aggiungi evento riunione per domani', 'cosa ho oggi'\n")
        self.scrivi("   📝 Note: 'aggiungi a lista spesa latte', 'leggi lista spesa'\n")
        self.scrivi("   💬 WhatsApp: 'apri whatsapp con Marco'\n")
        self.scrivi("   🌐 Traduci: 'traduci in inglese ciao come stai'\n\n")

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

    def imposta_api_key(self):
        msg = "Incolla la tua API key Gemini (inizia con AIza... oppure AQ.):"
        chiave = simpledialog.askstring("🔑 API Key", msg, parent=self.root,
                                        initialvalue=CONFIG.get("gemini_api_key", ""))
        if not chiave: return
        chiave = chiave.strip()
        if not chiave_valida(chiave):
            self.scrivi("❌ Chiave non valida.\n")
            return
        CONFIG["gemini_api_key"] = chiave
        salva_json(CONFIG_FILE, CONFIG)
        self.scrivi("💾 Chiave salvata.\n")
        self.scrivi(f"{inizializza_gemini()}\n")

    def imposta_gmail(self):
        msg = ("Per inviare email serve:\n"
               "1. Il tuo indirizzo Gmail (es. mario@gmail.com)\n"
               "2. Una 'password per le app' di Google\n\n"
               "Come ottenere la password:\n"
               "1. Vai su https://myaccount.google.com/apppasswords\n"
               "2. Crea una password per 'SHAULA'\n"
               "3. Copiala (16 caratteri senza spazi)\n\n"
               "Inserisci il tuo indirizzo Gmail:")
        user = simpledialog.askstring("📧 Gmail - Indirizzo", msg, parent=self.root,
                                      initialvalue=CONFIG.get("gmail_user", ""))
        if not user: return
        pwd = simpledialog.askstring("📧 Gmail - Password app",
                                     "Incolla la password per le app (16 caratteri):",
                                     parent=self.root, show="*")
        if not pwd: return
        CONFIG["gmail_user"] = user.strip()
        CONFIG["gmail_password"] = pwd.strip().replace(" ", "")
        salva_json(CONFIG_FILE, CONFIG)
        self.scrivi(f"✅ Gmail configurato per {user}\n")

    def cambia_modalita(self, val):
        CONFIG["modalita"] = val
        salva_json(CONFIG_FILE, CONFIG)
        ricarica_gemini()
        self.scrivi(f"🎭 Modalità cambiata: {val}\n")

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
            self.status.config(text="Pronta", fg="#7fdb8f")
            return
        risposta = chiedi_gemini(cmd)
        if risposta:
            parla(risposta, self.output)
        else:
            parla("Shaula non ha il cervello AI attivo! Clicca 🔑 API Key.", self.output)
        self.status.config(text="Pronta", fg="#7fdb8f")

def main():
    root = tk.Tk()
    GUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
