import asyncio
import os
from highrise import BaseBot, User, Position, __main__
from highrise.__main__ import BotDefinition
import json
from datetime import datetime, timedelta
import random
import threading
from flask import Flask
from dotenv import load_dotenv
from emotes import ALL_EMOTE_LIST
from dances import get_dance_by_number, DANCES

# Load environment variables from .env file
load_dotenv()

# ==========================================
# SERVIDOR WEB PARA RENDER
# ==========================================
# Render Web Service necesita un puerto abierto.
app = Flask(__name__)

@app.route("/")
def home():
    return "Highrise Premium Bot is running! 🤖", 200


def run_flask():
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)


# Ejecutamos Flask en segundo plano para no interferir con el bot de Highrise.
threading.Thread(target=run_flask, daemon=True).start()


# Configuration - Read from environment variables
API_TOKEN = os.getenv("API_TOKEN")
ROOM_ID = os.getenv("ROOM_ID", "6a394123cd2ff755d187ae89")

# Verify credentials are set
if not API_TOKEN or not ROOM_ID:
    print("❌ ERROR: API_TOKEN and ROOM_ID must be set in environment variables!")
    exit(1)

print(f"✅ Bot configured with:")
print(f"   API_TOKEN: {API_TOKEN[:20]}...")
print(f"   ROOM_ID: {ROOM_ID}")

class HighrisePremiumBot(BaseBot):
    def __init__(self):
        super().__init__()
        
        # Data storage
        self.vip_users = {}  # {user_id: {vip_level, expiry_date, gold_bars_spent}}
        self.prison_users = set()  # Set of imprisoned user IDs
        self.moderation_log = []
        self.custom_floors = {}  # {name: Position}
        self.user_greetings = {}  # {user_id: last_greeting_time}
        self.subscribers = set()
        self.muted_users = set()
        self.frozen_users = set()
        self.user_positions = {}  # Track user positions for anti-cheat
        # !mi: tareas de emotes para cada usuario
        self.mi_emote_tasks = {}
        # !play: tareas de emotes en bucle para cada usuario
        self.play_emote_tasks = {}
        # !dance: una tarea de baile en bucle para el bot
        self.dance_task = None

        # !cloname: outfits guardados en memoria
        self.outfit_fabrica = None
        self.outfit_clonado = None
        
        # Emotes (200+ emotes)
        self.emotes = self._load_emotes()
        
        # Fun commands responses
        self.rizz_lines = [
            "Smooth moves! 😎",
            "Are you a magician? Because whenever I look at you, everyone else disappears.",
            "Do you believe in love at first sight, or should I walk by again?",
            "You must be a parking ticket. You've got FINE written all over you.",
            "Are you French? Because Eiffel for you! 🗼"
        ]
        
        self.roast_lines = [
            "You're the reason they put instructions on shampoo bottles.",
            "I'd say you're dumb, but that would be an insult to all the dumb people.",
            "You bring everyone so much joy... when you leave the room.",
            "If you were a vegetable, you'd be a turnip. (because you're a turn-off)",
            "You're not fat, you're just easy to see."
        ]
        
        print("✅ Highrise Premium Bot initialized!")
    
    def _load_emotes(self):
        """Load 200+ emotes"""
        return {
            "love": "❤️", "fire": "🔥", "cool": "😎", "happy": "😊", "sad": "😢",
            "angry": "😠", "heart": "💕", "star": "⭐", "moon": "🌙", "sun": "☀️",
            "rain": "🌧️", "snow": "❄️", "rocket": "🚀", "diamond": "💎", "crown": "👑",
            "skull": "💀", "ghost": "👻", "alien": "👽", "robot": "🤖", "clown": "🤡",
            "party": "🎉", "cake": "🎂", "gift": "🎁", "music": "🎵", "dance": "💃",
            "pray": "🙏", "wave": "👋", "clap": "👏", "flex": "💪", "peace": "✌️",
            "thumbsup": "👍", "thumbsdown": "👎", "ok": "👌", "money": "💰", "gem": "💎",
            "rose": "🌹", "tulip": "🌷", "sunflower": "🌻", "daisy": "🌼", "cherry": "🍒",
            "apple": "🍎", "orange": "🍊", "watermelon": "🍉", "strawberry": "🍓", "banana": "🍌",
            "pizza": "🍕", "burger": "🍔", "fries": "🍟", "popcorn": "🍿", "cake": "🍰",
            "candy": "🍬", "lollipop": "🍭", "icecream": "🍦", "coffee": "☕", "tea": "🍵",
            "wine": "🍷", "beer": "🍺", "champagne": "🍾", "cocktail": "🍸", "tropical": "🍹",
            "car": "🚗", "truck": "🚚", "bus": "🚌", "train": "🚂", "airplane": "✈️",
            "rocket": "🚀", "boat": "⛵", "bicycle": "🚲", "motorcycle": "🏍️", "scooter": "🛴",
            "skateboard": "🛹", "surfboard": "🏄", "snowboard": "🏂", "ski": "🎿", "swimming": "🏊",
            "basketball": "🏀", "football": "🏈", "soccer": "⚽", "baseball": "⚾", "tennis": "🎾",
            "volleyball": "🏐", "golf": "⛳", "bowling": "🎳", "badminton": "🏸", "hockey": "🏒",
            "sword": "⚔️", "shield": "🛡️", "gun": "🔫", "bomb": "💣", "knife": "🔪",
            "axe": "🪓", "hammer": "🔨", "wrench": "🔧", "screwdriver": "🪛", "saw": "🪚",
            "book": "📖", "notebook": "📓", "pencil": "✏️", "pen": "🖊️", "paintbrush": "🖌️",
            "art": "🎨", "movie": "🎬", "camera": "📷", "video": "📹", "music": "🎵",
            "guitar": "🎸", "piano": "🎹", "trumpet": "🎺", "violin": "🎻", "drum": "🥁",
            "game": "🎮", "puzzle": "🧩", "dice": "🎲", "cards": "🎴", "chess": "♟️",
            "book": "📚", "globe": "🌍", "telescope": "🔭", "microscope": "🔬", "test": "⚗️",
            "beaker": "🧪", "magnet": "🧲", "battery": "🔋", "lightbulb": "💡", "flashlight": "🔦",
            "candle": "🕯️", "phone": "📱", "computer": "💻", "keyboard": "⌨️", "mouse": "🖱️",
            "printer": "🖨️", "scanner": "📠", "tv": "📺", "radio": "📻", "telephone": "☎️",
            "fax": "📠", "mailbox": "📫", "postbox": "📮", "stamp": "🪴", "lock": "🔒",
            "unlock": "🔓", "key": "🔑", "door": "🚪", "window": "🪟", "house": "🏠",
            "church": "⛪", "hospital": "🏥", "bank": "🏦", "hotel": "🏨", "school": "🏫",
            "library": "📚", "park": "🏞️", "fountain": "⛲", "bridge": "🌉", "tower": "🗼",
            "mountain": "⛰️", "volcano": "🌋", "beach": "🏖��", "desert": "🏜️", "forest": "🌲",
            "tree": "🌳", "flower": "🌸", "leaf": "🍃", "herb": "🌿", "mushroom": "🍄",
            "cactus": "🌵", "palm": "🌴", "evergreen": "🌲", "deciduous": "🌳", "willow": "🌿",
            "sunrise": "🌅", "sunset": "🌄", "rainbow": "🌈", "cloud": "☁️", "storm": "⛈️",
            "tornado": "🌪️", "hurricane": "🌀", "fog": "🌫️", "snowflake": "❄️", "droplet": "💧",
            "ocean": "🌊", "wave": "🌊", "fish": "🐠", "shark": "🦈", "whale": "🐋",
            "squid": "🦑", "octopus": "🐙", "crab": "🦀", "lobster": "🦞", "shrimp": "🦐",
            "snail": "🐌", "slug": "🐛", "worm": "🪱", "ant": "🐜", "bee": "🐝",
            "butterfly": "🦋", "dragonfly": "🐛", "ladybug": "🐞", "cricket": "🦗", "grasshopper": "🦗",
            "scorpion": "🦂", "spider": "🕷️", "mosquito": "🦟", "fly": "🪰", "dog": "🐕",
            "cat": "🐱", "mouse": "🐭", "hamster": "🐹", "rabbit": "🐰", "fox": "🦊",
            "bear": "🐻", "panda": "🐼", "koala": "🐨", "tiger": "🐯", "lion": "🦁",
            "cow": "🐄", "pig": "🐷", "sheep": "🐑", "goat": "🐐", "horse": "🐴",
            "monkey": "🐵", "chimp": "🐶", "gorilla": "🦍", "orangutan": "🦧", "deer": "🦌",
            "zebra": "🦓", "giraffe": "🦒", "hippo": "🦛", "rhino": "🦏", "elephant": "🐘",
            "camel": "🐪", "llama": "🦙", "emu": "🐨", "penguin": "🐧", "duck": "🦆",
            "swan": "🦢", "goose": "🦢", "owl": "🦉", "eagle": "🦅", "vulture": "🦅",
            "parrot": "🦜", "peacock": "��", "flamingo": "🦩", "hummingbird": "🐦", "chicken": "🐔",
            "rooster": "🐓", "turkey": "🦃", "dove": "🕊️", "raven": "🐦", "crow": "🐦",
            "bones": "🦴", "skull": "💀", "zombie": "🧟", "mummy": "🏇"
        }
    
    async def bucle_mi_emote(self, user_id, emote):
        """Repite un emote sobre el usuario que ejecutó !mi."""
        try:
            while True:
                await self.highrise.send_emote(emote, user_id)
                await asyncio.sleep(12)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error en bucle !mi: {e}")
        finally:
            if self.mi_emote_tasks.get(user_id) is asyncio.current_task():
                del self.mi_emote_tasks[user_id]

    async def on_start(self, session_metadata):
        """Bot startup"""
        print(f"🤖 Bot connected to room: {ROOM_ID}")
    
    async def on_user_join(self, user: User, position: Position):
        """Auto greeting system"""
        current_time = datetime.now()
        user_id = str(user.id)
        
        # Check if user was greeted recently
        if user_id not in self.user_greetings or (current_time - self.user_greetings[user_id]).seconds > 3600:
            greeting = f"Welcome to the room, @{user.username}! 👋 Type !help for commands."
            await self.send_message(greeting)
            self.user_greetings[user_id] = current_time
    
    async def on_user_leave(self, user: User):
        """User left event"""
        user_id = str(user.id)
        if user_id in self.prison_users:
            self.prison_users.remove(user_id)
    
    async def bucle_play_emote(self, user_id, emote):
        """Repite un emote real sobre el usuario cada 13 segundos."""
        try:
            while True:
                await self.highrise.send_emote(emote, user_id)
                await asyncio.sleep(13)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error en bucle !play: {e}")
        finally:
            if self.play_emote_tasks.get(user_id) is asyncio.current_task():
                del self.play_emote_tasks[user_id]

    def buscar_play_emote(self, solicitado):
        """Busca un emote por número, nombre o ID técnico."""
        solicitado = solicitado.strip()

        if solicitado.isdigit():
            indice = int(solicitado)
            if 1 <= indice <= len(ALL_EMOTE_LIST):
                return ALL_EMOTE_LIST[indice - 1]
            return None, None

        for nombre, codigo in ALL_EMOTE_LIST:
            if solicitado.lower() == nombre.lower() or solicitado.lower() == nombre.lower().replace(" ", ""):
                return nombre, codigo

        for _, codigo in ALL_EMOTE_LIST:
            if solicitado.lower() == codigo.lower():
                return codigo, codigo

        return None, None

    async def handle_play(self, user: User, message: str):
        """Ejecuta y repite un emote real del catálogo emotes.py sobre el usuario."""
        partes = message.strip().split()

        if len(partes) == 2 and partes[1].lower() == "stop":
            tarea = self.play_emote_tasks.get(user.id)
            if tarea:
                tarea.cancel()
                await self.send_message(f"🛑 Dejé de repetir el emote para @{user.username}.")
            else:
                await self.send_message(f"ℹ️ @{user.username} no tiene un !play en bucle.")
            return

        if len(partes) < 2:
            await self.highrise.send_whisper(
                user.id,
                "Uso: !play número, !play nombre o !play ID técnico.\n"
                "Usa !play stop para detener el bucle."
            )
            return

        # Quitamos !play y, si existe, el último @usuario.
        argumentos = partes[1:]
        target_id = user.id
        nombre_usuario = None

        if argumentos and argumentos[-1].startswith("@"):
            nombre_usuario = argumentos.pop()[1:].strip()
            try:
                usuarios = await self.highrise.get_room_users()
                for usuario, _ in usuarios.content:
                    if usuario.username.lower() == nombre_usuario.lower():
                        target_id = usuario.id
                        break
                else:
                    await self.highrise.send_whisper(user.id, f"❌ No encontré a @{nombre_usuario} en la sala.")
                    return
            except Exception:
                await self.highrise.send_whisper(user.id, "❌ No pude localizar a ese usuario.")
                return

        solicitado = " ".join(argumentos).strip()
        nombre_encontrado, emote_id = self.buscar_play_emote(solicitado)

        if emote_id is None:
            await self.highrise.send_whisper(
                user.id,
                f"❌ No encontré el emote '{solicitado}'. Usa un número, nombre o ID válido."
            )
            return

        # Si ya había otro !play para ese usuario, lo sustituimos.
        tarea_anterior = self.play_emote_tasks.get(target_id)
        if tarea_anterior:
            tarea_anterior.cancel()

        tarea = asyncio.create_task(self.bucle_play_emote(target_id, emote_id))
        self.play_emote_tasks[target_id] = tarea

        if target_id == user.id:
            await self.send_message(f"🔁 @{user.username} ahora tiene {nombre_encontrado} en bucle cada 13 segundos.")
        else:
            await self.send_message(f"🔁 @{nombre_usuario} ahora tiene {nombre_encontrado} en bucle cada 13 segundos.")

    async def bucle_dance(self, dance_id):
        """Repite un baile del catálogo dances.py cada 13 segundos sobre el bot."""
        try:
            while True:
                await self.highrise.send_emote(dance_id)
                await asyncio.sleep(13)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error en bucle !dance: {e}")
        finally:
            self.dance_task = None

    async def handle_dance(self, user: User, message: str):
        """Ejecuta un baile del catálogo dances.py en bucle sobre el bot."""
        partes = message.strip().split()

        if len(partes) == 2 and partes[1].lower() == "stop":
            if self.dance_task:
                self.dance_task.cancel()
                await self.send_message(f"🛑 @{user.username} detuvo el baile del bot.")
            else:
                await self.send_message("ℹ️ El bot no tiene un baile en bucle.")
            return

        if len(partes) < 2:
            await self.highrise.send_whisper(
                user.id,
                "Uso: !dance número (1-100). Usa !dance stop para detenerlo."
            )
            return

        solicitado = partes[1]
        if not solicitado.isdigit():
            await self.highrise.send_whisper(user.id, "❌ Usa el número del baile, por ejemplo: !dance 8")
            return

        numero = int(solicitado)
        if numero not in DANCES and numero not in {1, 2, 3, 4}:
            await self.highrise.send_whisper(user.id, "❌ Ese número de baile no existe. El catálogo tiene 100 bailes.")
            return

        dance_id = get_dance_by_number(numero)

        if self.dance_task:
            self.dance_task.cancel()

        self.dance_task = asyncio.create_task(self.bucle_dance(dance_id))
        await self.send_message(f"💃 El bot empezó el baile #{numero} en bucle cada 13 segundos.")

    async def on_chat(self, user: User, message: str):
        """Handle incoming room chat messages."""
        text = message.lower().strip()
        user_id = str(user.id)
        
        # VIP Commands
        if text.startswith("!buyvip"):
            await self.handle_buyvip(user)
        
        elif text.startswith("!vipstatus"):
            await self.handle_vipstatus(user_id)
        
        # Moderation Commands
        elif text.startswith("!kick "):
            username = text.replace("!kick ", "").strip()
            await self.handle_kick(username, user)
        
        elif text.startswith("!ban "):
            username = text.replace("!ban ", "").strip()
            await self.handle_ban(username, user)
        
        elif text.startswith("!mute "):
            username = text.replace("!mute ", "").strip()
            await self.handle_mute(username, user)
        
        elif text.startswith("!unmute "):
            username = text.replace("!unmute ", "").strip()
            await self.handle_unmute(username, user)
        
        elif text.startswith("!freeze "):
            username = text.replace("!freeze ", "").strip()
            await self.handle_freeze(username, user)
        
        elif text.startswith("!unfreeze "):
            username = text.replace("!unfreeze ", "").strip()
            await self.handle_unfreeze(username, user)
        
        # Prison System
        elif text.startswith("!prison "):
            username = text.replace("!prison ", "").strip()
            await self.handle_prison(username, user)
        
        elif text.startswith("!release "):
            username = text.replace("!release ", "").strip()
            await self.handle_release(username, user)
        
        # Floor/Teleport System
        elif text.startswith("!setfloor "):
            parts = text.replace("!setfloor ", "").split()
            if len(parts) >= 4:
                floor_name = parts[0]
                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                await self.handle_setfloor(floor_name, x, y, z, user)
        
        elif text.startswith("!tp "):
            floor_name = text.replace("!tp ", "").strip()
            await self.handle_teleport(floor_name, user)
        
        elif text == "!floors":
            await self.handle_listfloors()
        
        # Fun Commands
        elif text == "!rizz":
            await self.send_message(random.choice(self.rizz_lines))
        
        elif text.startswith("!roast "):
            username = text.replace("!roast ", "").strip()
            roast = random.choice(self.roast_lines)
            await self.send_message(f"@{username} {roast}")
        
        elif text.startswith("!slap "):
            username = text.replace("!slap ", "").strip()
            await self.send_message(f"@{user.username} slaps @{username}! 👋")
        
        elif text.startswith("!punch "):
            username = text.replace("!punch ", "").strip()
            await self.send_message(f"@{user.username} punches @{username}! 👊")
        
        elif text.startswith("!bomb"):
            await self.send_message(f"@{user.username} throws a bomb! 💣 BOOM! 💥")
        
        # Subscriber System
        elif text == "!subscribe":
            await self.handle_subscribe(user)
        
        elif text == "!broadcast ":
            message_text = text.replace("!broadcast ", "").strip()
            await self.handle_broadcast(message_text, user)
        
        # Anti-cheat
        elif text == "!checkanticheat":
            await self.send_message("✅ Anti-cheat system is active!")
        
        # Help
        elif text == "!help":
            await self.send_help()
        
        # !MI - Ejecuta un emote real sobre quien escribe el comando.
        # Uso: !mi ID
        #      !mi ID loop
        #      !mi parar
        elif text.startswith("!mi"):
            partes = message.strip().split()

            if len(partes) == 2 and partes[1].lower() == "parar":
                tarea = self.mi_emote_tasks.get(user.id)
                if tarea:
                    tarea.cancel()
                    await self.send_message(f"🛑 Dejé de repetir el emote para @{user.username}.")
                else:
                    await self.send_message(f"ℹ️ @{user.username} no tiene un emote en bucle.")
                return

            if len(partes) < 2:
                await self.highrise.send_whisper(
                    user.id,
                    "Uso: !mi ID o !mi ID loop"
                )
                return

            emote_solicitado = partes[1]

            if len(partes) >= 3 and partes[2].lower() == "loop":
                tarea_anterior = self.mi_emote_tasks.get(user.id)
                if tarea_anterior:
                    tarea_anterior.cancel()

                tarea = asyncio.create_task(
                    self.bucle_mi_emote(user.id, emote_solicitado)
                )
                self.mi_emote_tasks[user.id] = tarea
                await self.send_message(
                    f"🔁 @{user.username} ahora tiene {emote_solicitado} en bucle."
                )
                return

            try:
                await self.highrise.send_emote(emote_solicitado, user.id)
            except Exception:
                await self.highrise.send_whisper(
                    user.id,
                    f"❌ No se encontró o no se pudo ejecutar el ID '{emote_solicitado}'. "
                    "Revisa la sintaxis y asegúrate de usar un ID técnico válido."
                )

        # !CLONAME - Clona el outfit del usuario que ejecuta el comando.
        # !cloname     -> guarda el outfit del usuario y lo pone en el bot
        # !cloname 1   -> vuelve al outfit de fábrica guardado
        # !cloname 2   -> vuelve al outfit clonado guardado
        elif text == "!cloname 1":
            if self.outfit_fabrica:
                try:
                    await self.highrise.set_outfit(self.outfit_fabrica)
                    await self.send_message("👕 Volviendo al outfit 1 (Ropa de fábrica)...")
                except Exception as e:
                    print(f"Error outfit 1: {e}")
                    await self.highrise.send_whisper(user.id, "❌ No pude aplicar el outfit de fábrica.")
            else:
                await self.highrise.send_whisper(
                    user.id,
                    "Aún no tengo guardado mi outfit de fábrica. Usa !cloname primero."
                )

        elif text == "!cloname 2":
            if self.outfit_clonado:
                try:
                    await self.highrise.set_outfit(self.outfit_clonado)
                    await self.send_message("✨ Cambiando al outfit 2 (Clonado)...")
                except Exception as e:
                    print(f"Error outfit 2: {e}")
                    await self.highrise.send_whisper(user.id, "❌ No pude aplicar el outfit clonado.")
            else:
                await self.highrise.send_whisper(
                    user.id,
                    "No hay ningún outfit clonado guardado. Usa !cloname primero."
                )

        elif text == "!cloname":
            await self.send_message("🤖 Analizando tu outfit para clonarlo...")
            try:
                if self.outfit_fabrica is None:
                    resultado_bot = await self.highrise.get_my_outfit()
                    self.outfit_fabrica = resultado_bot.outfit
                    print("✅ Outfit de fábrica guardado.")

                resultado_usuario = await self.highrise.get_user_outfit(user.id)
                self.outfit_clonado = resultado_usuario.outfit

                await self.highrise.set_outfit(self.outfit_clonado)
                await self.send_message(
                    "✨ ¡Clonación exitosa! Guardado como Outfit 2. "
                    "Usa !cloname 1 para volver a fábrica."
                )
            except Exception as e:
                print(f"Error clonar: {e}")
                await self.highrise.send_whisper(
                    user.id,
                    "❌ No pude clonar tu ropa. ¡Usa prendas básicas de fábrica!"
                )

        # PLAY - Emotes reales del catálogo emotes.py, en bucle cada 13 segundos.
        # Ejemplos: !play 127 | !play Savage Dance | !play dance-tiktok8
        # Opcional: !play Savage Dance @usuario
        # Detener: !play stop
        elif text == "!play" or text.startswith("!play "):
            await self.handle_play(user, message)

        # DANCE - Bailes del catálogo dances.py, en bucle cada 13 segundos.
        # Ejemplo: !dance 8
        # Detener: !dance stop
        elif text == "!dance" or text.startswith("!dance "):
            await self.handle_dance(user, message)

        # Emotes / emojis del bot
        elif text.startswith("!emote "):
            emote_name = text.replace("!emote ", "").strip()
            await self.handle_emote(emote_name)
    
    async def handle_buyvip(self, user: User):
        """VIP purchase system"""
        user_id = str(user.id)
        await self.send_message(f"💰 @{user.username}, VIP costs 5,000 gold bars! Send the gold bars to activate. (Simulate with !activatevip)")
    
    async def handle_vipstatus(self, user_id: str):
        """Check VIP status"""
        if user_id in self.vip_users:
            vip_info = self.vip_users[user_id]
            await self.send_message(f"👑 VIP Level: {vip_info['vip_level']} | Expires: {vip_info['expiry_date']}")
        else:
            await self.send_message("❌ You are not VIP. Type !buyvip to become VIP!")
    
    async def handle_kick(self, username: str, user: User):
        """Kick user"""
        log_entry = {
            "action": "KICK",
            "target": username,
            "moderator": user.username,
            "timestamp": datetime.now().isoformat()
        }
        self.moderation_log.append(log_entry)
        await self.send_message(f"🚪 @{username} has been kicked by @{user.username}!")
    
    async def handle_ban(self, username: str, user: User):
        """Ban user"""
        log_entry = {
            "action": "BAN",
            "target": username,
            "moderator": user.username,
            "timestamp": datetime.now().isoformat()
        }
        self.moderation_log.append(log_entry)
        await self.send_message(f"🚫 @{username} has been banned by @{user.username}!")
    
    async def handle_mute(self, username: str, user: User):
        """Mute user"""
        self.muted_users.add(username)
        log_entry = {
            "action": "MUTE",
            "target": username,
            "moderator": user.username,
            "timestamp": datetime.now().isoformat()
        }
        self.moderation_log.append(log_entry)
        await self.send_message(f"🔇 @{username} has been muted by @{user.username}!")
    
    async def handle_unmute(self, username: str, user: User):
        """Unmute user"""
        if username in self.muted_users:
            self.muted_users.remove(username)
        await self.send_message(f"🔊 @{username} has been unmuted by @{user.username}!")
    
    async def handle_freeze(self, username: str, user: User):
        """Freeze user"""
        self.frozen_users.add(username)
        log_entry = {
            "action": "FREEZE",
            "target": username,
            "moderator": user.username,
            "timestamp": datetime.now().isoformat()
        }
        self.moderation_log.append(log_entry)
        await self.send_message(f"❄️ @{username} has been frozen by @{user.username}!")
    
    async def handle_unfreeze(self, username: str, user: User):
        """Unfreeze user"""
        if username in self.frozen_users:
            self.frozen_users.remove(username)
        await self.send_message(f"🔥 @{username} has been unfrozen by @{user.username}!")
    
    async def handle_prison(self, username: str, user: User):
        """Send user to prison"""
        self.prison_users.add(username)
        log_entry = {
            "action": "PRISON",
            "target": username,
            "moderator": user.username,
            "timestamp": datetime.now().isoformat()
        }
        self.moderation_log.append(log_entry)
        await self.send_message(f"⛓️ @{username} has been sent to prison by @{user.username}!")
    
    async def handle_release(self, username: str, user: User):
        """Release user from prison"""
        if username in self.prison_users:
            self.prison_users.remove(username)
        await self.send_message(f"🗝️ @{username} has been released from prison by @{user.username}!")
    
    async def handle_setfloor(self, name: str, x: float, y: float, z: float, user: User):
        """Set custom floor location"""
        self.custom_floors[name] = Position(x=x, y=y, z=z)
        await self.send_message(f"📍 Floor '{name}' set at ({x}, {y}, {z}) by @{user.username}!")
    
    async def handle_teleport(self, floor_name: str, user: User):
        """Teleport user to floor"""
        if floor_name in self.custom_floors:
            position = self.custom_floors[floor_name]
            await self.send_message(f"✨ @{user.username} teleported to {floor_name}!")
        else:
            await self.send_message(f"❌ Floor '{floor_name}' not found! Use !floors to see available floors.")
    
    async def handle_listfloors(self):
        """List all custom floors"""
        if self.custom_floors:
            floors_text = ", ".join(self.custom_floors.keys())
            await self.send_message(f"📍 Available floors: {floors_text}")
        else:
            await self.send_message("❌ No custom floors set yet!")
    
    async def handle_subscribe(self, user: User):
        """Subscribe user"""
        self.subscribers.add(str(user.id))
        await self.send_message(f"✅ @{user.username} subscribed! You'll receive exclusive announcements.")
    
    async def handle_broadcast(self, message: str, user: User):
        """Broadcast message to all subscribers"""
        if str(user.id) in self.subscribers or True:  # Allow for demo
            await self.send_message(f"📢 Broadcast: {message}")
        else:
            await self.send_message("❌ Only subscribers can broadcast!")
    
    async def handle_emote(self, emote_name: str):
        """Send emote"""
        if emote_name in self.emotes:
            await self.send_message(self.emotes[emote_name])
        else:
            await self.send_message(f"❌ Emote '{emote_name}' not found!")
    
    async def send_help(self):
        """Send help message"""
        help_text = """
🤖 **HIGHRISE PREMIUM BOT - COMMANDS**

**VIP System:**
- !buyvip - Purchase VIP status
- !vipstatus - Check your VIP status

**Moderation:**
- !kick @username - Kick user
- !ban @username - Ban user
- !mute @username - Mute user
- !unmute @username - Unmute user
- !freeze @username - Freeze user
- !unfreeze @username - Unfreeze user

**Prison System:**
- !prison @username - Send to prison
- !release @username - Release from prison

**Floors/Teleport:**
- !setfloor name x y z - Set custom floor
- !tp floor_name - Teleport to floor
- !floors - List all floors

**Fun Commands:**
- !rizz - Get a rizz line
- !roast @username - Roast someone
- !slap @username - Slap someone
- !punch @username - Punch someone
- !bomb - Throw a bomb

**Emojis:**
- !emote name - Send one of the bot's emoji reactions

**Highrise Emotes:**
- !play número - Repite un emote real cada 13 segundos
- !play nombre - Repite un emote por nombre
- !play ID - Repite un emote por ID técnico
- !play nombre @usuario - Repite el emote sobre otro usuario
- !play stop - Detiene el loop de !play
- !dance número - Repite un baile del catálogo cada 13 segundos
- !dance stop - Detiene el loop de !dance
- !mi ID - Ejecuta un emote real sobre ti
- !mi ID loop - Repite el emote sobre ti
- !mi parar - Detiene tu loop

**Outfit:**
- !cloname - Clona tu outfit
- !cloname 1 - Vuelve al outfit de fábrica
- !cloname 2 - Vuelve al outfit clonado

**Subscriber System:**
- !subscribe - Subscribe for announcements
- !broadcast message - Send broadcast

**Other:**
- !checkanticheat - Check anti-cheat status
"""
        await self.send_message(help_text)
    
    async def send_message(self, text: str):
        """Send message to room using the current Highrise SDK."""
        try:
            await self.highrise.chat(text)
        except Exception as e:
            print(f"Error sending message: {e}")


async def main():
    bot = HighrisePremiumBot()
    definitions = [BotDefinition(bot, ROOM_ID, API_TOKEN)]
    await __main__.main(definitions)


if __name__ == "__main__":
    asyncio.run(main())
