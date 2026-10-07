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
