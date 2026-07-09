import json
import math
import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import tkinter.messagebox as messagebox
import tempfile
import urllib.request
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed

import customtkinter as ctk
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


APP_NAME = "PokeLike Bot"
APP_VERSION = "1.0.3"
UPDATE_REPO = "BIaze420/PokeLike-Bot"
UPDATE_API_URL = f"https://api.github.com/repos/{UPDATE_REPO}/releases/latest"
UPDATE_ASSET_NAMES = ("PokeLike Bot.exe", "PokeLike.Bot.exe")
APP_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = getattr(sys, "_MEIPASS", APP_DIR)
DATA_DIR = (
    os.path.join(os.environ.get("LOCALAPPDATA", APP_DIR), APP_NAME)
    if getattr(sys, "frozen", False)
    else APP_DIR
)
ASSETS_DIR = os.path.join(RESOURCE_DIR, "assets")
BRAND_URL = "https://lunaticlabs.shop/"
DISCORD_URL = "https://discord.gg/lunaticlabs"
BANNER_IMAGE_PATH = os.path.join(ASSETS_DIR, "lunaticlabs_banner.png")
FAVICON_IMAGE_PATH = os.path.join(ASSETS_DIR, "lunaticlabs_logo_transp.png")
FAVICON_ICO_PATH = os.path.join(ASSETS_DIR, "favicon.ico")
DISCORD_ICON_PATH = os.path.join(ASSETS_DIR, "discord_logo.png")
WEBSITE_ICON_PATH = os.path.join(ASSETS_DIR, "website_globe.png")
POKELIKE_URL = "https://pokelike.xyz/"
# The Chrome profile MUST NOT live in a cloud-synced folder (OneDrive/Dropbox):
# those services lock the profile files while Chrome is using them, which crashes
# Chrome on launch with "DevToolsActivePort file doesn't exist" and also blocks the
# profile-reset recovery (WinError 5 / Access denied). Always keep it under
# %LOCALAPPDATA% regardless of where the app or source is run from.
_PROFILE_BASE = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or DATA_DIR
SELENIUM_PROFILE_PATH = os.path.join(_PROFILE_BASE, APP_NAME, "selenium-profile")
LOG_PATH = os.path.join(DATA_DIR, "pokelike_bot.log")
MAX_BROWSER_COUNT = 67
TARGET_ITEM = "shiny charm"
TARGET_ITEM_ALIASES = ("shiny charm", "shiny hunter")
STARTER_NAME = "dratini"
STARTING_ITEM_PRIORITY = (
    "shiny hunter",
    "eject pack",
    "soft sand",
    "shiny power",
    "stardust",
    "yache berry",
    "grassy seed",
    "dragon scale",
    "light clay",
    "power bracer",
    "macho brace",
    "black belt",
    "wise glasses",
)
REGULAR_ITEM_PRIORITY = ("lucky egg", "leftovers", "shell bell", "dragon fang", "rare candy", "tm")
# Master list of every passive item the bot recognizes. Any offered passive whose
# name is NOT in here (and not in the user's priority/ignore lists) is treated as
# unrecognized: it is recorded to unknown_starting_items.json AND auto-added to the
# "don't pick up" set so the bot never selects an item it doesn't understand.
KNOWN_PASSIVE_ITEMS = (
    "adrenaline orb", "air balloon", "aspear berry", "babiri berry", "big mushroom",
    "big root", "binding band", "black belt", "black sludge", "body plate",
    "bright powder", "casteliacone", "cell battery", "charti berry", "chilan berry",
    "chople berry", "cleanse tag", "coba berry", "colbur berry", "comet shard",
    "custap berry", "damp rock", "dark stone", "destiny knot", "draco plate",
    "dragon fang", "dragon scale", "dread plate", "earth plate", "eject button",
    "eject pack", "electirizer", "electric seed", "everstone", "fist plate",
    "flame plate", "float stone", "focus band", "focus sash", "grassy seed",
    "haban berry", "hard stone", "hazard lens", "heat rock", "hp up", "icy rock",
    "insect plate", "iron ball", "iron plate", "iron thorns", "kasib berry",
    "kebia berry", "lagging tail", "lansat berry", "lead sparkle", "leaf stone",
    "legend aegis", "legend lure", "legend might", "legend s call", "life orb",
    "light clay", "lucky punch", "lum berry", "luminous moss", "macho brace",
    "magmarizer", "metal alloy", "metal coat", "metal powder", "mind plate",
    "mirror herb", "misty seed", "muscle band", "mystic water", "never melt ice",
    "occa berry", "oran berry", "pecha berry", "pink bow", "pixie plate",
    "poison barb", "power bracer", "power lens", "pretty feather", "pretty wing",
    "protective pads", "protector", "pure incense", "quick claw", "quick powder",
    "razor claw", "razor fang", "reaper cloth", "resonance", "revival herb",
    "ring target", "rock incense", "rocky helmet", "roseli berry", "sea incense",
    "shed shell", "shiny guard", "shiny hunter", "shiny power", "shoal salt",
    "shuca berry", "silver powder", "sitrus berry", "sky plate", "smoke ball",
    "smooth rock", "snowball", "soft sand", "soothe bell", "spooky plate",
    "star piece", "stardust", "stealth goggles", "sticky barb", "tanga berry",
    "tiny mushroom", "toxic orb", "toxic plate", "wacan berry", "weakness policy",
    "wise glasses", "yache berry",
)
DEFAULT_PASSIVE_ITEM_DETAILS = {
    "adrenaline orb": "The Pokemon with more Speed gains extra power.",
    "air balloon": "Flying Pokemon can dodge incoming damage.",
    "aspear berry": "When your Pokemon heals, it gains extra value from the heal.",
    "big mushroom": "When a Grass Pokemon heals, it gains an additional bonus.",
    "big root": "Your Pokemon heal for part of all damage inflicted.",
    "binding band": "Party slot 1 gains part of your team's power.",
    "black belt": "+35% ATK / +35% DEF.",
    "black sludge": "When an enemy faints, your active Pokemon gains poison-based value.",
    "body plate": "Normal Pokemon deal extra damage based on their bulk.",
    "bright powder": "Normal Pokemon get extra dodge or avoidance value.",
    "casteliacone": "On-hit effects against enemies are improved.",
    "cleanse tag": "Your Pokemon deal extra damage per level.",
    "coba berry": "Your Pokemon deal extra damage per positive stat stage.",
    "colbur berry": "+10% crit chance.",
    "comet shard": "On pickup, replace your team with special Pokemon.",
    "custap berry": "When a Rock Pokemon faints, it triggers a team benefit.",
    "damp rock": "Deal extra damage per negative stat stage on the enemy.",
    "dark stone": "Excessive damage from Dark Pokemon splashes onward.",
    "destiny knot": "When a Pokemon gains ATK, related stats can also improve.",
    "dragon scale": "The first Dragon Pokemon to act gains a strong bonus.",
    "eject button": "When the enemy active faints, your team gains momentum.",
    "eject pack": "Damage your active Pokemon takes is redirected or reduced.",
    "flame plate": "Fire Pokemon benefit more from attack and special attack boosts.",
    "float stone": "If you are faster, on-hit attacks deal extra damage.",
    "focus sash": "Each Pokemon survives a KO once per run or fight.",
    "grassy seed": "At fight start, Grass Pokemon gain defensive boosts.",
    "haban berry": "When a Dragon Pokemon defeats an enemy, it gains a bonus.",
    "hazard lens": "Your non-attack damage, splash, and hazards are stronger.",
    "heat rock": "Fire Pokemon share part of their ATK and Sp. ATK.",
    "hp up": "When your Pokemon defeats an enemy, it gains max HP.",
    "insect plate": "When a Bug Pokemon crits, it triggers extra value.",
    "iron ball": "Enemies deal less damage for each Speed difference or stage.",
    "iron plate": "Your Pokemon take less damage if Steel traits apply.",
    "iron thorns": "Enemy Pokemon take recoil damage based on their attacks.",
    "kebia berry": "Your Pokemon take less damage from poison-related effects.",
    "lagging tail": "If your Pokemon is slower, it gains a damage benefit.",
    "lansat berry": "Psychic splash damage can crit.",
    "lead sparkle": "At the start of combat, your lead Pokemon gains a bonus.",
    "leaf stone": "Grass Pokemon deal damage based on enemy max HP.",
    "legend aegis": "Your Pokemon take less damage for legendary synergy.",
    "legend lure": "From now on, every catch node becomes legendary-focused.",
    "legend might": "Your Pokemon deal more damage for legendary synergy.",
    "legend s call": "On pickup, replace your team with legendary Pokemon.",
    "life orb": "Your Pokemon deal more damage but take recoil.",
    "light clay": "Your Pokemon deal extra damage for each shield or defensive effect.",
    "lucky punch": "On KO, Normal Pokemon gain crit-related value.",
    "lum berry": "Your Pokemon get two random stat boosts.",
    "luminous moss": "When a Water Pokemon is hit, it gains a benefit.",
    "macho brace": "Your Pokemon deal half damage but attack twice.",
    "metal coat": "Damage blocked by Steel traits is reflected.",
    "metal powder": "Your Pokemon are faster.",
    "mirror herb": "When you debuff the enemy active, you gain matching value.",
    "muscle band": "+10% crit chance; crits can raise attack value.",
    "never melt ice": "Frozen shatter damage is improved.",
    "occa berry": "Fire Pokemon gain ATK and Sp. ATK.",
    "oran berry": "+10% crit chance; healing benefits from damage dealt.",
    "pecha berry": "Poison Pokemon heal from poison-related effects.",
    "poison barb": "Your attacks apply poison stacks.",
    "power bracer": "Your Pokemon deal more damage.",
    "power lens": "Your stat boosts are more effective.",
    "pretty feather": "When a Flying Pokemon acts, it gains extra value.",
    "pretty wing": "Your Pokemon deal less damage but gain a defensive benefit.",
    "protector": "Your Pokemon deal extra damage per positive defensive stage.",
    "pure incense": "Deal extra damage per held item slot or item count.",
    "quick claw": "Your Pokemon gain a Speed stage at fight start.",
    "quick powder": "The first Pokemon in your party gains a speed-focused bonus.",
    "razor claw": "+35% crit chance; excess crit chance becomes value.",
    "razor fang": "+10% crit chance; crits can trigger extra effects.",
    "reaper cloth": "Once per fight, Ghost Pokemon trigger a survival or damage effect.",
    "resonance": "Legendary Pokemon count twice for traits.",
    "revival herb": "Your Pokemon cannot heal, but gain a strong compensation bonus.",
    "ring target": "All moves are treated as neutrally effective.",
    "rock incense": "Rock Pokemon benefit more from defensive stats.",
    "rocky helmet": "When your Pokemon takes damage, enemies take recoil.",
    "shed shell": "Bug Pokemon attacks reduce enemy stats.",
    "shiny guard": "Your Pokemon take less damage for shiny synergy.",
    "shiny hunter": "Your shiny rate is doubled for the rest of the run.",
    "shiny power": "Your Pokemon deal extra damage for shiny synergy.",
    "shoal salt": "Normal Pokemon heal max HP each turn or trigger.",
    "sitrus berry": "All healing on your Pokemon is improved.",
    "sky plate": "Flying Pokemon deal bonus damage based on Speed.",
    "smoke ball": "Enemy Pokemon take extra damage from status or hazards.",
    "smooth rock": "When a Ground Pokemon defeats an enemy, it gains a bonus.",
    "soothe bell": "Start-of-fight traits and effects are improved.",
    "star piece": "After every boss, replace your team with special options.",
    "stardust": "Your Pokemon have a chance to level up after combat.",
    "stealth goggles": "Dark Pokemon gain extra value from stealth or status.",
    "sticky barb": "Pokemon you hit get a random stat reduction.",
    "tanga berry": "When a Bug Pokemon faints, your team gains a benefit.",
    "tiny mushroom": "Grass Pokemon use spore-related effects.",
    "toxic orb": "When a poisoned Pokemon faints, poison effects spread.",
    "toxic plate": "Poison Pokemon hitting poisoned targets trigger extra damage.",
    "weakness policy": "Taking super-effective damage grants a damage boost.",
    "wise glasses": "+35% Sp. ATK / +35% Sp. DEF.",
    "yache berry": "Pokemon get a random stat boost.",
}
CONSUMABLE_ITEM_ALIASES = ("rare candy", "tm")
MAIN_MOVE_TARGET_USES = 2
LEGENDARY_POKEMON_NAMES = {
    "articuno", "zapdos", "moltres", "mewtwo", "mew",
    "raikou", "entei", "suicune", "lugia", "ho-oh", "celebi",
    "regirock", "regice", "registeel", "latias", "latios", "kyogre", "groudon", "rayquaza", "jirachi", "deoxys",
    "uxie", "mesprit", "azelf", "dialga", "palkia", "heatran", "regigigas", "giratina", "cresselia", "phione",
    "manaphy", "darkrai", "shaymin", "arceus",
    "victini", "cobalion", "terrakion", "virizion", "tornadus", "thundurus", "reshiram", "zekrom", "landorus",
    "kyurem", "keldeo", "meloetta", "genesect",
}
MODE_FULL_RUN = "Full run"
MODE_SHINY_CHARM_REROLL = "Shiny Charm reroll"
MODE_SHINY_POKEMON_REROLL = "Shiny Pokemon reroll"
MODE_NORMAL_POKEMON_REROLL = "Normal Pokemon reroll"
RUN_TARGET_CHALLENGE = "Challenge Mode"
RUN_TARGET_WEEKLY = "Weekly Challenge"
RUN_TARGET_DAILY = "Daily Challenge"
TOWER_REGIONS = ("Kanto", "Johto", "Hoenn", "Sinnoh", "Unova")
STORY_REGIONS = ("Kanto", "Johto", "Hoenn")
STORY_MODES = ("Classic", "Nuzlocke")
RUN_TARGET_OPTIONS = (
    RUN_TARGET_CHALLENGE,
    RUN_TARGET_WEEKLY,
    RUN_TARGET_DAILY,
    *[f"Battle Tower - {region}" for region in TOWER_REGIONS],
    *[f"Story {mode} - {region}" for mode in STORY_MODES for region in STORY_REGIONS],
)
SCHEDULE_COMPLETION_OPTIONS = ("Wins", "Runs")
DEFAULT_TASK_SCHEDULE = (
    {"target": RUN_TARGET_DAILY, "goal": "Wins", "count": 1},
    {"target": RUN_TARGET_WEEKLY, "goal": "Wins", "count": 1},
    {"target": "Story Classic - Kanto", "goal": "Runs", "count": 100},
)
SETTINGS_PATH = os.path.join(DATA_DIR, "pokelike_settings.json")
UNKNOWN_STARTING_ITEMS_PATH = os.path.join(
    DATA_DIR,
    "unknown_starting_items.json",
)
PASSIVE_ITEM_DETAILS_PATH = os.path.join(
    DATA_DIR,
    "passive_item_details.json",
)
RUN_HISTORY_PATH = os.path.join(
    DATA_DIR,
    "run_history.json",
)
MAX_RUN_HISTORY = 50


def normalize_version_tag(value):
    text = str(value or "").strip().lower()
    if text.startswith("v"):
        text = text[1:]
    parts = []
    for piece in text.split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        if digits:
            parts.append(int(digits))
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:4])


def is_newer_version(remote_version, local_version=APP_VERSION):
    return normalize_version_tag(remote_version) > normalize_version_tag(local_version)


def normalize_asset_name(value):
    return "".join(ch.lower() for ch in str(value or "") if ch.isalnum())


def github_request_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{APP_NAME}/{APP_VERSION}",
        },
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


def latest_release_update_info():
    release = github_request_json(UPDATE_API_URL)
    tag_name = release.get("tag_name") or release.get("name") or ""
    if not is_newer_version(tag_name):
        return None
    wanted_assets = {normalize_asset_name(name) for name in UPDATE_ASSET_NAMES}
    for asset in release.get("assets", []) or []:
        name = asset.get("name") or ""
        if normalize_asset_name(name) in wanted_assets:
            return {
                "version": tag_name,
                "url": asset.get("browser_download_url"),
                "name": name,
            }
    return None


def download_update_asset(update_info):
    url = update_info.get("url")
    if not url:
        raise RuntimeError("Latest release does not include a downloadable bot exe.")
    target_dir = os.path.join(DATA_DIR, "updates")
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, f"{APP_NAME}-{update_info.get('version', 'latest')}.exe")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"},
    )
    with urllib.request.urlopen(request, timeout=60) as response, open(target_path, "wb") as out_file:
        shutil.copyfileobj(response, out_file)
    return target_path


def launch_self_updater(new_exe_path):
    current_exe = sys.executable
    script_path = os.path.join(tempfile.gettempdir(), f"{APP_NAME.replace(' ', '')}-update.ps1")
    script = f"""
$ErrorActionPreference = "Stop"
$pidToWait = {os.getpid()}
$current = {json.dumps(current_exe)}
$new = {json.dumps(new_exe_path)}
$backup = "$current.old"
try {{
    Wait-Process -Id $pidToWait -Timeout 30 -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 600
    if (Test-Path -LiteralPath $backup) {{
        Remove-Item -LiteralPath $backup -Force -ErrorAction SilentlyContinue
    }}
    if (Test-Path -LiteralPath $current) {{
        Move-Item -LiteralPath $current -Destination $backup -Force
    }}
    Move-Item -LiteralPath $new -Destination $current -Force
    Start-Process -FilePath $current
    if (Test-Path -LiteralPath $backup) {{
        Remove-Item -LiteralPath $backup -Force -ErrorAction SilentlyContinue
    }}
}} catch {{
    if ((-not (Test-Path -LiteralPath $current)) -and (Test-Path -LiteralPath $backup)) {{
        Move-Item -LiteralPath $backup -Destination $current -Force
    }}
    Start-Process -FilePath $current
}}
Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
"""
    with open(script_path, "w", encoding="utf-8") as script_file:
        script_file.write(script)
    subprocess.Popen(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            script_path,
        ],
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


class PokeLikeBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("900x700")
        self.minsize(820, 620)
        self.banner_image = None
        self.window_icon = None
        self.discord_icon = None
        self.website_icon = None
        os.makedirs(DATA_DIR, exist_ok=True)
        self.load_brand_assets()

        self.thread_local = threading.local()
        self._driver = None
        self._wait = None
        self.bot_thread = None
        self.stop_event = threading.Event()
        self.start_time = None
        self.stats_lock = threading.Lock()
        self.drivers_lock = threading.Lock()
        self.chromedriver_lock = threading.Lock()
        self.unknown_starting_items_lock = threading.Lock()
        self.passive_item_details_lock = threading.Lock()
        self.run_history_lock = threading.Lock()
        self.unknown_starting_items = self.load_unknown_starting_items()
        self.passive_item_details = self.load_passive_item_details()
        self.run_history = self.load_run_history()
        self.last_wallet_pokegold_total = self.last_run_history_wallet_total()
        self.chromedriver_path = None
        self.worker_drivers = []
        self.worker_errors = []
        self.winning_driver = None
        self.open_browser_thread = None
        self.windows_arranged = False

        self.run_count = 0
        self.next_history_run_number = self.next_run_history_number()
        self.maps_reached = 0
        self.maps_started = 0
        self.item_rolls_checked = 0
        self.total_encounters_checked = 0
        self.target_encounters_seen = 0
        self.total_shinies_seen = 0
        self.total_legendaries_seen = 0
        self.total_money_earned = 0
        self.main_move_upgrades_used = 0
        self.run_encounters_checked = 0
        self.run_target_encounters = 0
        self.run_legendaries_seen = 0
        self.run_leaders_defeated = 0
        self.encounter_history = []
        self.last_team_snapshot = []
        self.last_passive_items_snapshot = []
        self.last_legendary_signature = None
        self.awaiting_leader_item_roll = False
        self.restart_attempt = False
        self.last_item_signature = None
        self.last_money_signature = None
        self.pending_team_replace = False
        self.pending_replace_allow_any = False
        self.pending_replace_policy = "default"
        self.pending_passive_item_name = ""
        self.pending_passive_item_priority = None
        self.catch_reroll_used = False
        self.last_catch_scan_signature = None
        self.settings = self.load_settings()
        self.status_var = ctk.StringVar(value="Idle")
        self.mode_var = ctk.StringVar(value=self.settings.get("mode", MODE_FULL_RUN))
        self.manual_start_var = ctk.BooleanVar(value=bool(self.settings.get("manual_start", False)))
        self.headless_var = ctk.BooleanVar(value=bool(self.settings.get("headless", False)))
        self.current_mode = MODE_FULL_RUN
        self.manual_first_attempt = False
        self.run_target_var = ctk.StringVar(value=self.settings.get("run_target", RUN_TARGET_OPTIONS[0]))
        self.starter_var = ctk.StringVar(value=self.settings.get("starter", STARTER_NAME.title()))
        self.target_pokemon_var = ctk.StringVar(value=self.settings.get("shiny_whitelist", ""))
        self.browser_count_var = ctk.StringVar(value=str(self.settings.get("browser_count", 1)))
        self.schedule_enabled_var = ctk.BooleanVar(value=bool(self.settings.get("schedule_enabled", False)))
        self.browser_count = 1
        self.current_run_target = RUN_TARGET_OPTIONS[0]
        self.current_run_target_info = self.parse_run_target(RUN_TARGET_OPTIONS[0])
        self.current_tower = "Challenge Mode"
        self.current_starter_name = STARTER_NAME
        self.current_target_pokemon = ""
        self.current_target_pokemon_list = []
        self.starting_item_priority = self.parse_priority_text(
            self.settings.get("starting_item_priority", ""),
            STARTING_ITEM_PRIORITY,
        )
        self.regular_item_priority = self.parse_priority_text(
            self.settings.get("regular_item_priority", ""),
            REGULAR_ITEM_PRIORITY,
        )
        self.starting_item_ignore = self.parse_priority_text(
            self.settings.get("starting_item_ignore", ""),
            (),
        )
        # Fold every already-discovered unknown item into the never-pick list so it
        # is both applied (never picked) AND visible/editable in Item Priorities.
        self.merge_unknowns_into_ignore()
        self.priority_window = None
        self.schedule_window = None
        self.run_history_window = None
        self.run_history_list_frame = None
        self.task_schedule = self.parse_task_schedule(
            self.settings.get("task_schedule"),
            DEFAULT_TASK_SCHEDULE,
        )
        self.schedule_active = False
        self.schedule_index = 0
        self.schedule_progress = []
        self.schedule_result_signature = None

        self.build_gui()
        self.after(1000, self.start_update_check)

    def load_brand_assets(self):
        try:
            banner = Image.open(BANNER_IMAGE_PATH)
            self.banner_image = ctk.CTkImage(
                light_image=banner,
                dark_image=banner,
                size=(520, 97),
            )
        except Exception:
            self.banner_image = None

        try:
            self.iconbitmap(FAVICON_ICO_PATH)
            self.window_icon = tk.PhotoImage(file=FAVICON_IMAGE_PATH)
            self.iconphoto(True, self.window_icon)
        except Exception:
            self.window_icon = None

        try:
            discord = Image.open(DISCORD_ICON_PATH)
            self.discord_icon = ctk.CTkImage(
                light_image=discord,
                dark_image=discord,
                size=(40, 40),
            )
        except Exception:
            self.discord_icon = None

        try:
            website = Image.open(WEBSITE_ICON_PATH)
            self.website_icon = ctk.CTkImage(
                light_image=website,
                dark_image=website,
                size=(40, 40),
            )
        except Exception:
            self.website_icon = None

    def open_brand_link(self, _event=None):
        webbrowser.open_new_tab(BRAND_URL)

    def open_discord_link(self):
        webbrowser.open_new_tab(DISCORD_URL)

    def apply_window_icon(self, window):
        def set_icon():
            try:
                window.iconbitmap(FAVICON_ICO_PATH)
            except Exception:
                pass
            try:
                icon = tk.PhotoImage(file=FAVICON_IMAGE_PATH)
                window._lunatic_window_icon = icon
                window.iconphoto(False, icon)
            except Exception:
                try:
                    if self.window_icon is not None:
                        window.iconphoto(False, self.window_icon)
                except Exception:
                    pass

        set_icon()
        try:
            window.after(50, set_icon)
            window.after(250, set_icon)
            window.after(750, set_icon)
        except Exception:
            pass

    def bring_popup_to_front(self, window):
        def raise_window():
            try:
                window.deiconify()
            except Exception:
                pass
            try:
                window.state("normal")
            except Exception:
                pass
            try:
                window.lift()
                window.focus_set()
            except Exception:
                try:
                    window.focus_set()
                except Exception:
                    pass

        raise_window()
        try:
            window.after(50, raise_window)
            window.after(250, raise_window)
        except Exception:
            pass

    def prepare_popup_window(self, window):
        self.apply_window_icon(window)
        self.bring_popup_to_front(window)

    @property
    def driver(self):
        local_driver = getattr(self.thread_local, "driver", None)
        return local_driver or self._driver

    @driver.setter
    def driver(self, value):
        if getattr(self.thread_local, "use_local", False):
            self.thread_local.driver = value
        else:
            self._driver = value

    @property
    def wait(self):
        local_wait = getattr(self.thread_local, "wait", None)
        return local_wait or self._wait

    @wait.setter
    def wait(self, value):
        if getattr(self.thread_local, "use_local", False):
            self.thread_local.wait = value
        else:
            self._wait = value

    def get_context_attr(self, name, default=None):
        if getattr(self.thread_local, "use_local", False) and hasattr(self.thread_local, name):
            return getattr(self.thread_local, name)
        return getattr(self, f"_{name}", default)

    def set_context_attr(self, name, value):
        if getattr(self.thread_local, "use_local", False):
            setattr(self.thread_local, name, value)
        else:
            setattr(self, f"_{name}", value)

    @property
    def awaiting_leader_item_roll(self):
        return self.get_context_attr("awaiting_leader_item_roll", False)

    @awaiting_leader_item_roll.setter
    def awaiting_leader_item_roll(self, value):
        self.set_context_attr("awaiting_leader_item_roll", value)

    @property
    def restart_attempt(self):
        return self.get_context_attr("restart_attempt", False)

    @restart_attempt.setter
    def restart_attempt(self, value):
        self.set_context_attr("restart_attempt", value)

    @property
    def last_item_signature(self):
        return self.get_context_attr("last_item_signature", None)

    @last_item_signature.setter
    def last_item_signature(self, value):
        self.set_context_attr("last_item_signature", value)

    @property
    def last_money_signature(self):
        return self.get_context_attr("last_money_signature", None)

    @last_money_signature.setter
    def last_money_signature(self, value):
        self.set_context_attr("last_money_signature", value)

    @property
    def run_started_at(self):
        return self.get_context_attr("run_started_at", None)

    @run_started_at.setter
    def run_started_at(self, value):
        self.set_context_attr("run_started_at", value)

    @property
    def run_money_earned(self):
        return self.get_context_attr("run_money_earned", 0)

    @run_money_earned.setter
    def run_money_earned(self, value):
        self.set_context_attr("run_money_earned", value)

    @property
    def run_history_signature(self):
        return self.get_context_attr("run_history_signature", None)

    @run_history_signature.setter
    def run_history_signature(self, value):
        self.set_context_attr("run_history_signature", value)

    @property
    def current_history_run_number(self):
        return self.get_context_attr("current_history_run_number", None)

    @current_history_run_number.setter
    def current_history_run_number(self, value):
        self.set_context_attr("current_history_run_number", value)

    @property
    def last_team_snapshot_signature(self):
        return self.get_context_attr("last_team_snapshot_signature", None)

    @last_team_snapshot_signature.setter
    def last_team_snapshot_signature(self, value):
        self.set_context_attr("last_team_snapshot_signature", value)

    @property
    def pending_team_replace(self):
        return self.get_context_attr("pending_team_replace", False)

    @pending_team_replace.setter
    def pending_team_replace(self, value):
        self.set_context_attr("pending_team_replace", value)

    @property
    def pending_replace_allow_any(self):
        return self.get_context_attr("pending_replace_allow_any", False)

    @pending_replace_allow_any.setter
    def pending_replace_allow_any(self, value):
        self.set_context_attr("pending_replace_allow_any", value)

    @property
    def pending_replace_policy(self):
        return self.get_context_attr("pending_replace_policy", "default")

    @pending_replace_policy.setter
    def pending_replace_policy(self, value):
        self.set_context_attr("pending_replace_policy", value)

    @property
    def pending_passive_item_name(self):
        return self.get_context_attr("pending_passive_item_name", "")

    @pending_passive_item_name.setter
    def pending_passive_item_name(self, value):
        self.set_context_attr("pending_passive_item_name", value)

    @property
    def pending_passive_item_priority(self):
        return self.get_context_attr("pending_passive_item_priority", None)

    @pending_passive_item_priority.setter
    def pending_passive_item_priority(self, value):
        self.set_context_attr("pending_passive_item_priority", value)

    @property
    def catch_reroll_used(self):
        return self.get_context_attr("catch_reroll_used", False)

    @catch_reroll_used.setter
    def catch_reroll_used(self, value):
        self.set_context_attr("catch_reroll_used", value)

    @property
    def last_catch_scan_signature(self):
        return self.get_context_attr("last_catch_scan_signature", None)

    @last_catch_scan_signature.setter
    def last_catch_scan_signature(self, value):
        self.set_context_attr("last_catch_scan_signature", value)

    @property
    def run_encounters_checked(self):
        return self.get_context_attr("run_encounters_checked", 0)

    @run_encounters_checked.setter
    def run_encounters_checked(self, value):
        self.set_context_attr("run_encounters_checked", value)

    @property
    def run_target_encounters(self):
        return self.get_context_attr("run_target_encounters", 0)

    @run_target_encounters.setter
    def run_target_encounters(self, value):
        self.set_context_attr("run_target_encounters", value)

    def load_settings(self):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as settings_file:
                data = json.load(settings_file)
        except Exception:
            return {}
        if not isinstance(data, dict):
            return {}
        valid_modes = {
            MODE_FULL_RUN,
            MODE_SHINY_CHARM_REROLL,
            MODE_SHINY_POKEMON_REROLL,
            MODE_NORMAL_POKEMON_REROLL,
        }
        settings = {}
        mode = data.get("mode")
        if mode in valid_modes:
            settings["mode"] = mode
        run_target = data.get("run_target")
        if run_target in RUN_TARGET_OPTIONS:
            settings["run_target"] = run_target
        else:
            legacy_tower = data.get("tower")
            if isinstance(legacy_tower, str) and legacy_tower.strip():
                settings["run_target"] = self.legacy_tower_to_run_target(legacy_tower)
        for key in ["starter", "shiny_whitelist"]:
            value = data.get(key)
            if isinstance(value, str):
                settings[key] = value
        for key in ["starting_item_priority", "regular_item_priority", "starting_item_ignore"]:
            value = data.get(key)
            if isinstance(value, (str, list, tuple)):
                settings[key] = value
        browser_count = data.get("browser_count")
        if isinstance(browser_count, int) and browser_count > 0:
            settings["browser_count"] = min(browser_count, MAX_BROWSER_COUNT)
        for key in ["manual_start", "headless", "schedule_enabled"]:
            value = data.get(key)
            if isinstance(value, bool):
                settings[key] = value
        task_schedule = self.parse_task_schedule(data.get("task_schedule"), DEFAULT_TASK_SCHEDULE)
        if task_schedule:
            settings["task_schedule"] = task_schedule
        return settings

    def legacy_tower_to_run_target(self, value):
        normalized = " ".join(str(value or "").strip().split()).lower()
        if normalized in {"challenge", "challenge mode"}:
            return RUN_TARGET_CHALLENGE
        if normalized == "weekly challenge":
            return RUN_TARGET_WEEKLY
        if normalized == "daily challenge":
            return RUN_TARGET_DAILY
        for region in TOWER_REGIONS:
            if normalized == region.lower():
                return f"Battle Tower - {region}"
        return RUN_TARGET_CHALLENGE

    def parse_run_target(self, label):
        label = label if label in RUN_TARGET_OPTIONS else RUN_TARGET_OPTIONS[0]
        if label == RUN_TARGET_CHALLENGE:
            return {"kind": "challenge", "name": "Challenge Mode", "challenge": "challenge"}
        if label == RUN_TARGET_WEEKLY:
            return {"kind": "challenge", "name": "Weekly Challenge", "challenge": "weekly"}
        if label == RUN_TARGET_DAILY:
            return {"kind": "challenge", "name": "Daily Challenge", "challenge": "daily"}
        if label.startswith("Battle Tower - "):
            return {"kind": "tower", "name": label.replace("Battle Tower - ", "", 1)}
        if label.startswith("Story "):
            prefix, region = label.split(" - ", 1)
            mode = prefix.replace("Story ", "", 1)
            return {"kind": "story", "name": region, "story_mode": mode.lower()}
        return {"kind": "challenge", "name": "Challenge Mode", "challenge": "challenge"}

    def parse_task_schedule(self, value, default_values=()):
        raw_steps = value if isinstance(value, list) and value else list(default_values)
        steps = []
        for item in raw_steps:
            if not isinstance(item, dict):
                continue
            target = item.get("target")
            if target not in RUN_TARGET_OPTIONS:
                continue
            goal = str(item.get("goal", "Wins")).strip().title()
            if goal not in SCHEDULE_COMPLETION_OPTIONS:
                goal = "Wins"
            try:
                count = int(item.get("count", 1))
            except Exception:
                count = 1
            steps.append({"target": target, "goal": goal, "count": max(1, min(count, 9999))})
        return steps or [dict(step) for step in DEFAULT_TASK_SCHEDULE]

    def parse_priority_text(self, text, default_values):
        if isinstance(text, str) and text.strip():
            parts = text.replace(";", "\n").replace(",", "\n").splitlines()
        elif isinstance(text, (list, tuple)):
            parts = text
        else:
            parts = default_values
        seen = set()
        priorities = []
        for item in parts:
            name = self.normalize_item_name(item)
            if not name or name in seen:
                continue
            seen.add(name)
            priorities.append(name)
        return priorities or list(default_values)

    def priority_text(self, values):
        return "\n".join(self.item_label_with_detail(value) for value in values)

    def is_pokemon_reroll_mode(self):
        return self.current_mode in [MODE_SHINY_POKEMON_REROLL, MODE_NORMAL_POKEMON_REROLL]

    def normalize_item_name(self, name):
        name = self.strip_item_detail(name)
        return " ".join(
            "".join(ch.lower() if ch.isalnum() else " " for ch in str(name or "")).split()
        )

    def strip_item_detail(self, text):
        text = str(text or "").strip()
        if text.endswith("]") and "[" in text:
            return text.rsplit("[", 1)[0].strip()
        return text

    def clean_item_detail(self, detail, name=""):
        detail = " ".join(str(detail or "").replace("\n", " ").split())
        if name:
            normalized_name = self.normalize_item_name(name)
            normalized_detail = self.normalize_item_name(detail)
            if normalized_name and normalized_detail.startswith(normalized_name):
                detail = detail[len(str(name).strip()):].strip()
        for prefix in ("Passive", "Starting Item", "Held Item", "Item"):
            if detail.lower().startswith(prefix.lower()):
                detail = detail[len(prefix):].strip(" :-")
        if detail.startswith("[") and detail.endswith("]"):
            detail = detail[1:-1].strip()
        return detail[:160]

    def item_label_with_detail(self, name):
        normalized = self.normalize_item_name(name)
        display = str(name or "").strip() or normalized
        detail = self.passive_item_details.get(normalized, "") if hasattr(self, "passive_item_details") else ""
        return f"{display} [{detail}]" if detail else display

    def load_passive_item_details(self):
        details = {
            self.normalize_item_name(name): self.clean_item_detail(detail, name)
            for name, detail in DEFAULT_PASSIVE_ITEM_DETAILS.items()
            if self.normalize_item_name(name) and self.clean_item_detail(detail, name)
        }
        try:
            with open(PASSIVE_ITEM_DETAILS_PATH, "r", encoding="utf-8") as details_file:
                data = json.load(details_file)
        except Exception:
            return details
        if not isinstance(data, dict):
            return details
        for name, detail in data.items():
            normalized = self.normalize_item_name(name)
            cleaned = self.clean_item_detail(detail, normalized)
            if normalized and cleaned:
                details[normalized] = cleaned
        return details

    def record_passive_item_details(self, items):
        updates = []
        with self.passive_item_details_lock:
            for item in items or []:
                if not isinstance(item, dict):
                    continue
                name = item.get("name", "")
                normalized = self.normalize_item_name(name)
                detail = self.clean_item_detail(item.get("detail", ""), name)
                if not normalized or not detail:
                    continue
                if self.passive_item_details.get(normalized) == detail:
                    continue
                self.passive_item_details[normalized] = detail
                updates.append(normalized)
            if not updates:
                return
            try:
                with open(PASSIVE_ITEM_DETAILS_PATH, "w", encoding="utf-8") as details_file:
                    json.dump(self.passive_item_details, details_file, indent=2, sort_keys=True)
            except Exception as exc:
                self.log(f"Could not save passive item details: {exc}")
                return
        self.log("Passive item detail(s) recorded: " + ", ".join(sorted(updates)))

    def load_unknown_starting_items(self):
        try:
            with open(UNKNOWN_STARTING_ITEMS_PATH, "r", encoding="utf-8") as items_file:
                data = json.load(items_file)
        except Exception:
            return set()
        if not isinstance(data, list):
            return set()
        known_items = {self.normalize_item_name(item) for item in KNOWN_PASSIVE_ITEMS}
        default_priority = {self.normalize_item_name(item) for item in STARTING_ITEM_PRIORITY}
        return {
            self.normalize_item_name(item)
            for item in data
            if self.normalize_item_name(item)
            and self.normalize_item_name(item) not in known_items
            and self.normalize_item_name(item) not in default_priority
        }

    def record_unknown_starting_items(self, names):
        priority_names = {self.normalize_item_name(name) for name in self.starting_item_priority}
        new_items = []
        with self.unknown_starting_items_lock:
            for name in names or []:
                normalized = self.normalize_item_name(name)
                if not normalized or normalized in priority_names or normalized in self.unknown_starting_items:
                    continue
                self.unknown_starting_items.add(normalized)
                new_items.append(normalized)
            if not new_items:
                return
            try:
                with open(UNKNOWN_STARTING_ITEMS_PATH, "w", encoding="utf-8") as items_file:
                    json.dump(sorted(self.unknown_starting_items), items_file, indent=2)
            except Exception as exc:
                self.log(f"Could not save unknown starting items: {exc}")
                return
        # Also surface newly-found unknowns in the never-pick list.
        self.merge_unknowns_into_ignore()
        self.log("Unknown starting item(s) recorded: " + ", ".join(sorted(new_items)))

    def merge_unknowns_into_ignore(self):
        """Add every discovered unknown item to the never-pick (ignore) list so it
        is applied AND shown in the Item Priorities window. Idempotent."""
        try:
            priority_names = {self.normalize_item_name(x) for x in self.starting_item_priority}
            self.starting_item_ignore = [
                item for item in self.starting_item_ignore
                if self.normalize_item_name(item) not in priority_names
            ]
            have = {self.normalize_item_name(x) for x in self.starting_item_ignore}
            for item in sorted(self.unknown_starting_items):
                norm = self.normalize_item_name(item)
                if norm and norm not in priority_names and norm not in have:
                    self.starting_item_ignore.append(item)
                    have.add(norm)
        except Exception:
            pass

    def active_starting_item_ignore(self):
        priority_names = {self.normalize_item_name(name) for name in self.starting_item_priority}
        return [
            item for item in self.starting_item_ignore
            if self.normalize_item_name(item) not in priority_names
        ]

    def save_settings(self):
        settings = {
            "mode": self.mode_var.get(),
            "manual_start": bool(self.manual_start_var.get()),
            "headless": bool(self.headless_var.get()),
            "run_target": self.run_target_var.get(),
            "starter": self.starter_var.get().strip(),
            "shiny_whitelist": self.target_pokemon_var.get().strip(),
            "browser_count": self.parse_browser_count(),
            "schedule_enabled": bool(self.schedule_enabled_var.get()),
            "task_schedule": self.task_schedule,
            "starting_item_priority": self.starting_item_priority,
            "regular_item_priority": self.regular_item_priority,
            "starting_item_ignore": self.starting_item_ignore,
        }
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as settings_file:
                json.dump(settings, settings_file, indent=2)
        except Exception as exc:
            self.log(f"Could not save settings: {exc}")

    def build_gui(self):
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, corner_radius=14)
        header.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        logo = ctk.CTkLabel(
            header,
            image=self.banner_image,
            text="" if self.banner_image else "Lunatic Labs",
            font=ctk.CTkFont(size=28, weight="bold"),
            cursor="hand2",
        )
        logo.grid(row=0, column=0, padx=18, pady=16, sticky="w")
        logo.bind("<Button-1>", self.open_brand_link)

        brand_actions = ctk.CTkFrame(header, fg_color="transparent")
        brand_actions.grid(row=0, column=1, padx=(0, 18), pady=12, sticky="e")
        brand_actions.grid_columnconfigure((0, 1), weight=0)
        discord_button = ctk.CTkLabel(
            brand_actions,
            text="" if self.discord_icon else "Discord",
            image=self.discord_icon,
            width=48,
            height=48,
            cursor="hand2",
        )
        discord_button.grid(row=0, column=0, padx=(0, 12), sticky="e")
        discord_button.bind("<Button-1>", lambda _event: self.open_discord_link())

        website_button = ctk.CTkLabel(
            brand_actions,
            text="" if self.website_icon else "Website",
            image=self.website_icon,
            width=48,
            height=48,
            cursor="hand2",
        )
        website_button.grid(row=0, column=1, sticky="e")
        website_button.bind("<Button-1>", self.open_brand_link)

        controls = ctk.CTkFrame(self, corner_radius=14)
        controls.grid(row=1, column=0, padx=18, pady=8, sticky="ew")
        controls.grid_columnconfigure((0, 1, 2), weight=1)

        self.status_label = self.create_stat(controls, "Status", "Idle", 0, 0)
        self.runtime_label = self.create_stat(controls, "Runtime", "00:00:00", 0, 1)
        self.runs_label = self.create_stat(controls, "Runs", "0", 0, 2)
        self.rolls_label = self.create_stat(controls, "Item rolls checked", "0", 1, 0)
        self.encounters_label = self.create_stat(controls, "Encounters checked", "0", 1, 1)
        self.target_seen_label = self.create_stat(controls, "Target encounters", "0", 1, 2)
        self.shinies_seen_label = self.create_stat(controls, "Shinies seen", "0", 2, 0)
        self.money_label = self.create_stat(controls, "Pokegold", "0", 2, 1)
        self.money_per_hour_label = self.create_stat(controls, "Pokegold / hour", "0/h", 2, 2)

        mode_box = ctk.CTkFrame(controls, fg_color="transparent")
        mode_box.grid(row=3, column=0, columnspan=3, padx=12, pady=(0, 8), sticky="ew")
        mode_box.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(mode_box, text="Mode", text_color="gray70", width=76, anchor="w").grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )
        self.mode_selector = ctk.CTkSegmentedButton(
            mode_box,
            values=[
                MODE_FULL_RUN,
                MODE_SHINY_CHARM_REROLL,
                MODE_SHINY_POKEMON_REROLL,
                MODE_NORMAL_POKEMON_REROLL,
            ],
            variable=self.mode_var,
        )
        self.mode_selector.grid(row=0, column=1, sticky="ew")

        setup_box = ctk.CTkFrame(controls, fg_color="transparent")
        setup_box.grid(row=4, column=0, columnspan=3, padx=12, pady=(0, 8), sticky="ew")
        setup_box.grid_columnconfigure((1, 3, 5), weight=1)

        ctk.CTkLabel(setup_box, text="Run target", text_color="gray70", width=76, anchor="w").grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )
        self.run_target_selector = ctk.CTkOptionMenu(
            setup_box,
            values=list(RUN_TARGET_OPTIONS),
            variable=self.run_target_var,
        )
        self.run_target_selector.grid(row=0, column=1, padx=(0, 12), sticky="ew")

        ctk.CTkLabel(setup_box, text="Starter", text_color="gray70").grid(row=0, column=2, padx=(0, 8), sticky="w")
        self.starter_entry = ctk.CTkEntry(setup_box, textvariable=self.starter_var, placeholder_text="Dratini")
        self.starter_entry.grid(row=0, column=3, padx=(0, 12), sticky="ew")

        ctk.CTkLabel(setup_box, text="Pokemon whitelist", text_color="gray70").grid(row=0, column=4, padx=(0, 8), sticky="w")
        self.target_pokemon_entry = ctk.CTkEntry(setup_box, textvariable=self.target_pokemon_var, placeholder_text="Bagon, Ralts, Riolu")
        self.target_pokemon_entry.grid(row=0, column=5, sticky="ew")

        options_box = ctk.CTkFrame(controls, fg_color="transparent")
        options_box.grid(row=5, column=0, columnspan=3, padx=12, pady=(0, 10), sticky="ew")
        options_box.grid_columnconfigure(0, weight=1, uniform="options")
        options_box.grid_columnconfigure(1, weight=1, uniform="options")

        manual_box = ctk.CTkFrame(options_box, corner_radius=10, fg_color="#151f2c")
        manual_box.grid(row=0, column=0, padx=(0, 6), sticky="nsew")
        manual_box.grid_columnconfigure(0, weight=1)
        manual_box.grid_columnconfigure(2, weight=0)
        self.manual_start_checkbox = ctk.CTkCheckBox(
            manual_box,
            text="Use current run screen on first attempt",
            variable=self.manual_start_var,
        )
        self.manual_start_checkbox.grid(row=0, column=0, padx=12, pady=(10, 0), sticky="w")
        self.headless_checkbox = ctk.CTkCheckBox(
            manual_box,
            text="Run Chrome hidden (headless)",
            variable=self.headless_var,
        )
        self.headless_checkbox.grid(row=1, column=0, padx=12, pady=(6, 10), sticky="w")
        ctk.CTkLabel(manual_box, text="Browsers", text_color="gray70").grid(row=0, column=1, padx=(12, 8), pady=(10, 0), sticky="e")
        self.browser_count_entry = ctk.CTkEntry(manual_box, textvariable=self.browser_count_var, width=70)
        self.browser_count_entry.grid(row=0, column=2, padx=(0, 12), pady=(10, 0), sticky="e")

        schedule_box = ctk.CTkFrame(options_box, corner_radius=10, fg_color="#111827")
        schedule_box.grid(row=0, column=1, padx=(6, 0), sticky="nsew")
        schedule_box.grid_columnconfigure(0, weight=1)
        schedule_top = ctk.CTkFrame(schedule_box, fg_color="transparent")
        schedule_top.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="ew")
        schedule_top.grid_columnconfigure(0, weight=1)
        self.schedule_checkbox = ctk.CTkCheckBox(
            schedule_top,
            text="Task schedule",
            variable=self.schedule_enabled_var,
            command=self.update_schedule_summary,
        )
        self.schedule_checkbox.grid(row=0, column=0, sticky="w")
        self.schedule_button = ctk.CTkButton(
            schedule_top,
            text="Edit",
            command=self.open_schedule_window,
            width=72,
            height=30,
        )
        self.schedule_button.grid(row=0, column=1, padx=(10, 0), sticky="e")
        self.schedule_summary_label = ctk.CTkLabel(
            schedule_box,
            text="",
            text_color="gray78",
            anchor="w",
            justify="left",
            wraplength=360,
        )
        self.schedule_summary_label.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="ew")
        self.update_schedule_summary()

        button_box = ctk.CTkFrame(controls, fg_color="transparent")
        button_box.grid(row=6, column=0, columnspan=3, padx=12, pady=(2, 14), sticky="ew")
        button_box.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.open_browser_button = ctk.CTkButton(button_box, text="Open Browser", command=self.open_browser, height=38)
        self.open_browser_button.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.start_button = ctk.CTkButton(button_box, text="Start Bot", command=self.start_bot, height=38)
        self.start_button.grid(row=0, column=1, padx=6, sticky="ew")

        self.stop_button = ctk.CTkButton(
            button_box,
            text="Stop",
            command=self.stop_bot,
            state="disabled",
            fg_color="#173a63",
            hover_color="#245181",
            height=38,
        )
        self.stop_button.grid(row=0, column=2, padx=(6, 0), sticky="ew")

        self.priority_button = ctk.CTkButton(
            button_box,
            text="Item priorities",
            command=self.open_priority_window,
            height=38,
        )
        self.priority_button.grid(row=0, column=3, padx=(12, 6), sticky="ew")

        self.run_history_button = ctk.CTkButton(
            button_box,
            text="Run history",
            command=self.open_run_history_window,
            height=38,
        )
        self.run_history_button.grid(row=0, column=4, padx=(6, 0), sticky="ew")

    def create_stat(self, parent, label, value, row, column):
        box = ctk.CTkFrame(parent, corner_radius=10)
        box.grid(row=row, column=column, padx=10, pady=12, sticky="ew")
        box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(box, text=label, text_color="gray70").grid(
            row=0, column=0, padx=10, pady=(8, 0), sticky="w"
        )

        value_label = ctk.CTkLabel(box, text=value, font=ctk.CTkFont(size=18, weight="bold"))
        value_label.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="w")
        return value_label

    def schedule_step_label(self, step):
        target = step.get("target", RUN_TARGET_DAILY)
        goal = step.get("goal", "Wins")
        count = int(step.get("count", 1))
        suffix = "win" if goal == "Wins" and count == 1 else goal.lower()
        if goal == "Runs" and count == 1:
            suffix = "run"
        return f"{target} x{count} {suffix}"

    def update_schedule_summary(self):
        if not hasattr(self, "schedule_summary_label"):
            return
        if not self.schedule_enabled_var.get():
            text = "Off"
        else:
            labels = [self.schedule_step_label(step) for step in self.task_schedule[:3]]
            extra = len(self.task_schedule) - len(labels)
            text = "  ->  ".join(labels)
            if extra > 0:
                text = f"{text}  (+{extra})"
        self.schedule_summary_label.configure(text=text)

    def load_run_history(self):
        try:
            with open(RUN_HISTORY_PATH, "r", encoding="utf-8") as history_file:
                data = json.load(history_file)
        except Exception:
            return []
        if not isinstance(data, list):
            return []
        history = []
        for entry in data[-MAX_RUN_HISTORY:]:
            if not isinstance(entry, dict):
                continue
            pokemon = entry.get("pokemon", [])
            history.append({
                "run": int(entry.get("run") or 0),
                "target": str(entry.get("target") or ""),
                "result": str(entry.get("result") or ""),
                "duration": int(entry.get("duration") or 0),
                "money": int(entry.get("money") or 0),
                "wallet_total": (
                    int(entry.get("wallet_total"))
                    if entry.get("wallet_total") is not None
                    else None
                ),
                "score": int(entry.get("score") or 0),
                "score_text": str(entry.get("score_text") or ""),
                "leaders": int(entry.get("leaders") or 0),
                "legendaries": int(entry.get("legendaries") or 0),
                "passive_items": (
                    entry.get("passive_items", [])
                    if isinstance(entry.get("passive_items", []), list)
                    else []
                ),
                "pokemon": pokemon if isinstance(pokemon, list) else [],
                "timestamp": str(entry.get("timestamp") or ""),
            })
        return history[-MAX_RUN_HISTORY:]

    def next_run_history_number(self):
        numbers = [
            int(entry.get("run") or 0)
            for entry in getattr(self, "run_history", [])
            if isinstance(entry, dict)
        ]
        return (max(numbers) if numbers else 0) + 1

    def reserve_run_history_number(self):
        with self.run_history_lock:
            self.next_history_run_number = max(
                int(self.next_history_run_number or 1),
                self.next_run_history_number(),
            )
            run_number = self.next_history_run_number
            self.next_history_run_number += 1
            return run_number

    def last_run_history_wallet_total(self):
        for entry in reversed(getattr(self, "run_history", []) or []):
            if not isinstance(entry, dict):
                continue
            value = entry.get("wallet_total")
            if value is None:
                continue
            try:
                return int(value)
            except Exception:
                continue
        return None

    def save_run_history(self):
        try:
            with open(RUN_HISTORY_PATH, "w", encoding="utf-8") as history_file:
                json.dump(self.run_history[-MAX_RUN_HISTORY:], history_file, indent=2)
        except Exception as exc:
            self.log(f"Could not save run history: {exc}")

    def format_duration_seconds(self, seconds):
        seconds = max(0, int(seconds or 0))
        return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

    def format_team_line(self, pokemon):
        labels = []
        for slot in (pokemon or [])[:6]:
            if not isinstance(slot, dict):
                continue
            name = str(slot.get("name") or "Unknown").strip() or "Unknown"
            level = slot.get("level")
            shiny = " shiny" if slot.get("shiny") else ""
            if level:
                labels.append(f"{name} Lv.{level}{shiny}")
            else:
                labels.append(f"{name}{shiny}")
        return "  |  ".join(labels) if labels else "No team snapshot"

    def format_passive_items_line(self, items):
        labels = []
        seen = set()
        for item in items or []:
            label = " ".join(str(item or "").strip().split())
            key = self.normalize_item_name(label)
            if not label or not key or key in seen:
                continue
            seen.add(key)
            labels.append(label)
        return "  |  ".join(labels) if labels else "No passive snapshot"

    def render_run_history_rows(self):
        frame = self.run_history_list_frame
        if frame is None or not frame.winfo_exists():
            return
        for child in frame.winfo_children():
            child.destroy()

        with self.run_history_lock:
            entries = list(reversed(self.run_history[-MAX_RUN_HISTORY:]))

        if not entries:
            ctk.CTkLabel(
                frame,
                text="No completed runs recorded yet.",
                text_color="gray70",
            ).grid(row=0, column=0, padx=14, pady=14, sticky="w")
            return

        for row, entry in enumerate(entries):
            card = ctk.CTkFrame(frame, corner_radius=10, fg_color="#111827")
            card.grid(row=row, column=0, padx=8, pady=6, sticky="ew")
            card.grid_columnconfigure(0, weight=1)
            result = entry.get("result", "").title() or "Run"
            title = (
                f"Run #{entry.get('run', 0)}  -  {result}  -  "
                f"{self.format_duration_seconds(entry.get('duration', 0))}  -  "
                f"{int(entry.get('money') or 0):,} Pokegold"
            )
            ctk.CTkLabel(
                card,
                text=title,
                anchor="w",
                font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(row=0, column=0, padx=12, pady=(10, 2), sticky="ew")
            meta = entry.get("target") or "Unknown target"
            progress = f"Leaders/E4: {int(entry.get('leaders') or 0)}  -  Legendaries: {int(entry.get('legendaries') or 0)}"
            if entry.get("score"):
                progress = f"{progress}  -  Score: {int(entry.get('score') or 0):,}"
            meta = f"{meta}  -  {progress}"
            if entry.get("timestamp"):
                meta = f"{meta}  -  {entry.get('timestamp')}"
            ctk.CTkLabel(
                card,
                text=meta,
                anchor="w",
                text_color="gray70",
            ).grid(row=1, column=0, padx=12, pady=(0, 2), sticky="ew")
            ctk.CTkLabel(
                card,
                text=self.format_team_line(entry.get("pokemon", [])),
                anchor="w",
                justify="left",
                wraplength=760,
            ).grid(row=2, column=0, padx=12, pady=(0, 10), sticky="ew")
            ctk.CTkLabel(
                card,
                text="Passives: " + self.format_passive_items_line(entry.get("passive_items", [])),
                anchor="w",
                justify="left",
                text_color="gray78",
                wraplength=760,
            ).grid(row=3, column=0, padx=12, pady=(0, 10), sticky="ew")

    def clear_run_history(self):
        if not messagebox.askyesno(
            "Clear run history",
            "Delete all saved run history entries?",
            parent=self.run_history_window or self,
        ):
            return
        with self.run_history_lock:
            self.run_history = []
            self.next_history_run_number = 1
            self.last_wallet_pokegold_total = None
            self.save_run_history()
        self.render_run_history_rows()
        self.log("Run history cleared.")

    def open_run_history_window(self):
        if self.run_history_window is not None and self.run_history_window.winfo_exists():
            self.render_run_history_rows()
            self.bring_popup_to_front(self.run_history_window)
            return

        window = ctk.CTkToplevel(self)
        self.prepare_popup_window(window)
        window.title("Run history")
        window.geometry("860x560")
        window.minsize(700, 430)
        self.prepare_popup_window(window)
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(1, weight=1)
        self.run_history_window = window

        header = ctk.CTkFrame(window, corner_radius=12)
        header.grid(row=0, column=0, padx=16, pady=(16, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text=f"Last {MAX_RUN_HISTORY} completed runs",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=12, pady=12, sticky="w")
        ctk.CTkButton(
            header,
            text="Refresh",
            width=92,
            command=self.render_run_history_rows,
        ).grid(row=0, column=1, padx=(0, 12), pady=12, sticky="e")
        ctk.CTkButton(
            header,
            text="Clear",
            width=82,
            fg_color="#7c2424",
            hover_color="#963030",
            command=self.clear_run_history,
        ).grid(row=0, column=2, padx=(0, 12), pady=12, sticky="e")

        self.run_history_list_frame = ctk.CTkScrollableFrame(window, corner_radius=12)
        self.run_history_list_frame.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.run_history_list_frame.grid_columnconfigure(0, weight=1)
        self.render_run_history_rows()

        def close_window():
            self.run_history_window = None
            self.run_history_list_frame = None
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", close_window)
        self.bring_popup_to_front(window)

    def open_schedule_window(self):
        if self.schedule_window is not None and self.schedule_window.winfo_exists():
            self.bring_popup_to_front(self.schedule_window)
            return

        window = ctk.CTkToplevel(self)
        self.prepare_popup_window(window)
        window.title("Task schedule")
        window.geometry("860x560")
        window.minsize(760, 460)
        self.prepare_popup_window(window)
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(2, weight=1)
        self.schedule_window = window

        header = ctk.CTkFrame(window, corner_radius=12)
        header.grid(row=0, column=0, padx=16, pady=(16, 10), sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkCheckBox(
            header,
            text="Enable schedule",
            variable=self.schedule_enabled_var,
            command=self.update_schedule_summary,
        ).grid(row=0, column=0, padx=12, pady=12, sticky="w")
        ctk.CTkLabel(
            header,
            text="Each task advances when its win or run counter reaches the amount.",
            text_color="gray72",
            anchor="w",
        ).grid(row=0, column=1, padx=(0, 12), pady=12, sticky="ew")

        column_header = ctk.CTkFrame(window, fg_color="transparent")
        column_header.grid(row=1, column=0, padx=18, pady=(0, 4), sticky="ew")
        column_header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(column_header, text="#", width=36, text_color="gray70").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(column_header, text="Run target", text_color="gray70").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(column_header, text="Advance after", width=130, text_color="gray70").grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(column_header, text="Amount", width=90, text_color="gray70").grid(row=0, column=3, sticky="w")

        list_frame = ctk.CTkScrollableFrame(window, corner_radius=12)
        list_frame.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="nsew")
        list_frame.grid_columnconfigure(1, weight=1)
        row_vars = []

        def sync_rows_from_widgets():
            steps = []
            for row in row_vars:
                try:
                    count = int(row["count"].get().strip())
                except Exception:
                    count = 1
                steps.append({
                    "target": row["target"].get(),
                    "goal": row["goal"].get(),
                    "count": max(1, min(count, 9999)),
                })
            return self.parse_task_schedule(steps, DEFAULT_TASK_SCHEDULE)

        def redraw(rows=None):
            for child in list_frame.winfo_children():
                child.destroy()
            row_vars.clear()
            steps = rows if rows is not None else sync_rows_from_widgets()
            for index, step in enumerate(steps):
                target_var = ctk.StringVar(value=step["target"])
                goal_var = ctk.StringVar(value=step["goal"])
                count_var = ctk.StringVar(value=str(step["count"]))
                row_vars.append({"target": target_var, "goal": goal_var, "count": count_var})

                ctk.CTkLabel(list_frame, text=str(index + 1), width=36).grid(
                    row=index, column=0, padx=(8, 6), pady=7, sticky="w"
                )
                ctk.CTkOptionMenu(
                    list_frame,
                    values=list(RUN_TARGET_OPTIONS),
                    variable=target_var,
                ).grid(row=index, column=1, padx=6, pady=7, sticky="ew")
                ctk.CTkOptionMenu(
                    list_frame,
                    values=list(SCHEDULE_COMPLETION_OPTIONS),
                    variable=goal_var,
                    width=120,
                ).grid(row=index, column=2, padx=6, pady=7, sticky="ew")
                ctk.CTkEntry(list_frame, textvariable=count_var, width=76).grid(
                    row=index, column=3, padx=6, pady=7, sticky="ew"
                )
                ctk.CTkButton(
                    list_frame,
                    text="Up",
                    width=54,
                    command=lambda i=index: move_row(i, -1),
                ).grid(row=index, column=4, padx=(8, 3), pady=7)
                ctk.CTkButton(
                    list_frame,
                    text="Down",
                    width=62,
                    command=lambda i=index: move_row(i, 1),
                ).grid(row=index, column=5, padx=3, pady=7)
                ctk.CTkButton(
                    list_frame,
                    text="Remove",
                    width=74,
                    fg_color="#7c2424",
                    hover_color="#963030",
                    command=lambda i=index: remove_row(i),
                ).grid(row=index, column=6, padx=(3, 8), pady=7)

        def move_row(index, direction):
            steps = sync_rows_from_widgets()
            new_index = index + direction
            if new_index < 0 or new_index >= len(steps):
                return
            steps[index], steps[new_index] = steps[new_index], steps[index]
            redraw(steps)

        def remove_row(index):
            steps = sync_rows_from_widgets()
            if len(steps) <= 1:
                return
            del steps[index]
            redraw(steps)

        def add_row():
            steps = sync_rows_from_widgets()
            steps.append({"target": "Story Classic - Kanto", "goal": "Runs", "count": 1})
            redraw(steps)

        def reset_rows():
            redraw([dict(step) for step in DEFAULT_TASK_SCHEDULE])

        def apply_schedule():
            self.task_schedule = sync_rows_from_widgets()
            self.save_settings()
            self.update_schedule_summary()
            close_window()

        def close_window():
            self.schedule_window = None
            window.destroy()

        redraw([dict(step) for step in self.task_schedule])

        button_row = ctk.CTkFrame(window, fg_color="transparent")
        button_row.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="ew")
        button_row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        ctk.CTkButton(button_row, text="Add task", command=add_row).grid(
            row=0, column=0, padx=(0, 6), sticky="ew"
        )
        ctk.CTkButton(button_row, text="Reset default", command=reset_rows).grid(
            row=0, column=1, padx=6, sticky="ew"
        )
        ctk.CTkButton(button_row, text="Save", command=apply_schedule).grid(
            row=0, column=2, padx=6, sticky="ew"
        )
        ctk.CTkButton(button_row, text="Cancel", command=close_window).grid(
            row=0, column=3, padx=6, sticky="ew"
        )
        ctk.CTkButton(
            button_row,
            text="Use now",
            command=lambda: (self.schedule_enabled_var.set(True), apply_schedule()),
        ).grid(row=0, column=4, padx=(6, 0), sticky="ew")
        window.protocol("WM_DELETE_WINDOW", close_window)
        self.bring_popup_to_front(window)

    def open_priority_window(self):
        if self.priority_window is not None and self.priority_window.winfo_exists():
            self.bring_popup_to_front(self.priority_window)
            return

        window = ctk.CTkToplevel(self)
        self.prepare_popup_window(window)
        window.title("Item priorities")
        window.geometry("840x620")
        window.minsize(720, 520)
        self.prepare_popup_window(window)
        window.grid_columnconfigure((0, 1), weight=1)
        window.grid_rowconfigure((2, 4), weight=1)
        self.priority_window = window

        ctk.CTkLabel(
            window,
            text="One item per line. Higher priority lines are picked first; never-pick items are skipped. "
                 "Select a line (or click into it) and use ↓/↑ to move it between the two lists.",
            text_color="gray70",
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 10), sticky="w")

        ctk.CTkLabel(window, text="Starting / passive item priority").grid(
            row=1, column=0, padx=(16, 8), pady=(0, 6), sticky="w"
        )
        ctk.CTkLabel(window, text="Regular reward item priority").grid(
            row=1, column=1, padx=(8, 16), pady=(0, 6), sticky="w"
        )

        starting_text = ctk.CTkTextbox(window, corner_radius=10)
        starting_text.grid(row=2, column=0, padx=(16, 8), pady=(0, 12), sticky="nsew")
        starting_text.insert("1.0", self.priority_text(self.starting_item_priority))

        regular_text = ctk.CTkTextbox(window, corner_radius=10)
        regular_text.grid(row=2, column=1, rowspan=3, padx=(8, 16), pady=(0, 12), sticky="nsew")
        regular_text.insert("1.0", self.priority_text(self.regular_item_priority))

        ignore_header = ctk.CTkFrame(window, fg_color="transparent")
        ignore_header.grid(row=3, column=0, padx=(16, 8), pady=(0, 6), sticky="ew")
        ctk.CTkLabel(ignore_header, text="Starting / passive never-pick list").pack(side="left")
        ctk.CTkButton(
            ignore_header, text="↑ To priority", width=96,
            command=lambda: move_lines(ignore_text, starting_text),
        ).pack(side="right", padx=(6, 0))
        ctk.CTkButton(
            ignore_header, text="↓ To never-pick", width=118,
            command=lambda: move_lines(starting_text, ignore_text),
        ).pack(side="right")

        ignore_text = ctk.CTkTextbox(window, corner_radius=10)
        ignore_text.grid(row=4, column=0, padx=(16, 8), pady=(0, 12), sticky="nsew")
        ignore_text.insert("1.0", self.priority_text(self.starting_item_ignore))

        def _selected_lines(box):
            tb = getattr(box, "_textbox", box)
            try:
                r = tb.tag_ranges("sel")
            except Exception:
                r = None
            if r:
                start = tb.index("%s linestart" % r[0])
                end = tb.index("%s lineend" % r[1])
            else:  # no selection -> the line the cursor is on
                start = tb.index("insert linestart")
                end = tb.index("insert lineend")
            return [ln.strip() for ln in tb.get(start, end).splitlines() if ln.strip()]

        def move_lines(src, dst):
            picks = _selected_lines(src)
            if not picks:
                return
            picked = {p.lower() for p in picks}
            src_lines = [
                ln.strip() for ln in src.get("1.0", "end").splitlines()
                if ln.strip() and ln.strip().lower() not in picked
            ]
            dst_lines = [ln.strip() for ln in dst.get("1.0", "end").splitlines() if ln.strip()]
            have = {ln.lower() for ln in dst_lines}
            for p in picks:
                if p.lower() not in have:
                    dst_lines.append(p)
                    have.add(p.lower())
            src.delete("1.0", "end")
            src.insert("1.0", "\n".join(src_lines))
            dst.delete("1.0", "end")
            dst.insert("1.0", "\n".join(dst_lines))

        button_row = ctk.CTkFrame(window, fg_color="transparent")
        button_row.grid(row=5, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="ew")
        button_row.grid_columnconfigure((0, 1, 2), weight=1)

        def apply_priorities():
            self.starting_item_priority = self.parse_priority_text(
                starting_text.get("1.0", "end"),
                STARTING_ITEM_PRIORITY,
            )
            self.regular_item_priority = self.parse_priority_text(
                regular_text.get("1.0", "end"),
                REGULAR_ITEM_PRIORITY,
            )
            self.starting_item_ignore = self.parse_priority_text(
                ignore_text.get("1.0", "end"),
                (),
            )
            self.save_settings()
            self.log(
                "Updated item priorities: "
                f"{len(self.starting_item_priority)} starting, "
                f"{len(self.regular_item_priority)} regular, "
                f"{len(self.starting_item_ignore)} ignored."
            )
            close_window()

        def reset_priorities():
            starting_text.delete("1.0", "end")
            starting_text.insert("1.0", self.priority_text(STARTING_ITEM_PRIORITY))
            regular_text.delete("1.0", "end")
            regular_text.insert("1.0", self.priority_text(REGULAR_ITEM_PRIORITY))
            ignore_text.delete("1.0", "end")

        def close_window():
            self.priority_window = None
            window.destroy()

        ctk.CTkButton(button_row, text="Save", command=apply_priorities).grid(
            row=0, column=0, padx=(0, 8), sticky="ew"
        )
        ctk.CTkButton(button_row, text="Reset defaults", command=reset_priorities).grid(
            row=0, column=1, padx=8, sticky="ew"
        )
        ctk.CTkButton(button_row, text="Cancel", command=close_window).grid(
            row=0, column=2, padx=(8, 0), sticky="ew"
        )
        window.protocol("WM_DELETE_WINDOW", close_window)
        self.bring_popup_to_front(window)

    def safe_ui(self, fn):
        self.after(0, fn)

    def log(self, message):
        print(message, flush=True)
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(LOG_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass

    def set_status(self, text):
        self.status_var.set(text)
        self.safe_ui(lambda: self.status_label.configure(text=text))

    def start_update_check(self):
        if not getattr(sys, "frozen", False):
            self.log("Update check skipped in source mode.")
            return
        thread = threading.Thread(target=self.update_check_worker, daemon=True)
        thread.start()

    def update_check_worker(self):
        try:
            update_info = latest_release_update_info()
            if not update_info:
                self.log(f"No update available. Current version: {APP_VERSION}.")
                return
            version = update_info.get("version") or "latest"
            self.log(f"Update available: {version}. Downloading...")
            self.safe_ui(lambda: self.set_status(f"Updating to {version}"))
            new_exe_path = download_update_asset(update_info)
            self.safe_ui(lambda: self.install_update_and_exit(new_exe_path, version))
        except Exception as exc:
            self.log(f"Update check failed: {exc}")

    def install_update_and_exit(self, new_exe_path, version):
        self.log(f"Installing update {version}.")
        self.set_status("Restarting update")
        try:
            launch_self_updater(new_exe_path)
        except Exception as exc:
            self.log(f"Could not launch updater: {exc}")
            messagebox.showwarning(
                APP_NAME,
                f"Update {version} downloaded, but the updater could not start.\n\n{exc}",
            )
            self.set_status("Idle")
            return
        self.destroy()

    def format_runtime(self):
        if not self.start_time:
            return "00:00:00"
        seconds = int(time.time() - self.start_time)
        return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

    def format_money_per_hour(self):
        if not self.start_time:
            return "0/h"
        elapsed_seconds = max(time.time() - self.start_time, 1)
        with self.stats_lock:
            total_money = self.total_money_earned
        per_hour = int(total_money * 3600 / elapsed_seconds)
        return f"{per_hour:,}/h"

    def update_runtime_label(self):
        if self.start_time and not self.stop_event.is_set():
            self.runtime_label.configure(text=self.format_runtime())
            self.money_per_hour_label.configure(text=self.format_money_per_hour())
            self.after(1000, self.update_runtime_label)

    def update_stats_labels(self):
        self.safe_ui(lambda: self.runs_label.configure(text=str(self.run_count)))
        self.safe_ui(lambda: self.rolls_label.configure(text=str(self.item_rolls_checked)))
        self.safe_ui(lambda: self.encounters_label.configure(text=str(self.total_encounters_checked)))
        self.safe_ui(lambda: self.target_seen_label.configure(text=str(self.target_encounters_seen)))
        self.safe_ui(lambda: self.shinies_seen_label.configure(text=str(self.total_shinies_seen)))
        self.safe_ui(lambda: self.money_label.configure(text=str(self.total_money_earned)))
        self.safe_ui(lambda: self.money_per_hour_label.configure(text=self.format_money_per_hour()))
        self.safe_ui(self.update_dynamic_stat_cards)

    def update_dynamic_stat_cards(self):
        target_list = getattr(self, "current_target_pokemon_list", []) or []
        if self.current_mode == MODE_FULL_RUN:
            self.rolls_label.master.winfo_children()[0].configure(text="Leaders / E4")
            self.rolls_label.configure(text=str(self.maps_reached))
            self.target_seen_label.master.winfo_children()[0].configure(text="Legendaries")
            self.target_seen_label.configure(text=str(self.total_legendaries_seen))
        elif target_list:
            self.rolls_label.master.winfo_children()[0].configure(text="Item rolls checked")
            self.rolls_label.configure(text=str(self.item_rolls_checked))
            self.target_seen_label.master.winfo_children()[0].configure(text="Target encounters")
            self.target_seen_label.configure(text=str(self.target_encounters_seen))
        else:
            self.rolls_label.master.winfo_children()[0].configure(text="Item rolls checked")
            self.rolls_label.configure(text=str(self.item_rolls_checked))
            self.target_seen_label.master.winfo_children()[0].configure(text="Legendaries")
            self.target_seen_label.configure(text=str(self.total_legendaries_seen))

    def active_schedule_target(self):
        if not self.schedule_active or self.schedule_index >= len(self.task_schedule):
            return None
        return self.task_schedule[self.schedule_index].get("target")

    def apply_active_schedule_target(self):
        target = self.active_schedule_target()
        if not target:
            return False
        if target != self.current_run_target:
            self.current_run_target = target
            self.run_target_var.set(target)
            self.current_run_target_info = self.parse_run_target(target)
            self.current_tower = self.current_run_target_info.get("name", target)
            self.log(f"Schedule switched to: {target}")
        return True

    def result_screen_signature(self, screen):
        try:
            return self.driver.execute_script(
                """
                const active = document.querySelector('.screen.active') || document.body;
                const text = (active.innerText || active.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 200);
                return `${arguments[0]}|${text}`;
                """,
                screen,
            )
        except Exception:
            return f"{screen}|{time.time():.3f}"

    def update_schedule_after_result(self, won, screen):
        if not self.schedule_active:
            return "continue"
        if self.schedule_index >= len(self.task_schedule):
            self.stop_event.set()
            return "done"

        signature = self.result_screen_signature(screen)
        if signature == self.schedule_result_signature:
            return "duplicate"
        self.schedule_result_signature = signature

        step = self.task_schedule[self.schedule_index]
        goal = step.get("goal", "Wins")
        should_count = goal == "Runs" or (goal == "Wins" and won)
        if should_count:
            self.schedule_progress[self.schedule_index] += 1
        progress = self.schedule_progress[self.schedule_index]
        needed = int(step.get("count", 1))
        self.log(
            f"Schedule task {self.schedule_index + 1}/{len(self.task_schedule)} "
            f"{step.get('target')}: {progress}/{needed} {goal.lower()}."
        )

        if progress < needed:
            return "continue"

        self.schedule_index += 1
        self.schedule_result_signature = None
        if self.schedule_index >= len(self.task_schedule):
            self.set_status("Schedule done")
            self.log("Task schedule completed.")
            self.stop_event.set()
            return "done"

        self.apply_active_schedule_target()
        return "advance"

    def open_browser(self):
        if self.open_browser_thread and self.open_browser_thread.is_alive():
            return
        count = self.parse_browser_count()
        self.browser_count = count
        self.windows_arranged = False
        screen_w = max(800, self.winfo_screenwidth())
        screen_h = max(600, self.winfo_screenheight() - 80)
        self.open_browser_button.configure(state="disabled")
        self.set_status("Opening browsers")
        self.open_browser_thread = threading.Thread(
            target=self.open_browser_worker,
            args=(count, screen_w, screen_h),
            daemon=True,
        )
        self.open_browser_thread.start()

    def open_browser_worker(self, count, screen_w, screen_h):
        try:
            drivers = self.launch_missing_drivers(count)
            self.prepare_drivers_concurrently(drivers)
            if not self.headless_var.get():
                self.arrange_browser_windows(screen_w=screen_w, screen_h=screen_h)
            self.windows_arranged = True
            self.log(f"{count} browser window(s) opened on PokeLike. Navigate to the target tower/starter/run, then press Start Bot.")
            self.safe_ui(lambda: self.set_status("Idle"))
        except Exception as exc:
            self.clear_thread_driver()
            self.safe_ui(lambda: self.set_status("Error"))
            self.log(f"ERROR opening browser: {exc}")
            self.safe_ui(
                lambda exc=exc: messagebox.showerror(
                    "PokeLike Bot",
                    f"Could not open Chrome.\n\n{exc}\n\nLog file:\n{LOG_PATH}",
                )
            )
        finally:
            self.safe_ui(lambda: self.open_browser_button.configure(state="normal"))

    def parse_browser_count(self):
        try:
            count = int(str(self.browser_count_var.get()).strip())
        except Exception:
            count = 1
        return max(1, min(count, MAX_BROWSER_COUNT))

    def prepare_single_driver_page(self, driver):
        try:
            current_url = driver.current_url or ""
        except Exception:
            current_url = ""
        if not current_url.startswith(POKELIKE_URL):
            driver.get(POKELIKE_URL)
        WebDriverWait(driver, 20).until(
            lambda _: driver.execute_script("return document.readyState") in ["interactive", "complete"]
        )
        try:
            button = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".qc-cmp2-summary-buttons button:last-child"))
            )
            driver.execute_script(
                """
                arguments[0].scrollIntoView({block: 'center', inline: 'center'});
                arguments[0].dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                arguments[0].dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                arguments[0].click();
                arguments[0].dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                arguments[0].dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
                """,
                button,
            )
        except Exception:
            pass

    def prepare_drivers_concurrently(self, drivers):
        if not drivers:
            return
        max_workers = min(len(drivers), 12)
        self.log(f"Loading Pokelike in {len(drivers)} browser window(s) with {max_workers} parallel worker(s).")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.prepare_single_driver_page, driver) for driver in drivers]
            for future in as_completed(futures):
                future.result()

    def start_bot(self):
        selected_mode = self.mode_var.get()
        target_pokemon_list = [
            name.strip().lower()
            for name in self.target_pokemon_var.get().replace(";", ",").split(",")
            if name.strip()
        ]
        self.run_count = 0
        self.next_history_run_number = self.next_run_history_number()
        self.maps_reached = 0
        self.maps_started = 0
        self.item_rolls_checked = 0
        self.total_encounters_checked = 0
        self.target_encounters_seen = 0
        self.total_shinies_seen = 0
        self.total_legendaries_seen = 0
        self.total_money_earned = 0
        self.main_move_upgrades_used = 0
        self.run_encounters_checked = 0
        self.run_target_encounters = 0
        self.run_legendaries_seen = 0
        self.run_leaders_defeated = 0
        self.encounter_history = []
        self.last_team_snapshot = []
        self.last_passive_items_snapshot = []
        self.last_legendary_signature = None
        self.awaiting_leader_item_roll = False
        self.restart_attempt = False
        self.last_item_signature = None
        self.last_money_signature = None
        self.run_started_at = None
        self.run_money_earned = 0
        self.run_history_signature = None
        self.current_history_run_number = None
        self.last_team_snapshot_signature = None
        self.catch_reroll_used = False
        self.schedule_active = bool(self.schedule_enabled_var.get())
        self.schedule_index = 0
        self.schedule_progress = [0 for _ in self.task_schedule]
        self.schedule_result_signature = None
        self.pending_passive_item_name = ""
        self.pending_passive_item_priority = None
        self.start_time = time.time()
        self.stop_event.clear()
        self.current_mode = selected_mode
        self.manual_first_attempt = bool(self.manual_start_var.get())
        if self.schedule_active:
            self.browser_count_var.set("1")
            self.log("Task schedule enabled; using one browser so tasks advance in order.")
        self.current_run_target = self.active_schedule_target() or self.run_target_var.get()
        self.run_target_var.set(self.current_run_target)
        self.current_run_target_info = self.parse_run_target(self.current_run_target)
        self.current_tower = self.current_run_target_info.get("name", self.current_run_target)
        self.current_starter_name = (self.starter_var.get().strip() or STARTER_NAME).lower()
        self.current_target_pokemon_list = target_pokemon_list
        self.current_target_pokemon = ", ".join(target_pokemon_list)
        self.browser_count = self.parse_browser_count()
        self.winning_driver = None
        self.worker_errors = []
        self.save_settings()

        self.start_button.configure(state="disabled")
        self.open_browser_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.mode_selector.configure(state="disabled")
        self.manual_start_checkbox.configure(state="disabled")
        self.run_target_selector.configure(state="disabled")
        self.schedule_checkbox.configure(state="disabled")
        self.schedule_button.configure(state="disabled")
        self.priority_button.configure(state="disabled")
        self.starter_entry.configure(state="disabled")
        self.target_pokemon_entry.configure(state="disabled")
        self.browser_count_entry.configure(state="disabled")
        self.runtime_label.configure(text="00:00:00")
        self.money_per_hour_label.configure(text="0/h")
        self.update_stats_labels()
        self.set_status("Running")
        self.update_runtime_label()

        self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        self.log("Stopping...")
        self.set_status("Stopping")
        self.stop_event.set()

        self.finish_ui()

    def finish_ui(self):
        self.safe_ui(lambda: self.runtime_label.configure(text=self.format_runtime()))
        self.safe_ui(lambda: self.open_browser_button.configure(state="normal"))
        self.safe_ui(lambda: self.start_button.configure(state="normal"))
        self.safe_ui(lambda: self.stop_button.configure(state="disabled"))
        self.safe_ui(lambda: self.mode_selector.configure(state="normal"))
        self.safe_ui(lambda: self.manual_start_checkbox.configure(state="normal"))
        self.safe_ui(lambda: self.run_target_selector.configure(state="normal"))
        self.safe_ui(lambda: self.schedule_checkbox.configure(state="normal"))
        self.safe_ui(lambda: self.schedule_button.configure(state="normal"))
        self.safe_ui(lambda: self.priority_button.configure(state="normal"))
        self.safe_ui(lambda: self.starter_entry.configure(state="normal"))
        self.safe_ui(lambda: self.target_pokemon_entry.configure(state="normal"))
        self.safe_ui(lambda: self.browser_count_entry.configure(state="normal"))

    def profile_path_for_worker(self, worker_id=1):
        if worker_id <= 1:
            return SELENIUM_PROFILE_PATH
        return f"{SELENIUM_PROFILE_PATH}-{worker_id}"

    def ensure_worker_profile(self, worker_id):
        if worker_id <= 1:
            os.makedirs(SELENIUM_PROFILE_PATH, exist_ok=True)
            return

        source_path = SELENIUM_PROFILE_PATH
        target_path = self.profile_path_for_worker(worker_id)
        if os.path.isdir(os.path.join(target_path, "Default")):
            return

        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        if not os.path.isdir(source_path):
            os.makedirs(target_path, exist_ok=True)
            return

        ignore = shutil.ignore_patterns(
            "Singleton*",
            "LOCK",
            "lockfile",
            "Crashpad",
            "BrowserMetrics*",
            "ShaderCache",
            "GrShaderCache",
            "DawnCache",
            "GPUCache",
            "Code Cache",
            "Cache",
        )
        try:
            shutil.copytree(source_path, target_path, dirs_exist_ok=True, ignore=ignore)
            self.log(f"Seeded browser {worker_id} profile from main Chrome profile.")
        except Exception as exc:
            os.makedirs(target_path, exist_ok=True)
            self.log(f"Could not copy main profile for browser {worker_id}; using empty profile: {exc}")

    def get_chromedriver_path(self):
        with self.chromedriver_lock:
            if not self.chromedriver_path:
                self.chromedriver_path = ChromeDriverManager().install()
            return self.chromedriver_path

    def is_chrome_profile_startup_crash(self, exc):
        message = str(exc).lower()
        return (
            "devtoolsactiveport" in message
            or "chrome failed to start: crashed" in message
            or "processsingleton" in message
        )

    def quarantine_browser_profile(self, profile_path, worker_id):
        if not os.path.isdir(profile_path):
            return False
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        backup_path = f"{profile_path}.broken-{timestamp}"
        try:
            os.replace(profile_path, backup_path)
            self.log(
                f"Chrome profile for browser {worker_id} appears corrupted or locked; "
                f"moved it to {backup_path} and retrying with a fresh profile."
            )
            return True
        except Exception as exc:
            self.log(f"Could not move broken Chrome profile {profile_path}: {exc}")
            return False

    def recovery_profile_path_for_worker(self, worker_id):
        suffix = "" if worker_id <= 1 else f"-{worker_id}"
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        return f"{SELENIUM_PROFILE_PATH}{suffix}.recovery-{timestamp}"

    def launch_driver(self, worker_id=1, make_active=True):
        self.ensure_worker_profile(worker_id)
        profile_path = self.profile_path_for_worker(worker_id)
        os.makedirs(profile_path, exist_ok=True)

        try:
            headless = bool(self.headless_var.get())
        except Exception:
            headless = False

        def build_options(safe=False, active_profile_path=None):
            active_profile_path = active_profile_path or profile_path
            o = webdriver.ChromeOptions()
            o.add_argument(f"--user-data-dir={active_profile_path}")
            o.add_argument("--profile-directory=Default")
            o.add_argument("--no-first-run")
            o.add_argument("--no-default-browser-check")
            o.add_experimental_option("excludeSwitches", ["enable-logging"])
            if headless:
                # Headless needs these to launch reliably.
                o.add_argument("--headless=new")
                o.add_argument("--window-size=1400,1000")
                o.add_argument("--mute-audio")
                o.add_argument("--disable-gpu")
                o.add_argument("--no-sandbox")
                o.add_argument("--disable-dev-shm-usage")
            if safe:
                # Minimal, known-good config used as a fallback: if any enhancement
                # flag upsets this Chrome (e.g. "DevToolsActivePort file doesn't
                # exist"), we still launch. Visible mode gets --start-maximized.
                if not headless:
                    o.add_argument("--start-maximized")
                return o
            # Enhancements: keep the game's loop running while minimized/occluded,
            # and let Chrome pick a free DevTools port.
            o.add_argument("--disable-background-timer-throttling")
            o.add_argument("--disable-backgrounding-occluded-windows")
            o.add_argument("--disable-renderer-backgrounding")
            o.add_argument("--remote-debugging-port=0")
            if not headless:
                o.add_argument("--start-maximized")
            return o

        def start_chrome(opts):
            try:
                return webdriver.Chrome(
                    service=Service(self.get_chromedriver_path()),
                    options=opts,
                )
            except Exception as manager_exc:
                self.log(f"ChromeDriverManager launch failed, trying Selenium Manager fallback: {manager_exc}")
                try:
                    return webdriver.Chrome(options=opts)
                except Exception as selenium_exc:
                    raise RuntimeError(
                        "Chrome could not be opened. Make sure Google Chrome is installed, then try Open Browser again. "
                        f"ChromeDriverManager error: {manager_exc}; Selenium Manager error: {selenium_exc}"
                    ) from selenium_exc

        try:
            driver = start_chrome(build_options(safe=False))
        except Exception as first_exc:
            if not self.is_chrome_profile_startup_crash(first_exc):
                raise
            # 1) Retry with the minimal/known-good flags (rules out a bad flag).
            self.log("Chrome failed to start; retrying with minimal launch flags.")
            try:
                driver = start_chrome(build_options(safe=True))
            except Exception as safe_exc:
                # 2) Still failing -> the profile is likely locked/corrupt: reset it.
                if self.quarantine_browser_profile(profile_path, worker_id):
                    os.makedirs(profile_path, exist_ok=True)
                    try:
                        driver = start_chrome(build_options(safe=True))
                    except Exception as retry_exc:
                        recovery_profile_path = self.recovery_profile_path_for_worker(worker_id)
                        os.makedirs(recovery_profile_path, exist_ok=True)
                        self.log(
                            f"Chrome still failed after profile reset; retrying browser {worker_id} "
                            f"with clean recovery profile {recovery_profile_path}."
                        )
                        try:
                            driver = start_chrome(build_options(safe=True, active_profile_path=recovery_profile_path))
                        except Exception as recovery_exc:
                            raise RuntimeError(
                                f"Chrome still could not be opened after resetting the browser {worker_id} profile "
                                f"and trying a clean recovery profile. Original error: {first_exc}; "
                                f"reset retry error: {retry_exc}; recovery retry error: {recovery_exc}"
                            ) from recovery_exc
                else:
                    recovery_profile_path = self.recovery_profile_path_for_worker(worker_id)
                    os.makedirs(recovery_profile_path, exist_ok=True)
                    self.log(
                        f"Chrome profile for browser {worker_id} could not be reset; "
                        f"retrying with clean recovery profile {recovery_profile_path}."
                    )
                    try:
                        driver = start_chrome(build_options(safe=True, active_profile_path=recovery_profile_path))
                    except Exception as recovery_exc:
                        raise RuntimeError(
                            f"Chrome still could not be opened after retrying browser {worker_id} "
                            f"with minimal flags and a clean recovery profile. Original error: {first_exc}; "
                            f"minimal-flags error: {safe_exc}; recovery retry error: {recovery_exc}"
                        ) from recovery_exc
        wait = WebDriverWait(driver, 30)
        if make_active:
            self.driver = driver
            self.wait = wait
        with self.drivers_lock:
            if driver not in self.worker_drivers:
                self.worker_drivers.append(driver)
        return driver

    def launch_missing_drivers(self, count):
        live_drivers = self.get_live_drivers()
        missing_worker_ids = list(range(len(live_drivers) + 1, count + 1))
        if missing_worker_ids:
            max_workers = min(len(missing_worker_ids), 12)
            self.log(f"Launching {len(missing_worker_ids)} browser window(s) with {max_workers} parallel worker(s).")
            launched = {}
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.launch_driver, worker_id, False): worker_id
                    for worker_id in missing_worker_ids
                }
                for future in as_completed(futures):
                    worker_id = futures[future]
                    launched[worker_id] = future.result()
            live_drivers.extend(launched[worker_id] for worker_id in missing_worker_ids)
        if live_drivers and not self._driver:
            self._driver = live_drivers[0]
            self._wait = WebDriverWait(self._driver, 30)
        return live_drivers[:count]

    def get_live_drivers(self):
        live = []
        with self.drivers_lock:
            for driver in self.worker_drivers:
                try:
                    _ = driver.current_url
                    live.append(driver)
                except Exception:
                    pass
            self.worker_drivers = live
        if not live and self._driver:
            try:
                _ = self._driver.current_url
                live.append(self._driver)
                with self.drivers_lock:
                    self.worker_drivers = live
            except Exception:
                self._driver = None
                self._wait = None
        return live

    def clear_thread_driver(self):
        self.thread_local.driver = None
        self.thread_local.wait = None
        self.thread_local.use_local = False

    def arrange_browser_windows(self, screen_w=None, screen_h=None):
        drivers = self.get_live_drivers()[: self.browser_count or self.parse_browser_count()]
        if not drivers:
            return
        count = len(drivers)
        cols = max(1, math.ceil(math.sqrt(count)))
        rows = max(1, math.ceil(count / cols))
        screen_w = screen_w or max(800, self.winfo_screenwidth())
        screen_h = screen_h or max(600, self.winfo_screenheight() - 80)
        width = max(120, screen_w // cols)
        height = max(120, screen_h // rows)
        for idx, driver in enumerate(drivers):
            try:
                x = (idx % cols) * width
                y = (idx // cols) * height
                driver.set_window_rect(x=x, y=y, width=width, height=height)
            except Exception:
                pass

    def close_other_drivers(self, keep_driver):
        with self.drivers_lock:
            drivers = list(self.worker_drivers)
        for driver in drivers:
            if driver is keep_driver:
                continue
            try:
                driver.quit()
            except Exception:
                pass
        with self.drivers_lock:
            self.worker_drivers = [keep_driver]
        self._driver = keep_driver
        self._wait = WebDriverWait(keep_driver, 30)

    def sync_session_state_to_drivers(self):
        drivers = self.get_live_drivers()
        if len(drivers) <= 1:
            return
        source = drivers[0]
        try:
            source.get(POKELIKE_URL)
            WebDriverWait(source, 10).until(
                lambda _: source.execute_script("return document.readyState") in ["interactive", "complete"]
            )
            cookies = source.get_cookies()
            storage_items = source.execute_script(
                """
                const items = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    items[key] = localStorage.getItem(key);
                }
                return items;
                """
            )
        except Exception as exc:
            self.log(f"Could not read browser 1 session state: {exc}")
            return

        synced = 0
        for driver in drivers[1:]:
            try:
                driver.get(POKELIKE_URL)
                WebDriverWait(driver, 10).until(
                    lambda _: driver.execute_script("return document.readyState") in ["interactive", "complete"]
                )
                for cookie in cookies:
                    clean_cookie = {
                        key: value
                        for key, value in cookie.items()
                        if key in ["name", "value", "path", "domain", "secure", "httpOnly", "expiry", "sameSite"]
                            and value is not None
                    }
                    try:
                        driver.add_cookie(clean_cookie)
                    except Exception:
                        clean_cookie.pop("sameSite", None)
                        clean_cookie.pop("domain", None)
                        try:
                            driver.add_cookie(clean_cookie)
                        except Exception:
                            pass
                driver.execute_script(
                    """
                    const items = arguments[0] || {};
                    for (const [key, value] of Object.entries(items)) {
                        localStorage.setItem(key, value);
                    }
                    """,
                    storage_items,
                )
                driver.refresh()
                synced += 1
            except Exception as exc:
                self.log(f"Could not sync session to browser window: {exc}")
        if synced:
            self.log(f"Synced browser 1 cookies/localStorage to {synced} other browser(s).")

    def active_screen_id(self):
        return self.driver.execute_script(
            "return document.querySelector('.screen.active')?.id || '';"
        )

    def visible_text(self, selector):
        return self.driver.execute_script(
            "const el = document.querySelector(arguments[0]); return el ? (el.innerText || '') : '';",
            selector,
        )

    def js_click(self, selector, timeout=30):
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        self.driver.execute_script(
            """
            arguments[0].scrollIntoView({block: 'center', inline: 'center'});
            arguments[0].dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
            arguments[0].dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            arguments[0].click();
            arguments[0].dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            arguments[0].dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            """,
            element,
        )
        return element

    def click_card_by_text(self, container_selector, card_selector, text):
        script = """
            const clickCenter = (el) => {
                el.scrollIntoView({block: 'center', inline: 'center'});
                const rect = el.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;
                const target = document.elementFromPoint(x, y) || el;
                const pointer = (type, node) => {
                    if (typeof PointerEvent === 'function') {
                        node.dispatchEvent(new PointerEvent(type, {
                            bubbles: true,
                            cancelable: true,
                            clientX: x,
                            clientY: y,
                            button: 0,
                            buttons: type === 'pointerdown' ? 1 : 0,
                            pointerId: 1,
                            pointerType: 'mouse',
                            isPrimary: true
                        }));
                    }
                };
                for (const node of [...new Set([target, el])]) {
                    if (typeof node.focus === 'function') node.focus({preventScroll: true});
                    pointer('pointerdown', node);
                    node.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 1}));
                    pointer('pointerup', node);
                    node.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0}));
                    node.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0}));
                    node.dispatchEvent(new KeyboardEvent('keydown', {bubbles: true, cancelable: true, key: 'Enter', code: 'Enter'}));
                    node.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, cancelable: true, key: 'Enter', code: 'Enter'}));
                }
                if (typeof el.click === 'function') el.click();
            };
            const container = document.querySelector(arguments[0]);
            if (!container) return false;
            const wanted = arguments[2].toLowerCase();
            const cards = [...container.querySelectorAll(arguments[1])];
            const card = cards.find(el => (el.innerText || '').toLowerCase().includes(wanted));
            if (!card) return false;
            clickCenter(card);
            return true;
        """
        if not self.driver.execute_script(script, container_selector, card_selector, text):
            raise RuntimeError(f"Could not find card containing '{text}'")

    def wait_for_screen(self, screen_id, timeout=20):
        WebDriverWait(self.driver, timeout).until(lambda _: self.active_screen_id() == screen_id)

    def wait_until_screen_changes(self, previous_screen, timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(lambda _: self.active_screen_id() != previous_screen)
        except Exception:
            pass

    def browser_center_click(self, element, press_enter=False):
        self.driver.execute_script(
            """
            window.focus();
            arguments[0].scrollIntoView({block: 'center', inline: 'center'});
            if (typeof arguments[0].focus === 'function') {
                arguments[0].focus({preventScroll: true});
            }
            """,
            element,
        )
        rect = self.driver.execute_script(
            """
            const rect = arguments[0].getBoundingClientRect();
            return {
                x: Math.max(1, rect.left + rect.width / 2),
                y: Math.max(1, rect.top + rect.height / 2),
                width: rect.width,
                height: rect.height
            };
            """,
            element,
        )
        if not rect or rect.get("width", 0) <= 0 or rect.get("height", 0) <= 0:
            return False
        x = float(rect["x"])
        y = float(rect["y"])
        try:
            self.driver.execute_cdp_cmd("Page.bringToFront", {})
            self.driver.execute_script(
                """
                const el = arguments[0];
                const rect = el.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;
                const target = document.elementFromPoint(x, y) || el;
                for (const type of ['pointerover', 'mouseover', 'mousemove']) {
                    const EventClass = type.startsWith('pointer') && window.PointerEvent ? PointerEvent : MouseEvent;
                    target.dispatchEvent(new EventClass(type, {
                        bubbles: true,
                        cancelable: true,
                        clientX: x,
                        clientY: y,
                        pointerId: 1,
                        pointerType: 'mouse'
                    }));
                }
                """,
                element,
            )
            self.driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                "type": "mouseMoved",
                "x": x,
                "y": y,
                "button": "none",
                "buttons": 0,
                "pointerType": "mouse",
            })
            time.sleep(0.08)
            self.driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                "type": "mousePressed",
                "x": x,
                "y": y,
                "button": "left",
                "buttons": 1,
                "clickCount": 1,
                "pointerType": "mouse",
            })
            self.driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
                "type": "mouseReleased",
                "x": x,
                "y": y,
                "button": "left",
                "buttons": 0,
                "clickCount": 1,
                "pointerType": "mouse",
            })
            if press_enter:
                self.driver.execute_cdp_cmd("Input.dispatchKeyEvent", {
                    "type": "keyDown",
                    "key": "Enter",
                    "code": "Enter",
                    "windowsVirtualKeyCode": 13,
                    "nativeVirtualKeyCode": 13,
                })
                self.driver.execute_cdp_cmd("Input.dispatchKeyEvent", {
                    "type": "keyUp",
                    "key": "Enter",
                    "code": "Enter",
                    "windowsVirtualKeyCode": 13,
                    "nativeVirtualKeyCode": 13,
                })
            return True
        except Exception:
            try:
                ActionChains(self.driver).move_to_element(element).pause(0.12).click().perform()
                if press_enter:
                    element.send_keys(Keys.ENTER)
                return True
            except Exception:
                return False

    def native_click_starter(self, starter_name):
        wanted = (starter_name or STARTER_NAME).strip().lower()
        selectors = [
            "#starter-choices .dex-grid .dex-card",
            "#starter-choices .dex-card",
            "#shiny-content .dex-card",
            ".dex-grid .dex-card",
            "#starter-choices .poke-card",
        ]
        for selector in selectors:
            for card in self.driver.find_elements(By.CSS_SELECTOR, selector):
                try:
                    text = (card.text or "").strip().lower()
                    alt = self.driver.execute_script(
                        "return arguments[0].querySelector('img[alt]')?.getAttribute('alt') || '';",
                        card,
                    ).strip().lower()
                    if wanted != alt and wanted not in text:
                        continue
                    self.browser_center_click(card)
                    time.sleep(0.25)
                    if self.active_screen_id() != "starter-screen":
                        return True
                    self.browser_center_click(card, press_enter=True)
                    time.sleep(0.25)
                    if self.active_screen_id() != "starter-screen":
                        return True
                except Exception:
                    continue
        return False

    def select_shiny_starter(self):
        starter_name = self.current_starter_name or STARTER_NAME
        result = self.driver.execute_script(
            """
            const itemChoiceVisible = [...document.querySelectorAll([
                '#item-choices .item-card',
                '#passive-choices .item-card',
                '#passive-choices .passive-card',
                '.item-card.passive-card'
            ].join(','))].some(el => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            });
            if (itemChoiceVisible) {
                return {clicked: false, total: 0, dexTotal: 0, names: [], skippedForItems: true};
            }
            const wanted = arguments[0].toLowerCase();
            const active = document.querySelector('.screen.active');
            const roots = [
                active?.id === 'starter-screen' ? active : null,
                document.querySelector('#starter-choices'),
                document.querySelector('#shiny-content')
            ].filter(Boolean);
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                const style = getComputedStyle(el);
                return rect.width > 0 && rect.height > 0
                    && style.display !== 'none'
                    && style.visibility !== 'hidden';
            };
            const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const wantedNorm = normalize(wanted);
            const clickCenter = (el) => {
                el.scrollIntoView({block: 'center', inline: 'center'});
                const rect = el.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;
                const target = document.elementFromPoint(x, y) || el;
                const pointer = (type, node) => {
                    if (typeof PointerEvent === 'function') {
                        node.dispatchEvent(new PointerEvent(type, {
                            bubbles: true,
                            cancelable: true,
                            clientX: x,
                            clientY: y,
                            button: 0,
                            buttons: type === 'pointerdown' ? 1 : 0,
                            pointerId: 1,
                            pointerType: 'mouse',
                            isPrimary: true
                        }));
                    }
                };
                for (const node of [...new Set([target, el])]) {
                    if (typeof node.focus === 'function') node.focus({preventScroll: true});
                    pointer('pointerdown', node);
                    node.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 1}));
                    pointer('pointerup', node);
                    node.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0}));
                    node.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0}));
                    node.dispatchEvent(new KeyboardEvent('keydown', {bubbles: true, cancelable: true, key: 'Enter', code: 'Enter'}));
                    node.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, cancelable: true, key: 'Enter', code: 'Enter'}));
                }
                if (typeof el.click === 'function') el.click();
            };
            const selector = [
                '.dex-grid .dex-card',
                '.dex-card',
                '.poke-card',
                '[role="button"]'
            ].join(',');
            const cards = [...new Set(roots.flatMap(root => [...root.querySelectorAll(selector)]))]
                .filter(visible);
            const dexTotal = cards.filter(card => card.matches('.dex-card, .poke-card')).length;
            const seen = cards.map(card => ({
                text: (card.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 60),
                name: (card.querySelector('.dex-name, .poke-name')?.innerText || '').trim(),
                alt: (card.querySelector('img[alt]')?.getAttribute('alt') || '').trim(),
                shiny: card.classList.contains('pc-dex-card--shiny')
                    || !!card.querySelector('.pc-shiny-star')
                    || (card.querySelector('img')?.src || '').includes('/shiny/')
            }));
            const matchesName = (card) => {
                const name = normalize(card.querySelector('.dex-name, .poke-name')?.innerText || '');
                const alt = normalize(card.querySelector('img[alt]')?.getAttribute('alt') || '');
                const text = normalize(card.innerText || '');
                return name === wantedNorm || alt === wantedNorm || text.split(' ').includes(wantedNorm);
            };
            const isShiny = (card) => card.classList.contains('pc-dex-card--shiny')
                || !!card.querySelector('.pc-shiny-star')
                || (card.querySelector('img')?.src || '').includes('/shiny/');
            let card = cards.find(card => isShiny(card) && matchesName(card));
            if (!card) {
                const img = [...new Set(roots.flatMap(root => [...root.querySelectorAll('.dex-grid img[alt], img[alt]')]))]
                    .filter(visible)
                    .find(img => normalize(img.getAttribute('alt') || '') === wantedNorm);
                card = img ? img.closest('.dex-card, .poke-card, [role="button"]') : null;
            }
            if (!card) card = cards.find(matchesName);
            if (!card) {
                return {
                    clicked: false,
                    total: cards.length,
                    dexTotal,
                    names: seen.slice(0, 20)
                };
            }
            const clickTarget = card.closest('.dex-card, .poke-card, [role="button"]') || card;
            clickCenter(clickTarget);
            return {
                clicked: true,
                total: cards.length,
                dexTotal,
                selected: (clickTarget.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 80)
            };
            """,
            starter_name,
        )
        if result.get("clicked"):
            self.log(f"Selected shiny starter: {starter_name.title()}.")
            time.sleep(0.18)
            if self.active_screen_id() == "starter-screen" and self.native_click_starter(starter_name):
                self.log(f"Selected {starter_name.title()} with WebDriver fallback.")
            return True

        if not result.get("dexTotal"):
            return False

        names = result.get("names", [])
        sample = ", ".join(
            (entry.get("name") or entry.get("alt") or entry.get("text") or "?")
            for entry in names[:10]
        )
        self.log(f"{starter_name.title()} not found in dex grid. Cards seen={result.get('total', 0)}; sample={sample}")
        return False

    def visible_item_choice_context(self):
        return self.driver.execute_script(
            """
            const selectors = [
                '#item-choices .item-card',
                '#passive-choices .item-card',
                '#passive-choices .passive-card',
                '.item-card.passive-card'
            ];
            return selectors.some(selector => [...document.querySelectorAll(selector)].some(el => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            }));
            """
        )

    def click_run_target_choice_if_visible(self):
        info = self.current_run_target_info or {}
        kind = info.get("kind")
        if kind == "challenge":
            challenge = info.get("challenge", "challenge")
            target = {
                "challenge": "Challenge Mode",
                "weekly": "Weekly Challenge",
                "daily": "Daily Challenge",
            }.get(challenge, "Challenge Mode")
        else:
            target = (info.get("name") or self.current_tower or "").strip()
        if not target:
            return False
        result = self.driver.execute_script(
            """
            const wanted = arguments[0].toLowerCase();
            const kind = arguments[1];
            const challenge = arguments[2];
            const normalize = (text) => (text || '')
                .toLowerCase()
                .replace(/[\\u2010-\\u2015]/g, '-')
                .replace(/[^a-z0-9]+/g, ' ')
                .trim();
            const wantedNorm = normalize(wanted);
            const wantedCompact = wantedNorm.replace(/\\s+/g, '');
            const wantedAliases = new Set([wantedNorm]);
            if (wantedNorm.includes('hoenn') && wantedNorm.includes('ability')) {
                wantedAliases.add('hoenn ability challenge');
            }
            if (wantedNorm === 'hoenn ability' || wantedNorm === 'ability hoenn') {
                wantedAliases.add('hoenn ability challenge');
            }
            if (wantedNorm === 'ability challenge') {
                wantedAliases.add('hoenn ability challenge');
            }
            if (wantedNorm.includes('mono') && wantedNorm.includes('ice')) {
                wantedAliases.add('mono ice challenge');
            }
            const textMatches = (text) => {
                const norm = normalize(text);
                const compact = norm.replace(/\\s+/g, '');
                for (const alias of wantedAliases) {
                    const aliasCompact = alias.replace(/\\s+/g, '');
                    if (norm.includes(alias) || compact.includes(aliasCompact)) return true;
                }
                return norm.includes(wantedNorm) || compact.includes(wantedCompact);
            };
            const directSelector = kind === 'challenge' && challenge === 'weekly'
                ? '#chal-weekly, .chal-weekly-card'
                : kind === 'challenge' && challenge === 'daily'
                    ? '#chal-daily, .chal-daily-card'
                    : kind === 'challenge' && challenge === 'challenge'
                        ? '#chal-intro.chal-intro--launch, #chal-intro:not(.weekly-sub)'
                        : '';
            if (directSelector) {
                const directCard = document.querySelector(directSelector);
                if (directCard) {
                    const rect = directCard.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        directCard.scrollIntoView({block: 'center', inline: 'center'});
                        directCard.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                        directCard.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                        directCard.click();
                        directCard.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                        directCard.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
                        return {clicked: true, text: (directCard.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 80)};
                    }
                }
            }
            const roots = [
                document.querySelector('.screen.active'),
                document.querySelector('#challenge-select'),
                document.querySelector('#stage-select-list'),
                document.querySelector('#history-region-list'),
                document.querySelector('#challenge-list'),
                document.querySelector('#challenges-list'),
                document.querySelector('#challenge-choices'),
                document.querySelector('#challenge-select-list'),
                document
            ].filter(Boolean);
            const selector = [
                '[role="button"]',
                'button',
                '[onclick]',
                '[data-challenge]',
                '[data-id]',
                '#chal-weekly',
                '#chal-daily',
                '.chal-weekly-card',
                '.chal-weekly-tag',
                '.chal-weekly-main',
                '.chal-weekly-title',
                '.chal-weekly-cta',
                '.challenge-card',
                '.challenge-btn',
                '.challenge-option',
                '.history-region-btn',
                '.run-menu-btn',
                '.btn-primary'
            ].join(',');
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };
            for (const root of roots) {
                const candidates = [...root.querySelectorAll(selector)].filter(visible);
                const card = candidates.find(el => textMatches(el.innerText || el.textContent || ''));
                if (!card) continue;
                const clickTarget = card.closest('.chal-weekly-card, .chal-weekly-main, .challenge-card, .history-region-btn, [role="button"], button') || card;
                clickTarget.scrollIntoView({block: 'center', inline: 'center'});
                clickTarget.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                clickTarget.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                clickTarget.click();
                clickTarget.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                clickTarget.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
                return {clicked: true, text: (clickTarget.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 80)};
            }
            const visibleText = roots
                .map(root => (root.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 300))
                .find(Boolean) || '';
            return {clicked: false, visibleText};
            """,
            target,
            kind,
            info.get("challenge", ""),
        )
        if result.get("clicked"):
            self.log(f"Selected run target: {result.get('text') or target}")
            return True
        if self.active_screen_id() in ["challenge-select", "history-region-select", "endless-stage-select"]:
            self.log(f"Run target '{target}' not found. Visible text: {result.get('visibleText') or ''}")
        return False

    def click_weekly_sub_choice_if_visible(self):
        result = self.driver.execute_script(
            """
            const wanted = (arguments[0] || '').toLowerCase();
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };
            const cards = [...document.querySelectorAll('.chal-intro.weekly-sub, .weekly-sub, [data-sub]')]
                .filter(visible);
            if (!cards.length) return {clicked: false};
            let card = null;
            if (wanted.includes('hoenn') || wanted.includes('ability')) {
                card = cards.find(el => (el.innerText || el.textContent || '').toLowerCase().includes('norman'))
                    || cards.find(el => (el.querySelector('img[alt]')?.getAttribute('alt') || '').toLowerCase().includes('norman'))
                    || cards.find(el => (el.dataset.sub || '').toLowerCase() === 'medium');
            }
            if (!card && (wanted.includes('mono') || wanted.includes('ice'))) {
                card = cards.find(el => (el.innerText || el.textContent || '').toLowerCase().includes('pryce'))
                    || cards.find(el => (el.dataset.sub || '').toLowerCase() === 'medium');
            }
            if (!card) {
                card = cards.find(el => (el.dataset.sub || '').toLowerCase() === 'medium') || cards[0];
            }
            const clickTarget = card.closest('.chal-intro.weekly-sub, .weekly-sub, [data-sub], [role="button"]') || card;
            clickTarget.scrollIntoView({block: 'center', inline: 'center'});
            clickTarget.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
            clickTarget.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            clickTarget.click();
            clickTarget.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            clickTarget.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            return {
                clicked: true,
                text: (clickTarget.innerText || clickTarget.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 100)
            };
            """,
            self.current_tower,
        )
        if result.get("clicked"):
            self.log(f"Selected weekly sub challenge: {result.get('text') or 'sub challenge'}")
            return True
        return False

    def click_story_mode_if_visible(self):
        info = self.current_run_target_info or {}
        if info.get("kind") != "story":
            return False
        mode = info.get("story_mode", "classic")
        selector = "#btn-history-nuzlocke" if mode == "nuzlocke" else "#btn-history-classic"
        result = self.driver.execute_script(
            """
            const selector = arguments[0];
            const mode = arguments[1];
            const button = document.querySelector(selector);
            if (!button) return {clicked: false};
            const rect = button.getBoundingClientRect();
            if (rect.width <= 0 || rect.height <= 0) return {clicked: false};
            if (button.classList.contains('history-mode-btn--selected')) {
                return {clicked: false, selected: true, text: button.innerText || mode};
            }
            button.scrollIntoView({block: 'center', inline: 'center'});
            button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            button.click();
            button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            return {clicked: true, text: button.innerText || mode};
            """,
            selector,
            mode,
        )
        if result.get("clicked"):
            self.log(f"Selected story mode: {result.get('text') or mode.title()}")
            return True
        return False

    def prepare_page(self):
        self.driver.get(POKELIKE_URL)
        self.wait.until(lambda _: self.driver.execute_script("return document.readyState") in ["interactive", "complete"])

        try:
            self.js_click(".qc-cmp2-summary-buttons button:last-child", timeout=4)
            self.log("Cookie prompt accepted.")
        except Exception:
            pass

    def click_optional_confirm(self):
        try:
            dialog = self.driver.switch_to.alert
            dialog.accept()
            time.sleep(0.08)
            return True
        except Exception:
            return False

    def reset_current_run_if_needed(self):
        run_screens = [
            "map-screen",
            "battle-screen",
            "item-screen",
            "catch-screen",
            "badge-screen",
            "passive-screen",
            "stat-buff-screen",
            "move-tutor-screen",
        ]

        if not self.driver.current_url.startswith(POKELIKE_URL):
            self.prepare_page()
            time.sleep(0.15)

        if self.active_screen_id() in run_screens:
            self.log("Existing run detected; using in-game reset to preserve login.")
            reset_result = self.driver.execute_script(
                """
                const visible = (el) => {
                    const rect = el.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                };
                const clickElement = (el) => {
                    el.scrollIntoView({block: 'center', inline: 'center'});
                    el.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                    el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                    el.click();
                    el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                    el.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
                };
                const findResetButton = () => [...document.querySelectorAll('button, [role="button"]')]
                    .find(btn => {
                        const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                        const id = (btn.id || '').toLowerCase();
                        const cls = (btn.className || '').toString().toLowerCase();
                        return btn.dataset?.menu === 'reset'
                            || btn.dataset?.i18n === 'menu.resetRun'
                            || text === 'reset run'
                            || text.includes('reset run')
                            || id.includes('reset')
                            || cls.includes('run-menu-btn--reset');
                    });
                const callResetFunction = () => {
                    if (typeof window.confirmResetRun !== 'function') return false;
                    const oldConfirm = window.confirm;
                    window.confirm = () => true;
                    try {
                        window.confirmResetRun();
                    } finally {
                        window.confirm = oldConfirm;
                    }
                    return true;
                };

                let button = findResetButton();
                if (!button) {
                    const toggle = document.querySelector('#run-menu-toggle, .run-menu-toggle');
                    if (toggle) clickElement(toggle);
                    button = findResetButton();
                }
                if (button) {
                    clickElement(button);
                    return {clicked: true, method: 'button', text: (button.innerText || button.textContent || '').trim()};
                }
                if (callResetFunction()) {
                    return {clicked: true, method: 'function'};
                }
                return {clicked: false};
                """
            )
            if reset_result.get("clicked"):
                time.sleep(0.08)
                self.click_optional_confirm()
                self.driver.execute_script(
                    """
                    const visible = (el) => {
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    };
                    const clickButton = (button) => {
                        button.scrollIntoView({block: 'center', inline: 'center'});
                        button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                        button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                        button.click();
                        button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                        button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
                    };
                    const findConfirm = () => {
                        const exact = document.querySelector('#btn-reset-confirm');
                        if (exact && visible(exact)) return exact;
                        return [...document.querySelectorAll('button, [role="button"]')]
                            .filter(visible)
                            .find(btn => {
                                const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                                const id = (btn.id || '').toLowerCase();
                                return id === 'btn-reset-confirm'
                                    || ['restart', 'reset', 'yes', 'ok', 'confirm'].includes(text)
                                    || text.includes('restart')
                                    || text.includes('reset run')
                                    || text.includes('confirm');
                            });
                    };
                    const started = Date.now();
                    while (Date.now() - started < 800) {
                        const button = findConfirm();
                        if (button && button.dataset?.menu !== 'reset') {
                            clickButton(button);
                            return true;
                        }
                    }
                    return false;
                    """
                )
                try:
                    WebDriverWait(self.driver, 1.5).until(
                        lambda _: self.active_screen_id() in ["title-screen", "challenge-select"]
                    )
                except Exception:
                    pass
                self.log(f"In-game reset requested via {reset_result.get('method')}.")
            if self.active_screen_id() in run_screens:
                if self.current_mode == MODE_SHINY_CHARM_REROLL or self.is_pokemon_reroll_mode():
                    self.log(f"Reset returned to run screen={self.active_screen_id()}; continuing reroll.")
                    time.sleep(0.35)
                    return
                raise RuntimeError(f"Could not leave active run screen after reset; current screen={self.active_screen_id()}")
            return

        if self.active_screen_id() not in ["title-screen", "challenge-select"]:
            self.prepare_page()
            time.sleep(0.15)

    def is_active_run_screen(self):
        return self.active_screen_id() in [
            "map-screen",
            "battle-screen",
            "item-screen",
            "catch-screen",
            "badge-screen",
            "passive-screen",
            "stat-buff-screen",
            "move-tutor-screen",
            "swap-screen",
            "trade-screen",
            "starter-screen",
        ]

    def select_challenge_or_starter(self):
        for _ in range(30):
            screen = self.active_screen_id()
            if screen in [
                "map-screen",
                "battle-screen",
                "item-screen",
                "catch-screen",
                "passive-screen",
                "stat-buff-screen",
                "move-tutor-screen",
                "swap-screen",
                "trade-screen",
                "elite-prep-screen",
            ]:
                self.log(f"Start complete; continuing from screen={screen}.")
                return

            if self.click_weekly_sub_choice_if_visible():
                self.wait_until_screen_changes(screen, timeout=0.45)
                continue

            if self.visible_item_choice_context():
                self.choose_passive_item()
                self.wait_until_screen_changes(screen, timeout=0.45)
                if self.active_screen_id() == "map-screen":
                    return False
                continue

            if self.click_story_mode_if_visible():
                time.sleep(0.2)
                continue

            if self.click_run_target_choice_if_visible():
                self.wait_until_screen_changes(screen, timeout=0.35)
                continue

            intro_clicked = self.driver.execute_script(
                """
                const targetKind = arguments[0] || '';
                const targetChallenge = arguments[1] || '';
                const allowGenericIntro = targetKind === 'challenge' && targetChallenge === 'challenge';
                if (!allowGenericIntro) return false;
                const intro = document.querySelector('#chal-intro.chal-intro--launch, #chal-intro:not(.weekly-sub)');
                if (!intro) return false;
                const rect = intro.getBoundingClientRect();
                if (rect.width <= 0 || rect.height <= 0) return false;
                intro.scrollIntoView({block: 'center', inline: 'center'});
                intro.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                intro.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                intro.click();
                intro.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                intro.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
                return true;
                """,
                self.current_run_target_info.get("kind", ""),
                self.current_run_target_info.get("challenge", ""),
            )
            if intro_clicked:
                self.log("Challenge intro clicked.")
                self.wait_until_screen_changes(screen, timeout=0.45)
                continue

            if screen == "starter-screen":
                old_starter_cards = self.driver.execute_script(
                    "return !!document.querySelector('#starter-choices .poke-card');"
                )
                if old_starter_cards:
                    if self.native_click_starter(self.current_starter_name):
                        self.wait_until_screen_changes(screen, timeout=0.45)
                        continue
                    self.log(f"Legacy starter picker missed {self.current_starter_name.title()}; trying dex grid.")

            if self.select_shiny_starter():
                self.wait_until_screen_changes(screen, timeout=0.45)
                if self.active_screen_id() == "map-screen":
                    return
                continue

            if screen == "trainer-screen":
                self.js_click("#trainer-boy")
                self.wait_until_screen_changes(screen, timeout=0.45)
                continue

            clicked = self.driver.execute_script(
                """
                const wanted = arguments[0].toLowerCase();
                const clickCenter = (el) => {
                    el.scrollIntoView({block: 'center', inline: 'center'});
                    const rect = el.getBoundingClientRect();
                    const x = rect.left + rect.width / 2;
                    const y = rect.top + rect.height / 2;
                    const target = document.elementFromPoint(x, y) || el;
                    const pointer = (type, node) => {
                        if (typeof PointerEvent === 'function') {
                            node.dispatchEvent(new PointerEvent(type, {
                                bubbles: true,
                                cancelable: true,
                                clientX: x,
                                clientY: y,
                                button: 0,
                                buttons: type === 'pointerdown' ? 1 : 0,
                                pointerId: 1,
                                pointerType: 'mouse',
                                isPrimary: true
                            }));
                        }
                    };
                    for (const node of [...new Set([target, el])]) {
                        if (typeof node.focus === 'function') node.focus({preventScroll: true});
                        pointer('pointerdown', node);
                        node.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 1}));
                        pointer('pointerup', node);
                        node.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0}));
                        node.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0}));
                        node.dispatchEvent(new KeyboardEvent('keydown', {bubbles: true, cancelable: true, key: 'Enter', code: 'Enter'}));
                        node.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, cancelable: true, key: 'Enter', code: 'Enter'}));
                    }
                    if (typeof el.click === 'function') el.click();
                };
                const active = document.querySelector('.screen.active');
                const activeId = active ? `#${active.id}` : '';
                const containers = [
                    activeId,
                    '#starter-choices',
                    '#shiny-content'
                ].filter(Boolean);
                const clickableSelector = [
                    '[role="button"]',
                    'button',
                    '[onclick]',
                    '.dex-card',
                    '.pc-dex-card--shiny',
                    '.poke-card'
                ].join(',');
                for (const selector of containers) {
                    const container = document.querySelector(selector);
                    if (!container) continue;
                    const candidates = [...container.querySelectorAll(clickableSelector)]
                        .filter(el => {
                            const rect = el.getBoundingClientRect();
                            return rect.width > 0 && rect.height > 0;
                        });
                    let card = candidates.find(el => (el.innerText || '').toLowerCase().includes(wanted));
                    if (!card) {
                        card = candidates.find(el => {
                            const text = (el.innerText || el.textContent || '').toLowerCase();
                            const alt = (el.querySelector('img[alt]')?.getAttribute('alt') || '').toLowerCase();
                            return alt === wanted || text.includes(wanted);
                        });
                    }
                    if (card) {
                        card = card.closest('.dex-card, .poke-card, [role="button"], button') || card;
                        clickCenter(card);
                        return true;
                    }
                }
                return false;
                """,
                self.current_starter_name,
            )
            if clicked:
                self.wait_until_screen_changes(screen, timeout=0.45)
                continue

            generic_clicked = self.driver.execute_script(
                """
                const active = document.querySelector('.screen.active');
                if (active && active.id === 'starter-screen') return false;
                const clickCenter = (el) => {
                    el.scrollIntoView({block: 'center', inline: 'center'});
                    const rect = el.getBoundingClientRect();
                    const x = rect.left + rect.width / 2;
                    const y = rect.top + rect.height / 2;
                    const target = document.elementFromPoint(x, y) || el;
                    const pointer = (type, node) => {
                        if (typeof PointerEvent === 'function') {
                            node.dispatchEvent(new PointerEvent(type, {
                                bubbles: true,
                                cancelable: true,
                                clientX: x,
                                clientY: y,
                                button: 0,
                                buttons: type === 'pointerdown' ? 1 : 0,
                                pointerId: 1,
                                pointerType: 'mouse',
                                isPrimary: true
                            }));
                        }
                    };
                    for (const node of [...new Set([target, el])]) {
                        if (typeof node.focus === 'function') node.focus({preventScroll: true});
                        pointer('pointerdown', node);
                        node.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 1}));
                        pointer('pointerup', node);
                        node.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0}));
                        node.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0}));
                        node.dispatchEvent(new KeyboardEvent('keydown', {bubbles: true, cancelable: true, key: 'Enter', code: 'Enter'}));
                        node.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, cancelable: true, key: 'Enter', code: 'Enter'}));
                    }
                    if (typeof el.click === 'function') el.click();
                };
                const root = active || document;
                const selectors = [
                    '#starter-choices [role="button"]',
                    '#starter-choices .poke-card',
                    '#shiny-content [role="button"]',
                    '#shiny-content .dex-card'
                ];
                for (const selector of selectors) {
                    const card = root.querySelector(selector);
                    if (card) {
                        clickCenter(card);
                        return true;
                    }
                }
                return false;
                """
            )
            if generic_clicked:
                self.wait_until_screen_changes(screen, timeout=0.45)
                continue

            time.sleep(0.12)

        screen_text = self.driver.execute_script(
            "const active = document.querySelector('.screen.active'); return active ? (active.innerText || '').slice(0, 1200) : '';"
        )
        self.log(f"Start screen text: {screen_text}")
        raise RuntimeError(
            f"Could not start {self.current_run_target} with {self.current_starter_name.title()}; "
            f"current screen={self.active_screen_id()}"
        )

    def title_action_i18n(self):
        kind = (self.current_run_target_info or {}).get("kind")
        if kind == "story":
            return "title.playStory", "Play Story"
        if kind == "challenge":
            return "title.takeChallenge", "Take Challenge"
        return "title.enterTower", "Enter Tower"

    def title_card_selector(self):
        kind = (self.current_run_target_info or {}).get("kind")
        if kind == "story":
            return "#btn-history-run"
        if kind == "challenge":
            return "#btn-challenges-run"
        return "#btn-endless-run"

    def click_title_mode(self, allow_resume=False, prefer_resume=False):
        i18n_key, action_name = self.title_action_i18n()
        direct_selector = self.title_card_selector()
        result = self.driver.execute_script(
            """
            const i18nKey = arguments[0];
            const actionName = arguments[1].toLowerCase();
            const allowResume = arguments[2];
            const preferResume = arguments[3];
            const directSelector = arguments[4];
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };
            const allCandidates = () => [...document.querySelectorAll('.title-mode-card, .title-mode-card-action, button, [role="button"]')]
                .filter(visible);
            const findResume = () => allCandidates().find(el => {
                const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                return text.includes('resume');
            });
            let resumed = false;
            let card = null;
            if (preferResume && allowResume) {
                card = findResume();
                resumed = !!card;
            }
            if (!card && directSelector) {
                const direct = document.querySelector(directSelector);
                if (direct && visible(direct)) card = direct;
            }
            const action = [...document.querySelectorAll('.title-mode-card-action, [data-i18n]')]
                .filter(visible)
                .find(el => el.dataset.i18n === i18nKey);
            if (!card) card = action ? action.closest('.title-mode-card, [role="button"], button') || action : null;
            if (!card) {
                const candidates = allCandidates();
                card = candidates.find(el => {
                    const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                    return text.includes(actionName) && !text.includes('resume');
                });
            }
            if (!card && allowResume) {
                card = findResume();
                resumed = !!card;
            }
            if (!card) {
                const candidates = allCandidates();
                const visibleText = candidates.map(el => (el.innerText || el.textContent || '').trim()).filter(Boolean).join(' | ').slice(0, 500);
                return {clicked: false, visibleText};
            }
            const clickTarget = card.closest('.title-mode-card, [role="button"], button') || card;
            const clickText = (clickTarget.innerText || clickTarget.textContent || '').trim().toLowerCase();
            if (clickText.includes('resume') && !allowResume) {
                return {clicked: false, resumeOnly: true, visibleText: clickText};
            }
            if (clickText.includes('resume')) resumed = true;
            clickTarget.scrollIntoView({block: 'center', inline: 'center'});
            clickTarget.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
            clickTarget.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            clickTarget.click();
            clickTarget.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            clickTarget.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            return {
                clicked: true,
                resumed,
                disabled: !!clickTarget.disabled || clickTarget.classList.contains('title-mode-card--locked'),
                text: (clickTarget.innerText || clickTarget.textContent || '').trim()
            };
            """,
            i18n_key,
            action_name,
            allow_resume,
            prefer_resume,
            direct_selector,
        )
        if not result.get("clicked"):
            if result.get("resumeOnly"):
                raise RuntimeError(f"Only Resume is visible for {action_name}; refusing to resume a random run.")
            self.log(f"{action_name} not found. Visible title actions: {result.get('visibleText') or ''}")
            raise RuntimeError(f"{action_name} button/card was not found on the title screen.")
        if result.get("disabled"):
            raise RuntimeError(
                f"{action_name} is locked or this Selenium profile is not logged in. "
                f"Profile in use: {SELENIUM_PROFILE_PATH}"
            )
        if result.get("resumed"):
            self.log("Clicked title action: Resume manual run.")
        else:
            self.log(f"Clicked title action: {action_name}")
        return result

    def start_challenge_run(self):
        self.apply_active_schedule_target()
        self.reset_current_run_if_needed()

        if (self.current_mode == MODE_SHINY_CHARM_REROLL or self.is_pokemon_reroll_mode()) and self.is_active_run_screen():
            self.log(f"Using active run after reset; screen={self.active_screen_id()}.")
            return False

        title_result = self.click_title_mode(
            allow_resume=False,
            prefer_resume=False,
        )
        self.wait_until_screen_changes("title-screen", timeout=0.45)
        if title_result.get("resumed"):
            self.log("Manual run resumed.")
            return False

        self.select_challenge_or_starter()
        self.log(f"{self.current_run_target} started with {self.current_starter_name.title()}.")
        return False

    def get_item_choices(self):
        return self.driver.execute_script(
            """
            return [...document.querySelectorAll('#item-choices .item-card')]
                .filter(card => {
                    const rect = card.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                })
                .map((card, index) => ({
                index,
                name: (card.querySelector('.item-name')?.innerText || card.innerText || '').trim(),
                text: (card.innerText || '').trim()
            }));
            """
        )

    def choose_item(self, target_only=False):
        choices = self.get_item_choices()
        if not choices:
            if target_only:
                return False
            self.js_click("#btn-skip-item")
            return False

        names = [choice["name"] for choice in choices]
        signature = "|".join(names)
        if signature != self.last_item_signature:
            self.last_item_signature = signature
            with self.stats_lock:
                self.item_rolls_checked += len(names)
            self.update_stats_labels()
            self.log("Item rolls: " + ", ".join(names))

        for choice in choices:
            choice_text = f"{choice['name']} {choice.get('text', '')}".lower()
            if any(alias in choice_text for alias in TARGET_ITEM_ALIASES):
                screen_before = self.active_screen_id()
                self.click_item_index(choice["index"])
                self.wait_until_screen_changes(screen_before, timeout=1.2)
                self.set_status("Target found")
                self.log(f"TARGET FOUND: {choice['name']} selected.")
                return True

        if target_only:
            return False

        decision = self.driver.execute_script(
            """
            const priority = arguments[0].map(name => name.toLowerCase());
            const consumables = new Set(arguments[1].map(name => name.toLowerCase()));
            const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const priorityIndex = (name) => {
                const norm = normalize(name);
                const idx = priority.findIndex(alias => norm.includes(alias));
                return idx < 0 ? null : idx;
            };
            const isConsumable = (name) => {
                const norm = normalize(name);
                return [...consumables].some(alias => norm.includes(alias));
            };
            const choiceCards = [...document.querySelectorAll('#item-choices .item-card')]
                .filter(card => {
                    const rect = card.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                });
            const choices = choiceCards.map((card, index) => {
                const name = (
                    card.querySelector('.item-name')?.innerText
                    || card.querySelector('img[alt]')?.getAttribute('alt')
                    || card.querySelector('img[title]')?.getAttribute('title')
                    || card.innerText
                    || ''
                ).trim();
                return {index, name, priority: priorityIndex(name), consumable: isConsumable(name)};
            });
            const ownedRoots = ['#item-bar', '#elite-prep-items', '#item-team-bar', '#catch-team-bar', '#passive-team-bar'];
            const owned = ownedRoots.flatMap(selector => [...document.querySelectorAll(`${selector} img[alt], ${selector} img[title]`)])
                .concat([...document.querySelectorAll('.team-slot-item img[alt], .team-slot-item img[title], .battle-poke-item img[alt], .battle-poke-item img[title]')])
                .map(img => img.getAttribute('alt') || img.getAttribute('title') || '')
                .filter(Boolean);
            const ownedPriority = owned
                .map(priorityIndex)
                .filter(value => value !== null && value < priority.indexOf('rare candy'));
            const bestOwnedHeld = ownedPriority.length ? Math.min(...ownedPriority) : null;

            const ranked = choices
                .filter(choice => choice.priority !== null)
                .sort((a, b) => a.priority - b.priority);
            for (const choice of ranked) {
                if (choice.consumable) {
                    return {take: true, index: choice.index, name: choice.name, reason: 'consumable', owned};
                }
                if (bestOwnedHeld === null || choice.priority < bestOwnedHeld) {
                    return {take: true, index: choice.index, name: choice.name, reason: 'upgrade', owned};
                }
            }
            return {take: false, owned, offered: choices.map(choice => choice.name)};
            """,
            list(self.regular_item_priority),
            list(CONSUMABLE_ITEM_ALIASES),
        )
        if not decision.get("take"):
            self.skip_item_choice()
            offered = ", ".join(decision.get("offered") or names)
            owned = ", ".join(decision.get("owned") or [])
            self.log(f"Skipped item reward. Offered: {offered}; owned priority items: {owned or 'none'}")
            return False

        selected = int(decision["index"])
        screen_before = self.active_screen_id()
        self.click_item_index(selected)
        self.wait_until_screen_changes(screen_before, timeout=1.2)
        self.log(f"Selected support item: {decision.get('name') or choices[selected]['name']} ({decision.get('reason')})")
        return False

    def skip_item_choice(self):
        result = self.driver.execute_script(
            """
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };
            const button = [...document.querySelectorAll('#btn-skip-item, .choice-skip-btn, .choice-skip-cell, button')]
                .filter(visible)
                .find(btn => {
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    return btn.id === 'btn-skip-item' || text.includes('skip') || text.includes('no item');
                });
            if (!button) return false;
            button.scrollIntoView({block: 'center', inline: 'center'});
            button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            button.click();
            button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            return true;
            """
        )
        if not result:
            raise RuntimeError("No skip/no item button found on item reward screen.")

    def handle_take_shiny_reward(self):
        result = self.driver.execute_script(
            """
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0
                    && getComputedStyle(el).display !== 'none'
                    && getComputedStyle(el).visibility !== 'hidden';
            };
            const button = document.querySelector('#btn-take-shiny');
            if (!button || !visible(button)) return {clicked: false};
            button.scrollIntoView({block: 'center', inline: 'center'});
            button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            button.click();
            button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            return {clicked: true, text: (button.innerText || button.textContent || '').trim()};
            """
        )
        if result.get("clicked"):
            self.log(f"Shiny reward: {result.get('text') or 'Take shiny Pokemon'}")
            # This is always a shiny (#btn-take-shiny). Count it. Only reached if
            # handle_pokemon_reward_policy did not already take/count it this pass,
            # so there is no double count.
            with self.stats_lock:
                self.total_shinies_seen += 1
            self.update_stats_labels()
            time.sleep(0.6)
            return True
        return False

    def handle_passive_replace_choice(self):
        result = self.driver.execute_script(
            """
            const priority = arguments[0].map(name => name.toLowerCase());
            const newItemName = arguments[1] || '';
            const newItemPriority = arguments[2];
            const protectedAliases = arguments[3].map(name => name.toLowerCase());
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0
                    && getComputedStyle(el).display !== 'none'
                    && getComputedStyle(el).visibility !== 'hidden';
            };
            const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const nameFor = (card) => (
                card.querySelector('.item-name')?.innerText
                || card.querySelector('img[alt]')?.getAttribute('alt')
                || card.querySelector('img[title]')?.getAttribute('title')
                || card.innerText
                || 'passive item'
            ).trim().replace(/\\s+/g, ' ').slice(0, 80);
            const priorityIndex = (name) => {
                const norm = normalize(name);
                const idx = priority.findIndex(alias => norm.includes(alias));
                return idx < 0 ? null : idx;
            };
            const isProtected = (name) => {
                const norm = normalize(name);
                return protectedAliases.some(alias => norm.includes(alias));
            };
            const clickCenter = (el) => {
                el.scrollIntoView({block: 'center', inline: 'center'});
                const rect = el.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;
                const target = document.elementFromPoint(x, y) || el;
                target.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true, clientX: x, clientY: y}));
                target.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, clientX: x, clientY: y}));
                target.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, clientX: x, clientY: y}));
                target.dispatchEvent(new MouseEvent('click', {bubbles: true, clientX: x, clientY: y}));
                el.click();
                target.dispatchEvent(new MouseEvent('pointerup', {bubbles: true, clientX: x, clientY: y}));
            };
            const cancelReplacement = (reason, candidates) => {
                const cancel = [...document.querySelectorAll('button, [role="button"]')]
                    .filter(visible)
                    .find(btn => {
                        const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                        const id = (btn.id || '').toLowerCase();
                        return text.includes('cancel') || text.includes('skip') || text.includes('keep')
                            || id.includes('cancel') || id.includes('skip') || id.includes('keep');
                    });
                if (!cancel) return {clicked: false, skipped: true, reason, candidates};
                clickCenter(cancel);
                return {clicked: true, skipped: true, reason, text: (cancel.innerText || cancel.textContent || '').trim(), candidates};
            };
            const cards = [...document.querySelectorAll('#passive-choices .item-card, #passive-choices .passive-card, .item-card.passive-card')]
                .filter(visible);
            const replaceCards = cards.filter(card => {
                const tagText = [...card.querySelectorAll('.item-tag')]
                    .map(tag => (tag.innerText || tag.textContent || '').trim().toLowerCase())
                    .join(' ');
                return tagText.includes('replace');
            });
            if (!replaceCards.length) return {clicked: false};
            const candidates = replaceCards.map(card => {
                const name = nameFor(card);
                return {
                    card,
                    name,
                    priority: priorityIndex(name),
                    protected: isProtected(name)
                };
            });
            const replaceable = candidates.filter(candidate => !candidate.protected);
            if (!replaceable.length) {
                return cancelReplacement('all replace candidates are protected', candidates.map(({name, priority, protected: protectedItem}) => ({name, priority, protected: protectedItem})));
            }
            if (newItemPriority === null || newItemPriority === undefined) {
                return cancelReplacement('new passive item has no configured priority', candidates.map(({name, priority, protected: protectedItem}) => ({name, priority, protected: protectedItem})));
            }
            replaceable.sort((a, b) => {
                const ap = a.priority === null ? Number.POSITIVE_INFINITY : a.priority;
                const bp = b.priority === null ? Number.POSITIVE_INFINITY : b.priority;
                return bp - ap;
            });
            const worst = replaceable[0];
            const worstPriority = worst.priority === null ? Number.POSITIVE_INFINITY : worst.priority;
            if (newItemPriority >= worstPriority) {
                return cancelReplacement('new passive item is not higher priority than the lowest replaceable item', candidates.map(({name, priority, protected: protectedItem}) => ({name, priority, protected: protectedItem})));
            }
            clickCenter(worst.card);
            return {
                clicked: true,
                skipped: false,
                name: worst.name,
                oldPriority: worst.priority,
                newItemName,
                newItemPriority,
                candidates: candidates.map(({name, priority, protected: protectedItem}) => ({name, priority, protected: protectedItem}))
            };
            """,
            list(self.starting_item_priority),
            self.pending_passive_item_name,
            self.pending_passive_item_priority,
            list(TARGET_ITEM_ALIASES),
        )
        if result.get("clicked"):
            if result.get("skipped"):
                self.log(f"Passive replace screen: kept current items ({result.get('reason')}).")
            else:
                old_rank = (
                    int(result["oldPriority"]) + 1
                    if result.get("oldPriority") is not None
                    else "unlisted"
                )
                new_rank = (
                    int(result["newItemPriority"]) + 1
                    if result.get("newItemPriority") is not None
                    else "unlisted"
                )
                self.log(
                    "Passive replace screen: replaced "
                    f"{result.get('name') or 'lowest priority passive item'} "
                    f"(priority {old_rank}) with {result.get('newItemName') or 'new passive item'} "
                    f"(priority {new_rank})."
                )
                self.record_run_passive_item(result.get("newItemName") or "")
            self.pending_passive_item_name = ""
            self.pending_passive_item_priority = None
            # Replacing a passive is still a per-map passive pick → new map.
            self.maps_started += 1
            time.sleep(0.35)
            return True
        if result.get("skipped"):
            self.log(f"Passive replace screen: no cancel/skip button found ({result.get('reason')}).")
        return False

    def handle_final_fight_confirm(self):
        result = self.driver.execute_script(
            """
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0
                    && getComputedStyle(el).display !== 'none'
                    && getComputedStyle(el).visibility !== 'hidden';
            };
            const button = [...document.querySelectorAll('#btn-elite-prep-continue, button, [role="button"]')]
                .filter(visible)
                .find(btn => {
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    const id = (btn.id || '').toLowerCase();
                    return id === 'btn-elite-prep-continue'
                        || text === 'fight!'
                        || text === 'fight'
                        || text.includes('fight!');
                });
            if (!button) return {clicked: false};
            button.scrollIntoView({block: 'center', inline: 'center'});
            button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            button.click();
            button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            return {clicked: true, text: (button.innerText || button.textContent || '').trim()};
            """
        )
        if result.get("clicked"):
            self.log(f"Final battle confirm: {result.get('text') or 'FIGHT!'}")
            time.sleep(0.6)
            return True
        return False

    def record_money_earned_if_visible(self):
        result = self.driver.execute_script(
            """
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0
                    && getComputedStyle(el).display !== 'none'
                    && getComputedStyle(el).visibility !== 'hidden';
            };
            const el = [...document.querySelectorAll('.run-score-earned')]
                .filter(visible)[0];
            if (!el) return {found: false};
            const text = (el.innerText || el.textContent || '').trim();
            const match = text.match(/([0-9][0-9.,]*)\\s*Pok/i);
            if (!match) return {found: true, amount: 0, text};
            const amount = parseInt(match[1].replace(/[^0-9]/g, ''), 10) || 0;
            const lowerText = text.toLowerCase();
            return {
                found: true,
                amount,
                text,
                isEarnedAmount: lowerText.includes('earned') || lowerText.includes('you got')
            };
            """
        )
        if not result.get("found"):
            return
        signature = f"{self.active_screen_id()}|{result.get('text') or ''}"
        if signature == self.last_money_signature:
            return
        self.last_money_signature = signature
        observed_amount = int(result.get("amount") or 0)
        if result.get("isEarnedAmount"):
            amount = observed_amount
            wallet_total = (
                int(self.last_wallet_pokegold_total or 0) + amount
                if self.last_wallet_pokegold_total is not None
                else None
            )
        else:
            wallet_total = observed_amount
            previous_wallet_total = self.last_wallet_pokegold_total
            if previous_wallet_total is None:
                amount = 0
            elif wallet_total < previous_wallet_total:
                amount = wallet_total
            else:
                amount = wallet_total - previous_wallet_total
        if wallet_total is not None:
            self.last_wallet_pokegold_total = wallet_total
        with self.stats_lock:
            self.total_money_earned += amount
            self.run_money_earned = int(self.run_money_earned or 0) + amount
        self.update_stats_labels()
        self.log(
            f"Money earned: {amount}; wallet={wallet_total}; "
            f"session total={self.total_money_earned}"
        )

    def result_screen_details(self):
        try:
            return self.driver.execute_script(
                """
                const knownPassive = new Set(arguments[0].map(name => String(name || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()));
                const active = document.querySelector('.screen.active') || document.body;
                const visible = (el) => {
                    const rect = el.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0
                        && getComputedStyle(el).display !== 'none'
                        && getComputedStyle(el).visibility !== 'hidden';
                };
                const normalize = (text) => String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
                const clean = (text) => String(text || '').replace(/\\s+/g, ' ').trim();
                const scoreTexts = [
                    ...active.querySelectorAll('.run-score, .score, [class*="score"], [id*="score"]')
                ].filter(visible).map(el => clean(el.innerText || el.textContent));
                scoreTexts.push(clean(active.innerText || active.textContent));
                let scoreText = '';
                let score = 0;
                for (const text of scoreTexts) {
                    const match = text.match(/\\bscore\\b\\s*[:\\-]?\\s*([0-9][0-9.,]*)/i);
                    if (match) {
                        scoreText = match[0];
                        score = parseInt(match[1].replace(/[^0-9]/g, ''), 10) || 0;
                        break;
                    }
                }

                const passiveItems = [];
                const addName = (name, force) => {
                    name = clean(name).slice(0, 80);
                    const normalized = normalize(name);
                    if (!normalized) return;
                    const isKnown = knownPassive.has(normalized)
                        || [...knownPassive].some(passive => normalized === passive || normalized.includes(passive) || passive.includes(normalized));
                    if (!force && !isKnown) return;
                    if (!passiveItems.some(item => normalize(item) === normalized)) passiveItems.push(name);
                };
                const containers = [
                    ...active.querySelectorAll('[id*="passive"], [class*="passive"], [id*="item"], [class*="item"]')
                ].filter(visible);
                for (const container of containers) {
                    const marker = normalize(`${container.id || ''} ${container.className || ''} ${container.innerText || ''}`);
                    const force = marker.includes('passive');
                    for (const el of container.querySelectorAll('.item-name, [class*="item-name"], [class*="passive-name"]')) {
                        addName(el.innerText || el.textContent, force);
                    }
                    for (const img of container.querySelectorAll('img[alt], img[title]')) {
                        addName(img.getAttribute('alt') || img.getAttribute('title'), force);
                    }
                }
                return {score, scoreText, passiveItems};
                """,
                list(KNOWN_PASSIVE_ITEMS) + list(self.starting_item_priority) + list(self.starting_item_ignore),
            )
        except Exception:
            return {"score": 0, "scoreText": "", "passiveItems": []}

    def record_run_history_result(self, won, screen):
        signature = self.result_screen_signature(screen)
        if signature == self.run_history_signature:
            return
        self.run_history_signature = signature
        started_at = self.run_started_at or time.time()
        try:
            party = self.party_summary()
            pokemon = party.get("slots", [])[:6]
        except Exception:
            pokemon = []
        if not pokemon:
            pokemon = list(self.last_team_snapshot or [])[:6]
        result_details = self.result_screen_details()
        passive_items = result_details.get("passiveItems") or self.last_passive_items_snapshot or []
        run_number = self.current_history_run_number
        if not run_number:
            run_number = self.reserve_run_history_number()
            self.current_history_run_number = run_number
        entry = {
            "run": int(run_number),
            "target": self.current_run_target,
            "result": "win" if won else "loss",
            "duration": int(time.time() - started_at),
            "money": int(self.run_money_earned or 0),
            "wallet_total": self.last_wallet_pokegold_total,
            "score": int(result_details.get("score") or 0),
            "score_text": str(result_details.get("scoreText") or ""),
            "leaders": int(self.run_leaders_defeated or self.maps_reached or 0),
            "legendaries": int(self.run_legendaries_seen or 0),
            "passive_items": list(passive_items)[:12],
            "pokemon": [
                {
                    "name": str(slot.get("name") or "Unknown"),
                    "level": slot.get("level"),
                    "shiny": bool(slot.get("shiny")),
                }
                for slot in pokemon
                if isinstance(slot, dict)
            ][:6],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with self.run_history_lock:
            self.run_history.append(entry)
            self.run_history = self.run_history[-MAX_RUN_HISTORY:]
            self.save_run_history()
            self.next_history_run_number = max(self.next_history_run_number, entry["run"] + 1)
        self.safe_ui(self.render_run_history_rows)
        self.log(
            f"Run history saved: run #{entry['run']} {entry['result']} "
            f"{self.format_duration_seconds(entry['duration'])}, {entry['money']} Pokegold."
        )

    def record_legendary_encounter(self, signature):
        if not signature or signature == self.last_legendary_signature:
            return
        self.last_legendary_signature = signature
        with self.stats_lock:
            self.total_legendaries_seen += 1
            self.run_legendaries_seen = int(self.run_legendaries_seen or 0) + 1
        self.update_stats_labels()

    def record_run_passive_item(self, name):
        label = " ".join(str(name or "").strip().split())
        normalized = self.normalize_item_name(label)
        if not label or not normalized or normalized == "skip":
            return
        existing = {self.normalize_item_name(item) for item in self.last_passive_items_snapshot}
        if normalized not in existing:
            self.last_passive_items_snapshot.append(label)

    def handle_pokemon_reward_policy(self):
        party = self.party_summary()
        result = self.driver.execute_script(
            """
            const party = arguments[0] || {};
            const legendaryNames = new Set(arguments[1].map(name => name.toLowerCase()));
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0
                    && getComputedStyle(el).display !== 'none'
                    && getComputedStyle(el).visibility !== 'hidden';
            };
            const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const isLegendaryText = (text) => {
                const norm = normalize(text);
                if (norm.includes('legendary')) return true;
                return [...legendaryNames].some(legendary => norm.includes(legendary));
            };
            const buttons = [...document.querySelectorAll('button, [role="button"], .btn-primary, .btn-secondary')]
                .filter(visible);
            const takeButton = buttons.find(btn => {
                const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                const id = (btn.id || '').toLowerCase();
                return id === 'btn-take-shiny'
                    || text.includes('take this pokemon')
                    || text.includes('take this pok')
                    || text.includes('take pokemon')
                    || text.includes('take pok')
                    || /^take\\s+.+!$/.test(text);
            });
            if (!takeButton) return {clicked: false};
            const active = document.querySelector('.screen.active') || document;
            const rewardText = (() => {
                const clone = active.cloneNode(true);
                clone.querySelectorAll([
                    '#team-bar',
                    '#map-team-bar',
                    '#battle-team-bar',
                    '#catch-team-bar',
                    '#item-team-bar',
                    '#passive-team-bar',
                    '.screen-team-bar',
                    '.team-slot'
                ].join(',')).forEach(el => el.remove());
                return (clone.innerText || active.innerText || '').toLowerCase();
            })();
            let rewardShiny = takeButton.id === 'btn-take-shiny'
                || !!active.querySelector('#shiny-content .poke-sprite.shiny, #shiny-content img[src*="/shiny/"], #shiny-content .shiny-badge')
                || rewardText.includes('★ shiny');
            rewardShiny = rewardShiny || rewardText.includes('shiny');
            const rewardLegendary = isLegendaryText(rewardText)
                || isLegendaryText(takeButton.innerText || takeButton.textContent || '')
                || !!active.querySelector('img[src*="legendary"], img[alt*="Legendary"], img[title*="Legendary"]');
            const fullParty = (party.count || 0) >= 6;
            const canReplaceForLegendary = !fullParty
                || !!party.hasReplaceableNonShiny
                || (rewardShiny && !!party.hasReplaceableShinyNonLegendary);
            const shouldSkip = fullParty && (
                (rewardLegendary && !canReplaceForLegendary)
                || (!rewardLegendary && !rewardShiny && !party.hasNonShiny)
            );
            if (shouldSkip) {
                const skipButton = buttons.find(btn => {
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    return btn.id === 'btn-skip-shiny' || text.includes('skip') || text.includes('decline');
                });
                if (!skipButton) return {clicked: false, blocked: true, fullParty, rewardShiny, rewardLegendary};
                skipButton.scrollIntoView({block: 'center', inline: 'center'});
                skipButton.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                skipButton.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                skipButton.click();
                skipButton.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                skipButton.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
                return {clicked: true, skipped: true, text: (skipButton.innerText || skipButton.textContent || '').trim(), fullParty, rewardShiny, rewardLegendary};
            }
            takeButton.scrollIntoView({block: 'center', inline: 'center'});
            takeButton.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
            takeButton.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            takeButton.click();
            takeButton.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            takeButton.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            return {clicked: true, skipped: false, text: (takeButton.innerText || takeButton.textContent || '').trim(), fullParty, rewardShiny, rewardLegendary};
            """,
            party,
            list(LEGENDARY_POKEMON_NAMES),
        )
        if not result.get("clicked"):
            return False
        if result.get("skipped"):
            if result.get("rewardLegendary"):
                self.log("Legendary reward skipped: full team had no valid replacement.")
            else:
                self.log("Pokemon reward skipped: full shiny team and reward was not shiny.")
        else:
            if result.get("fullParty"):
                self.pending_team_replace = True
                self.pending_replace_allow_any = bool(result.get("rewardShiny"))
                if result.get("rewardLegendary"):
                    self.pending_replace_policy = "legendary_shiny" if result.get("rewardShiny") else "legendary"
                else:
                    self.pending_replace_policy = "shiny" if result.get("rewardShiny") else "default"
            self.log(f"Pokemon reward: {result.get('text') or 'Take this Pokemon'}")
            # Count shinies obtained from the dedicated "A Shiny appeared!" /
            # take-reward screen. The catch-screen path counts via
            # record_catch_scan; this screen never goes through it, so without
            # this the shiny tally under-counts. (This handler runs before
            # handle_take_shiny_reward and short-circuits it, so no double count.)
            if result.get("rewardShiny"):
                with self.stats_lock:
                    self.total_shinies_seen += 1
                self.update_stats_labels()
        time.sleep(0.6)
        return True

    def swap_incoming_info(self):
        """Read the Pokémon being offered on the swap screen (name / legendary /
        shiny), from the incoming card or an 'Add X to team!' button."""
        return self.driver.execute_script(
            """
            const legendaryNames = arguments[0].map(n => n.toLowerCase());
            const active = document.querySelector('#swap-screen') || document.querySelector('.screen.active') || document;
            const text = (active.innerText || '').toLowerCase();
            const inc = active.querySelector('#swap-incoming') || active;
            const img = inc.querySelector('img.poke-sprite, img[src*="/pokemon/"]');
            const name = (inc.querySelector('.poke-name')?.innerText || img?.getAttribute('alt') || '').trim();
            const addBtn = [...active.querySelectorAll('button, [role="button"]')]
                .find(b => /add .*to team/i.test(b.innerText || b.textContent || ''));
            const addName = addBtn
                ? (addBtn.innerText || '').replace(/add/i, '').replace(/to team.*/i, '').trim()
                : '';
            const cands = [name, addName].map(s => s.toLowerCase()).filter(Boolean);
            const legendary = text.includes('legendary')
                || legendaryNames.some(l => cands.some(c => c === l || c.includes(l)));
            const src = img?.src || '';
            const shiny = !!inc.querySelector('.shiny-badge, .pc-shiny-star, .shiny-star')
                || src.includes('/shiny/');
            return {name: name || addName, legendary, shiny, hasAdd: !!addBtn};
            """,
            list(LEGENDARY_POKEMON_NAMES),
        )

    def handle_team_replace_choice(self):
        if not self.pending_team_replace:
            return False
        result = self.driver.execute_script(
            """
            const allowAny = arguments[0];
            const policy = arguments[1] || 'default';
            const legendaryNames = new Set(arguments[2].map(name => name.toLowerCase()));
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0
                    && getComputedStyle(el).display !== 'none'
                    && getComputedStyle(el).visibility !== 'hidden';
            };
            const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const isLegendary = (name, text, src) => {
                const normName = normalize(name);
                const normText = normalize(text);
                if (normText.includes('legendary') || String(src || '').toLowerCase().includes('legendary')) return true;
                return [...legendaryNames].some(legendary => normName === legendary || normText.includes(legendary));
            };
            const clickElement = (el) => {
                el.scrollIntoView({block: 'center', inline: 'center'});
                const rect = el.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;
                const target = document.elementFromPoint(x, y) || el;
                for (const clickTarget of [target, el]) {
                    clickTarget.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true, clientX: x, clientY: y}));
                    clickTarget.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, clientX: x, clientY: y}));
                    clickTarget.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, clientX: x, clientY: y}));
                    clickTarget.dispatchEvent(new MouseEvent('click', {bubbles: true, clientX: x, clientY: y}));
                    clickTarget.dispatchEvent(new MouseEvent('pointerup', {bubbles: true, clientX: x, clientY: y}));
                }
                if (typeof el.click === 'function') el.click();
            };
            const active = document.querySelector('.screen.active') || document;
            const addButton = [...active.querySelectorAll('#swap-choices button, #swap-choices [role="button"], button, [role="button"]')]
                .filter(visible)
                .find(btn => {
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    return text.includes('add ') && text.includes(' to team');
                });
            if (addButton) {
                clickElement(addButton);
                return {clicked: true, addClicked: true, text: (addButton.innerText || addButton.textContent || '').trim(), policy};
            }
            const selectors = [
                '.screen.active .team-slot',
                '.screen.active .poke-card',
                '#swap-team-list .team-slot',
                '#swap-team-list .poke-card',
                '#trade-team-list .team-slot',
                '#trade-team-list .poke-card'
            ];
            const seen = new Set();
            const candidates = [];
            for (const selector of selectors) {
                for (const card of document.querySelectorAll(selector)) {
                    if (seen.has(card) || !visible(card)) continue;
                    if (card.closest('#swap-incoming')) continue;
                    seen.add(card);
                    const img = card.querySelector('img.team-sprite, img.poke-sprite, img[src*="/pokemon/"]');
                    const text = (card.innerText || '').toLowerCase();
                    const src = img?.src || '';
                    const shiny = card.classList.contains('shiny')
                        || !!card.querySelector('.shiny-badge, .pc-shiny-star, .shiny-star')
                        || src.includes('/shiny/')
                        || text.includes('shiny');
                    const name = (
                        card.querySelector('.team-slot-name, .poke-name, .battle-poke-name')?.innerText
                        || img?.getAttribute('alt')
                        || card.innerText
                        || 'Pokemon'
                    ).trim().replace(/\\s+/g, ' ').slice(0, 80);
                    candidates.push({
                        card,
                        index: candidates.length,
                        shiny,
                        legendary: isLegendary(name, text, src),
                        name
                    });
                }
            }
            const keepTeamButton = [...active.querySelectorAll('#btn-cancel-swap, button, [role="button"]')]
                .filter(visible)
                .find(btn => {
                    const text = normalize(btn.innerText || btn.textContent || '');
                    return btn.id === 'btn-cancel-swap'
                        || text.includes('keep team as is')
                        || text.includes('keep team')
                        || text.includes('cancel swap');
                });
            let selected = null;
            if (policy === 'legendary' || policy === 'legendary_shiny') {
                // A non-shiny legendary only ever releases a non-shiny, non-legendary
                // Pokémon — never sacrifice a shiny for a non-shiny legendary. If the
                // whole team is shiny, selected stays null -> keep team as-is.
                selected = candidates.find(candidate => !candidate.shiny && !candidate.legendary);
                // A SHINY legendary may release a shiny (shiny-for-shiny), keeping slot 0.
                if (!selected && policy === 'legendary_shiny') {
                    selected = candidates.find(candidate => candidate.index > 0 && candidate.shiny && !candidate.legendary);
                }
            } else {
                selected = candidates.find(candidate => !candidate.shiny) || (allowAny ? candidates[0] : null);
            }
            if (!selected) {
                if (!keepTeamButton) return {clicked: false, count: candidates.length, keepTeamMissing: true, policy};
                clickElement(keepTeamButton);
                return {
                    clicked: true,
                    keptTeam: true,
                    count: candidates.length,
                    text: (keepTeamButton.innerText || keepTeamButton.textContent || '').trim(),
                    policy
                };
            }
            clickElement(selected.card);
            return {clicked: true, name: selected.name, shiny: selected.shiny, legendary: selected.legendary, policy};
            """,
            self.pending_replace_allow_any,
            self.pending_replace_policy,
            list(LEGENDARY_POKEMON_NAMES),
        )
        if not result.get("clicked"):
            return False
        if result.get("addClicked"):
            self.log(f"Team replace: clicked {result.get('text') or 'Add to team'}.")
            time.sleep(0.6)
            return True
        if result.get("keptTeam"):
            self.pending_team_replace = False
            self.pending_replace_allow_any = False
            self.pending_replace_policy = "default"
            self.log(f"Team replace: kept team as-is ({result.get('policy') or 'default'} policy).")
            time.sleep(0.6)
            return True
        self.pending_team_replace = False
        self.pending_replace_allow_any = False
        self.pending_replace_policy = "default"
        self.log(f"Team replace: replaced {result.get('name') or 'Pokemon'}.")
        time.sleep(0.6)
        return True

    def handle_event_pokemon_reward(self):
        result = self.driver.execute_script(
            """
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };
            const buttons = [...document.querySelectorAll('button, [role="button"], .btn-primary, .btn-secondary')]
                .filter(visible);
            const button = buttons.find(btn => {
                const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                return text.includes('take this pokemon')
                    || text.includes('take this pokémon')
                    || text.includes('take pokemon')
                    || text.includes('take pokémon');
            });
            if (!button) return {clicked: false};
            button.scrollIntoView({block: 'center', inline: 'center'});
            button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            button.click();
            button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            return {clicked: true, text: (button.innerText || button.textContent || '').trim()};
            """
        )
        if result.get("clicked"):
            self.log(f"Random event Pokemon reward: {result.get('text') or 'Take this Pokemon'}")
            time.sleep(0.6)
            return True
        return False

    def handle_evolution_choice(self):
        result = self.driver.execute_script(
            """
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0
                    && getComputedStyle(el).display !== 'none'
                    && getComputedStyle(el).visibility !== 'hidden';
            };
            const textRoot = document.querySelector('.screen.active') || document.body;
            const titleText = (textRoot.innerText || document.body.innerText || '').toLowerCase();
            const choiceRoots = [
                '#eevee-choice-overlay',
                '#eevee-choices',
                '#evo-overlay',
                '#evo-choices',
                '#evolution-choices',
                '[id*="evol"]',
                '[class*="evol"]',
                '[id*="variant"]',
                '[class*="variant"]',
                '.evo-choice-overlay',
                '.evolution-choice-overlay',
                '.evolution-choices'
            ].flatMap(selector => [...document.querySelectorAll(selector)]).filter(Boolean);
            const hasVisibleRoot = choiceRoots.some(visible);
            const inlineEvolutionCandidates = [...document.querySelectorAll('img[src*="/pokemon/"]')]
                .map(img => {
                    let el = img.parentElement;
                    while (el && el !== document.body && el !== document.documentElement) {
                        if (el.closest('#team-hover-card, #item-bar, #team-bar, .team-slot, .battle-poke-item')) {
                            return null;
                        }
                        const style = getComputedStyle(el);
                        const sprites = el.querySelectorAll('img[src*="/pokemon/"]').length;
                        const text = (el.innerText || el.textContent || '').trim();
                        const rect = el.getBoundingClientRect();
                        const isPointerCard = style.cursor === 'pointer'
                            && sprites === 1
                            && text
                            && rect.width >= 80
                            && rect.height >= 80;
                        const isKnownEvolutionCard = el.matches('.dex-card, .poke-card, .evo-choice, .evolution-choice, .evo-card, .evolution-card, .evo-option, .evolution-option, [data-evolution], [data-evo], [role="button"]');
                        if (visible(el) && (isPointerCard || isKnownEvolutionCard)) {
                            return el;
                        }
                        el = el.parentElement;
                    }
                    return null;
                })
                .filter(Boolean);
            const hasInlineChoices = inlineEvolutionCandidates.length > 0;
            const hasEvolutionText = titleText.includes('choose its evolution')
                || titleText.includes('choose evolution')
                || titleText.includes('choose an evolution')
                || titleText.includes('choose a evolution')
                || titleText.includes('evolution variant')
                || titleText.includes('evolution:');
            // Guard: the shiny/catch/item/etc. reward screens also contain
            // clickable .poke-card / .dex-card sprites, which the inline heuristic
            // (hasInlineChoices) would otherwise mistake for an evolution choice
            // and click — stalling the run on e.g. the "A Shiny Pokemon appeared"
            // screen. A real evolution is ALWAYS shown via the fixed overlays
            // (#evo-overlay / #eevee-choice-overlay) or explicit evolution text,
            // never inside an active .screen. So on those screens, only trust a
            // visible evolution overlay or evolution text.
            const activeScreen = document.querySelector('.screen.active');
            const activeId = activeScreen ? activeScreen.id : '';
            const NON_EVO_SCREENS = [
                'shiny-screen', 'catch-screen', 'item-screen', 'passive-screen',
                'swap-screen', 'trade-screen', 'stat-buff-screen', 'badge-screen',
                'starter-screen', 'elite-prep-screen', 'gameover-screen', 'win-screen'
            ];
            if (NON_EVO_SCREENS.includes(activeId) && !hasVisibleRoot && !hasEvolutionText) {
                return {clicked: false};
            }
            if (!hasVisibleRoot && !hasEvolutionText && !hasInlineChoices) {
                return {clicked: false};
            }
            const root = choiceRoots.find(visible) || document.querySelector('.screen.active') || document.body || document;
            const selectors = [
                '#eevee-choices [role="button"]',
                '#eevee-choices button',
                '#eevee-choices .dex-card',
                '#eevee-choices .poke-card',
                '#evo-choices [role="button"]',
                '#evo-choices button',
                '#evo-choices .dex-card',
                '#evo-choices .poke-card',
                '#evolution-choices [role="button"]',
                '#evolution-choices button',
                '#evolution-choices .dex-card',
                '#evolution-choices .poke-card',
                '.evo-choice',
                '.evolution-choice',
                '.evo-card',
                '.evolution-card',
                '.evo-option',
                '.evolution-option',
                '[data-evolution]',
                '[data-evo]',
                '[id*="evol"] [role="button"]',
                '[class*="evol"] [role="button"]',
                '[id*="variant"] [role="button"]',
                '[class*="variant"] [role="button"]',
                '.dex-card',
                '.poke-card',
                '[role="button"]',
                'button'
            ];
            const explicitCandidates = [...root.querySelectorAll(selectors.join(','))];
            const spriteCandidates = [...root.querySelectorAll('img[src*="/pokemon/"]')]
                .map(img => {
                    let el = img.parentElement;
                    while (el && el !== root && el !== document.body) {
                        const style = getComputedStyle(el);
                        const pokemonSprites = el.querySelectorAll('img[src*="/pokemon/"]').length;
                        const text = (el.innerText || el.textContent || '').trim();
                        if (pokemonSprites === 1 && text && (
                            style.cursor === 'pointer'
                            || el.onclick
                            || el.getAttribute('role') === 'button'
                            || el.matches('.dex-card, .poke-card, .evo-choice, .evolution-choice, .evo-card, .evolution-card, .evo-option, .evolution-option, [data-evolution], [data-evo]')
                        )) {
                            return el;
                        }
                        el = el.parentElement;
                    }
                    return img.parentElement;
                })
                .filter(Boolean);
            const candidates = [...new Set([...explicitCandidates, ...spriteCandidates, ...inlineEvolutionCandidates])]
                .filter(visible)
                .filter(el => {
                    const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                    const id = (el.id || '').toLowerCase();
                    const cls = (el.className || '').toString().toLowerCase();
                    const aria = (el.getAttribute('aria-label') || '').toLowerCase();
                    const looksLikeChoice = el.matches('.dex-card, .poke-card, .evo-choice, .evolution-choice, .evo-card, .evolution-card, .evo-option, .evolution-option, [data-evolution], [data-evo], [role="button"]')
                        || !!el.querySelector('img[src*="/pokemon/"], .dex-name, .poke-name')
                        || text.length > 0;
                    return !text.includes('cancel') && !text.includes('back')
                        && !text.includes('skip') && !text.includes('reset') && !text.includes('menu')
                        && !id.includes('cancel') && !id.includes('back') && !id.includes('reset') && !id.includes('menu')
                        && !cls.includes('cancel') && !cls.includes('back') && !cls.includes('reset') && !cls.includes('menu')
                        && !aria.includes('menu') && !aria.includes('reset')
                        && !id.includes('cancel') && !id.includes('back')
                        && !cls.includes('cancel') && !cls.includes('back')
                        && looksLikeChoice;
                });
            const card = candidates.find(el => el.querySelector('img[src*="/pokemon/"], .dex-name, .poke-name'))
                || candidates.find(el => !el.matches('button'))
                || candidates[0];
            if (!card) return {clicked: false};
            const name = (
                card.querySelector('.dex-name, .poke-name')?.innerText
                || card.querySelector('img[alt]')?.getAttribute('alt')
                || card.innerText
                || card.textContent
                || 'evolution'
            ).trim().replace(/\\s+/g, ' ').slice(0, 80);
            // Tag the chosen card and let Python click it NATIVELY. The evolution
            // options are dynamically-created divs whose click handler needs a
            // real, trusted pointer (JS-dispatched MouseEvents are isTrusted:false
            // and don't move the OS cursor, which is why the overlay only cleared
            // when the user physically moved the mouse in). A Selenium ActionChains
            // move+click sends a genuine hover+click that the handler accepts.
            card.setAttribute('data-bot-evo-target', '1');
            card.scrollIntoView({block: 'center', inline: 'center'});
            return {found: true, name};
            """
        )
        if not result.get("found"):
            return False
        name = result.get("name") or "random option"
        clicked = False
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, '[data-bot-evo-target="1"]')
            clicked = self.browser_center_click(el, press_enter=True)
            time.sleep(0.25)
            if clicked and self.driver.execute_script(
                "return !!document.querySelector('[data-bot-evo-target=\"1\"]');"
            ):
                self.browser_center_click(el, press_enter=True)
                self.driver.execute_script(
                    """
                    const el = document.querySelector('[data-bot-evo-target="1"]');
                    if (!el) return;
                    el.scrollIntoView({block: 'center', inline: 'center'});
                    const rect = el.getBoundingClientRect();
                    const x = rect.left + rect.width / 2;
                    const y = rect.top + rect.height / 2;
                    const under = document.elementFromPoint(x, y);
                    const targets = [
                        under,
                        under?.closest?.('button, [role="button"], .dex-card, .poke-card, .evo-choice, .evolution-choice, .evo-card, .evolution-card, .evo-option, .evolution-option, [data-evolution], [data-evo]'),
                        el.querySelector('button, [role="button"], img'),
                        el
                    ].filter(Boolean);
                    for (const target of [...new Set(targets)]) {
                        for (const type of ['pointerover', 'mouseover', 'mousemove', 'pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
                            const EventClass = type.startsWith('pointer') && window.PointerEvent ? PointerEvent : MouseEvent;
                            target.dispatchEvent(new EventClass(type, {
                                bubbles: true,
                                cancelable: true,
                                clientX: x,
                                clientY: y,
                                pointerId: 1,
                                pointerType: 'mouse',
                                buttons: type.includes('down') ? 1 : 0
                            }));
                        }
                        if (typeof target.click === 'function') target.click();
                    }
                    """,
                )
            if not clicked:
                raise RuntimeError("CDP center click returned false")
        except Exception as exc:
            self.log(f"Evolution choice: native click failed ({exc}); trying fallback.")
            try:
                self.driver.execute_script(
                    "const el=document.querySelector('[data-bot-evo-target=\"1\"]');"
                    "if(el){el.dispatchEvent(new MouseEvent('mouseover',{bubbles:true}));"
                    "el.dispatchEvent(new MouseEvent('mouseenter',{bubbles:true}));"
                    "el.click();}"
                )
                clicked = True
            except Exception:
                clicked = False
        finally:
            try:
                self.driver.execute_script(
                    "document.querySelector('[data-bot-evo-target=\"1\"]')?.removeAttribute('data-bot-evo-target');"
                )
            except Exception:
                pass
        if clicked:
            self.log(f"Evolution choice: selected {name}.")
            time.sleep(0.6)
            return True
        return False

    def click_play_again_if_visible(self):
        result = self.driver.execute_script(
            """
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };
            const selectors = [
                '#btn-retry',
                '#btn-play-again',
                '#btn-stage-again',
                'button',
                '[role="button"]'
            ];
            const buttons = [...document.querySelectorAll(selectors.join(','))]
                .filter(visible);
            const button = buttons.find(btn => {
                const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                const id = (btn.id || '').toLowerCase();
                return id === 'btn-retry'
                    || id === 'btn-play-again'
                    || id === 'btn-stage-again'
                    || text.includes('play again');
            });
            if (!button) return {clicked: false};
            button.scrollIntoView({block: 'center', inline: 'center'});
            button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            button.click();
            button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            return {clicked: true, text: (button.innerText || button.textContent || '').trim()};
            """
        )
        if result.get("clicked"):
            self.log(f"Clicked {result.get('text') or 'Play Again'}.")
            time.sleep(0.6)
            return True
        return False

    def click_home_if_visible(self):
        result = self.driver.execute_script(
            """
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };
            const buttons = [...document.querySelectorAll('button, [role="button"], a')]
                .filter(visible);
            const button = buttons.find(btn => {
                const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                const id = (btn.id || '').toLowerCase();
                return id === 'btn-home'
                    || id === 'btn-stage-home'
                    || id === 'btn-title'
                    || text === 'home'
                    || text.includes('back home')
                    || text.includes('main menu');
            });
            if (!button) return {clicked: false};
            button.scrollIntoView({block: 'center', inline: 'center'});
            button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            button.click();
            button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            return {clicked: true, text: (button.innerText || button.textContent || '').trim()};
            """
        )
        if result.get("clicked"):
            self.log(f"Clicked {result.get('text') or 'Home'}.")
            time.sleep(0.8)
            return True
        return False

    def click_item_index(self, index):
        elements = [
            element
            for element in self.driver.find_elements(By.CSS_SELECTOR, "#item-choices .item-card")
            if element.rect.get("width", 0) > 0 and element.rect.get("height", 0) > 0
        ]
        if index < len(elements):
            try:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
                    elements[index],
                )
                elements[index].click()
                return
            except Exception:
                pass

        ok = self.driver.execute_script(
            """
            const cards = [...document.querySelectorAll('#item-choices .item-card')]
                .filter(card => {
                    const rect = card.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                });
            const card = cards[arguments[0]];
            if (!card) return false;
            card.scrollIntoView({block: 'center', inline: 'center'});
            const rect = card.getBoundingClientRect();
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;
            const target = document.elementFromPoint(x, y) || card;
            target.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true, clientX: x, clientY: y}));
            target.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, clientX: x, clientY: y}));
            target.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, clientX: x, clientY: y}));
            target.dispatchEvent(new MouseEvent('click', {bubbles: true, clientX: x, clientY: y}));
            card.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true, clientX: x, clientY: y}));
            card.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, clientX: x, clientY: y}));
            card.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, clientX: x, clientY: y}));
            card.dispatchEvent(new MouseEvent('click', {bubbles: true, clientX: x, clientY: y}));
            card.click();
            target.dispatchEvent(new MouseEvent('pointerup', {bubbles: true, clientX: x, clientY: y}));
            card.dispatchEvent(new MouseEvent('pointerup', {bubbles: true, clientX: x, clientY: y}));
            return true;
            """,
            index,
        )
        if not ok:
            raise RuntimeError(f"Could not click item choice #{index}")

    def choose_passive_item(self, target_only=False):
        result = self.driver.execute_script(
            """
            const priority = arguments[0].map(name => name.toLowerCase());
            const targetAliases = arguments[1].map(name => name.toLowerCase());
            const targetOnly = arguments[2];
            const ignored = arguments[3].map(name => name.toLowerCase());
            const allCards = [...document.querySelectorAll('#passive-choices .item-card, #passive-choices .passive-card, #item-choices .item-card, .item-card.passive-card')];
            const isVisible = (card) => {
                const rect = card.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };
            const isLocked = (card) => card.classList.contains('locked')
                || !!card.querySelector('.starting-item-lock')
                || card.getAttribute('aria-disabled') === 'true'
                || card.getAttribute('disabled') !== null;
            // Use ONLY the item name (the label / sprite alt), never the full
            // card innerText — otherwise the name gets concatenated with the
            // description (e.g. "black belt black belt 35 atk 35 def passive"),
            // which polluted the unknown-items list and broke name matching.
            const nameFor = (card) => (
                card.querySelector('.item-name')?.innerText
                || card.querySelector('img[alt]')?.getAttribute('alt')
                || card.querySelector('img[title]')?.getAttribute('title')
                || ''
            ).trim();
            const detailFor = (card) => {
                const name = nameFor(card).replace(/\\s+/g, ' ').trim();
                let detail = (card.innerText || card.textContent || '').replace(/\\s+/g, ' ').trim();
                if (name && detail.toLowerCase().startsWith(name.toLowerCase())) {
                    detail = detail.slice(name.length).trim();
                }
                detail = detail
                    .replace(/\\b(passive|starting item|held item|item)\\b/ig, ' ')
                    .replace(/\\s+/g, ' ')
                    .replace(/^[-:|]+/, '')
                    .trim();
                return detail.slice(0, 160);
            };
            const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const known = (arguments[4] || []).map(name => name.toLowerCase());
            const priorityMatches = (card) => {
                const norm = normalize(nameFor(card));
                return priority.some(alias => norm.includes(alias));
            };
            const isRecognized = (card) => {
                const norm = normalize(nameFor(card));
                if (!norm) return false;
                return priorityMatches(card)
                    || ignored.some(a => norm.includes(a))
                    || known.some(a => norm.includes(a));
            };
            const ignoredMatches = (card) => {
                const norm = normalize(nameFor(card));
                return !priorityMatches(card) && ignored.some(alias => norm.includes(alias));
            };
            const visibleCards = allCards.filter(card => isVisible(card) && !isLocked(card));
            const itemDetails = visibleCards
                .map(card => ({
                    name: nameFor(card).replace(/\\s+/g, ' ').slice(0, 80),
                    detail: detailFor(card)
                }))
                .filter(item => item.name && item.detail);
            const ignoredNames = visibleCards
                .filter(ignoredMatches)
                .map(card => nameFor(card).replace(/\\s+/g, ' ').slice(0, 80));
            // Unrecognized = not ignored, but also not in priority/known/ignore.
            // These are brand-new items the bot doesn't understand: report them so
            // Python can record + auto-ignore, and never pick them here.
            const unrecognizedNames = visibleCards
                .filter(card => !ignoredMatches(card) && !isRecognized(card))
                .map(card => nameFor(card).replace(/\\s+/g, ' ').slice(0, 80));
            const cards = visibleCards.filter(card => !ignoredMatches(card) && isRecognized(card));
            const clickCard = (card) => {
                card.scrollIntoView({block: 'center', inline: 'center'});
                const rect = card.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;
                const target = document.elementFromPoint(x, y) || card;
                for (const el of [target, card]) {
                    el.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, clientX: x, clientY: y, pointerId: 1, pointerType: 'mouse'}));
                    el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, clientX: x, clientY: y}));
                }
                for (const el of [target, card]) {
                    el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, clientX: x, clientY: y}));
                    el.dispatchEvent(new MouseEvent('click', {bubbles: true, clientX: x, clientY: y}));
                    el.dispatchEvent(new PointerEvent('pointerup', {bubbles: true, clientX: x, clientY: y, pointerId: 1, pointerType: 'mouse'}));
                }
                card.click();
            };
            const names = cards.map(card => nameFor(card).replace(/\\s+/g, ' ').slice(0, 80));
            const priorityIndex = (card) => {
                const norm = normalize(nameFor(card));
                const idx = priority.findIndex(alias => norm.includes(alias));
                return idx < 0 ? null : idx;
            };
            if (targetOnly) {
                let target = cards.find(card => {
                    const text = nameFor(card).toLowerCase();
                    return targetAliases.some(alias => text.includes(alias));
                });
                if (target) {
                    const selectedName = nameFor(target) || (target.innerText || '').trim();
                    clickCard(target);
                    return {clicked: true, target: true, fallback: false, name: selectedName.replace(/\\s+/g, ' ').slice(0, 80), names, ignoredNames, unrecognizedNames, itemDetails};
                }
                return {clicked: false, target: false, names, ignoredNames, unrecognizedNames, itemDetails};
            }

            const ranked = cards
                .map(card => ({card, priority: priorityIndex(card)}))
                .filter(choice => choice.priority !== null)
                .sort((a, b) => a.priority - b.priority);
            let card = ranked.length ? ranked[0].card : null;
            let fallback = false;
            if (!card) {
                card = cards[0] || [...document.querySelectorAll('#passive-choices .trait-choice')]
                    .find(el => isVisible(el) && !isLocked(el));
                fallback = true;
            }
            if (!card) {
                // Nothing pickable (all offered items are unrecognized/ignored):
                // skip the screen rather than picking an unknown item.
                const skip = [...document.querySelectorAll('#passive-choices .choice-skip-cell, .choice-skip-btn, #passive-choices button')]
                    .find(el => isVisible(el) && /skip/i.test(el.innerText || el.textContent || ''));
                if (skip) { clickCard(skip); return {clicked: true, skipped: true, name: 'skip', names, ignoredNames, unrecognizedNames, itemDetails}; }
                return {clicked: false, name: '', names, ignoredNames, unrecognizedNames, itemDetails};
            }
            const selectedName = nameFor(card) || (card.innerText || '').trim();
            clickCard(card);
            return {
                clicked: true,
                target: false,
                fallback,
                priority: ranked.length ? ranked[0].priority : null,
                name: selectedName.replace(/\\s+/g, ' ').slice(0, 80),
                names,
                ignoredNames,
                unrecognizedNames,
                itemDetails
            };
            """,
            list(self.starting_item_priority),
            list(TARGET_ITEM_ALIASES),
            target_only,
            # "Don't pick" set = user's ignore list + every unknown item already
            # discovered (kept separate from the user's editable ignore list).
            self.active_starting_item_ignore() + sorted(self.unknown_starting_items),
            list(KNOWN_PASSIVE_ITEMS),
        )
        names = result.get("names") or []
        ignored_names = result.get("ignoredNames") or []
        unrecognized_names = result.get("unrecognizedNames") or []
        item_details = result.get("itemDetails") or []
        if item_details:
            self.record_passive_item_details(item_details)
        if names:
            self.log("Starting item rolls: " + ", ".join(names))
        if unrecognized_names:
            # Save unrecognized items to the list; they are now auto-ignored
            # (fed into the "don't pick" set above on the next offer).
            self.log("Unrecognized passive item(s) → don't pick: " + ", ".join(unrecognized_names))
            self.record_unknown_starting_items(unrecognized_names)
        if ignored_names:
            self.log("Ignored starting item(s): " + ", ".join(ignored_names))
        if not result.get("clicked"):
            if target_only:
                return False
            raise RuntimeError("Could not click a passive choice after applying the never-pick list.")
        if result.get("skipped"):
            # Everything offered was unrecognized/ignored — skipped the screen.
            return False
        # A passive item is offered once per map (start of each Tower/Challenge
        # map), so a successful pick marks entering a new map. Used to re-enable
        # catching from map 3 onward (see prioritize_party_fill in pick_map_node).
        self.maps_started += 1
        if result.get("target"):
            self.pending_passive_item_name = result.get("name") or ""
            self.pending_passive_item_priority = 0
            self.record_run_passive_item(result.get("name") or "")
            self.set_status("Target found")
            self.log(f"TARGET FOUND: {result.get('name')} selected.")
            return True
        self.pending_passive_item_name = result.get("name") or ""
        self.pending_passive_item_priority = result.get("priority")
        self.record_run_passive_item(self.pending_passive_item_name)
        if result.get("fallback"):
            self.log(f"No known starting priority item offered; selected passive fallback: {result.get('name')}")
        else:
            priority = result.get("priority")
            rank = int(priority) + 1 if priority is not None else "unknown"
            self.log(f"Selected passive item: {result.get('name')} (priority {rank})")
        return False

    def get_clickable_map_nodes(self):
        return self.driver.execute_script(
            """
            return [...document.querySelectorAll('#map-container svg g.map-node')]
                .map((node, index) => {
                    const img = node.querySelector('image');
                    const href = img ? (img.getAttribute('href') || img.getAttribute('xlink:href') || '') : '';
                    const rect = node.getBoundingClientRect();
                    return {
                        index,
                        href,
                        cursor: getComputedStyle(node).cursor,
                        y: rect.top + rect.height / 2
                    };
                })
                .filter(node => node.cursor === 'pointer');
            """
        )

    def party_summary(self):
        return self.driver.execute_script(
            """
            const legendaryNames = new Set(arguments[0].map(name => name.toLowerCase()));
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };
            const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const isLegendary = (name, text, src) => {
                const normName = normalize(name);
                const normText = normalize(text);
                if (normText.includes('legendary') || String(src || '').toLowerCase().includes('legendary')) return true;
                return [...legendaryNames].some(legendary => normName === legendary || normText.includes(legendary));
            };
            const selectors = [
                '#team-bar .team-slot',
                '#map-team-bar .team-slot',
                '#battle-team-bar .team-slot',
                '#catch-team-bar .team-slot',
                '#item-team-bar .team-slot',
                '#passive-team-bar .team-slot',
                '.screen.active .team-slot',
                '.screen.active [class*="team"] img[src*="/pokemon/"]',
                '[class*="team"] img[src*="/pokemon/"]'
            ];
            const seen = new Set();
            const slots = [];
            const nameFromSrc = (src) => {
                const file = String(src || '').split('/').pop().split('?')[0].split('#')[0];
                const base = file.replace(/\\.[a-z0-9]+$/i, '').replace(/[-_]+/g, ' ').trim();
                return base.replace(/\\b\\w/g, ch => ch.toUpperCase());
            };
            for (const selector of selectors) {
                for (const raw of document.querySelectorAll(selector)) {
                    const slot = raw.matches('img') ? (raw.closest('.team-slot, [class*="team"]') || raw.parentElement || raw) : raw;
                    if (!slot || !visible(slot) || seen.has(slot)) continue;
                    const img = raw.matches('img') ? raw : slot.querySelector('img.team-sprite, img.poke-sprite, img[src*="/pokemon/"]');
                    if (!img || !visible(img)) continue;
                    const src = img.src || '';
                    const key = `${src}|${slots.length}`;
                    if (seen.has(key)) continue;
                    seen.add(slot);
                    seen.add(key);
                    const name = (
                        slot.querySelector('.team-slot-name, .poke-name, .battle-poke-name')?.innerText
                        || img?.getAttribute('alt')
                        || img?.getAttribute('title')
                        || img?.getAttribute('aria-label')
                        || nameFromSrc(src)
                        || ''
                    ).trim();
                    if (!name) continue;
                    const rawText = slot.innerText || '';
                    const text = rawText.toLowerCase();
                    const levelText = (
                        slot.querySelector('.level, .poke-level, .team-slot-level, [class*="level"]')?.innerText
                        || rawText
                    );
                    const levelMatch = String(levelText || '').match(/(?:lv\\.?|level)\\s*([0-9]+)/i);
                    const shiny = slot.classList.contains('shiny')
                        || !!slot.querySelector('.shiny-badge, .pc-shiny-star, .shiny-star')
                        || src.includes('/shiny/')
                        || text.includes('shiny');
                    slots.push({
                        index: slots.length,
                        name,
                        level: levelMatch ? parseInt(levelMatch[1], 10) : null,
                        shiny,
                        legendary: isLegendary(name, text, src)
                    });
                }
            }
            return {
                count: slots.length,
                hasNonShiny: slots.some(slot => !slot.shiny),
                hasReplaceableNonShiny: slots.some(slot => !slot.shiny && !slot.legendary),
                hasReplaceableShinyNonLegendary: slots.some(slot => slot.index > 0 && slot.shiny && !slot.legendary),
                allShiny: slots.length > 0 && slots.every(slot => slot.shiny),
                slots
            };
            """,
            list(LEGENDARY_POKEMON_NAMES),
        )

    def refresh_team_snapshot(self):
        try:
            party = self.party_summary()
        except Exception:
            return
        slots = party.get("slots", []) if isinstance(party, dict) else []
        if not slots:
            return
        snapshot = [
            {
                "name": str(slot.get("name") or "Unknown"),
                "level": slot.get("level"),
                "shiny": bool(slot.get("shiny")),
            }
            for slot in slots[:6]
            if isinstance(slot, dict)
        ]
        signature = "|".join(
            f"{slot.get('name')}:{slot.get('level')}:{slot.get('shiny')}"
            for slot in snapshot
        )
        if snapshot and signature != self.last_team_snapshot_signature:
            self.last_team_snapshot = snapshot
            self.last_team_snapshot_signature = signature

    def get_map_route_data(self):
        return self.driver.execute_script(
            """
            const svg = document.querySelector('#map-container svg');
            if (!svg) return {nodes: [], edges: []};
            const parseTranslate = (value) => {
                const match = String(value || '').match(/translate\\(([-0-9.]+)[, ]+([-0-9.]+)\\)/);
                return match ? {x: parseFloat(match[1]), y: parseFloat(match[2])} : {x: 0, y: 0};
            };
            const kindFor = (href, html) => {
                const text = `${href || ''} ${html || ''}`.toLowerCase();
                // Legendary encounters use a MASTER BALL node sprite (instead of
                // the normal pokeball). Match masterball / master-ball / master_ball
                // so these get top routing priority instead of falling through to
                // 'other' (which the bot deprioritizes and walks past).
                if (text.includes('legendary') || /master.?ball/.test(text)) return 'legendary';
                if (text.includes('move-tutor')) return 'move-tutor';
                if (text.includes('pokeball') || /poke.?ball/.test(text)) return 'pokeball';
                if (text.includes('grass')) return 'grass';
                if (text.includes('question')) return 'question';
                if (text.includes('item-icon')) return 'item';
                if (text.includes('poke-center')) return 'poke-center';
                if (text.includes('trade')) return 'trade';
                if (text.includes('leader') || text.includes('gym') || text.includes('boss')
                    || text.includes('team-rocket') || text.includes('policeman') || text.includes('hiker')
                    || text.includes('scientist') || text.includes('old-guy') || text.includes('fire-spitter')
                    || text.includes('mistery-trainer') || text.includes('mystery-trainer')) return 'trainer';
                // Region maps use generation-specific sprite folders for
                // trainers and bosses, e.g. g2/captain.png, school-boy.png,
                // falkner.png. Non-trainer map icons are handled above, so any
                // remaining regional sprite should route as a battle node.
                if (/img\\/sprites\\/g\\d+\\//.test(text)) return 'trainer';
                return 'other';
            };
            const nodes = [...svg.querySelectorAll('g.map-node')].map((node, index) => {
                const image = node.querySelector('image');
                const href = image ? (image.getAttribute('href') || image.getAttribute('xlink:href') || '') : '';
                const html = (node.outerHTML || '').toLowerCase();
                const pos = parseTranslate(node.getAttribute('transform'));
                const rect = node.getBoundingClientRect();
                const cursor = getComputedStyle(node).cursor;
                return {
                    index,
                    x: pos.x,
                    y: pos.y,
                    href,
                    html: html.slice(0, 800),
                    kind: kindFor(href, html),
                    clickable: cursor === 'pointer' || node.classList.contains('map-node--clickable'),
                    visible: rect.width > 0 && rect.height > 0
                };
            }).filter(node => node.visible);
            const findNode = (x, y) => nodes.find(node => Math.abs(node.x - x) < 0.75 && Math.abs(node.y - y) < 0.75);
            const edges = [...svg.querySelectorAll('line')].map(line => {
                const a = findNode(parseFloat(line.getAttribute('x1')), parseFloat(line.getAttribute('y1')));
                const b = findNode(parseFloat(line.getAttribute('x2')), parseFloat(line.getAttribute('y2')));
                if (!a || !b) return null;
                return a.y < b.y ? {from: a.index, to: b.index} : {from: b.index, to: a.index};
            }).filter(Boolean);
            return {nodes, edges};
            """
        )

    def get_visible_map_nodes(self):
        return self.driver.execute_script(
            """
            return [...document.querySelectorAll('#map-container svg g.map-node')]
                .map((node, index) => {
                    const img = node.querySelector('image');
                    const href = img ? (img.getAttribute('href') || img.getAttribute('xlink:href') || '') : '';
                    const rect = node.getBoundingClientRect();
                    return {
                        index,
                        href,
                        cursor: getComputedStyle(node).cursor,
                        visible: rect.width > 0 && rect.height > 0,
                        y: rect.top + rect.height / 2,
                        html: node.outerHTML.toLowerCase().slice(0, 600)
                    };
                })
                .filter(node => node.visible);
            """
        )

    def click_map_node(self, node):
        ok = self.driver.execute_script(
            """
            const node = document.querySelectorAll('#map-container svg g.map-node')[arguments[0]];
            if (!node) return false;
            node.scrollIntoView({block: 'center', inline: 'center'});
            const rect = node.getBoundingClientRect();
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;
            const transparentRect = node.querySelector('rect[fill="transparent"], rect');
            const target = transparentRect || document.elementFromPoint(x, y) || node.querySelector('image') || node;
            for (const el of [target, node]) {
                el.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true, clientX: x, clientY: y}));
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, clientX: x, clientY: y}));
                el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, clientX: x, clientY: y}));
                el.dispatchEvent(new MouseEvent('click', {bubbles: true, clientX: x, clientY: y}));
                el.dispatchEvent(new MouseEvent('pointerup', {bubbles: true, clientX: x, clientY: y}));
            }
            if (typeof target.click === 'function') target.click();
            if (typeof node.click === 'function') node.click();
            return true;
            """,
            node["index"],
        )
        if not ok:
            raise RuntimeError(f"Could not click map node #{node['index']}")

    def pick_map_node(self):
        route = self.get_map_route_data()
        nodes = [node for node in route.get("nodes", []) if node.get("clickable")]
        if not nodes:
            raise RuntimeError("No reachable map nodes found.")

        if self.is_pokemon_reroll_mode():
            catch_nodes = [
                node for node in nodes
                if node.get("kind") == "pokeball" or "pokeball" in node.get("href", "").lower()
            ]
            if not catch_nodes:
                return None
            return sorted(catch_nodes, key=lambda node: -node["y"])[0]

        party = self.party_summary()
        party_count = int(party.get("count") or 0)
        # Catch-avoidance: no catching on the first two maps, then resume.
        # Story mode advances maps via badges (maps_reached increments on the
        # badge screen); Battle Tower / Challenge advance via the per-map
        # passive-item pick (maps_started). Reaching map 3 by either signal
        # re-enables party fill / catching.
        prioritize_party_fill = self.maps_reached >= 2 or self.maps_started >= 3
        needs_move_tutor = self.main_move_upgrades_used < MAIN_MOVE_TARGET_USES
        node_by_index = {node["index"]: node for node in route.get("nodes", [])}
        outgoing = {}
        for edge in route.get("edges", []):
            outgoing.setdefault(edge["from"], []).append(edge["to"])

        def reachable_kinds(start_index):
            found = set()
            stack = [start_index]
            seen = set()
            while stack:
                index = stack.pop()
                if index in seen:
                    continue
                seen.add(index)
                node = node_by_index.get(index)
                if node:
                    found.add(node.get("kind"))
                stack.extend(outgoing.get(index, []))
            return found

        def route_bonus(node):
            kinds = reachable_kinds(node["index"])
            if "legendary" in kinds:
                return -300
            if needs_move_tutor and "move-tutor" in kinds:
                return -200
            return 0

        def score(node):
            kind = node.get("kind") or "other"
            if kind == "legendary":
                base = 0
            elif needs_move_tutor and kind == "move-tutor":
                base = 1
            elif kind == "trainer":
                base = 2
            elif prioritize_party_fill and party_count < 6 and kind == "pokeball":
                base = 3
            elif prioritize_party_fill and party_count < 6 and kind == "grass":
                base = 4
            elif kind == "grass":
                base = 3
            elif kind == "question":
                base = 4
            elif kind == "item":
                base = 5
            elif kind == "pokeball":
                base = 6
            elif kind == "poke-center":
                base = 7
            elif kind == "move-tutor":
                base = 8
            elif kind == "trade":
                base = 9
            else:
                base = 10
            return (base + route_bonus(node), 0)

        # Tie-break downward to make steady progress toward the leader.
        chosen = sorted(nodes, key=lambda node: (*score(node), -node["y"]))[0]
        if chosen.get("kind") == "legendary":
            self.log("Map route: prioritizing reachable legendary node.")
        elif route_bonus(chosen) <= -300:
            self.log("Map route: choosing path toward legendary node.")
        elif needs_move_tutor and (chosen.get("kind") == "move-tutor" or route_bonus(chosen) <= -200):
            self.log(f"Map route: choosing path toward move tutor ({self.main_move_upgrades_used}/{MAIN_MOVE_TARGET_USES}).")
        elif prioritize_party_fill and party_count < 6 and chosen.get("kind") == "pokeball":
            self.log(f"Map route: map {self.maps_reached + 1}; party has {party_count}/6 Pokemon; prioritizing pokeball over grass.")
        return chosen

    def wait_for_catch_map_node(self, timeout=2.0):
        deadline = time.time() + timeout
        last_nodes = []
        while time.time() < deadline and not self.stop_event.is_set():
            nodes = self.get_visible_map_nodes()
            last_nodes = nodes
            catch_nodes = [
                node for node in nodes
                if (
                    "pokeball" in node["href"].lower()
                    or "pokeball" in node.get("html", "")
                )
            ]
            if catch_nodes:
                return sorted(catch_nodes, key=lambda node: -node["y"])[0]
            time.sleep(0.12)
        if last_nodes:
            fallback = sorted(last_nodes, key=lambda node: -node["y"])[0]
            hrefs = ", ".join((node.get("href") or "unlabeled") for node in last_nodes[:8])
            self.log(f"No labeled catch node visible; clicking fallback visible map node. Visible nodes: {hrefs}.")
            return fallback
        self.log("No map nodes visible after waiting.")
        return None

    def click_catch_map_node_direct(self, timeout=2.0):
        deadline = time.time() + timeout
        last_summary = ""
        while time.time() < deadline and not self.stop_event.is_set():
            nodes = self.driver.find_elements(By.CSS_SELECTOR, "#map-container svg g.map-node--clickable")
            candidates = []
            for node in nodes:
                try:
                    info = self.driver.execute_script(
                        """
                        const node = arguments[0];
                        const img = node.querySelector('image');
                        const href = img ? (img.getAttribute('href') || img.getAttribute('xlink:href') || '') : '';
                        const rect = node.getBoundingClientRect();
                        return {
                            href,
                            visible: rect.width > 0 && rect.height > 0,
                            y: rect.top + rect.height / 2,
                            text: (node.outerHTML || '').toLowerCase().slice(0, 500)
                        };
                        """,
                        node,
                    )
                except Exception:
                    continue
                if not info.get("visible"):
                    continue
                text = f"{info.get('href') or ''} {info.get('text') or ''}".lower()
                if "pokeball" in text:
                    candidates.append((node, info))

            if candidates:
                node, info = sorted(candidates, key=lambda entry: entry[1].get("y") or 0)[0]
                target = node
                rects = node.find_elements(By.CSS_SELECTOR, 'rect[fill="transparent"], rect')
                if rects:
                    target = rects[-1]
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", node)
                try:
                    target.click()
                except Exception:
                    self.driver.execute_script(
                        """
                        const node = arguments[0];
                        const target = arguments[1];
                        const rect = target.getBoundingClientRect();
                        const x = rect.left + rect.width / 2;
                        const y = rect.top + rect.height / 2;
                        for (const el of [target, node]) {
                            el.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true, clientX:x, clientY:y, pointerId:1, pointerType:'mouse', isPrimary:true}));
                            el.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, clientX:x, clientY:y, button:0, buttons:1}));
                            el.dispatchEvent(new PointerEvent('pointerup', {bubbles:true, clientX:x, clientY:y, pointerId:1, pointerType:'mouse', isPrimary:true}));
                            el.dispatchEvent(new MouseEvent('mouseup', {bubbles:true, clientX:x, clientY:y, button:0, buttons:0}));
                            el.dispatchEvent(new MouseEvent('click', {bubbles:true, clientX:x, clientY:y, button:0}));
                        }
                        """,
                        node,
                        target,
                    )
                self.log(f"Clicked pokeball map node: {info.get('href') or 'unlabeled clickable node'}")
                time.sleep(0.8)
                return True

            all_nodes = self.get_visible_map_nodes()
            last_summary = ", ".join((node.get("href") or "unlabeled") for node in all_nodes[:8])
            time.sleep(0.12)

        self.log(f"No clickable pokeball map node found. Visible map nodes: {last_summary or 'none'}.")
        return False

    def advance_battle(self):
        time.sleep(0.5)
        for _ in range(40):
            if self.stop_event.is_set():
                return

            screen = self.active_screen_id()
            if screen != "battle-screen":
                return

            continue_visible = self.driver.execute_script(
                """
                const btn = document.querySelector('#btn-continue-battle');
                if (!btn) return false;
                const rect = btn.getBoundingClientRect();
                return getComputedStyle(btn).display !== 'none' && rect.width > 0 && rect.height > 0;
                """
            )
            if continue_visible:
                self.js_click("#btn-continue-battle", timeout=3)
                time.sleep(0.7)
                return

            auto_visible = self.driver.execute_script(
                """
                const btn = document.querySelector('#btn-auto-battle');
                if (!btn) return false;
                const rect = btn.getBoundingClientRect();
                return getComputedStyle(btn).display !== 'none' && rect.width > 0 && rect.height > 0;
                """
            )
            if auto_visible:
                self.js_click("#btn-auto-battle", timeout=3)

            time.sleep(0.5)

    def handle_move_tutor(self):
        skip_move_tutor = self.current_mode == MODE_FULL_RUN and self.main_move_upgrades_used >= MAIN_MOVE_TARGET_USES
        result = self.driver.execute_script(
            """
            const skipMoveTutor = arguments[0];
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                const style = getComputedStyle(el);
                return rect.width > 0 && rect.height > 0
                    && style.display !== 'none'
                    && style.visibility !== 'hidden';
            };
            const click = (el) => {
                el.scrollIntoView({block: 'center', inline: 'center'});
                el.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                el.click();
                el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            };
            const modal = document.querySelector('#item-equip-modal');
            const modalText = (modal?.innerText || modal?.textContent || '').toLowerCase();
            const rows = [...document.querySelectorAll('#item-equip-modal .equip-pokemon-row, .equip-pokemon-row')]
                .filter(visible);
            const activeText = [
                modalText,
                document.querySelector('.screen.active')?.innerText || '',
                document.body.innerText || ''
            ].join('\\n').toLowerCase();
            const hasTutorContext = rows.some(row => !!row.querySelector('button[data-tutor]'))
                || !!document.querySelector('button[data-tutor]')
                || !!document.querySelector('#btn-skip-tutor')
                || activeText.includes('move tutor')
                || activeText.includes('teach')
                || activeText.includes('learn move')
                || activeText.includes('tm ');
            if (!hasTutorContext) return {clicked: false};
            const skipButton = [...document.querySelectorAll('#btn-skip-tutor, button, [role="button"]')]
                .filter(visible)
                .find(btn => {
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    const id = (btn.id || '').toLowerCase();
                    const cls = (btn.className || '').toString().toLowerCase();
                    return text.includes('skip') || text.includes('cancel') || text.includes('no thanks')
                        || id.includes('skip') || id.includes('cancel')
                        || cls.includes('skip') || cls.includes('cancel');
                });
            if (skipMoveTutor && rows.length) {
                if (!skipButton) return {clicked: false, blocked: true, reason: 'move tutor quota reached and no skip button was visible'};
                click(skipButton);
                return {clicked: true, skipped: true, text: (skipButton.innerText || skipButton.textContent || '').trim()};
            }
            let row = rows[0] || null;
            let button = row ? row.querySelector('button[data-tutor], button') : null;
            if (!button || !visible(button)) {
                button = [...document.querySelectorAll('button[data-tutor]')].find(visible) || null;
                row = button ? button.closest('.equip-pokemon-row') : row;
            }
            if (!button && rows.length && skipButton) {
                const allRowsMastered = rows.every(candidate => {
                    const text = (candidate.innerText || candidate.textContent || '').toLowerCase();
                    return text.includes('already mastered') || text.includes('(mastered)');
                });
                if (allRowsMastered) {
                    click(skipButton);
                    return {clicked: true, skipped: true, reason: 'all Pokemon already mastered', text: (skipButton.innerText || skipButton.textContent || '').trim()};
                }
            }
            if (!button) return {clicked: false};
            const pokemon = row?.querySelector('.equip-poke-name')?.innerText || '';
            const move = button.innerText || '';
            click(button);
            return {
                clicked: true,
                pokemon: pokemon.trim(),
                move: move.trim()
            };
            """,
            skip_move_tutor,
        )
        if result.get("clicked"):
            if result.get("skipped"):
                reason = result.get("reason") or f"main Pokemon already has {MAIN_MOVE_TARGET_USES} move upgrade(s)"
                self.log(f"Move tutor/TM skipped: {reason}.")
                return True
            if self.current_mode == MODE_FULL_RUN and self.main_move_upgrades_used < MAIN_MOVE_TARGET_USES:
                self.main_move_upgrades_used += 1
            self.log(f"Move tutor: {result.get('pokemon') or 'first Pokemon'} {result.get('move')}")
            return True
        if result.get("blocked"):
            self.log(f"Move tutor/TM screen blocked: {result.get('reason')}")
        return False

    def handle_regular_item_equip(self):
        result = self.driver.execute_script(
            """
            const visible = (el) => {
                if (!el) return false;
                const rect = el.getBoundingClientRect();
                const style = getComputedStyle(el);
                return rect.width > 0 && rect.height > 0
                    && style.display !== 'none'
                    && style.visibility !== 'hidden';
            };
            const click = (el) => {
                el.scrollIntoView({block: 'center', inline: 'center'});
                const rect = el.getBoundingClientRect();
                const x = rect.left + rect.width / 2;
                const y = rect.top + rect.height / 2;
                const target = document.elementFromPoint(x, y) || el;
                for (const node of [...new Set([target, el])]) {
                    node.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true, cancelable: true, clientX: x, clientY: y}));
                    node.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, clientX: x, clientY: y}));
                    node.click();
                    node.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, clientX: x, clientY: y}));
                    node.dispatchEvent(new MouseEvent('pointerup', {bubbles: true, cancelable: true, clientX: x, clientY: y}));
                }
            };
            const active = document.querySelector('.screen.active');
            if (active?.id && active.id !== 'item-screen' && active.id !== 'elite-prep-screen') {
                return {clicked: false};
            }
            const modal = document.querySelector('#item-equip-modal');
            const rows = [...document.querySelectorAll('#item-equip-modal .equip-pokemon-row, .equip-pokemon-row')]
                .filter(visible);
            if (!rows.length) return {clicked: false};
            const activeText = [
                modal?.innerText || modal?.textContent || '',
                active?.innerText || '',
                document.body.innerText || ''
            ].join('\\n').toLowerCase();
            const hasTutorContext = rows.some(row => !!row.querySelector('button[data-tutor]'))
                || !!document.querySelector('button[data-tutor]')
                || !!document.querySelector('#btn-skip-tutor')
                || activeText.includes('move tutor')
                || activeText.includes('teach')
                || activeText.includes('learn move')
                || activeText.includes('tm ');
            if (hasTutorContext) return {clicked: false, blocked: true, reason: 'tutor context'};

            let row = rows.find(candidate => (candidate.getAttribute('data-idx') || '') === '0') || rows[0];
            let button = [...row.querySelectorAll('button, [role="button"]')]
                .filter(visible)
                .find(btn => {
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    return text.includes('equip') || text.includes('use') || text.includes('select');
                }) || null;
            if (!button) {
                button = [...document.querySelectorAll('button, [role="button"]')]
                    .filter(visible)
                    .find(btn => {
                        if (btn.closest('#item-choices')) return false;
                        const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                        return text.includes('equip') || text.includes('use') || text.includes('select') || text.includes('swap');
                    }) || null;
            }
            const target = button || row;
            const pokemon = row.querySelector('.equip-poke-name')?.innerText || row.innerText || 'first Pokemon';
            click(target);
            return {
                clicked: true,
                pokemon: pokemon.trim(),
                targetText: (target.innerText || target.textContent || '').trim()
            };
            """
        )
        if result.get("clicked"):
            self.log(f"Equipped item on {result.get('pokemon') or 'first Pokemon'}.")
            time.sleep(0.45)
            return True
        return False

    def use_rare_candy_on_starter_if_available(self):
        click_script = """
            const el = arguments[0];
            el.scrollIntoView({block: 'center', inline: 'center'});
            const rect = el.getBoundingClientRect();
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;
            const target = document.elementFromPoint(x, y) || el;
            for (const node of [...new Set([target, el])]) {
                if (typeof PointerEvent === 'function') {
                    node.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 1, pointerId: 1, pointerType: 'mouse', isPrimary: true}));
                    node.dispatchEvent(new PointerEvent('pointerup', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0, pointerId: 1, pointerType: 'mouse', isPrimary: true}));
                }
                node.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 1}));
                node.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0}));
                node.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0}));
            }
            if (typeof el.click === 'function') el.click();
        """

        def visible_rare_candy_badge():
            return self.driver.execute_script(
                """
                const visible = (el) => {
                    if (!el) return false;
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0
                        && style.display !== 'none'
                        && style.visibility !== 'hidden';
                };
                const badges = [...document.querySelectorAll([
                    '#item-bar .item-badge',
                    '#elite-prep-items .item-badge',
                    '#item-team-bar .item-badge',
                    '#catch-team-bar .item-badge',
                    '#passive-team-bar .item-badge',
                    '.screen.active .item-badge'
                ].join(','))];
                return badges.find(el => {
                    if (!visible(el)) return false;
                    const imgText = [...el.querySelectorAll('img')]
                        .map(img => `${img.getAttribute('alt') || ''} ${img.getAttribute('title') || ''} ${img.getAttribute('src') || ''}`)
                        .join(' ')
                        .toLowerCase();
                    return imgText.includes('rare candy') || imgText.includes('rare-candy');
                }) || null;
                """
            )

        def first_equip_row():
            return self.driver.execute_script(
                """
                const visible = (el) => {
                    if (!el) return false;
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0
                        && style.display !== 'none'
                        && style.visibility !== 'hidden';
                };
                return [...document.querySelectorAll('.equip-pokemon-row')]
                    .filter(visible)
                    .sort((a, b) => {
                        const ai = parseInt(a.getAttribute('data-idx') || '999', 10);
                        const bi = parseInt(b.getAttribute('data-idx') || '999', 10);
                        return ai - bi;
                    })[0] || null;
                """
            )

        badge = visible_rare_candy_badge()
        if not badge:
            return False
        self.driver.execute_script(click_script, badge)
        row = None
        deadline = time.time() + 1.2
        while time.time() < deadline and not self.stop_event.is_set():
            row = first_equip_row()
            if row:
                break
            time.sleep(0.08)
        if not row:
            self.log("Rare Candy: clicked badge, but no Pokemon target picker appeared; resuming run.")
            return False

        pokemon = self.driver.execute_script(
            "return arguments[0].querySelector('.equip-poke-name')?.innerText || arguments[0].innerText || 'first Pokemon';",
            row,
        )
        self.driver.execute_script(click_script, row)
        self.log(f"Rare Candy: used on {(pokemon or 'first Pokemon').strip()}.")
        time.sleep(0.45)
        return True
        return False

    def record_catch_scan(self, result, phase):
        checked = int(result.get("checked") or 0)
        target_count = int(result.get("targetCount") or 0)
        shiny_names = result.get("shinyNames") or []
        signature = result.get("signature") or result.get("names") or ""
        already_counted = signature == self.last_catch_scan_signature
        if checked:
            if not already_counted:
                with self.stats_lock:
                    self.total_encounters_checked += checked
                    self.target_encounters_seen += target_count
                    self.total_shinies_seen += len(shiny_names)
                    self.run_encounters_checked = self.run_encounters_checked + checked
                    self.run_target_encounters = self.run_target_encounters + target_count
                self.last_catch_scan_signature = signature
                self.update_stats_labels()

        names = result.get("names") or "unknown"
        shiny_text = ", ".join(shiny_names) if shiny_names else "none"
        counted_text = "already counted; " if already_counted else ""
        self.log(
            f"Catch {phase}: {counted_text}checked {checked}; "
            f"target seen {target_count}; shinies {shiny_text}; {names}"
        )

    def click_catch_rerolls_if_available(self):
        result = self.driver.execute_script(
            """
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };
            const isReroll = (btn) => {
                const text = (btn.innerText || btn.textContent || '').toLowerCase();
                const id = (btn.id || '').toLowerCase();
                const cls = (btn.className || '').toString().toLowerCase();
                return text.includes('reroll') || id.includes('reroll') || cls.includes('reroll');
            };
            const clickButton = (button) => {
                button.scrollIntoView({block: 'center', inline: 'center'});
                button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                button.click();
                button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            };
            const cards = [...document.querySelectorAll('#catch-choices .poke-card, #catch-choices [role="button"], .catch-card')]
                .filter(visible);
            const buttons = [];
            for (const card of cards) {
                const button = [...card.querySelectorAll('button, [role="button"], [data-reroll], .reroll-btn, .catch-reroll')]
                    .find(el => visible(el) && isReroll(el));
                if (button && !buttons.includes(button)) buttons.push(button);
            }
            if (!buttons.length) {
                for (const button of [...document.querySelectorAll('button, [role="button"], [data-reroll], .reroll-btn, .catch-reroll')]) {
                    if (visible(button) && isReroll(button) && !buttons.includes(button)) buttons.push(button);
                    if (buttons.length >= Math.max(1, cards.length)) break;
                }
            }
            for (const button of buttons) clickButton(button);
            return {
                clicked: buttons.length > 0,
                count: buttons.length,
                text: buttons.map(btn => (btn.innerText || btn.textContent || '').trim()).filter(Boolean).join(', ')
            };
            """
        )
        if result.get("clicked"):
            self.catch_reroll_used = True
            self.log(f"Catch target missed; clicked {result.get('count')} catch reroll button(s).")
            return True
        return False

    def handle_target_pokemon_catch(self, target_shiny):
        result = self.driver.execute_script(
            """
            const targets = arguments[0].map(name => name.toLowerCase());
            const targetShiny = arguments[1];
            const matchAnyTarget = targets.length === 0;
            const cards = [...document.querySelectorAll('#catch-choices .poke-card, #catch-choices [role="button"], .catch-card')]
                .filter(card => {
                    const rect = card.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                });
            if (!cards.length) return {exists: false};
            const targetMatches = (info) => {
                if (matchAnyTarget) return true;
                const name = (info.name || '').toLowerCase();
                const text = (info.text || '').toLowerCase();
                const alt = (info.alt || '').toLowerCase();
                return targets.some(target => name === target || alt === target || text.includes(target));
            };
            const infoFor = (card, index) => {
                const name = (
                    card.querySelector('.poke-name, .dex-name, .catch-name')?.innerText
                    || card.querySelector('img[alt]')?.getAttribute('alt')
                    || card.innerText
                    || ''
                ).trim();
                const text = (card.innerText || '').toLowerCase();
                const alt = (card.querySelector('img[alt]')?.getAttribute('alt') || '').toLowerCase();
                const src = card.querySelector('img')?.src || '';
                const shiny = card.classList.contains('pc-dex-card--shiny')
                    || card.classList.contains('shiny')
                    || !!card.querySelector('.pc-shiny-star, .shiny-star')
                    || src.includes('/shiny/')
                    || text.includes('shiny');
                const info = {card, index, name, alt, shiny, text: (card.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 100)};
                info.target = targetMatches(info);
                info.matched = info.target && info.shiny === targetShiny;
                return info;
            };
            const infos = cards.map(infoFor);
            const match = infos.find(info => info.matched);
            const targetCount = infos.filter(info => info.target).length;
            const shinyNames = infos.filter(info => info.shiny).map(info => info.name || info.text || 'unknown');
            const names = infos.map(info => `${info.index + 1}:${info.name || info.text || 'unknown'} shiny=${info.shiny}`).join(' | ');
            const signature = infos.map(info => `${info.index}:${info.name || info.text || 'unknown'}:${info.shiny}`).join('|');
            if (!match) {
                return {
                    exists: true,
                    matched: false,
                    checked: infos.length,
                    targetCount,
                    shinyNames,
                    names,
                    signature
                };
            }
            const card = match.card;
            card.scrollIntoView({block: 'center', inline: 'center'});
            card.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
            card.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            card.click();
            card.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            card.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            return {
                exists: true,
                matched: true,
                name: match.name,
                shiny: match.shiny,
                checked: infos.length,
                targetCount,
                shinyNames,
                names,
                signature
            };
            """,
            self.current_target_pokemon_list,
            target_shiny,
        )
        if not result.get("exists"):
            self.log("Catch screen had no visible Pokemon cards.")
            return False
        if result.get("matched"):
            self.record_catch_scan(result, "target found")
            self.set_status("Target found")
            target_name = result.get("name") or self.current_target_pokemon or "any Pokemon"
            shiny_label = "shiny" if target_shiny else "normal"
            self.log(f"TARGET FOUND: {shiny_label} {target_name} in catch choices.")
            return True

        if not self.catch_reroll_used and self.click_catch_rerolls_if_available():
            self.record_catch_scan(result, "before reroll")
            return self.handle_target_pokemon_catch(target_shiny)

        self.record_catch_scan(result, "after reroll")
        self.log(
            "Catch target miss after rerolls: "
            f"{result.get('names') or 'unknown'}. Restarting attempt."
        )
        self.restart_attempt = True
        return False

    def handle_target_shiny_catch(self):
        return self.handle_target_pokemon_catch(target_shiny=True)

    def handle_target_normal_catch(self):
        return self.handle_target_pokemon_catch(target_shiny=False)

    def choose_priority_catch(self):
        def click_priority_choice(immediate_only=False):
            return self.driver.execute_script(
                """
                const immediateOnly = arguments[0];
                const priorityNames = arguments[1].map(name => name.toLowerCase());
                const legendaryNames = new Set(arguments[2].map(name => name.toLowerCase()));
                const matchAnyPriorityName = priorityNames.length === 0;
                const visible = (el) => {
                    const rect = el.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                };
                const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
                const cards = [...document.querySelectorAll('#catch-choices .poke-card, #catch-choices [role="button"], .catch-card')]
                    .filter(visible);
                if (!cards.length) return {clicked: false, reason: 'none'};
                const infoFor = (card, index) => {
                    const text = (card.innerText || card.textContent || '').toLowerCase();
                    const src = card.querySelector('img')?.src || '';
                    const name = (
                        card.querySelector('.poke-name, .dex-name, .catch-name')?.innerText
                        || card.querySelector('img[alt]')?.getAttribute('alt')
                        || card.innerText
                        || ''
                    ).trim().replace(/\\s+/g, ' ').slice(0, 80);
                    const alt = (card.querySelector('img[alt]')?.getAttribute('alt') || '').toLowerCase();
                    const nameLower = name.toLowerCase();
                    const normalizedText = normalize(`${name} ${alt} ${text} ${src}`);
                    const priorityName = !matchAnyPriorityName && priorityNames.some(target =>
                        nameLower === target || alt === target || text.includes(target)
                    );
                    return {
                        card,
                        index,
                        name,
                        priorityName,
                        shiny: card.classList.contains('pc-dex-card--shiny')
                            || card.classList.contains('shiny')
                            || !!card.querySelector('.pc-shiny-star, .shiny-star')
                            || src.includes('/shiny/')
                            || text.includes('shiny'),
                        legendary: normalizedText.includes('legendary')
                            || [...legendaryNames].some(legendary => nameLower === legendary || alt === legendary || normalizedText.includes(legendary)),
                        dragon: text.includes('dragon') || card.querySelector('.type-dragon'),
                        bug: text.includes('bug') || card.querySelector('.type-bug')
                    };
                };
                const infos = cards.map(infoFor);
                const targetCount = infos.filter(info => info.priorityName).length;
                const shinyNames = infos.filter(info => info.shiny).map(info => info.name || 'unknown');
                const names = infos.map(info => `${info.index + 1}:${info.name || 'unknown'} shiny=${info.shiny}`).join(' | ');
                const signature = infos.map(info => `${info.index}:${info.name || 'unknown'}:${info.shiny}`).join('|');
                const selected = infos.find(info => info.shiny)
                    || infos.find(info => info.legendary)
                    || infos.find(info => info.priorityName)
                    || infos.find(info => info.dragon)
                    || infos.find(info => info.bug)
                    || infos[0];
                const reason = selected.shiny ? 'shiny'
                    : selected.legendary ? 'legendary'
                    : selected.priorityName ? 'pokemon list'
                    : selected.dragon ? 'dragon'
                    : selected.bug ? 'bug'
                    : 'random';
                if (immediateOnly && reason !== 'pokemon list' && reason !== 'shiny' && reason !== 'legendary' && reason !== 'dragon') {
                    return {
                        clicked: false,
                        deferred: true,
                        name: selected.name,
                        reason,
                        offered: infos.map(info => `${info.name || 'unknown'}:${info.priorityName ? 'list' : info.shiny ? 'shiny' : info.dragon ? 'dragon' : info.bug ? 'bug' : 'other'}`),
                        checked: infos.length,
                        targetCount,
                        shinyNames,
                        names,
                        signature
                    };
                }
                const card = selected.card;
                card.scrollIntoView({block: 'center', inline: 'center'});
                card.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                card.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                card.click();
                card.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                card.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
                return {
                    clicked: true,
                    name: selected.name,
                    reason,
                    offered: infos.map(info => `${info.name || 'unknown'}:${info.priorityName ? 'list' : info.shiny ? 'shiny' : info.dragon ? 'dragon' : info.bug ? 'bug' : 'other'}`),
                    checked: infos.length,
                    targetCount,
                    shinyNames,
                    names,
                    signature
                };
                """,
                immediate_only,
                self.current_target_pokemon_list,
                list(LEGENDARY_POKEMON_NAMES),
            )

        result = click_priority_choice(immediate_only=True)
        if result.get("deferred") and not self.catch_reroll_used and self.click_catch_rerolls_if_available():
            self.record_catch_scan(result, "full run before reroll")
            time.sleep(0.4)
            result = click_priority_choice(immediate_only=False)
        elif result.get("deferred"):
            result = click_priority_choice(immediate_only=False)

        if result.get("clicked"):
            self.record_catch_scan(result, "full run")
            if result.get("reason") == "legendary":
                self.record_legendary_encounter(f"catch:{result.get('signature')}:{result.get('name')}")
            self.log(f"Catch screen: selected {result.get('name') or 'Pokemon'} by {result.get('reason')} priority.")
            time.sleep(0.8)
            return False
        self.log("Catch screen had no clickable Pokemon choices.")
        return False

    def handle_active_screen(self):
        screen = self.active_screen_id()

        if self.current_mode == MODE_FULL_RUN:
            self.record_money_earned_if_visible()
        if screen not in ["gameover-screen", "win-screen"]:
            self.refresh_team_snapshot()
        if (
            self.current_mode == MODE_FULL_RUN
            and screen not in ["gameover-screen", "win-screen"]
            and self.click_play_again_if_visible()
        ):
            return False

        if self.handle_evolution_choice():
            return False

        if self.handle_move_tutor():
            time.sleep(0.5)
            return False

        if self.handle_regular_item_equip():
            return False

        if self.handle_team_replace_choice():
            return False

        if self.handle_passive_replace_choice():
            return False

        if self.handle_final_fight_confirm():
            return False

        if self.handle_pokemon_reward_policy():
            return False

        if self.handle_take_shiny_reward():
            return False

        if self.handle_event_pokemon_reward():
            return False

        if self.is_pokemon_reroll_mode() and screen in [
            "battle-screen",
            "swap-screen",
            "trade-screen",
            "stat-buff-screen",
            "badge-screen",
        ]:
            self.restart_attempt = True
            self.log(f"Reached {screen} in Pokemon reroll mode. Restarting instead of playing it.")
            return False

        if screen == "starter-screen":
            if self.select_shiny_starter():
                self.wait_until_screen_changes(screen, timeout=0.8)
                return False
            self.log(f"Starter screen: could not select {self.current_starter_name.title()} yet.")
            time.sleep(0.25)
            return False

        if self.current_mode == MODE_FULL_RUN and screen in [
            "map-screen",
            "item-screen",
            "catch-screen",
            "passive-screen",
            "elite-prep-screen",
        ]:
            if self.use_rare_candy_on_starter_if_available():
                return False

        if screen == "map-screen":
            self.catch_reroll_used = False
            if self.is_pokemon_reroll_mode():
                if self.click_catch_map_node_direct():
                    return False
                node = None
            else:
                node = self.pick_map_node()
            if node is None:
                self.restart_attempt = True
                self.log("No reachable catch node left for whitelist checks. Restarting attempt.")
                return False
            self.log(f"Map node: {node['href'] or 'start'}")
            if node.get("kind") == "legendary":
                self.record_legendary_encounter(f"map:{node.get('index')}:{node.get('href')}")
            self.click_map_node(node)
            time.sleep(0.8)
            return False

        if screen == "battle-screen":
            self.advance_battle()
            return False

        if screen == "item-screen":
            if self.is_pokemon_reroll_mode():
                if self.visible_item_choice_context():
                    self.choose_item(target_only=False)
                    return False
                self.restart_attempt = True
                self.log("Reached non-starting item screen in Pokemon reroll mode. Restarting.")
                return False

            if self.awaiting_leader_item_roll:
                self.awaiting_leader_item_roll = False
                if self.current_mode == MODE_SHINY_CHARM_REROLL:
                    self.log("Regular item reward screen reached; waiting for starting item rolls.")
                    return self.choose_item(target_only=False)
                reroll_mode = self.current_mode == MODE_SHINY_CHARM_REROLL
                found = self.choose_item(target_only=reroll_mode)
                if not found:
                    if reroll_mode:
                        self.restart_attempt = True
                        self.log("Target shiny item was not in the first leader item rolls. Restarting.")
                    else:
                        self.log("Shiny Charm was not in the first leader item rolls; continuing full run.")
                return found

            return self.choose_item(target_only=False)

        if screen == "catch-screen":
            if self.current_mode == MODE_SHINY_POKEMON_REROLL:
                return self.handle_target_shiny_catch()
            if self.current_mode == MODE_NORMAL_POKEMON_REROLL:
                return self.handle_target_normal_catch()

            return self.choose_priority_catch()

        if screen == "swap-screen":
            # A legendary from a map node arrives directly on the swap screen
            # (no take/skip step), so pending_team_replace isn't set. If the
            # incoming Pokémon is a legendary, route it through the team-replace
            # handler: it clicks "Add X to team!" when there's room, or releases a
            # valid Pokémon when the team is full. Otherwise keep the team as-is.
            incoming = self.swap_incoming_info() or {}
            if incoming.get("legendary"):
                self.record_legendary_encounter(f"swap:{incoming.get('name')}:{self.active_screen_id()}")
                self.pending_team_replace = True
                self.pending_replace_allow_any = bool(incoming.get("shiny"))
                self.pending_replace_policy = "legendary_shiny" if incoming.get("shiny") else "legendary"
                if self.handle_team_replace_choice():
                    return False
                self.pending_team_replace = False
            self.js_click("#btn-cancel-swap")
            time.sleep(0.6)
            return False

        if screen == "trade-screen":
            self.js_click("#btn-skip-trade")
            time.sleep(0.6)
            return False

        if screen == "passive-screen":
            if self.current_mode == MODE_SHINY_CHARM_REROLL:
                found = self.choose_passive_item(target_only=True)
                if not found:
                    self.restart_attempt = True
                    self.log("Shiny Hunter was not in the starting item rolls. Restarting.")
                return found

            self.choose_passive_item()
            time.sleep(0.25)
            return False

        if screen == "stat-buff-screen":
            self.js_click("#stat-buff-choices .stat-buff-card")
            time.sleep(0.6)
            return False

        if screen == "badge-screen":
            self.maps_reached += 1
            self.run_leaders_defeated = self.maps_reached
            self.awaiting_leader_item_roll = True
            self.log("Badge screen reached.")
            self.update_stats_labels()
            self.js_click("#btn-next-map")
            time.sleep(1.0)
            return False

        if screen == "gameover-screen":
            self.record_money_earned_if_visible()
            self.record_run_history_result(False, screen)
            schedule_action = self.update_schedule_after_result(False, screen)
            if schedule_action == "done":
                return False
            if schedule_action == "advance":
                if self.click_home_if_visible():
                    self.restart_attempt = True
                    return False
                raise RuntimeError("Schedule needs the next task, but Home was not available on the result screen.")
            if self.click_play_again_if_visible():
                return False
            if self.is_pokemon_reroll_mode():
                self.restart_attempt = True
                self.log("Run ended without a whitelist hit. Starting another attempt.")
                return False
            raise RuntimeError("Run ended and Play Again was not available.")

        if screen == "win-screen":
            self.record_money_earned_if_visible()
            self.record_run_history_result(True, screen)
            schedule_action = self.update_schedule_after_result(True, screen)
            if schedule_action == "done":
                return False
            if schedule_action == "advance":
                if self.click_home_if_visible():
                    self.restart_attempt = True
                    return False
                raise RuntimeError("Schedule needs the next task, but Home was not available on the result screen.")
            if self.click_play_again_if_visible():
                return False
            if self.is_pokemon_reroll_mode():
                self.restart_attempt = True
                self.log("Run won without a whitelist hit. Starting another attempt.")
                return False
            raise RuntimeError("Run reached win screen before target item appeared.")

        time.sleep(0.5)
        return False

    def run_single_attempt(self):
        with self.stats_lock:
            self.run_count += 1
            run_number = self.run_count
        self.update_stats_labels()
        self.awaiting_leader_item_roll = False
        self.restart_attempt = False
        self.catch_reroll_used = False
        self.last_catch_scan_signature = None
        self.last_item_signature = None
        self.last_money_signature = None
        self.run_started_at = time.time()
        self.run_money_earned = 0
        self.run_history_signature = None
        self.current_history_run_number = self.reserve_run_history_number()
        self.maps_reached = 0
        self.maps_started = 0
        self.run_legendaries_seen = 0
        self.run_leaders_defeated = 0
        self.last_team_snapshot_signature = None
        self.last_team_snapshot = []
        self.last_passive_items_snapshot = []
        self.pending_team_replace = False
        self.pending_replace_allow_any = False
        self.pending_replace_policy = "default"
        self.pending_passive_item_name = ""
        self.pending_passive_item_priority = None
        self.run_encounters_checked = 0
        self.run_target_encounters = 0
        worker_id = getattr(self.thread_local, "worker_id", 1)
        worker_attempt = getattr(self.thread_local, "attempt_count", 0) + 1
        self.thread_local.attempt_count = worker_attempt
        prefix = f"B{worker_id} " if self.browser_count > 1 else ""
        self.log(f"========== {prefix}RUN #{run_number} ==========")
        if self.manual_first_attempt and worker_attempt == 1:
            if not self.driver:
                raise RuntimeError("Open Browser first, navigate to the run screen, then press Start Bot.")
            if not self.is_active_run_screen():
                screen = self.active_screen_id()
                self.log(
                    f"{prefix}manual start requested, but screen={screen or 'unknown'} is not a run screen; "
                    "starting configured tower instead."
                )
                self.start_challenge_run()
            else:
                self.log(f"{prefix}manual start: using current screen={self.active_screen_id()}.")
        else:
            self.start_challenge_run()

        step = 0
        while not self.stop_event.is_set():
            if self.stop_event.is_set():
                return False
            if self.handle_active_screen():
                self.encounter_history.append(self.run_target_encounters)
                self.update_stats_labels()
                return True
            if self.restart_attempt:
                self.encounter_history.append(self.run_target_encounters)
                self.update_stats_labels()
                return False
            step += 1
            if step and step % 20 == 0:
                self.log(f"Still running {prefix}attempt #{run_number}; screen={self.active_screen_id()}")

        self.encounter_history.append(self.run_target_encounters)
        self.update_stats_labels()
        return False

    def run_bot_worker(self, worker_id, driver):
        self.thread_local.use_local = True
        self.thread_local.worker_id = worker_id
        self.thread_local.attempt_count = 0
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)
        try:
            try:
                self.log(f"B{worker_id} ready: screen={self.active_screen_id() or 'unknown'}")
            except Exception as exc:
                self.log(f"B{worker_id} ready check failed: {exc}")
            recoveries = 0
            while not self.stop_event.is_set():
                try:
                    found = self.run_single_attempt()
                    recoveries = 0
                except Exception as e:
                    if not self.is_pokemon_reroll_mode() or self.stop_event.is_set():
                        raise
                    recoveries += 1
                    screen = "unknown"
                    try:
                        screen = self.active_screen_id()
                    except Exception:
                        pass
                    self.log(f"Recovering Pokemon reroll loop after error on {screen}: {e}")
                    if recoveries >= 5:
                        raise RuntimeError(f"Pokemon reroll loop failed {recoveries} times in a row: {e}")
                    time.sleep(0.4)
                    continue
                if found:
                    self.winning_driver = driver
                    self.stop_event.set()
                    self.close_other_drivers(driver)
                    self.log(f"B{worker_id} found target. Final runtime: {self.format_runtime()}")
                    break
                if self.is_pokemon_reroll_mode():
                    target_kind = "shiny" if self.current_mode == MODE_SHINY_POKEMON_REROLL else "normal"
                    self.log(f"B{worker_id}: no whitelisted {target_kind} Pokemon found. Restarting...")
                else:
                    self.log(f"B{worker_id}: no Shiny Charm yet. Restarting...")

        except Exception as e:
            if not self.stop_event.is_set():
                with self.stats_lock:
                    self.worker_errors.append(worker_id)
                    all_workers_failed = len(set(self.worker_errors)) >= max(1, self.browser_count)
                self.log(f"ERROR in browser {worker_id}: {e}")
                if all_workers_failed:
                    self.set_status("Error")
                    self.stop_event.set()

        finally:
            self.clear_thread_driver()

    def run_bot(self):
        threads = []
        try:
            live_before_launch = len(self.get_live_drivers())
            drivers = self.launch_missing_drivers(self.browser_count)
            if not self.headless_var.get() and (not self.windows_arranged or len(drivers) != live_before_launch):
                self.arrange_browser_windows()
                self.windows_arranged = True
            self.log(f"Running with {len(drivers)} browser window(s).")

            for worker_id, driver in enumerate(drivers, start=1):
                thread = threading.Thread(target=self.run_bot_worker, args=(worker_id, driver), daemon=True)
                threads.append(thread)
                thread.start()

            while any(thread.is_alive() for thread in threads):
                for thread in threads:
                    thread.join(timeout=0.2)

            if self.status_var.get() not in ["Target found", "Error"]:
                self.set_status("Stopped")

        except Exception as e:
            if not self.stop_event.is_set():
                self.set_status("Error")
                self.log(f"ERROR: {e}")

        finally:
            self.stop_event.set()
            for thread in threads:
                if thread.is_alive():
                    thread.join(timeout=1)
            self.finish_ui()
            self.log("Bot stopped.")


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = PokeLikeBotGUI()
    app.mainloop()
