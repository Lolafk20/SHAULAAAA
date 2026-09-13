# ============================================================
# S.H.A.U.L.A. v4.5 - Gestione errori Gemini migliorata
# ============================================================
import os, sys, json, time, shutil, datetime, subprocess
import threading, webbrowser, ctypes, random, re
import importlib

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
PROMEMORIA_FILE = os.path.join(BASE_DIR, "promemoria.json")

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
    "wake_word": "shaula",
    "voce_attiva": True,
    "voce_rate": 180,
    "lingua": "it-IT",
    "wake_word_attivo": False,
    "modalita": "normale",
    "nome_utente": "",
    "compleanno": "",
    "citta": "Roma"
})
MEMORIA = carica_json(MEMORIA_FILE, {"ricordi": [], "preferenze": {}, "info": {}})
STORICO = carica_json(STORICO_FILE, {"conversazioni": []})
PROMEMORIA = carica_json(PROMEMORIA_FILE, [])

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
    "replit": "https://replit.com",
}

VERBI_COMANDO = [
    "apri", "chiudi", "cerca", "crea", "elimina", "cancella",
    "imposta", "avvia", "metti", "spegni", "riavvia", "blocca",
    "trova", "mostra", "timer", "svegliami", "leggi", "scrivi",
    "copia", "sposta", "rinomina", "fai", "riproduci", "play",
    "pausa", "minimizza", "massimizza", "alza", "abbassa",
    "muto", "silenzio", "screenshot", "converti", "traduci",
    "riassumi", "ricorda", "dimentica", "modalità", "modalita"
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

# Modelli in ordine di quota gratuita (dal più permissivo)
MODELLI_CANDIDATI = [
    "gemini-2.5-flash-lite",   # 1000/giorno
    "gemini-2.0-flash-lite",   # 1000/giorno
    "gemini-2.0-flash",        # 200/giorno
    "gemini-2.5-flash",        # 20/giorno
]

PROMPT_BASE = (
    "Sei Shaula di Re:Zero. Chiami l'utente 'Padrone'{nome}. "
    "Parli in terza persona di te. Usi '~' e 'ehehe' spesso. "
    "Rispondi in italiano, massimo 4 frasi. Emoji ogni tanto (🦂💕✨). "
    "IMPORTANTE: NON puoi eseguire azioni sul PC del Padrone (aprire programmi, "
    "creare file, avviare timer, ecc). Il Padrone ha già un sistema di comandi diretto "
    "che gestisce queste cose. Se ti chiede di fare qualcosa sul PC, "
    "NON dire di averlo fatto, ma rispondi che deve dirlo come comando diretto. "
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

def inizializza_gemini():
    """Inizializza Gemini mostrando errori chiari e distinguendo i casi."""
    global modello, chat, MODELLO_ATTIVO
    if not genai:
        return "⚠️ Libreria google-generativeai mancante"

    key = CONFIG.get("gemini_api_key", "").strip()
    if not key:
        return "⚠️ Nessuna API key configurata. Clicca 🔑 API Key."

    # Configura la chiave
    try:
        genai.configure(api_key=key)
    except Exception as e:
        return f"❌ Errore configure: {str(e)[:150]}"

    # Verifica che la chiave funzioni listando i modelli
    try:
        modelli_disponibili = [m.name for m in genai.list_models()]
        print(f"📋 Modelli disponibili: {len(modelli_disponibili)}")
        # Filtra solo i modelli che supportano generateContent
        supportati = [m.name for m in genai.list_models()
                      if 'generateContent' in m.supported_generation_methods]
        print(f"📋 Modelli supportati: {len(supportati)}")
    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "API key not valid" in err:
            return "❌ Chiave API non valida. Controlla di averla copiata bene."
        if "PERMISSION_DENIED" in err:
            return "❌ Chiave API senza permessi. Abilita l'API Gemini su Google Cloud."
        return f"❌ Errore verifica chiave: {err[:150]}"

    # Prova i modelli in ordine
    sys_prompt = build_system_prompt()
    errori = []

    for nome_modello in MODELLI_CANDIDATI:
        try:
            modello_test = genai.GenerativeModel(nome_modello, system_instruction=sys_prompt)
            chat_test = modello_test.start_chat(history=[])
            # Prova a mandare un messaggio minimo per verificare che funzioni
            chat_test.send_message("ping")
            modello = modello_test
            chat = chat_test
            MODELLO_ATTIVO = nome_modello
            return f"✅ Modello attivo: {nome_modello} (modalità: {CONFIG.get('modalita','normale')})"
        except Exception as e:
            err_msg = str(e)[:200]
            errori.append(f"  • {nome_modello}: {err_msg[:80]}")
            print(f"⚠️ {nome_modello}: {err_msg}")
            continue

    # Nessun modello ha funzionato
    if errori:
        dettaglio = "\n".join(errori)
        return f"❌ Nessun modello disponibile.\nDettagli:\n{dettaglio}"
    return "❌ Nessun modello Gemini disponibile"

def ricarica_gemini():
    if not genai or not CONFIG.get("gemini_api_key"):
        return "⚠️ Gemini non configurato"
    try:
        global modello, chat, MODELLO_ATTIVO
        modello = genai.GenerativeModel(MODELLO_ATTIVO or MODELLI_CANDIDATI[0],
                                        system_instruction=build_system_prompt())
        chat = modello.start_chat(history=[])
        return "✅ Modalità aggiornata"
    except Exception as e:
        return f"❌ Errore: {e}"

def salva_storico(utente, shaula):
    STORICO["conversazioni"].append({
        "data": datetime.datetime.now().isoformat(),
        "utente": utente,
        "shaula": shaula
    })
    STORICO["conversazioni"] = STORICO["conversazioni"][-200:]
    salva_json(STORICO_FILE, STORICO)

def chiedi_gemini(testo):
    """Chiama Gemini, con fallback automatico su modelli alternativi se quota esaurita."""
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

        # Quota esaurita → prova il modello successivo
        if "429" in err or "quota" in err.lower() or "exceeded" in err.lower():
            try:
                idx = MODELLI_CANDIDATI.index(MODELLO_ATTIVO) if MODELLO_ATTIVO in MODELLI_CANDIDATI else -1
            except ValueError:
                idx = -1

            # Prova i modelli successivi
            for i in range(idx + 1, len(MODELLI_CANDIDATI)):
                nuovo_modello = MODELLI_CANDIDATI[i]
                try:
                    sys_prompt = build_system_prompt()
                    modello = genai.GenerativeModel(nuovo_modello, system_instruction=sys_prompt)
                    chat = modello.start_chat(history=[])
                    MODELLO_ATTIVO = nuovo_modello
                    r = chat.send_message(ctx + testo)
                    salva_storico(testo, r.text)
                    return r.text
                except Exception as e2:
                    print(f"⚠️ Fallback su {nuovo_modello} fallito: {str(e2)[:100]}")
                    continue

            # Tutti i modelli esauriti
            return ("⚠️ Quota gratuita esaurita per oggi, Padrone~! "
                    "Riprova domani (la quota si resetta a mezzanotte PT = 9:00 italiane) "
                    "oppure crea una nuova API key con un altro account Google. 🦂")

        # Altri errori
        if "API_KEY_INVALID" in err:
            return "❌ La chiave API non è più valida. Clicca 🔑 API Key per aggiornarla."
        if "SAFETY" in err or "blocked" in err.lower():
            return "⚠️ Gemini ha bloccato questa risposta per motivi di sicurezza, Padrone~"
        if "DEADLINE" in err or "timeout" in err.lower():
            return "⚠️ Timeout nella risposta, Padrone~. Riprova."

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
            valore = m.group(1).strip()
            MEMORIA["info"][chiave] = valore
            if chiave == "nome":
                CONFIG["nome_utente"] = valore
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
    if risposta:
        parla(risposta, output)
    else:
        parla(risultati[0].get('body', '')[:300], output)

# ============================================================
# VOLUME
# ============================================================
def cambia_volume(delta):
    if PYCAW_OK:
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            attuale = volume.GetMasterVolumeLevelScalar()
            nuovo = max(0.0, min(1.0, attuale + delta))
            volume.SetMasterVolumeLevelScalar(nuovo, None)
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

def media_key(tasto):
    if keyboard:
        try:
            keyboard.press_and_release(tasto)
            return True
        except Exception:
            pass
    return False

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
        parla("Serve la API key Gemini per vedere lo schermo, Padrone~", output)
        return
    try:
        img = PIL_ImageGrab.grab()
        p = os.path.join(BASE_DIR, "_temp_screen.png")
        img.save(p)

        from PIL import Image as _PILImage
        img_pil = _PILImage.open(p)

        vision_model = genai.GenerativeModel(MODELLO_ATTIVO or "gemini-2.0-flash-lite")
        prompt = (
            "Questa è un'immagine dello schermo del mio Padrone. "
            "Descrivi cosa vedi in massimo 3 frasi, con la personalità di Shaula "
            "(devota, '~', 'ehehe', emoji 🦂💕✨). "
            "Se c'è testo importante sullo schermo, leggilo. "
            "Se c'è un errore o un problema, dillo al Padrone."
        )
        risposta = vision_model.generate_content([prompt, img_pil])
        parla(risposta.text, output)

        try: os.remove(p)
        except: pass
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower():
            parla("⚠️ Quota esaurita anche per la visione, Padrone~", output)
        else:
            parla(f"Errore analisi schermo: {err[:150]}", output)

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
                parla(f"Shaula passa in modalità {mod}, Padrone~! Ehehe~", output)
                return True
        parla("Modalità non riconosciuta. Prova: normale, tsundere, yandere, seria", output)
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
        parla(msg or "Non ricordo ancora nulla, Padrone~", output)
        return True
    if "dimentica tutto" in c:
        MEMORIA = {"ricordi": [], "preferenze": {}, "info": {}}
        salva_json(MEMORIA_FILE, MEMORIA)
        parla("Memoria azzerata, Padrone~", output)
        return True

    # ---- RIASSUNTO ----
    if "riassumi" in c and ("conversazione" in c or "discorso" in c or "detto" in c):
        if not chat or not STORICO["conversazioni"]:
            parla("Nessuna conversazione da riassumere, Padrone~", output)
            return True
        ultime = STORICO["conversazioni"][-20:]
        testo = "\n".join(f"Tu: {x['utente']}\nShaula: {x['shaula']}" for x in ultime)
        risposta = chiedi_gemini(f"Riassumi questa conversazione in 3 frasi:\n\n{testo}")
        parla(risposta or "Errore nel riassunto, Padrone~", output)
        return True

    # ---- RICERCA SU SITI SPECIFICI ----
    if "cerca su google" in c or "cerca google" in c:
        q = re.sub(r"cerca (su )?google", "", c).strip()
        if not q:
            parla("Cosa cerco su Google, Padrone~?", output)
            return True
        webbrowser.open(f"https://www.google.com/search?q={q}")
        parla(f"Cerco '{q}' su Google, Padrone~", output)
        return True

    if "cerca su youtube" in c or "cerca youtube" in c or "cerca su yt" in c or "cerca yt" in c:
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
        if not q:
            parla("Cosa cerco su Wikipedia, Padrone~?", output)
            return True
        webbrowser.open(f"https://it.wikipedia.org/wiki/Special:Search?search={q}")
        parla(f"Cerco '{q}' su Wikipedia, Padrone~", output)
        return True

    m = re.match(r"^cerca\s+(\w+)$", c)
    if m and m.group(1) in SITI_WEB:
        sito = m.group(1)
        webbrowser.open(SITI_WEB[sito])
        parla(f"Apro {sito}, Padrone~!", output)
        return True

    # ---- RICERCA GENERICA ----
    if c.startswith("cerca ") and not c.startswith("cerca su "):
        q = cl[6:].strip()
        if q:
            threading.Thread(target=rispondi_con_ricerca, args=(q, output), daemon=True).start()
        else:
            parla("Cosa cerco, Padrone~?", output)
        return True

    if c.startswith("apri sito") or c.startswith("vai su"):
        url = cl.replace("apri sito", "").replace("vai su", "").strip()
        if not url:
            parla("Quale sito, Padrone~?", output)
            return True
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
    parole_musica = [
        "metti musica", "play musica", "metti un po di musica",
        "metti un pò di musica", "metti un po' di musica", "metti un pò",
        "voglio musica", "ascoltiamo musica", "metti su musica",
        "riproduci musica", "fammi sentire musica", "metti della musica",
    ]
    if any(p in c for p in parole_musica) or c == "musica":
        webbrowser.open("https://music.youtube.com/")
        parla("Shaula mette la musica per te, Padrone~! 🎵 Ehehe~", output)
        return True

    if c.startswith("play ") or c.startswith("riproduci "):
        q = cl[5:] if c.startswith("play ") else cl[10:]
        if q.strip():
            webbrowser.open(f"https://music.youtube.com/search?q={q.strip()}")
            parla(f"Riproduco {q}, Padrone~", output)
        else:
            parla("Cosa riproduco, Padrone~?", output)
        return True

    if "pausa musica" in c or c == "pausa":
        media_key('play/pause media')
        parla("Pausa, Padrone~", output)
        return True
    if "canzone successiva" in c or "prossima canzone" in c or c == "skip":
        media_key('next track')
        parla("Cambio canzone, Padrone~", output)
        return True
    if "canzone precedente" in c:
        media_key('previous track')
        parla("Torno indietro, Padrone~", output)
        return True

    # ---- VOLUME ----
    if any(p in c for p in ["alza volume", "alza il volume", "alzare volume", "volume su", "aumenta volume", "più volume", "piu volume"]):
        cambia_volume(0.10)
        parla("Volume alzato, Padrone~!", output)
        return True
    if any(p in c for p in ["abbassa volume", "abbassa il volume", "volume giù", "volume giu", "diminuisci volume", "meno volume"]):
        cambia_volume(-0.10)
        parla("Volume abbassato, Padrone~", output)
        return True
    if any(p in c for p in ["muto", "silenzio", "muta audio", "togli audio"]):
        toggle_mute()
        parla("Silenziato, Padrone~", output)
        return True

    # ---- TIMER ----
    m = re.search(r"timer\D*(\d+)\s*(secondi|secondo|sec|minuti|minuto|min|ore|ora|h)\b", c)
    if m:
        val = int(m.group(1))
        unit = m.group(2)
        if "sec" in unit:
            sec = val
            unit_txt = f"{val} secondi"
        elif "min" in unit:
            sec = val * 60
            unit_txt = f"{val} minuti"
        else:
            sec = val * 3600
            unit_txt = f"{val} ore"
        avvia_timer(sec, f"Timer di {unit_txt} scaduto!", output)
        parla(f"Timer di {unit_txt} avviato, Padrone~!", output)
        return True

    if "timer" in c:
        parla("Per quanto tempo, Padrone~? Dì: 'timer 5 minuti' o 'imposta un timer di 20 secondi'", output)
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
        parla(f"Shaula ti sveglierà alle {ora}:{minuto:02d}, Padrone~!", output)
        return True

    if "svegliami" in c:
        parla("A che ora devo svegliarti, Padrone~? Dì: 'svegliami alle 7:30'", output)
        return True

    # ---- SCHERMO ----
    if "screenshot" in c:
        if PIL_ImageGrab:
            n = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            PIL_ImageGrab.grab().save(os.path.join(desktop(), n))
            parla(f"Screenshot salvato: {n}", output)
        else:
            parla("Pillow non installato, Padrone~", output)
        return True
    if "cosa vedi" in c or "leggi schermo" in c or "leggi lo schermo" in c or "cosa c'è sullo schermo" in c:
        threading.Thread(target=analizza_schermo, args=(output,), daemon=True).start()
        return True
    if "minimizza tutto" in c or "mostra desktop" in c:
        if keyboard:
            keyboard.press_and_release('windows+d')
        parla("Fatto, Padrone~", output)
        return True
    if "chiudi finestra" in c:
        if keyboard:
            keyboard.press_and_release('alt+f4')
        parla("Finestra chiusa, Padrone~", output)
        return True
    if "modalità scura" in c or "modalita scura" in c:
        try:
            subprocess.run([
                "reg", "add",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                "/v", "AppsUseLightTheme", "/t", "REG_DWORD", "/d", "0", "/f"
            ], capture_output=True)
            parla("Tema scuro attivato, Padrone~", output)
        except Exception as e:
            parla(f"Errore: {e}", output)
        return True

    # ---- UTILITY ----
    m = re.search(r"converti ([\d.]+) ([\w]+) in ([\w]+)", c)
    if m:
        q = f"{m.group(1)} {m.group(2)} in {m.group(3)}"
        webbrowser.open(f"https://www.google.com/search?q={q}")
        parla(f"Cerco la conversione, Padrone~", output)
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
    m = re.search(r"che giorno (?:era|sarà|sara) (?:il )?(\d{1,2})[/\s](\d{1,2})[/\s](\d{2,4})", c)
    if m:
        try:
            g, me, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if a < 100: a += 2000
            d = datetime.date(a, me, g)
            giorni = ["lunedì","martedì","mercoledì","giovedì","venerdì","sabato","domenica"]
            parla(f"Era {giorni[d.weekday()]}, Padrone~!", output)
        except Exception:
            parla("Data non valida, Padrone~", output)
        return True

    # ---- CARTELLE E FILE ----
    if "crea cartella" in c:
        n = cl.lower().replace("crea cartella", "").strip()
        if n:
            os.makedirs(os.path.join(desktop(), n), exist_ok=True)
            parla(f"Cartella '{n}' creata, Padrone~!", output)
        else:
            parla("Nome mancante, Padrone~", output)
        return True
    if "elimina cartella" in c:
        n = cl.lower().replace("elimina cartella", "").strip()
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
    if "cerca file" in c:
        n = cl.lower().replace("cerca file", "").strip()
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
        n = cl[12:].strip() or desktop()
        p = n if os.path.isabs(n) else os.path.join(desktop(), n)
        if os.path.isdir(p):
            os.startfile(p)
            parla("Cartella aperta, Padrone~", output)
        else:
            parla("Non trovata, Padrone~", output)
        return True

    # ---- PROGRAMMI E SITI ----
    if c.startswith("apri "):
        prog = cl[5:].strip()
        prog_low = prog.lower()

        if prog_low in SITI_WEB:
            webbrowser.open(SITI_WEB[prog_low])
            parla(f"Ho aperto {prog}, Padrone~! Ehehe~", output)
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
        else:
            parla("psutil non installato, Padrone~", output)
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

    # ---- APPUNTI ----
    if c.startswith("scrivi appunto"):
        t = cl.replace("scrivi appunto", "").strip()
        if t:
            with open(os.path.join(BASE_DIR, "appunti.txt"), "a", encoding="utf-8") as f:
                f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] {t}\n")
            parla("Appunto salvato, Padrone~", output)
        else:
            parla("Cosa scrivo, Padrone~?", output)
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
        parla("Buonanotte, Padrone~! Shaula veglia su di te! 🌙💕", output)
        return True
    if "buongiorno" in c:
        parla("Buongiorno, Padrone~! Shaula è felicissima di vederti! ☀️🦂", output)
        return True

    # ---- PLUGIN ----
    if os.path.exists(PLUGIN_FILE):
        try:
            import plugins
            importlib.reload(plugins)
            if hasattr(plugins, "esegui"):
                r = plugins.esegui(c, cl, CONFIG, MEMORIA, output)
                if r: return True
        except Exception as e:
            print(f"Errore plugin: {e}")

    # ---- ANTI-ALLUCINAZIONE ----
    if sembra_comando(c):
        parla(f"Shaula non ha capito il comando '{comando}', Padrone~! "
              f"Prova a riformularlo. Ehehe, Shaula è ancora piccolina~ 🦂", output)
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
        root.title("🦂 S.H.A.U.L.A. v4.5")
        root.geometry("900x700")
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
        tk.Button(f, text="🔑 API Key", command=self.imposta_api_key,
                  bg="#ffcc66", fg="#1a1a2e", font=("Segoe UI", 10, "bold"),
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
                        relief=tk.FLAT, activebackground="#ff6b9d",
                        highlightthickness=0)
        mod_menu["menu"].config(bg="#252540", fg="white")
        mod_menu.pack(side=tk.LEFT)

        self.status = tk.Label(f2, text="Pronta, Padrone~!",
                               bg="#1a1a2e", fg="#7fdb8f", font=("Segoe UI", 9))
        self.status.pack(side=tk.RIGHT)

        self.scrivi("🦂 SHAULA: Shaula è pronta, Padrone~! Ehehe~ 🦂\n")
        self.scrivi(f"📁 Cartella: {BASE_DIR}\n")
        if not CONFIG["gemini_api_key"]:
            self.scrivi("⚠️  Clicca il pulsante 🔑 API Key per inserire la chiave Gemini!\n")
        else:
            self.scrivi(f"{inizializza_gemini()}\n")
        self.scrivi("💡 Se vedi errori di quota, riprova più tardi o usa un'altra API key.\n\n")

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
        msg = ("Incolla la tua API key Gemini (inizia con AIza... oppure AQ.):")
        chiave = simpledialog.askstring("🔑 API Key", msg, parent=self.root,
                                        initialvalue=CONFIG.get("gemini_api_key", ""))
        if not chiave: return
        chiave = chiave.strip()
        if not chiave_valida(chiave):
            self.scrivi("❌ Chiave non valida.\n")
            return
        CONFIG["gemini_api_key"] = chiave
        salva_json(CONFIG_FILE, CONFIG)
        self.scrivi(f"💾 Chiave salvata.\n")
        self.scrivi(f"{inizializza_gemini()}\n")

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
