import json
import math
import os
import shutil
import sys
import threading
import time
import tkinter as tk
import tkinter.messagebox as messagebox
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed

import customtkinter as ctk
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


APP_NAME = "PokeLike Bot"
APP_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = getattr(sys, "_MEIPASS", APP_DIR)
DATA_DIR = (
    os.path.join(os.environ.get("LOCALAPPDATA", APP_DIR), APP_NAME)
    if getattr(sys, "frozen", False)
    else APP_DIR
)
ASSETS_DIR = os.path.join(RESOURCE_DIR, "assets")
BRAND_URL = "https://lunaticlabs.shop/"
BANNER_IMAGE_PATH = os.path.join(ASSETS_DIR, "lunaticlabs_banner.png")
FAVICON_IMAGE_PATH = os.path.join(ASSETS_DIR, "lunaticlabs_logo_transp.png")
FAVICON_ICO_PATH = os.path.join(ASSETS_DIR, "favicon.ico")
POKELIKE_URL = "https://pokelike.xyz/"
SELENIUM_PROFILE_PATH = os.path.join(DATA_DIR, "selenium-profile")
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
SETTINGS_PATH = os.path.join(DATA_DIR, "pokelike_settings.json")
UNKNOWN_STARTING_ITEMS_PATH = os.path.join(
    DATA_DIR,
    "unknown_starting_items.json",
)


class PokeLikeBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("900x700")
        self.minsize(820, 620)
        self.banner_image = None
        self.window_icon = None
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
        self.unknown_starting_items = self.load_unknown_starting_items()
        self.chromedriver_path = None
        self.worker_drivers = []
        self.worker_errors = []
        self.winning_driver = None
        self.open_browser_thread = None
        self.windows_arranged = False

        self.run_count = 0
        self.maps_reached = 0
        self.maps_started = 0
        self.item_rolls_checked = 0
        self.total_encounters_checked = 0
        self.target_encounters_seen = 0
        self.total_shinies_seen = 0
        self.total_money_earned = 0
        self.main_move_upgrades_used = 0
        self.run_encounters_checked = 0
        self.run_target_encounters = 0
        self.encounter_history = []
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
        self.current_mode = MODE_FULL_RUN
        self.manual_first_attempt = False
        self.run_target_var = ctk.StringVar(value=self.settings.get("run_target", RUN_TARGET_OPTIONS[0]))
        self.starter_var = ctk.StringVar(value=self.settings.get("starter", STARTER_NAME.title()))
        self.target_pokemon_var = ctk.StringVar(value=self.settings.get("shiny_whitelist", ""))
        self.browser_count_var = ctk.StringVar(value=str(self.settings.get("browser_count", 1)))
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
        self.priority_window = None

        self.build_gui()

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

    def open_brand_link(self, _event=None):
        webbrowser.open_new_tab(BRAND_URL)

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
            name = " ".join(str(item or "").strip().lower().split())
            if not name or name in seen:
                continue
            seen.add(name)
            priorities.append(name)
        return priorities or list(default_values)

    def priority_text(self, values):
        return "\n".join(values)

    def is_pokemon_reroll_mode(self):
        return self.current_mode in [MODE_SHINY_POKEMON_REROLL, MODE_NORMAL_POKEMON_REROLL]

    def normalize_item_name(self, name):
        return " ".join(
            "".join(ch.lower() if ch.isalnum() else " " for ch in str(name or "")).split()
        )

    def load_unknown_starting_items(self):
        try:
            with open(UNKNOWN_STARTING_ITEMS_PATH, "r", encoding="utf-8") as items_file:
                data = json.load(items_file)
        except Exception:
            return set()
        if not isinstance(data, list):
            return set()
        return {self.normalize_item_name(item) for item in data if self.normalize_item_name(item)}

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
        self.log("Unknown starting item(s) recorded: " + ", ".join(sorted(new_items)))

    def save_settings(self):
        settings = {
            "mode": self.mode_var.get(),
            "manual_start": bool(self.manual_start_var.get()),
            "run_target": self.run_target_var.get(),
            "starter": self.starter_var.get().strip(),
            "shiny_whitelist": self.target_pokemon_var.get().strip(),
            "browser_count": self.parse_browser_count(),
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

        logo = ctk.CTkLabel(
            header,
            image=self.banner_image,
            text="" if self.banner_image else "Lunatic Labs",
            font=ctk.CTkFont(size=28, weight="bold"),
            cursor="hand2",
        )
        logo.grid(row=0, column=0, padx=18, pady=16, sticky="w")
        logo.bind("<Button-1>", self.open_brand_link)

        controls = ctk.CTkFrame(self, corner_radius=14)
        controls.grid(row=1, column=0, padx=18, pady=8, sticky="ew")
        controls.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.status_label = self.create_stat(controls, "Status", "Idle", 0, 0)
        self.runtime_label = self.create_stat(controls, "Runtime", "00:00:00", 0, 1)
        self.runs_label = self.create_stat(controls, "Runs", "0", 0, 2)
        self.rolls_label = self.create_stat(controls, "Item rolls checked", "0", 0, 3)
        self.encounters_label = self.create_stat(controls, "Encounters checked", "0", 1, 0)
        self.target_seen_label = self.create_stat(controls, "Target encounters", "0", 1, 1)
        self.shinies_seen_label = self.create_stat(controls, "Shinies seen", "0", 1, 2)
        self.money_label = self.create_stat(controls, "Pokegold", "0", 1, 3)
        self.money_per_hour_label = self.create_stat(controls, "Pokegold / hour", "0/h", 2, 0)

        mode_box = ctk.CTkFrame(controls, fg_color="transparent")
        mode_box.grid(row=3, column=0, columnspan=4, padx=12, pady=(0, 8), sticky="ew")
        mode_box.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(mode_box, text="Mode", text_color="gray70").grid(row=0, column=0, padx=(0, 10), sticky="w")
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
        setup_box.grid(row=4, column=0, columnspan=4, padx=12, pady=(0, 8), sticky="ew")
        setup_box.grid_columnconfigure((1, 3, 5), weight=1)

        ctk.CTkLabel(setup_box, text="Run target", text_color="gray70").grid(row=0, column=0, padx=(0, 8), sticky="w")
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

        manual_box = ctk.CTkFrame(controls, fg_color="transparent")
        manual_box.grid(row=5, column=0, columnspan=4, padx=12, pady=(0, 8), sticky="ew")
        manual_box.grid_columnconfigure(0, weight=1)
        manual_box.grid_columnconfigure(2, weight=0)
        self.manual_start_checkbox = ctk.CTkCheckBox(
            manual_box,
            text="Use current run screen on first attempt",
            variable=self.manual_start_var,
        )
        self.manual_start_checkbox.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(manual_box, text="Browsers", text_color="gray70").grid(row=0, column=1, padx=(12, 8), sticky="e")
        self.browser_count_entry = ctk.CTkEntry(manual_box, textvariable=self.browser_count_var, width=70)
        self.browser_count_entry.grid(row=0, column=2, sticky="e")

        button_box = ctk.CTkFrame(controls, fg_color="transparent")
        button_box.grid(row=6, column=0, columnspan=4, padx=12, pady=(4, 14), sticky="ew")
        button_box.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.open_browser_button = ctk.CTkButton(button_box, text="Open Browser", command=self.open_browser, height=38)
        self.open_browser_button.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        self.start_button = ctk.CTkButton(button_box, text="Start Bot", command=self.start_bot, height=38)
        self.start_button.grid(row=0, column=1, padx=6, sticky="ew")

        self.stop_button = ctk.CTkButton(
            button_box,
            text="Stop",
            command=self.stop_bot,
            state="disabled",
            fg_color="#8a2424",
            hover_color="#a52d2d",
            height=38,
        )
        self.stop_button.grid(row=0, column=2, padx=(6, 0), sticky="ew")

        self.priority_button = ctk.CTkButton(
            button_box,
            text="Item priorities",
            command=self.open_priority_window,
            height=38,
        )
        self.priority_button.grid(row=0, column=3, padx=(12, 0), sticky="ew")

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

    def open_priority_window(self):
        if self.priority_window is not None and self.priority_window.winfo_exists():
            self.priority_window.focus()
            return

        window = ctk.CTkToplevel(self)
        window.title("Item priorities")
        window.geometry("840x620")
        window.minsize(720, 520)
        window.grid_columnconfigure((0, 1), weight=1)
        window.grid_rowconfigure((2, 4), weight=1)
        self.priority_window = window

        ctk.CTkLabel(
            window,
            text="One item per line. Higher priority lines are picked first. Ignored starting items are never picked.",
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

        ctk.CTkLabel(window, text="Starting / passive never-pick list").grid(
            row=3, column=0, padx=(16, 8), pady=(0, 6), sticky="w"
        )
        ignore_text = ctk.CTkTextbox(window, corner_radius=10)
        ignore_text.grid(row=4, column=0, padx=(16, 8), pady=(0, 12), sticky="nsew")
        ignore_text.insert("1.0", self.priority_text(self.starting_item_ignore))

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
        self.maps_reached = 0
        self.maps_started = 0
        self.item_rolls_checked = 0
        self.total_encounters_checked = 0
        self.target_encounters_seen = 0
        self.total_shinies_seen = 0
        self.total_money_earned = 0
        self.main_move_upgrades_used = 0
        self.run_encounters_checked = 0
        self.run_target_encounters = 0
        self.encounter_history = []
        self.awaiting_leader_item_roll = False
        self.restart_attempt = False
        self.last_item_signature = None
        self.last_money_signature = None
        self.catch_reroll_used = False
        self.pending_passive_item_name = ""
        self.pending_passive_item_priority = None
        self.start_time = time.time()
        self.stop_event.clear()
        self.current_mode = selected_mode
        self.manual_first_attempt = bool(self.manual_start_var.get())
        self.current_run_target = self.run_target_var.get()
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

    def launch_driver(self, worker_id=1, make_active=True):
        self.ensure_worker_profile(worker_id)
        profile_path = self.profile_path_for_worker(worker_id)
        os.makedirs(profile_path, exist_ok=True)

        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={profile_path}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        try:
            driver = webdriver.Chrome(
                service=Service(self.get_chromedriver_path()),
                options=options,
            )
        except Exception as manager_exc:
            self.log(f"ChromeDriverManager launch failed, trying Selenium Manager fallback: {manager_exc}")
            try:
                driver = webdriver.Chrome(options=options)
            except Exception as selenium_exc:
                raise RuntimeError(
                    "Chrome could not be opened. Make sure Google Chrome is installed, then try Open Browser again. "
                    f"ChromeDriverManager error: {manager_exc}; Selenium Manager error: {selenium_exc}"
                ) from selenium_exc
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
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center', inline: 'center'}); arguments[0].focus?.({preventScroll: true});",
                        card,
                    )
                    card.click()
                    time.sleep(0.18)
                    if self.active_screen_id() != "starter-screen":
                        return True
                    card.send_keys(Keys.ENTER)
                    time.sleep(0.18)
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
                    try:
                        self.click_card_by_text("#starter-choices", ".poke-card", self.current_starter_name)
                        self.wait_until_screen_changes(screen, timeout=0.45)
                        continue
                    except Exception as exc:
                        self.log(f"Legacy starter picker missed {self.current_starter_name.title()}; trying dex grid. ({exc})")

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
                const active = document.querySelector('.screen.active');
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
            return {found: true, amount, text};
            """
        )
        if not result.get("found"):
            return
        signature = f"{self.active_screen_id()}|{result.get('text') or ''}"
        if signature == self.last_money_signature:
            return
        self.last_money_signature = signature
        amount = int(result.get("amount") or 0)
        with self.stats_lock:
            self.total_money_earned += amount
        self.update_stats_labels()
        self.log(f"Money earned: {amount}; total={self.total_money_earned}")

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
        time.sleep(0.6)
        return True

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
            const active = document.querySelector('.screen.active') || document;
            const addButton = [...active.querySelectorAll('#swap-choices button, #swap-choices [role="button"], button, [role="button"]')]
                .filter(visible)
                .find(btn => {
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    return text.includes('add ') && text.includes(' to team');
                });
            if (addButton) {
                addButton.scrollIntoView({block: 'center', inline: 'center'});
                addButton.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                addButton.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                addButton.click();
                addButton.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                addButton.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
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
            let selected = null;
            if (policy === 'legendary' || policy === 'legendary_shiny') {
                selected = candidates.find(candidate => !candidate.shiny && !candidate.legendary);
                if (!selected && policy === 'legendary_shiny') {
                    selected = candidates.find(candidate => candidate.index > 0 && candidate.shiny && !candidate.legendary);
                }
            } else {
                selected = candidates.find(candidate => !candidate.shiny) || (allowAny ? candidates[0] : null);
            }
            if (!selected) return {clicked: false, count: candidates.length};
            const card = selected.card;
            card.scrollIntoView({block: 'center', inline: 'center'});
            const rect = card.getBoundingClientRect();
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;
            const target = document.elementFromPoint(x, y) || card;
            for (const el of [target, card]) {
                el.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true, clientX: x, clientY: y}));
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, clientX: x, clientY: y}));
                el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, clientX: x, clientY: y}));
                el.dispatchEvent(new MouseEvent('click', {bubbles: true, clientX: x, clientY: y}));
                el.dispatchEvent(new MouseEvent('pointerup', {bubbles: true, clientX: x, clientY: y}));
            }
            if (typeof card.click === 'function') card.click();
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
                '.evo-choice-overlay',
                '.evolution-choice-overlay',
                '.evolution-choices'
            ].map(selector => document.querySelector(selector)).filter(Boolean);
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
            card.scrollIntoView({block: 'center', inline: 'center'});
            const rect = card.getBoundingClientRect();
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;
            const target = document.elementFromPoint(x, y) || card;
            for (const el of [target, card]) {
                if (typeof PointerEvent === 'function') {
                    el.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, clientX: x, clientY: y, pointerId: 1, pointerType: 'mouse'}));
                }
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, clientX: x, clientY: y}));
                el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, clientX: x, clientY: y}));
                el.dispatchEvent(new MouseEvent('click', {bubbles: true, clientX: x, clientY: y}));
                if (typeof PointerEvent === 'function') {
                    el.dispatchEvent(new PointerEvent('pointerup', {bubbles: true, clientX: x, clientY: y, pointerId: 1, pointerType: 'mouse'}));
                }
            }
            if (typeof card.click === 'function') card.click();
            return {clicked: true, name};
            """
        )
        if result.get("clicked"):
            self.log(f"Evolution choice: selected {result.get('name') or 'random option'}.")
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
            const nameFor = (card) => [
                card.querySelector('.item-name')?.innerText || '',
                card.querySelector('img[alt]')?.getAttribute('alt') || '',
                card.querySelector('img[title]')?.getAttribute('title') || '',
                card.innerText || ''
            ].join(' ').trim();
            const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const ignoredMatches = (card) => {
                const norm = normalize(nameFor(card));
                return ignored.some(alias => norm.includes(alias));
            };
            const visibleCards = allCards.filter(card => isVisible(card) && !isLocked(card));
            const ignoredNames = visibleCards
                .filter(ignoredMatches)
                .map(card => nameFor(card).replace(/\\s+/g, ' ').slice(0, 80));
            const cards = visibleCards.filter(card => !ignoredMatches(card));
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
                    return {clicked: true, target: true, fallback: false, name: selectedName.replace(/\\s+/g, ' ').slice(0, 80), names, ignoredNames};
                }
                return {clicked: false, target: false, names, ignoredNames};
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
            if (!card) return {clicked: false, name: '', names, ignoredNames};
            const selectedName = nameFor(card) || (card.innerText || '').trim();
            clickCard(card);
            return {
                clicked: true,
                target: false,
                fallback,
                priority: ranked.length ? ranked[0].priority : null,
                name: selectedName.replace(/\\s+/g, ' ').slice(0, 80),
                names,
                ignoredNames
            };
            """,
            list(self.starting_item_priority),
            list(TARGET_ITEM_ALIASES),
            target_only,
            list(self.starting_item_ignore),
        )
        names = result.get("names") or []
        ignored_names = result.get("ignoredNames") or []
        if names:
            self.log("Starting item rolls: " + ", ".join(names))
            self.record_unknown_starting_items(names)
        if ignored_names:
            self.log("Ignored starting item(s): " + ", ".join(ignored_names))
        if not result.get("clicked"):
            if target_only:
                return False
            raise RuntimeError("Could not click a passive choice after applying the never-pick list.")
        # A passive item is offered once per map (start of each Tower/Challenge
        # map), so a successful pick marks entering a new map. Used to re-enable
        # catching from map 3 onward (see prioritize_party_fill in pick_map_node).
        self.maps_started += 1
        if result.get("target"):
            self.pending_passive_item_name = result.get("name") or ""
            self.pending_passive_item_priority = 0
            self.set_status("Target found")
            self.log(f"TARGET FOUND: {result.get('name')} selected.")
            return True
        self.pending_passive_item_name = result.get("name") or ""
        self.pending_passive_item_priority = result.get("priority")
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
                '.screen.active .team-slot'
            ];
            const seen = new Set();
            const slots = [];
            for (const selector of selectors) {
                for (const slot of document.querySelectorAll(selector)) {
                    if (!visible(slot) || seen.has(slot)) continue;
                    seen.add(slot);
                    const img = slot.querySelector('img.team-sprite, img.poke-sprite, img[src*="/pokemon/"]');
                    const name = (
                        slot.querySelector('.team-slot-name, .poke-name, .battle-poke-name')?.innerText
                        || img?.getAttribute('alt')
                        || ''
                    ).trim();
                    if (!name && !img) continue;
                    const text = (slot.innerText || '').toLowerCase();
                    const src = img?.src || '';
                    const shiny = slot.classList.contains('shiny')
                        || !!slot.querySelector('.shiny-badge, .pc-shiny-star, .shiny-star')
                        || src.includes('/shiny/')
                        || text.includes('shiny');
                    slots.push({
                        index: slots.length,
                        name,
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
                if (text.includes('pokeball')) return 'pokeball';
                if (text.includes('grass')) return 'grass';
                if (text.includes('question')) return 'question';
                if (text.includes('item-icon')) return 'item';
                if (text.includes('poke-center')) return 'poke-center';
                if (text.includes('trade')) return 'trade';
                if (text.includes('leader') || text.includes('gym') || text.includes('boss')
                    || text.includes('team-rocket') || text.includes('policeman') || text.includes('hiker')
                    || text.includes('scientist') || text.includes('old-guy') || text.includes('fire-spitter')
                    || text.includes('mistery-trainer') || text.includes('mystery-trainer')) return 'trainer';
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
            const rows = [...document.querySelectorAll('.equip-pokemon-row')].filter(visible);
            const activeText = (document.querySelector('.screen.active')?.innerText || document.body.innerText || '').toLowerCase();
            const hasTutorContext = rows.some(row => !!row.querySelector('button[data-tutor]'))
                || !!document.querySelector('button[data-tutor]')
                || activeText.includes('move tutor')
                || activeText.includes('teach')
                || activeText.includes('learn move')
                || activeText.includes('tm ');
            if (!hasTutorContext) return {clicked: false};
            const skipButton = [...document.querySelectorAll('button, [role="button"]')]
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
                self.log(f"Move tutor/TM skipped: main Pokemon already has {MAIN_MOVE_TARGET_USES} move upgrade(s).")
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
            const rows = [...document.querySelectorAll('.equip-pokemon-row')].filter(visible);
            if (!rows.length) return {clicked: false};
            const activeText = (active?.innerText || document.body.innerText || '').toLowerCase();
            const hasTutorContext = rows.some(row => !!row.querySelector('button[data-tutor]'))
                || !!document.querySelector('button[data-tutor]')
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
            self.log(f"Catch screen: selected {result.get('name') or 'Pokemon'} by {result.get('reason')} priority.")
            time.sleep(0.8)
            return False
        self.log("Catch screen had no clickable Pokemon choices.")
        return False

    def handle_active_screen(self):
        screen = self.active_screen_id()

        if self.current_mode == MODE_FULL_RUN:
            self.record_money_earned_if_visible()
        if self.current_mode == MODE_FULL_RUN and self.click_play_again_if_visible():
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
            self.awaiting_leader_item_roll = True
            self.log("Badge screen reached.")
            self.js_click("#btn-next-map")
            time.sleep(1.0)
            return False

        if screen == "gameover-screen":
            self.record_money_earned_if_visible()
            if self.click_play_again_if_visible():
                return False
            if self.is_pokemon_reroll_mode():
                self.restart_attempt = True
                self.log("Run ended without a whitelist hit. Starting another attempt.")
                return False
            raise RuntimeError("Run ended and Play Again was not available.")

        if screen == "win-screen":
            self.record_money_earned_if_visible()
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
            if not self.windows_arranged or len(drivers) != live_before_launch:
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
