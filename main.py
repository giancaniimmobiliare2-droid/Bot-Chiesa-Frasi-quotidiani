import os
import requests
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import textwrap
import random
import json
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageOps, ImageDraw, ImageFont

# --- CONFIGURAZIONE ---
FACEBOOK_TOKEN = os.environ.get("FACEBOOK_TOKEN")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ENV_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") 

PAGE_ID = "1479209002311050"
MAKE_WEBHOOK_URL = "https://hook.eu1.make.com/mv1cutubs9k3cxedjkkjhuj1g25smgvq"

CSV_FILE = "Frasichiesa.csv"
LOGO_PATH = "logo.png"
FONT_NAME = "arial.ttf" 

# --- 1. GESTIONE DATI ---
def get_random_verse():
    try:
        df = pd.read_csv(CSV_FILE)
        if df.empty: return None
        return df.sample(1).iloc[0]
    except Exception as e:
        print(f"⚠️ Errore lettura CSV: {e}")
        return None

# --- 2. GENERATORE PROMPT ---
def get_image_prompt(categoria):
    cat = str(categoria).lower().strip()
    base_style = "bright, divine light, photorealistic, 8k, sun rays, cinematic"
    
    prompts_consolazione = [
        f"peaceful sunset over calm lake, warm golden light, {base_style}",
        f"gentle morning light through trees, forest path, {base_style}",
        f"hands holding light, soft warm background, {base_style}"
    ]
    prompts_esortazione = [
        f"majestic mountain peak, sunrise rays, dramatic sky, {base_style}",
        f"eagle flying in blue sky, sun flare, freedom, {base_style}",
        f"running water stream, clear river, energy, {base_style}"
    ]
    prompts_altro = [
        f"beautiful blue sky with white clouds, heaven light, {base_style}",
        f"field of flowers, spring, colorful, creation beauty, {base_style}"
    ]

    if "consolazione" in cat: return random.choice(prompts_consolazione)
    elif "esortazione" in cat: return random.choice(prompts_esortazione)
    else: return random.choice(prompts_altro)

# --- 3. AI & IMMAGINI ---
def get_ai_image(prompt_text):
    print(f"🎨 Generazione immagine: {prompt_text}")
    try:
        clean_prompt = prompt_text.replace(" ", "%20")
        url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1080&height=1080&nologo=true"
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"⚠️ Errore AI: {e}")
    return Image.new('RGBA', (1080, 1080), (50, 50, 70))

# --- 4. FUNZIONE CARICAMENTO FONT ---
def load_font(size):
    fonts_to_try = [FONT_NAME, "DejaVuSans-Bold.ttf", "arial.ttf"]
    for font_path in fonts_to_try:
        try:
            return ImageFont.truetype(font_path, size)
        except: continue
    return ImageFont.load_default()

# --- 5. CREAZIONE IMMAGINE ---
def create_verse_image(row):
    prompt = get_image_prompt(row['Categoria'])
    base_img = get_ai_image(prompt).resize((1080, 1080))
    
    overlay = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    W, H = base_img.size
    
    font_txt = load_font(100)  
    font_ref = load_font(60)   

    text = f"“{row['Frase']}”"
    lines = textwrap.wrap(text, width=16) 
    
    line_height = 110
    text_block_height = len(lines) * line_height
    ref_height = 80
    total_content_height = text_block_height + ref_height
    
    start_y = ((H - total_content_height) / 2) - 150
    
    padding = 50
    box_left = 40
    box_top = start_y - padding
    box_right = W - 40
    box_bottom = start_y + total_content_height + padding
    
    draw.rectangle(
        [(box_left, box_top), (box_right, box_bottom)], 
        fill=(0, 0, 0, 140), 
        outline=None
    )
    
    final_img = Image.alpha_composite(base_img, overlay)
    draw_final = ImageDraw.Draw(final_img)
    
    current_y = start_y
    for line in lines:
        bbox = draw_final.textbbox((0, 0), line, font=font_txt)
        w = bbox[2] - bbox[0]
        draw_final.text(((W - w)/2, current_y), line, font=font_txt, fill="white")
        current_y += line_height
        
    ref = str(row['Riferimento'])
    bbox_ref = draw_final.textbbox((0, 0), ref, font=font_ref)
    w_ref = bbox_ref[2] - bbox_ref[0]
    draw_final.text(((W - w_ref)/2, current_y + 25), ref, font=font_ref, fill="#FFD700")

    return final_img

# --- 6. LOGO ---
def add_logo(img):
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH).convert("RGBA")
            w = int(img.width * 0.20)
            h = int(w * (logo.height / logo.width))
            logo = logo.resize((w, h))
            img.paste(logo, ((img.width - w)//2, img.height - h - 30), logo)
        except: pass
    return img

# --- 7. TESTI DINAMICI (MEDITAZIONE & FOOTER WEEKEND) ---
def genera_meditazione(row):
    cat = str(row['Categoria']).lower()
    intro = random.choice(["🔥 𝗣𝗮𝗿𝗼𝗹𝗮 𝗱𝗶 𝗩𝗶𝘁𝗮:", "🕊️ 𝗚𝘂𝗶𝗱𝗮 𝗱𝗲𝗹𝗹𝗼 𝗦𝗽𝗶𝗿𝗶𝘁𝗼:", "🙏 𝗣𝗲𝗿 𝗶𝗹 𝘁𝘂𝗼 𝗖𝘂𝗼𝗿𝗲:", "🙌 𝗚𝗹𝗼𝗿𝗶𝗮 𝗮 𝗗𝗶𝗼:"])
    
    if "consolazione" in cat:
        msgs = ["Fratello, sorella, non temere! Lo Spirito Santo è il Consolatore e oggi asciuga ogni tua lacrima.", "Affida ogni peso a Gesù. Lui ha già portato le tue sofferenze sulla croce per darti pace."]
    elif "esortazione" in cat:
        msgs = ["Alzati nel nome di Gesù! Dichiara vittoria sulla tua situazione.", "Sii forte e coraggioso. Non guardare alle circostanze!"]
    else:
        msgs = ["Metti Dio al primo posto e Lui si prenderà cura di tutto il resto. Amen!", "Ricorda: se Dio è per noi, chi sarà contro di noi?"]

    msg_scelto = random.choice(msgs)
    return f"{intro}\n{msg_scelto}"

def get_footer_message(row):
    """
    Gestisce il messaggio finale in base a GIORNO e ORA.
    - Mattina (tutti i giorni): Frase spirituale standard.
    - Pomeriggio (Sabato): Invito per Domenica.
    - Pomeriggio (Domenica): Invito per il culto delle 18:00.
    """
    # Orario UTC (GitHub) + 1 ora (per approssimare l'Italia)
    now = datetime.utcnow()
    ora_italia = now.hour + 1 
    giorno_settimana = now.weekday() # 5=Sab, 6=Dom

    # Definiamo "Pomeriggio" se sono passate le 13:00
    is_pomeriggio = ora_italia >= 13

    # --- CASO 1: WEEKEND POMERIGGIO (Inviti) ---
    if is_pomeriggio:
        if giorno_settimana == 6: # Domenica Pomeriggio
            frasi_domenica = [
                "Vieni in Chiesa stasera alle 18:00! Gesù ti sta aspettando per dirti parole di vita.",
                "Ti ricordo l'appuntamento con Gesù alle 18:00. Non mancare, c'è una benedizione per te!",
                "La Parola di Dio oggi alle 18:00 sarà detta proprio per il tuo bisogno. Vieni ad ascoltarla!",
                "Gesù ha preparato qualcosa di speciale per te. Ci vediamo al culto delle 18:00!"
            ]
            return f"🚨 𝗔𝗩𝗩𝗜𝗦𝗢 𝗜𝗠𝗣𝗢𝗥𝗧𝗔𝗡𝗧𝗘:\n{random.choice(frasi_domenica)}"
        
        elif giorno_settimana == 5: # Sabato Pomeriggio
            frasi_sabato = [
                "Preparati! Domani alle 18:00 ci riuniamo per lodare il Signore. Non mancare!",
                "Domani è il giorno del Signore! Ti aspettiamo alle 18:00 per ricevere la tua benedizione.",
                "Un invito speciale per te: domani ore 18:00 culto di adorazione. Gesù ti aspetta!"
            ]
            return f"🗓️ 𝗣𝗥𝗢𝗠𝗘𝗠𝗢𝗥𝗜𝗔 𝗣𝗘𝗥 𝗗𝗢𝗠𝗔𝗡𝗜:\n{random.choice(frasi_sabato)}"

    # --- CASO 2: MATTINA o GIORNI FERIALI (Standard) ---
    # Questo scatta sempre la mattina, anche sabato e domenica
    cat = str(row['Categoria']).lower()
    if "consolazione" in cat:
        return random.choice([
            "Nutri il tuo spirito. Dio è il tuo rifugio sicuro nei momenti difficili. Pace a te!",
            "Lascia che la Sua pace custodisca il tuo cuore oggi. Egli è fedele in eterno.",
            "Non sei mai solo: la Sua Parola è balsamo per l'anima. Alleluia!"
        ])
    elif "esortazione" in cat:
        return random.choice([
            "La fede viene dall'udire la Parola di Dio. Alzati e risplendi per la Sua gloria!",
            "Sii un operatore della Parola e non soltanto un uditore. Corri la buona gara!",
            "Nutri il tuo spirito con potenza! Chi confida nell'Eterno rinnova le forze."
        ])
    else:
        return "Nutri il tuo spirito con la Parola oggi. La fede viene dall'udire la Parola di Dio. Alleluia!"

# --- 8. SOCIAL & WEBHOOK ---
def send_telegram(img_bytes, caption):
    if not TELEGRAM_TOKEN: 
        print("⚠️ Token Telegram mancante.")
        return

    recipients = []
    # 1. Vecchio ID da variabili ambiente
    if ENV_CHAT_ID:
        recipients.extend([x.strip() for x in ENV_CHAT_ID.split(',') if x.strip()])
    
    # 2. Nuovo ID manuale
    new_id = "8039921447"
    if new_id not in recipients:
        recipients.append(new_id)

    print(f"📤 Invio Telegram a {len(recipients)} destinatari...")
    
    for chat_id in recipients:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            files = {'photo': ('img.png', img_bytes, 'image/png')}
            data = {'chat_id': chat_id, 'caption': caption}
            response = requests.post(url, files=files, data=data)
            
            if response.status_code == 200:
                print(f"✅ Inviato correttamente a: {chat_id}")
            else:
                print(f"❌ Errore Telegram ({chat_id}): {response.text}")
        except Exception as e:
            print(f"❌ Errore connessione Telegram ({chat_id}): {e}")

def post_facebook(img_bytes, message):
    if not FACEBOOK_TOKEN: return
    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/photos?access_token={FACEBOOK_TOKEN}"
    files = {'file': ('img.png', img_bytes, 'image/png')}
    data = {'message': message, 'published': 'true'}
    try:
        requests.post(url, files=files, data=data)
    except: pass

def trigger_make_webhook(row, img_bytes, meditazione_text):
    print(f"📡 Inviando al nuovo Webhook: {MAKE_WEBHOOK_URL}")
    data_payload = {
        "categoria": row.get('Categoria', 'N/A'),
        "riferimento": row.get('Riferimento', 'N/A'),
        "frase": row.get('Frase', 'N/A'),
        "meditazione": meditazione_text
    }
    files_payload = {'upload_file': ('post_chiesa.png', img_bytes, 'image/png')}
    try:
        response = requests.post(MAKE_WEBHOOK_URL, data=data_payload, files=files_payload)
        if response.status_code == 200:
            print("✅ Webhook Make attivato con successo!")
        else:
            print(f"❌ Errore Webhook: {response.status_code}")
    except Exception as e:
        print(f"❌ Errore connessione Webhook: {e}")

# --- MAIN ---
if __name__ == "__main__":
    row = get_random_verse()
    if row is not None:
        img = add_logo(create_verse_image(row))
        buf = BytesIO()
        img.save(buf, format='PNG')
        img_data = buf.getvalue()
        
        # Genera testi dinamici (con logica Orario + Giorno)
        meditazione = genera_meditazione(row)
        messaggio_footer = get_footer_message(row)
        
        caption = (
            f"📖 {row['Riferimento']}\n\n"
            f"{meditazione}\n\n"
            f"──────────────── 𝗚𝗹𝗼𝗿𝗶𝗮 𝗮 𝗗𝗶𝗼:\n"
            f"{messaggio_footer}\n"
            f"────────────────\n"
            f"⛪ Chiesa L'Eterno Nostra Giustizia\n"
            f"📍 Piazza Umberto I, Grotte (AG)\n"
            f"👤 Pastore Infatino Giuseppe\n\n"
            f"#fede #vangelodelgiorno #chiesa #gesù #preghiera #bibbia #paroladidio #pentecostale"
        )
        
        send_telegram(img_data, caption)
        post_facebook(img_data, caption)
        trigger_make_webhook(row, img_data, meditazione)
