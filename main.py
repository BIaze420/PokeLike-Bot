import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import tempfile
import urllib.request
import webbrowser
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, as_completed, wait

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
APP_VERSION = "1.0.7"
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
GITHUB_URL = "https://github.com/BIaze420/PokeLike-Bot"
BANNER_IMAGE_PATH = os.path.join(ASSETS_DIR, "lunaticlabs_banner.png")
FAVICON_IMAGE_PATH = os.path.join(ASSETS_DIR, "lunaticlabs_logo_transp.png")
FAVICON_ICO_PATH = os.path.join(ASSETS_DIR, "favicon.ico")
DISCORD_ICON_PATH = os.path.join(ASSETS_DIR, "discord_logo.png")
WEBSITE_ICON_PATH = os.path.join(ASSETS_DIR, "website_globe.png")
GITHUB_ICON_PATH = os.path.join(ASSETS_DIR, "github_logo.png")
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
SHOP_REROLL_PREWARM_COUNT = 6
SHOP_REROLL_LOADING_BROWSER_COUNT = 0
SHOP_REROLL_MAX_PARALLEL_ATTEMPTS = 6
CHROME_DEBUG_PORT_BASE = 49220
DEFAULT_ITEM_REROLL_TARGET = "shiny hunter"
COMPLETE_POKEDEX_ITEM_TARGET = "legend lure"
STARTING_ITEM_REROLL_ALIASES = ("shiny charm", "shiny hunter")
STARTER_NAME = "dratini"
STARTING_ITEM_PRIORITY = (
    "mind plate",
    "weakness policy",
    "hp up",
    "big root",
    "cleanse tag",
    "eject pack",
    "stardust",
    "black sludge",
    "legend lure",
    "power bracer",
    "shiny hunter",
    "yache berry",
    "legend aegis",
    "legend might",
    "pure incense",
    "quick powder",
    "razor claw",
    "muscle band",
    "oran berry",
)
REGULAR_ITEM_PRIORITY = (
    "lucky egg",
    "twisted spoon",
    "rare candy",
    "leftovers",
    "shell bell",
    "tm",
    "choice scarf",
    "choice specs",
    "wide lens",
    "scope lens",
)
COMBAT_HELD_ITEM_PRIORITY = (
    "twisted spoon",
    "leftovers",
    "shell bell",
    "choice scarf",
    "choice specs",
    "wide lens",
    "scope lens",
)
STARTING_ITEM_IGNORE = (
    "adrenaline orb", "air balloon", "aspear berry", "babiri berry", "big mushroom",
    "body plate", "bright powder", "casteliacone", "cell battery", "charti berry",
    "chilan berry", "chople berry", "coba berry", "colbur berry", "comet shard",
    "custap berry", "damp rock", "dark stone", "destiny knot", "draco plate",
    "dragon fang", "dread plate", "earth plate", "eject button", "electirizer",
    "electric seed", "everstone", "fist plate", "flame plate", "float stone",
    "focus band", "focus sash", "haban berry", "hard stone", "hazard lens",
    "heat rock", "icy rock", "insect plate", "iron ball", "iron plate",
    "iron thorns", "kasib berry", "kebia berry", "lagging tail", "lansat berry",
    "lead sparkle", "leaf stone", "legend s call", "life orb", "lucky punch",
    "lum berry", "luminous moss", "macho brace", "magmarizer", "metal alloy",
    "metal coat", "metal powder", "mirror herb", "misty seed", "mystic water",
    "never melt ice", "occa berry", "pecha berry", "pink bow", "pixie plate",
    "poison barb", "power lens", "pretty feather", "pretty wing", "protective pads",
    "protector", "quick claw", "razor fang", "reaper cloth", "resonance",
    "revival herb", "ring target", "rock incense", "rocky helmet", "roseli berry",
    "sea incense", "shed shell", "shiny guard", "shoal salt", "shuca berry",
    "sitrus berry", "sky plate", "smoke ball", "smooth rock", "snowball",
    "soothe bell", "spooky plate", "star piece", "stealth goggles", "sticky barb",
    "tanga berry", "tiny mushroom", "toxic orb", "toxic plate", "wacan berry",
    "soft sand", "dragon scale", "silver powder", "binding band", "light clay",
    "grassy seed", "shiny power", "wise glasses", "black belt",
)
REGULAR_ITEM_IGNORE = (
    "eviolite",
    "red card",
    "dragon fang",
    "choice band",
    "expert belt",
    "metronome",
    "sharp beak",
    "king s rock",
    "assault vest",
    "miracle seed",
    "moon stone",
    "silk scarf",
)
DEX_TARGET_OFF = "Off"
DEX_TARGET_NORMAL = "Missing normal Dex"
DEX_TARGET_SHINY = "Missing shiny Dex"
DEX_TARGET_BOTH = "Missing normal + shiny Dex"
DEX_TARGET_OPTIONS = (DEX_TARGET_OFF, DEX_TARGET_NORMAL, DEX_TARGET_SHINY, DEX_TARGET_BOTH)
FULL_RUN_DEX_PRIORITY_OPTIONS = DEX_TARGET_OPTIONS
POKEMON_FILTER_PRIORITIZE = "Prioritize"
POKEMON_FILTER_ONLY = "Only"
POKEMON_FILTER_OPTIONS = (POKEMON_FILTER_PRIORITIZE, POKEMON_FILTER_ONLY)
POKEMON_WHITELIST_PRIORITIZE = "Prioritize whitelist"
POKEMON_WHITELIST_ONLY = "Only whitelist"
POKEMON_WHITELIST_ONLY_OR_SHINY = "Only whitelist + shiny"
POKEMON_WHITELIST_OPTIONS = (
    POKEMON_WHITELIST_PRIORITIZE,
    POKEMON_WHITELIST_ONLY,
    POKEMON_WHITELIST_ONLY_OR_SHINY,
)
REROLL_COMPLETE_STOP_NOW = "Stop when target appears"
REROLL_COMPLETE_ONE_FULL_RUN = "Complete 1 full run"
REROLL_COMPLETE_CHAIN_FULL_RUNS = "Chain full runs"
REROLL_COMPLETION_OPTIONS = (
    REROLL_COMPLETE_STOP_NOW,
    REROLL_COMPLETE_ONE_FULL_RUN,
    REROLL_COMPLETE_CHAIN_FULL_RUNS,
)
SHOP_REROLL_AFTER_HIT_STOP = "Stop after cloud upload"
SHOP_REROLL_AFTER_HIT_CONTINUE = "Ignore uploaded hit + continue"
SHOP_REROLL_AFTER_HIT_OPTIONS = (
    SHOP_REROLL_AFTER_HIT_STOP,
    SHOP_REROLL_AFTER_HIT_CONTINUE,
)
SHOP_REROLL_POST_HIT_RUN_SECONDS = 5 * 60
SHOP_REROLL_POST_HIT_MAX_TRIES = 10
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
CONSUMABLE_ITEM_ALIASES = ("rare candy", "tm", "sacred ash")
MAIN_MOVE_TARGET_USES = 2
POKEMON_TYPE_NAMES = (
    "normal", "fire", "water", "electric", "grass", "ice", "fighting",
    "poison", "ground", "flying", "psychic", "bug", "rock", "ghost",
    "dragon", "dark", "steel", "fairy",
)
POKEMON_TYPE_GROUPS = tuple(f"{type_name.title()} type" for type_name in POKEMON_TYPE_NAMES)
POKEMON_GENERATION_OPTIONS = (
    "Kanto", "Johto", "Hoenn", "Sinnoh", "Unova", "Kalos", "Alola", "Galar", "Paldea",
)
POKEMON_TYPE_COLORS = {
    "Normal type": "#a8a77a",
    "Fire type": "#ee8130",
    "Water type": "#6390f0",
    "Electric type": "#f7d02c",
    "Grass type": "#7ac74c",
    "Ice type": "#96d9d6",
    "Fighting type": "#c22e28",
    "Poison type": "#a33ea1",
    "Ground type": "#e2bf65",
    "Flying type": "#a98ff3",
    "Psychic type": "#f95587",
    "Bug type": "#a6b91a",
    "Rock type": "#b6a136",
    "Ghost type": "#735797",
    "Dragon type": "#6f35fc",
    "Dark type": "#705746",
    "Steel type": "#b7b7ce",
    "Fairy type": "#d685ad",
    "General": "#94a3b8",
}
LEGENDARY_POKEMON_NAMES = {
    "articuno", "zapdos", "moltres", "mewtwo", "mew",
    "raikou", "entei", "suicune", "lugia", "ho-oh", "celebi",
    "regirock", "regice", "registeel", "latias", "latios", "kyogre", "groudon", "rayquaza", "jirachi", "deoxys",
    "uxie", "mesprit", "azelf", "dialga", "palkia", "heatran", "regigigas", "giratina", "cresselia", "phione",
    "manaphy", "darkrai", "shaymin", "arceus",
    "victini", "cobalion", "terrakion", "virizion", "tornadus", "thundurus", "reshiram", "zekrom", "landorus",
    "kyurem", "keldeo", "meloetta", "genesect",
}
EVOLUTION_CHAIN_TEXT = """
bulbasaur>ivysaur>venusaur
charmander>charmeleon>charizard
squirtle>wartortle>blastoise
caterpie>metapod>butterfree
weedle>kakuna>beedrill
pidgey>pidgeotto>pidgeot
pichu>pikachu>raichu
nidoran f>nidorina>nidoqueen
nidoran m>nidorino>nidoking
cleffa>clefairy>clefable
vulpix>ninetales
igglybuff>jigglypuff>wigglytuff
zubat>golbat>crobat
oddish>gloom>vileplume
oddish>gloom>bellossom
poliwag>poliwhirl>poliwrath
poliwag>poliwhirl>politoed
abra>kadabra>alakazam
machop>machoke>machamp
bellsprout>weepinbell>victreebel
geodude>graveler>golem
slowpoke>slowbro
slowpoke>slowking
magnemite>magneton>magnezone
onix>steelix
rhyhorn>rhydon>rhyperior
happiny>chansey>blissey
tangela>tangrowth
horsea>seadra>kingdra
staryu>starmie
scyther>scizor
scyther>kleavor
elekid>electabuzz>electivire
magby>magmar>magmortar
eevee>vaporeon
eevee>jolteon
eevee>flareon
eevee>espeon
eevee>umbreon
eevee>leafeon
eevee>glaceon
eevee>sylveon
porygon>porygon2>porygon z
dratini>dragonair>dragonite
chikorita>bayleef>meganium
cyndaquil>quilava>typhlosion
totodile>croconaw>feraligatr
togepi>togetic>togekiss
mareep>flaaffy>ampharos
azurill>marill>azumarill
hoppip>skiploom>jumpluff
swinub>piloswine>mamoswine
larvitar>pupitar>tyranitar
treecko>grovyle>sceptile
torchic>combusken>blaziken
mudkip>marshtomp>swampert
wurmple>silcoon>beautifly
wurmple>cascoon>dustox
ralts>kirlia>gardevoir
ralts>kirlia>gallade
slakoth>vigoroth>slaking
aron>lairon>aggron
trapinch>vibrava>flygon
duskull>dusclops>dusknoir
snorunt>glalie
snorunt>froslass
bagon>shelgon>salamence
beldum>metang>metagross
turtwig>grotle>torterra
chimchar>monferno>infernape
piplup>prinplup>empoleon
starly>staravia>staraptor
shinx>luxio>luxray
gible>gabite>garchomp
riolu>lucario
snivy>servine>serperior
tepig>pignite>emboar
oshawott>dewott>samurott
lillipup>herdier>stoutland
roggenrola>boldore>gigalith
timburr>gurdurr>conkeldurr
tympole>palpitoad>seismitoad
venipede>whirlipede>scolipede
sandile>krokorok>krookodile
litwick>lampent>chandelure
axew>fraxure>haxorus
klink>klang>klinklang
tynamo>eelektrik>eelektross
golett>golurk
pawniard>bisharp>kingambit
deino>zweilous>hydreigon
chespin>quilladin>chesnaught
fennekin>braixen>delphox
froakie>frogadier>greninja
fletchling>fletchinder>talonflame
honedge>doublade>aegislash
goomy>sliggoo>goodra
rowlet>dartrix>decidueye
litten>torracat>incineroar
popplio>brionne>primarina
pikipek>trumbeak>toucannon
grubbin>charjabug>vikavolt
bounsweet>steenee>tsareena
jangmo o>hakamo o>kommo o
grookey>thwackey>rillaboom
scorbunny>raboot>cinderace
sobble>drizzile>inteleon
rookidee>corvisquire>corviknight
rolycoly>carkol>coalossal
applin>flapple
applin>appletun
applin>dipplin>hydrapple
hatenna>hattrem>hatterene
impidimp>morgrem>grimmsnarl
dreepy>drakloak>dragapult
sprigatito>floragato>meowscarada
fuecoco>crocalor>skeledirge
quaxly>quaxwell>quaquaval
pawmi>pawmo>pawmot
smoliv>dolliv>arboliva
nacli>naclstack>garganacl
charcadet>armarouge
charcadet>ceruledge
tinkatink>tinkatuff>tinkaton
frigibax>arctibax>baxcalibur
"""
POKEMON_GENERATION_NAME_GROUPS = {
    "kanto": """
        bulbasaur ivysaur venusaur charmander charmeleon charizard squirtle wartortle blastoise
        caterpie metapod butterfree weedle kakuna beedrill pidgey pidgeotto pidgeot pikachu raichu
        nidoran f nidorina nidoqueen nidoran m nidorino nidoking clefairy clefable vulpix ninetales
        jigglypuff wigglytuff zubat golbat oddish gloom vileplume poliwag poliwhirl poliwrath abra
        kadabra alakazam machop machoke machamp bellsprout weepinbell victreebel geodude graveler
        golem slowpoke slowbro magnemite magneton onix rhyhorn rhydon chansey tangela horsea seadra
        staryu starmie scyther electabuzz magmar eevee vaporeon jolteon flareon porygon dratini
        dragonair dragonite articuno zapdos moltres mewtwo mew
    """,
    "johto": """
        pichu cleffa igglybuff crobat bellossom politoed slowking steelix blissey kingdra scizor
        elekid magby espeon umbreon porygon2 chikorita bayleef meganium cyndaquil quilava typhlosion
        totodile croconaw feraligatr togepi togetic mareep flaaffy ampharos azurill marill azumarill
        hoppip skiploom jumpluff swinub piloswine larvitar pupitar tyranitar raikou entei suicune
        lugia ho-oh celebi
    """,
    "hoenn": """
        treecko grovyle sceptile torchic combusken blaziken mudkip marshtomp swampert wurmple silcoon
        beautifly cascoon dustox ralts kirlia gardevoir slakoth vigoroth slaking aron lairon aggron
        trapinch vibrava flygon duskull dusclops snorunt glalie bagon shelgon salamence beldum metang
        metagross regirock regice registeel latias latios kyogre groudon rayquaza jirachi deoxys
    """,
    "sinnoh": """
        magnezone rhyperior tangrowth electivire magmortar leafeon glaceon porygon z mamoswine
        dusknoir froslass gallade togekiss turtwig grotle torterra chimchar monferno infernape piplup
        prinplup empoleon starly staravia staraptor shinx luxio luxray gible gabite garchomp riolu
        lucario uxie mesprit azelf dialga palkia heatran regigigas giratina cresselia phione manaphy
        darkrai shaymin arceus
    """,
    "unova": """
        snivy servine serperior tepig pignite emboar oshawott dewott samurott lillipup herdier stoutland
        roggenrola boldore gigalith timburr gurdurr conkeldurr tympole palpitoad seismitoad venipede
        whirlipede scolipede sandile krokorok krookodile litwick lampent chandelure axew fraxure haxorus
        klink klang klinklang tynamo eelektrik eelektross golett golurk pawniard bisharp deino zweilous
        hydreigon victini cobalion terrakion virizion tornadus thundurus reshiram zekrom landorus kyurem
        keldeo meloetta genesect
    """,
    "kalos": """
        chespin quilladin chesnaught fennekin braixen delphox froakie frogadier greninja fletchling
        fletchinder talonflame honedge doublade aegislash goomy sliggoo goodra sylveon
    """,
    "alola": """
        rowlet dartrix decidueye litten torracat incineroar popplio brionne primarina pikipek trumbeak
        toucannon grubbin charjabug vikavolt bounsweet steenee tsareena jangmo o hakamo o kommo o
    """,
    "galar": """
        grookey thwackey rillaboom scorbunny raboot cinderace sobble drizzile inteleon rookidee
        corvisquire corviknight rolycoly carkol coalossal applin flapple appletun hatenna hattrem
        hatterene impidimp morgrem grimmsnarl dreepy drakloak dragapult
    """,
    "paldea": """
        sprigatito floragato meowscarada fuecoco crocalor skeledirge quaxly quaxwell quaquaval pawmi
        pawmo pawmot smoliv dolliv arboliva nacli naclstack garganacl charcadet armarouge ceruledge
        tinkatink tinkatuff tinkaton frigibax arctibax baxcalibur dipplin hydrapple
    """,
}
POKEMON_TYPE_NAME_GROUPS = {
    "dragon": "dratini dragonair dragonite horsea seadra kingdra trapinch vibrava flygon bagon shelgon salamence gible gabite garchomp axew fraxure haxorus deino zweilous hydreigon goomy sliggoo goodra jangmo o hakamo o kommo o applin flapple appletun dipplin hydrapple dreepy drakloak dragapult frigibax arctibax baxcalibur latias latios rayquaza dialga palkia giratina reshiram zekrom kyurem",
    "bug": "caterpie metapod butterfree weedle kakuna beedrill scyther scizor wurmple silcoon beautifly cascoon dustox venipede whirlipede scolipede grubbin charjabug vikavolt",
    "grass": "bulbasaur ivysaur venusaur oddish gloom vileplume bellossom bellsprout weepinbell victreebel tangela tangrowth chikorita bayleef meganium hoppip skiploom jumpluff treecko grovyle sceptile turtwig grotle torterra snivy servine serperior chespin quilladin chesnaught rowlet dartrix decidueye bounsweet steenee tsareena grookey thwackey rillaboom applin flapple appletun dipplin hydrapple sprigatito floragato meowscarada smoliv dolliv arboliva shaymin",
    "fire": "charmander charmeleon charizard vulpix ninetales magby magmar magmortar cyndaquil quilava typhlosion torchic combusken blaziken chimchar monferno infernape tepig pignite emboar litwick lampent chandelure fennekin braixen delphox litten torracat incineroar scorbunny raboot cinderace rolycoly carkol coalossal fuecoco crocalor skeledirge charcadet armarouge ceruledge moltres entei heatran victini reshiram",
    "water": "squirtle wartortle blastoise poliwag poliwhirl poliwrath politoed slowpoke slowbro slowking horsea seadra kingdra staryu starmie vaporeon totodile croconaw feraligatr azurill marill azumarill mudkip marshtomp swampert piplup prinplup empoleon tympole palpitoad seismitoad oshawott dewott samurott froakie frogadier greninja popplio brionne primarina sobble drizzile inteleon quaxly quaxwell quaquaval articuno suicune lugia kyogre palkia phione manaphy keldeo",
    "electric": "pichu pikachu raichu magnemite magneton magnezone elekid electabuzz electivire mareep flaaffy ampharos shinx luxio luxray tynamo eelektrik eelektross grubbin charjabug vikavolt pawmi pawmo pawmot zapdos raikou thundurus zekrom",
    "normal": "pidgey pidgeotto pidgeot cleffa clefairy clefable igglybuff jigglypuff wigglytuff happiny chansey blissey eevee porygon porygon2 porygon z togepi togetic starly staravia staraptor lillipup herdier stoutland",
    "flying": "charizard butterfree pidgey pidgeotto pidgeot zubat golbat crobat scyther hoppip skiploom jumpluff togetic togekiss starly staravia staraptor fletchling fletchinder talonflame rowlet dartrix decidueye pikipek trumbeak toucannon rookidee corvisquire corviknight articuno zapdos moltres lugia ho-oh rayquaza tornadus landorus",
    "poison": "bulbasaur ivysaur venusaur weedle kakuna beedrill nidoran f nidorina nidoqueen nidoran m nidorino nidoking zubat golbat crobat oddish gloom vileplume bellsprout weepinbell victreebel venipede whirlipede scolipede",
    "ground": "geodude graveler golem onix rhyhorn rhydon rhyperior swinub piloswine mamoswine mudkip marshtomp swampert trapinch vibrava flygon turtwig grotle torterra gible gabite garchomp roggenrola boldore gigalith tympole palpitoad seismitoad sandile krokorok krookodile golett golurk groudon landorus",
    "psychic": "abra kadabra alakazam staryu starmie ralts kirlia gardevoir gallade fennekin braixen delphox hatenna hattrem hatterene mewtwo mew celebi latias latios jirachi deoxys uxie mesprit azelf cresselia victini meloetta",
    "rock": "geodude graveler golem onix rhydon rhyperior larvitar pupitar tyranitar aron lairon aggron roggenrola boldore gigalith rolycoly carkol coalossal nacli naclstack garganacl regirock",
    "ice": "swinub piloswine mamoswine snorunt glalie froslass glaceon frigibax arctibax baxcalibur articuno regice kyurem",
    "fighting": "poliwrath machop machoke machamp combusken blaziken gallade monferno infernape riolu lucario pignite emboar timburr gurdurr conkeldurr chesnaught hakamo o kommo o quaquaval cobalion terrakion virizion keldeo",
    "ghost": "duskull dusclops dusknoir froslass litwick lampent chandelure golett golurk honedge doublade aegislash dreepy drakloak dragapult giratina",
    "dark": "umbreon larvitar pupitar tyranitar sneasel sandile krokorok krookodile pawniard bisharp kingambit deino zweilous hydreigon impidimp morgrem grimmsnarl meowscarada incineroar greninja darkrai",
    "steel": "magnemite magneton magnezone steelix scizor aron lairon aggron beldum metang metagross piplup prinplup empoleon riolu lucario klink klang klinklang pawniard bisharp kingambit honedge doublade aegislash corvisquire corviknight tinkatink tinkatuff tinkaton registeel dialga genesect",
    "fairy": "cleffa clefairy clefable igglybuff jigglypuff wigglytuff azurill marill azumarill ralts kirlia gardevoir togepi togetic togekiss sylveon primarina impidimp morgrem grimmsnarl tinkatink tinkatuff tinkaton xerneas",
}
LEADER_OR_ELITE_TRAINER_NAMES = {
    "brock", "misty", "lt surge", "surge", "erika", "koga", "sabrina", "blaine", "giovanni",
    "lorelei", "bruno", "agatha", "lance", "blue", "red",
    "falkner", "bugsy", "whitney", "morty", "chuck", "jasmine", "pryce", "clair", "will", "karen",
    "roxanne", "brawly", "wattson", "flannery", "norman", "winona", "tate", "liza", "wallace",
    "juan", "sidney", "phoebe", "glacia", "drake", "steven",
    "roark", "gardenia", "maylene", "crasher wake", "wake", "fantina", "byron", "candice", "volkner",
    "aaron", "bertha", "flint", "lucian", "cynthia", "cyrus",
    "cilan", "chili", "cress", "lenora", "burgh", "elesa", "clay", "skyla", "brycen", "drayden", "iris",
    "marlon", "shauntal", "marshal", "grimsley", "caitlin", "alder", "n", "ghetsis", "colress",
    "viola", "grant", "korrina", "ramos", "clemont", "valerie", "olympia", "wulfric",
    "malva", "siebold", "wikstrom", "drasna", "diantha", "lysandre",
    "hala", "olivia", "nanu", "hapuu", "ilima", "lana", "kiawe", "mallow", "sophocles", "acerola", "mina",
    "molayne", "kahili", "kukui", "lusamine", "guzma",
    "milo", "nessa", "kabu", "bea", "allister", "opal", "bede", "gordie", "melony", "piers", "marnie",
    "raihan", "leon", "rose", "oleana", "klara", "avery", "mustard", "peony",
    "katy", "brassius", "iono", "kofu", "larry", "ryme", "tulip", "grusha",
    "rika", "poppy", "hassel", "geeta", "nemona", "clavell", "penny", "arven", "sada", "turo",
}
MODE_FULL_RUN = "Full run"
LEGACY_MODE_SHINY_CHARM_REROLL = "Shiny Charm reroll"
MODE_ITEM_REROLL = "Item reroll"
MODE_SHINY_CHARM_REROLL = MODE_ITEM_REROLL
MODE_SHINY_POKEMON_REROLL = "Shiny Pokemon reroll"
MODE_NORMAL_POKEMON_REROLL = "Normal Pokemon reroll"
MODE_COMPLETE_POKEDEX = "Complete Pokedex"
MODE_POKEGOLD_FARM = "Farm Pokegold"
MODE_SHINY_SHOP_REROLL = "Shiny Pokemon shop reroll"
MODE_LEGENDARY_SHOP_REROLL = "Legendary shop reroll"
SHOP_REROLL_WINDOW_AREA_RATIO = 0.25
SHOP_REROLL_MAX_WINDOW_SIZE = (900, 700)
SHOP_REROLL_MIN_WINDOW_SIZE = (560, 420)
RUN_TARGET_CHALLENGE = "Challenge Mode"
RUN_TARGET_WEEKLY = "Weekly Challenge"
RUN_TARGET_DAILY = "Daily Challenge"
TOWER_REGIONS = ("Kanto", "Johto", "Hoenn", "Sinnoh", "Unova", "Kalos")
STORY_REGIONS = ("Kanto", "Johto", "Hoenn")
STORY_MODES = ("Classic", "Nuzlocke")
RUN_TARGET_OPTIONS = (
    RUN_TARGET_CHALLENGE,
    RUN_TARGET_WEEKLY,
    RUN_TARGET_DAILY,
    *[f"Battle Tower - {region}" for region in TOWER_REGIONS],
    *[f"Story {mode} - {region}" for mode in STORY_MODES for region in STORY_REGIONS],
)
SCHEDULE_COMPLETION_ATTEMPTS = "Attempts"
SCHEDULE_COMPLETION_WINS = "Completed runs"
SCHEDULE_COMPLETION_CHALLENGE = "Challenge complete"
SCHEDULE_COMPLETION_POKEGOLD = "Pokegold"
SCHEDULE_COMPLETION_SHOP_BUDGET = "Until shop funds low"
SCHEDULE_COMPLETION_FOREVER = "Forever"
SCHEDULE_COMPLETION_OPTIONS = (
    SCHEDULE_COMPLETION_ATTEMPTS,
    SCHEDULE_COMPLETION_WINS,
    SCHEDULE_COMPLETION_CHALLENGE,
    SCHEDULE_COMPLETION_POKEGOLD,
    SCHEDULE_COMPLETION_SHOP_BUDGET,
    SCHEDULE_COMPLETION_FOREVER,
)
DEFAULT_TASK_SCHEDULE = (
    {"name": "Daily", "target": RUN_TARGET_DAILY, "goal": SCHEDULE_COMPLETION_CHALLENGE, "count": 1},
    {"name": "Weekly", "target": RUN_TARGET_WEEKLY, "goal": SCHEDULE_COMPLETION_CHALLENGE, "count": 1},
    {"name": "Kanto story", "target": "Story Classic - Kanto", "goal": SCHEDULE_COMPLETION_ATTEMPTS, "count": 100},
)
SETTINGS_PATH = os.path.join(DATA_DIR, "pokelike_settings.json")
UNKNOWN_STARTING_ITEMS_PATH = os.path.join(
    DATA_DIR,
    "unknown_starting_items.json",
)
UNKNOWN_REGULAR_ITEMS_PATH = os.path.join(
    DATA_DIR,
    "unknown_regular_items.json",
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
        self.geometry("900x890")
        self.minsize(820, 850)
        self.banner_image = None
        self.window_icon = None
        self.discord_icon = None
        self.website_icon = None
        self.github_icon = None
        os.makedirs(DATA_DIR, exist_ok=True)
        self.load_brand_assets()

        self.thread_local = threading.local()
        self._driver = None
        self._wait = None
        self.bot_thread = None
        self.stop_event = threading.Event()
        self.active_bot_run_token = 0
        self.start_time = None
        self.stats_lock = threading.Lock()
        self.drivers_lock = threading.Lock()
        self.bot_run_token_lock = threading.Lock()
        self.chromedriver_lock = threading.Lock()
        self.unknown_starting_items_lock = threading.Lock()
        self.unknown_regular_items_lock = threading.Lock()
        self.passive_item_details_lock = threading.Lock()
        self.run_history_lock = threading.Lock()
        self.unknown_starting_items = self.load_unknown_starting_items()
        self.unknown_regular_items = self.load_unknown_regular_items()
        self.passive_item_details = self.load_passive_item_details()
        self.run_history = self.load_run_history()
        self.last_wallet_pokegold_total = None
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
        self.last_shiny_pokemon_name = ""
        self.shop_targets_obtained = 0
        self.total_legendaries_seen = 0
        self.total_money_earned = 0
        self.last_wallet_pokegold_total = None
        self.main_move_upgrades_used = 0
        self.run_encounters_checked = 0
        self.run_target_encounters = 0
        self.run_legendaries_seen = 0
        self.run_leaders_defeated = 0
        self.encounter_history = []
        self.gui_log_lines = []
        self.shop_roll_log_lines = []
        self.last_team_snapshot = []
        self.last_passive_items_snapshot = []
        self.last_legendary_signature = None
        self.last_leader_signature = None
        self.awaiting_leader_item_roll = False
        self.boss_combat_item_equipped = False
        self.resumed_existing_challenge_run = False
        self.restart_attempt = False
        self.last_item_signature = None
        self.last_money_signature = None
        self.pending_team_replace = False
        self.pending_replace_allow_any = False
        self.pending_replace_policy = "default"
        self.pending_replace_add_clicked = False
        self.pending_passive_item_name = ""
        self.pending_passive_item_priority = None
        self.catch_reroll_used = False
        self.last_catch_scan_signature = None
        self.settings = self.load_settings()
        self.status_var = ctk.StringVar(value="Idle")
        self.shop_shiny_rate_var = ctk.StringVar(value="Log")
        self.mode_var = ctk.StringVar(value=self.settings.get("mode", MODE_FULL_RUN))
        self.manual_start_var = ctk.BooleanVar(value=bool(self.settings.get("manual_start", False)))
        self.headless_var = ctk.BooleanVar(value=bool(self.settings.get("headless", False)))
        self.current_mode = MODE_FULL_RUN
        self.manual_first_attempt = False
        self.run_target_var = ctk.StringVar(value=self.settings.get("run_target", RUN_TARGET_OPTIONS[0]))
        self.starter_var = ctk.StringVar(value=self.settings.get("starter", STARTER_NAME.title()))
        self.target_pokemon_var = ctk.StringVar(value=self.settings.get("shiny_whitelist", ""))
        self.shop_ignore_pokemon_var = ctk.StringVar(value=self.settings.get("shop_ignore_pokemon", ""))
        self.evolution_preference_var = ctk.StringVar(value=self.settings.get("evolution_preference", ""))
        self.dex_target_var = ctk.StringVar(value=self.settings.get("dex_target_mode", DEX_TARGET_OFF))
        self.full_run_dex_priority_var = ctk.StringVar(
            value=self.settings.get("full_run_dex_priority_mode", DEX_TARGET_OFF)
        )
        self.ignore_pokemon_var = ctk.BooleanVar(value=bool(self.settings.get("ignore_pokemon", False)))
        self.ignore_pokecenter_var = ctk.BooleanVar(value=bool(self.settings.get("ignore_pokecenter", False)))
        self.shiny_only_pokemon_var = ctk.BooleanVar(value=bool(self.settings.get("shiny_only_pokemon", False)))
        self.start_shiny_filter_reroll_var = ctk.BooleanVar(
            value=bool(self.settings.get("start_shiny_filter_reroll", False))
        )
        self.no_tm_move_tutor_var = ctk.BooleanVar(value=bool(self.settings.get("no_tm_move_tutor", False)))
        self.boss_combat_item_swap_var = ctk.BooleanVar(value=bool(self.settings.get("boss_combat_item_swap", False)))
        self.combat_held_item_var = ctk.StringVar(value=self.settings.get("combat_held_item", ""))
        self.prioritize_party_fill_var = ctk.BooleanVar(
            value=bool(self.settings.get("prioritize_party_fill", True))
        )
        self.delay_party_fill_var = ctk.BooleanVar(value=bool(self.settings.get("delay_party_fill_until_map3", False)))
        self.smart_trait_choice_var = ctk.BooleanVar(value=bool(self.settings.get("smart_trait_choice", True)))
        self.type_whitelist_var = ctk.StringVar(value=self.settings.get("pokemon_type_whitelist", ""))
        self.type_filter_mode_var = ctk.StringVar(
            value=self.settings.get("pokemon_type_filter_mode", POKEMON_FILTER_PRIORITIZE)
        )
        self.whitelist_filter_mode_var = ctk.StringVar(
            value=self.settings.get("pokemon_whitelist_mode", POKEMON_WHITELIST_ONLY)
        )
        self.generation_whitelist_var = ctk.StringVar(value=self.settings.get("pokemon_generation_whitelist", ""))
        self.dex_missing_summary_var = ctk.StringVar(value="Dex missing: not refreshed")
        self.reroll_completion_var = ctk.StringVar(
            value=self.settings.get("reroll_completion_mode", REROLL_COMPLETE_STOP_NOW)
        )
        self.shop_reroll_after_hit_var = ctk.StringVar(
            value=self.settings.get("shop_reroll_after_hit", SHOP_REROLL_AFTER_HIT_STOP)
        )
        self.item_reroll_target_var = ctk.StringVar(
            value=self.settings.get("item_reroll_target", DEFAULT_ITEM_REROLL_TARGET.title())
        )
        self.pokegold_farm_target_var = ctk.StringVar(value=self.settings.get("pokegold_farm_target", "100000"))
        self.browser_count_var = ctk.StringVar(value=str(self.settings.get("browser_count", 1)))
        self.chrome_restart_minutes_var = ctk.StringVar(value=str(self.settings.get("chrome_restart_minutes", 0)))
        self.schedule_enabled_var = ctk.BooleanVar(value=bool(self.settings.get("schedule_enabled", False)))
        self.browser_count = 1
        self.chrome_restart_minutes = 0.0
        self.current_run_target = RUN_TARGET_OPTIONS[0]
        self.current_run_target_info = self.parse_run_target(RUN_TARGET_OPTIONS[0])
        self.current_tower = "Challenge Mode"
        self.current_starter_name = STARTER_NAME
        self.current_target_pokemon = ""
        self.current_target_pokemon_list = []
        self.current_shop_ignore_pokemon_list = []
        self.current_manual_target_pokemon_list = []
        self.current_evolution_preference_list = []
        self.current_dex_target_mode = DEX_TARGET_OFF
        self.current_dex_targets = []
        self.current_dex_target_names = set()
        self.current_dex_target_by_name = {}
        self.current_dex_missing_counts = {}
        self.current_ignore_pokemon = False
        self.current_ignore_pokecenter = False
        self.current_shiny_only_pokemon = False
        self.current_start_shiny_filter_reroll = False
        self.start_shiny_filter_acquired = False
        self.current_no_tm_move_tutor = False
        self.current_boss_combat_item_swap = False
        self.current_combat_held_item = ""
        self.current_combat_held_items = []
        self.boss_combat_item_equipped = False
        self.current_prioritize_party_fill = True
        self.current_delay_party_fill = False
        self.current_smart_trait_choice = True
        self.current_type_whitelist = set()
        self.current_type_filter_mode = POKEMON_FILTER_PRIORITIZE
        self.current_whitelist_filter_mode = POKEMON_WHITELIST_ONLY
        self.current_generation_whitelist = set()
        self.current_type_filter_names = set()
        self.current_generation_filter_names = set()
        self.cached_dex_targets = {}
        self.cached_dex_target_mode = None
        self.current_primary_target_names = set()
        self.complete_pokedex_phase = ""
        self.complete_pokedex_phase_label = ""
        self.current_reroll_completion_mode = REROLL_COMPLETE_STOP_NOW
        self.current_shop_reroll_after_hit = SHOP_REROLL_AFTER_HIT_STOP
        self.shop_post_hit_safety_run_active = False
        self.reroll_target_acquired = False
        self.reroll_acquired_target_name = ""
        self.reroll_chain_completed_targets = set()
        self.current_item_reroll_target = DEFAULT_ITEM_REROLL_TARGET
        self.current_item_reroll_targets = [DEFAULT_ITEM_REROLL_TARGET]
        self.current_pokegold_farm_target = 100000
        self.starting_item_priority = self.parse_priority_text(
            self.settings.get("starting_item_priority", ""),
            STARTING_ITEM_PRIORITY,
        )
        self.regular_item_priority = self.parse_priority_text(
            self.settings.get("regular_item_priority", ""),
            REGULAR_ITEM_PRIORITY,
        )
        self.regular_item_priority_by_starter = self.parse_starter_item_priority_map(
            self.settings.get("regular_item_priority_by_starter", {})
        )
        self.combat_held_item_priority = self.parse_priority_text(
            self.settings.get("combat_held_item_priority", ""),
            COMBAT_HELD_ITEM_PRIORITY,
        )
        self.starting_item_ignore = self.parse_priority_text(
            self.settings.get("starting_item_ignore", ""),
            STARTING_ITEM_IGNORE,
        )
        self.regular_item_ignore = self.parse_priority_text(
            self.settings.get("regular_item_ignore", ""),
            REGULAR_ITEM_IGNORE,
        )
        # Fold every already-discovered unknown item into the never-pick list so it
        # is both applied (never picked) AND visible/editable in Item Priorities.
        self.merge_unknowns_into_ignore()
        self.merge_unknowns_into_regular_ignore()
        self.priority_window = None
        self.settings_window = None
        self.settings_controls = []
        self.dex_preload_thread = None
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
        self.schedule_default_starter_name = STARTER_NAME

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

        try:
            github = Image.open(GITHUB_ICON_PATH)
            self.github_icon = ctk.CTkImage(
                light_image=github,
                dark_image=github,
                size=(40, 40),
            )
        except Exception:
            self.github_icon = None

    def open_brand_link(self, _event=None):
        webbrowser.open_new_tab(BRAND_URL)

    def open_discord_link(self):
        webbrowser.open_new_tab(DISCORD_URL)

    def open_github_link(self):
        webbrowser.open_new_tab(GITHUB_URL)

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
    def pending_replace_add_clicked(self):
        return self.get_context_attr("pending_replace_add_clicked", False)

    @pending_replace_add_clicked.setter
    def pending_replace_add_clicked(self, value):
        self.set_context_attr("pending_replace_add_clicked", value)

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
        return self.sanitize_settings_data(data)

    def sanitize_settings_data(self, data):
        if not isinstance(data, dict):
            return {}
        if isinstance(data.get("settings"), dict):
            data = data["settings"]
        valid_modes = {
            MODE_FULL_RUN,
            MODE_SHINY_CHARM_REROLL,
            MODE_SHINY_POKEMON_REROLL,
            MODE_NORMAL_POKEMON_REROLL,
            MODE_COMPLETE_POKEDEX,
            MODE_POKEGOLD_FARM,
            MODE_SHINY_SHOP_REROLL,
            MODE_LEGENDARY_SHOP_REROLL,
        }
        settings = {}
        mode = data.get("mode")
        if mode == LEGACY_MODE_SHINY_CHARM_REROLL:
            mode = MODE_ITEM_REROLL
        if mode in valid_modes:
            settings["mode"] = mode
        run_target = data.get("run_target")
        if run_target in RUN_TARGET_OPTIONS:
            settings["run_target"] = run_target
        else:
            legacy_tower = data.get("tower")
            if isinstance(legacy_tower, str) and legacy_tower.strip():
                settings["run_target"] = self.legacy_tower_to_run_target(legacy_tower)
        for key in [
            "starter",
            "shiny_whitelist",
            "shop_ignore_pokemon",
            "evolution_preference",
            "item_reroll_target",
            "pokegold_farm_target",
            "combat_held_item",
            "pokemon_type_whitelist",
            "pokemon_type_filter_mode",
            "pokemon_whitelist_mode",
            "pokemon_generation_whitelist",
        ]:
            value = data.get(key)
            if isinstance(value, str):
                settings[key] = value
        if settings.get("pokemon_type_filter_mode") not in POKEMON_FILTER_OPTIONS:
            settings.pop("pokemon_type_filter_mode", None)
        if settings.get("pokemon_whitelist_mode") not in POKEMON_WHITELIST_OPTIONS:
            settings.pop("pokemon_whitelist_mode", None)
        dex_target_mode = data.get("dex_target_mode")
        if dex_target_mode in DEX_TARGET_OPTIONS:
            settings["dex_target_mode"] = dex_target_mode
        full_run_dex_priority_mode = data.get("full_run_dex_priority_mode")
        if full_run_dex_priority_mode in FULL_RUN_DEX_PRIORITY_OPTIONS:
            settings["full_run_dex_priority_mode"] = full_run_dex_priority_mode
        reroll_completion_mode = data.get("reroll_completion_mode")
        if reroll_completion_mode in REROLL_COMPLETION_OPTIONS:
            settings["reroll_completion_mode"] = reroll_completion_mode
        shop_reroll_after_hit = data.get("shop_reroll_after_hit")
        if shop_reroll_after_hit in SHOP_REROLL_AFTER_HIT_OPTIONS:
            settings["shop_reroll_after_hit"] = shop_reroll_after_hit
        for key in ["starting_item_priority", "regular_item_priority", "combat_held_item_priority", "starting_item_ignore", "regular_item_ignore"]:
            value = data.get(key)
            if isinstance(value, (str, list, tuple)):
                settings[key] = value
        starter_priorities = data.get("regular_item_priority_by_starter")
        if isinstance(starter_priorities, dict):
            settings["regular_item_priority_by_starter"] = starter_priorities
        browser_count = data.get("browser_count")
        if isinstance(browser_count, int) and browser_count > 0:
            settings["browser_count"] = min(browser_count, MAX_BROWSER_COUNT)
        chrome_restart_minutes = data.get("chrome_restart_minutes")
        if isinstance(chrome_restart_minutes, (int, float)) and chrome_restart_minutes >= 0:
            settings["chrome_restart_minutes"] = min(float(chrome_restart_minutes), 1440.0)
        for key in [
            "manual_start",
            "headless",
            "schedule_enabled",
            "ignore_pokemon",
            "ignore_pokecenter",
            "shiny_only_pokemon",
            "start_shiny_filter_reroll",
            "no_tm_move_tutor",
            "boss_combat_item_swap",
            "prioritize_party_fill",
            "delay_party_fill_until_map3",
            "smart_trait_choice",
        ]:
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

    def normalize_schedule_goal(self, value):
        raw = " ".join(str(value or "").strip().split()).lower()
        aliases = {
            "run": SCHEDULE_COMPLETION_ATTEMPTS,
            "runs": SCHEDULE_COMPLETION_ATTEMPTS,
            "attempt": SCHEDULE_COMPLETION_ATTEMPTS,
            "attempts": SCHEDULE_COMPLETION_ATTEMPTS,
            "win": SCHEDULE_COMPLETION_WINS,
            "wins": SCHEDULE_COMPLETION_WINS,
            "completed run": SCHEDULE_COMPLETION_WINS,
            "completed runs": SCHEDULE_COMPLETION_WINS,
            "complete run": SCHEDULE_COMPLETION_WINS,
            "complete runs": SCHEDULE_COMPLETION_WINS,
            "challenge": SCHEDULE_COMPLETION_CHALLENGE,
            "challenge complete": SCHEDULE_COMPLETION_CHALLENGE,
            "complete challenge": SCHEDULE_COMPLETION_CHALLENGE,
            "pokegold": SCHEDULE_COMPLETION_POKEGOLD,
            "gold": SCHEDULE_COMPLETION_POKEGOLD,
            "shop": SCHEDULE_COMPLETION_SHOP_BUDGET,
            "shop budget": SCHEDULE_COMPLETION_SHOP_BUDGET,
            "shop funds": SCHEDULE_COMPLETION_SHOP_BUDGET,
            "until shop funds low": SCHEDULE_COMPLETION_SHOP_BUDGET,
            "until no money": SCHEDULE_COMPLETION_SHOP_BUDGET,
            "forever": SCHEDULE_COMPLETION_FOREVER,
            "infinite": SCHEDULE_COMPLETION_FOREVER,
            "infinitely": SCHEDULE_COMPLETION_FOREVER,
        }
        return aliases.get(raw, value if value in SCHEDULE_COMPLETION_OPTIONS else SCHEDULE_COMPLETION_WINS)

    def parse_task_schedule(self, value, default_values=()):
        raw_steps = value if isinstance(value, list) and value else list(default_values)
        steps = []
        for item in raw_steps:
            if not isinstance(item, dict):
                continue
            settings = item.get("settings")
            if not isinstance(settings, dict):
                settings = {}
            target = item.get("target")
            if target not in RUN_TARGET_OPTIONS:
                target = settings.get("run_target")
            if target not in RUN_TARGET_OPTIONS:
                continue
            goal = self.normalize_schedule_goal(item.get("goal", SCHEDULE_COMPLETION_WINS))
            try:
                count = int(item.get("count", 1))
            except Exception:
                count = 1
            starter = " ".join(str(item.get("starter") or "").strip().split())
            max_count = 999999999 if goal in {SCHEDULE_COMPLETION_POKEGOLD, SCHEDULE_COMPLETION_FOREVER} else 9999
            name = " ".join(str(item.get("name") or "").strip().split())
            parsed_settings = self.parse_task_settings_snapshot(settings)
            steps.append({
                "name": name,
                "target": target,
                "starter": starter,
                "goal": goal,
                "count": max(1, min(count, max_count)),
                "settings": parsed_settings,
            })
        return steps or [dict(step) for step in DEFAULT_TASK_SCHEDULE]

    def parse_task_settings_snapshot(self, value):
        if not isinstance(value, dict):
            return {}
        result = {}
        string_keys = {
            "mode",
            "run_target",
            "starter",
            "shiny_whitelist",
            "shop_ignore_pokemon",
            "evolution_preference",
            "dex_target_mode",
            "full_run_dex_priority_mode",
            "reroll_completion_mode",
            "shop_reroll_after_hit",
            "item_reroll_target",
            "pokegold_farm_target",
            "combat_held_item",
            "pokemon_type_whitelist",
            "pokemon_type_filter_mode",
            "pokemon_whitelist_mode",
            "pokemon_generation_whitelist",
        }
        bool_keys = {
            "manual_start",
            "headless",
            "ignore_pokemon",
            "ignore_pokecenter",
            "shiny_only_pokemon",
            "start_shiny_filter_reroll",
            "no_tm_move_tutor",
            "boss_combat_item_swap",
            "prioritize_party_fill",
            "delay_party_fill_until_map3",
            "smart_trait_choice",
        }
        for key in string_keys:
            raw = value.get(key)
            if isinstance(raw, str):
                result[key] = raw.strip()
        if result.get("mode") not in {
            MODE_FULL_RUN,
            MODE_ITEM_REROLL,
            MODE_SHINY_POKEMON_REROLL,
            MODE_NORMAL_POKEMON_REROLL,
            MODE_COMPLETE_POKEDEX,
            MODE_POKEGOLD_FARM,
            MODE_SHINY_SHOP_REROLL,
            MODE_LEGENDARY_SHOP_REROLL,
        }:
            result.pop("mode", None)
        if result.get("run_target") not in RUN_TARGET_OPTIONS:
            result.pop("run_target", None)
        if result.get("dex_target_mode") not in DEX_TARGET_OPTIONS:
            result.pop("dex_target_mode", None)
        if result.get("full_run_dex_priority_mode") not in FULL_RUN_DEX_PRIORITY_OPTIONS:
            result.pop("full_run_dex_priority_mode", None)
        if result.get("reroll_completion_mode") not in REROLL_COMPLETION_OPTIONS:
            result.pop("reroll_completion_mode", None)
        if result.get("shop_reroll_after_hit") not in SHOP_REROLL_AFTER_HIT_OPTIONS:
            result.pop("shop_reroll_after_hit", None)
        if result.get("pokemon_type_filter_mode") not in POKEMON_FILTER_OPTIONS:
            result.pop("pokemon_type_filter_mode", None)
        if result.get("pokemon_whitelist_mode") not in POKEMON_WHITELIST_OPTIONS:
            result.pop("pokemon_whitelist_mode", None)
        for key in bool_keys:
            if isinstance(value.get(key), bool):
                result[key] = bool(value.get(key))
        for key in ["starting_item_priority", "regular_item_priority", "combat_held_item_priority", "starting_item_ignore", "regular_item_ignore"]:
            raw = value.get(key)
            if isinstance(raw, (list, tuple, str)):
                result[key] = self.parse_priority_text(raw, ())
        starter_priorities = value.get("regular_item_priority_by_starter")
        if isinstance(starter_priorities, dict):
            result["regular_item_priority_by_starter"] = self.parse_starter_item_priority_map(starter_priorities)
        return result

    def current_task_settings_snapshot(self):
        return {
            "mode": self.mode_var.get(),
            "manual_start": bool(self.manual_start_var.get()),
            "headless": bool(self.headless_var.get()),
            "run_target": self.run_target_var.get(),
            "starter": self.starter_var.get().strip(),
            "shiny_whitelist": self.target_pokemon_var.get().strip(),
            "shop_ignore_pokemon": self.shop_ignore_pokemon_var.get().strip(),
            "evolution_preference": self.evolution_preference_var.get().strip(),
            "dex_target_mode": self.dex_target_var.get(),
            "full_run_dex_priority_mode": self.full_run_dex_priority_var.get(),
            "reroll_completion_mode": self.reroll_completion_var.get(),
            "shop_reroll_after_hit": self.shop_reroll_after_hit_var.get(),
            "item_reroll_target": self.item_reroll_target_var.get().strip(),
            "pokegold_farm_target": str(self.parse_pokegold_farm_target()),
            "ignore_pokemon": bool(self.ignore_pokemon_var.get()),
            "ignore_pokecenter": bool(self.ignore_pokecenter_var.get()),
            "shiny_only_pokemon": bool(self.shiny_only_pokemon_var.get()),
            "start_shiny_filter_reroll": bool(self.start_shiny_filter_reroll_var.get()),
            "no_tm_move_tutor": bool(self.no_tm_move_tutor_var.get()),
            "boss_combat_item_swap": bool(self.boss_combat_item_swap_var.get()),
            "combat_held_item": self.combat_held_item_var.get().strip(),
            "prioritize_party_fill": bool(self.prioritize_party_fill_var.get()),
            "delay_party_fill_until_map3": bool(self.delay_party_fill_var.get()),
            "smart_trait_choice": bool(self.smart_trait_choice_var.get()),
            "pokemon_type_whitelist": self.type_whitelist_var.get().strip(),
            "pokemon_type_filter_mode": self.type_filter_mode_var.get(),
            "pokemon_whitelist_mode": self.whitelist_filter_mode_var.get(),
            "pokemon_generation_whitelist": self.generation_whitelist_var.get().strip(),
            "starting_item_priority": list(self.starting_item_priority),
            "regular_item_priority": list(self.regular_item_priority),
            "regular_item_priority_by_starter": dict(self.regular_item_priority_by_starter),
            "combat_held_item_priority": list(self.combat_held_item_priority),
            "starting_item_ignore": list(self.starting_item_ignore),
            "regular_item_ignore": list(self.regular_item_ignore),
        }

    def build_settings_payload(self):
        return {
            "mode": self.mode_var.get(),
            "manual_start": bool(self.manual_start_var.get()),
            "headless": bool(self.headless_var.get()),
            "run_target": self.run_target_var.get(),
            "starter": self.starter_var.get().strip(),
            "shiny_whitelist": self.target_pokemon_var.get().strip(),
            "shop_ignore_pokemon": self.shop_ignore_pokemon_var.get().strip(),
            "evolution_preference": self.evolution_preference_var.get().strip(),
            "dex_target_mode": self.dex_target_var.get(),
            "full_run_dex_priority_mode": self.full_run_dex_priority_var.get(),
            "ignore_pokemon": bool(self.ignore_pokemon_var.get()),
            "ignore_pokecenter": bool(self.ignore_pokecenter_var.get()),
            "shiny_only_pokemon": bool(self.shiny_only_pokemon_var.get()),
            "start_shiny_filter_reroll": bool(self.start_shiny_filter_reroll_var.get()),
            "no_tm_move_tutor": bool(self.no_tm_move_tutor_var.get()),
            "boss_combat_item_swap": bool(self.boss_combat_item_swap_var.get()),
            "combat_held_item": self.combat_held_item_var.get().strip(),
            "prioritize_party_fill": bool(self.prioritize_party_fill_var.get()),
            "delay_party_fill_until_map3": bool(self.delay_party_fill_var.get()),
            "smart_trait_choice": bool(self.smart_trait_choice_var.get()),
            "pokemon_type_whitelist": self.type_whitelist_var.get().strip(),
            "pokemon_type_filter_mode": self.type_filter_mode_var.get(),
            "pokemon_whitelist_mode": self.whitelist_filter_mode_var.get(),
            "pokemon_generation_whitelist": self.generation_whitelist_var.get().strip(),
            "reroll_completion_mode": self.reroll_completion_var.get(),
            "shop_reroll_after_hit": self.shop_reroll_after_hit_var.get(),
            "item_reroll_target": self.item_reroll_target_var.get().strip(),
            "pokegold_farm_target": str(self.parse_pokegold_farm_target()),
            "browser_count": self.parse_browser_count(),
            "chrome_restart_minutes": self.parse_chrome_restart_minutes(),
            "schedule_enabled": bool(self.schedule_enabled_var.get()),
            "task_schedule": self.task_schedule,
            "starting_item_priority": list(self.starting_item_priority),
            "regular_item_priority": list(self.regular_item_priority),
            "regular_item_priority_by_starter": dict(self.regular_item_priority_by_starter),
            "combat_held_item_priority": list(self.combat_held_item_priority),
            "starting_item_ignore": list(self.starting_item_ignore),
            "regular_item_ignore": list(self.regular_item_ignore),
        }

    def apply_settings_payload_to_ui(self, settings):
        settings = self.sanitize_settings_data(settings)
        if not settings:
            return False

        def set_var(var, key):
            if key in settings:
                var.set(str(settings.get(key) or ""))

        def set_bool(var, key):
            if key in settings:
                var.set(bool(settings.get(key)))

        set_var(self.mode_var, "mode")
        set_bool(self.manual_start_var, "manual_start")
        set_bool(self.headless_var, "headless")
        set_var(self.run_target_var, "run_target")
        set_var(self.starter_var, "starter")
        set_var(self.target_pokemon_var, "shiny_whitelist")
        set_var(self.shop_ignore_pokemon_var, "shop_ignore_pokemon")
        set_var(self.evolution_preference_var, "evolution_preference")
        set_var(self.dex_target_var, "dex_target_mode")
        set_var(self.full_run_dex_priority_var, "full_run_dex_priority_mode")
        set_var(self.reroll_completion_var, "reroll_completion_mode")
        set_var(self.shop_reroll_after_hit_var, "shop_reroll_after_hit")
        set_var(self.item_reroll_target_var, "item_reroll_target")
        set_var(self.pokegold_farm_target_var, "pokegold_farm_target")
        set_bool(self.ignore_pokemon_var, "ignore_pokemon")
        set_bool(self.ignore_pokecenter_var, "ignore_pokecenter")
        set_bool(self.shiny_only_pokemon_var, "shiny_only_pokemon")
        set_bool(self.start_shiny_filter_reroll_var, "start_shiny_filter_reroll")
        set_bool(self.no_tm_move_tutor_var, "no_tm_move_tutor")
        set_bool(self.boss_combat_item_swap_var, "boss_combat_item_swap")
        set_var(self.combat_held_item_var, "combat_held_item")
        set_bool(self.prioritize_party_fill_var, "prioritize_party_fill")
        set_bool(self.delay_party_fill_var, "delay_party_fill_until_map3")
        set_bool(self.smart_trait_choice_var, "smart_trait_choice")
        set_var(self.type_whitelist_var, "pokemon_type_whitelist")
        set_var(self.type_filter_mode_var, "pokemon_type_filter_mode")
        set_var(self.whitelist_filter_mode_var, "pokemon_whitelist_mode")
        set_var(self.generation_whitelist_var, "pokemon_generation_whitelist")
        if "browser_count" in settings:
            self.browser_count_var.set(str(settings.get("browser_count") or 1))
        if "chrome_restart_minutes" in settings:
            self.chrome_restart_minutes_var.set(str(settings.get("chrome_restart_minutes") or 0))
        set_bool(self.schedule_enabled_var, "schedule_enabled")
        if "task_schedule" in settings:
            self.task_schedule = self.parse_task_schedule(settings.get("task_schedule"), DEFAULT_TASK_SCHEDULE)
        if "starting_item_priority" in settings:
            self.starting_item_priority = self.parse_priority_text(settings.get("starting_item_priority"), STARTING_ITEM_PRIORITY)
        if "regular_item_priority" in settings:
            self.regular_item_priority = self.parse_priority_text(settings.get("regular_item_priority"), REGULAR_ITEM_PRIORITY)
        if "starting_item_ignore" in settings:
            self.starting_item_ignore = self.parse_priority_text(settings.get("starting_item_ignore"), STARTING_ITEM_IGNORE)
        if "regular_item_ignore" in settings:
            self.regular_item_ignore = self.parse_priority_text(settings.get("regular_item_ignore"), REGULAR_ITEM_IGNORE)
        if "regular_item_priority_by_starter" in settings:
            self.regular_item_priority_by_starter = self.parse_starter_item_priority_map(
                settings.get("regular_item_priority_by_starter", {})
            )
        if "combat_held_item_priority" in settings:
            self.combat_held_item_priority = self.parse_priority_text(settings.get("combat_held_item_priority"), COMBAT_HELD_ITEM_PRIORITY)
        self.merge_unknowns_into_ignore()
        self.merge_unknowns_into_regular_ignore()
        self.update_schedule_summary()
        self.update_stats_labels()
        return True

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

    def parse_starter_item_priority_map(self, value):
        if not isinstance(value, dict):
            return {}
        result = {}
        for starter, items in value.items():
            starter_key = self.normalize_pokemon_name(starter)
            if not starter_key:
                continue
            priorities = self.parse_priority_text(items, ())
            if priorities:
                result[starter_key] = priorities
        return result

    def priority_text(self, values):
        return "\n".join(self.item_label_with_detail(value) for value in values)

    def is_pokemon_reroll_mode(self):
        return self.current_mode in [MODE_SHINY_POKEMON_REROLL, MODE_NORMAL_POKEMON_REROLL] or (
            self.current_mode == MODE_COMPLETE_POKEDEX
            and self.complete_pokedex_phase in {"normal_regular", "shiny_regular"}
        )

    def begin_bot_run_token(self):
        with self.bot_run_token_lock:
            self.active_bot_run_token += 1
            return self.active_bot_run_token

    def invalidate_bot_run_token(self):
        with self.bot_run_token_lock:
            self.active_bot_run_token += 1
            return self.active_bot_run_token

    def is_active_bot_run_token(self, run_token):
        with self.bot_run_token_lock:
            return run_token is not None and run_token == self.active_bot_run_token

    def is_complete_pokedex_mode(self):
        return self.current_mode == MODE_COMPLETE_POKEDEX

    def is_legendary_shop_reroll_mode(self):
        return self.current_mode == MODE_LEGENDARY_SHOP_REROLL

    def is_shop_reroll_mode(self):
        return self.current_mode in {MODE_SHINY_SHOP_REROLL, MODE_LEGENDARY_SHOP_REROLL}

    def current_shop_egg_config(self):
        if self.current_mode == MODE_LEGENDARY_SHOP_REROLL:
            return {
                "egg_type": "legendary",
                "expected_price": 10000,
                "label": "legendary egg",
                "mode_label": "Legendary shop reroll",
            }
        return {
            "egg_type": "shiny",
            "expected_price": 2000,
            "label": "shiny Pokemon egg",
            "mode_label": "Shiny Pokemon shop reroll",
        }

    def complete_pokedex_phase_is_legendary(self):
        return self.is_complete_pokedex_mode() and self.complete_pokedex_phase in {
            "normal_legendary",
            "shiny_legendary",
        }

    def is_target_item_reroll_mode(self):
        return self.current_mode == MODE_ITEM_REROLL or (
            self.complete_pokedex_phase_is_legendary()
            and not bool(getattr(self, "reroll_target_acquired", False))
        )

    def should_complete_current_reroll_run(self):
        return (
            (self.is_pokemon_reroll_mode() or self.complete_pokedex_phase_is_legendary())
            and bool(getattr(self, "reroll_target_acquired", False))
            and (
                self.is_complete_pokedex_mode()
                or self.current_reroll_completion_mode in {
                    REROLL_COMPLETE_ONE_FULL_RUN,
                    REROLL_COMPLETE_CHAIN_FULL_RUNS,
                }
            )
        )

    def should_use_full_run_logic(self):
        return self.current_mode in {MODE_FULL_RUN, MODE_POKEGOLD_FARM} or self.should_complete_current_reroll_run()

    def should_continue_shop_reroll_after_hit(self):
        return (
            self.is_shop_reroll_mode()
            and self.current_shop_reroll_after_hit == SHOP_REROLL_AFTER_HIT_CONTINUE
        )

    def should_allow_automated_shop_upload(self):
        return self.is_shop_reroll_mode() or bool(getattr(self, "shop_post_hit_safety_run_active", False))

    def should_count_run_shiny_stats(self):
        return not bool(getattr(self, "shop_post_hit_safety_run_active", False))

    def parse_pokemon_target_list(self, text):
        result = []
        seen = set()
        for raw in str(text or "").replace(";", ",").split(","):
            name = self.normalize_pokemon_name(raw)
            if not name or name in seen:
                continue
            seen.add(name)
            result.append(name)
        return result

    def dex_target_wants_normal(self):
        return self.current_dex_target_mode in {DEX_TARGET_NORMAL, DEX_TARGET_BOTH}

    def dex_target_wants_shiny(self):
        return self.current_dex_target_mode in {DEX_TARGET_SHINY, DEX_TARGET_BOTH}

    def desired_reroll_shiny_state(self):
        if self.current_mode == MODE_COMPLETE_POKEDEX:
            return self.complete_pokedex_phase == "shiny_regular"
        if self.current_mode == MODE_SHINY_POKEMON_REROLL:
            return True
        if self.current_mode == MODE_NORMAL_POKEMON_REROLL:
            return False
        if self.current_dex_target_mode == DEX_TARGET_SHINY:
            return True
        return False

    def normalize_item_name(self, name):
        name = self.strip_item_detail(name)
        normalized = self.raw_normalize_item_name(name)
        return self.canonical_item_name(normalized)

    def raw_normalize_item_name(self, name):
        return " ".join(
            "".join(ch.lower() if ch.isalnum() else " " for ch in str(name or "")).split()
        )

    def canonical_item_name(self, normalized):
        normalized = str(normalized or "").strip()
        if not normalized:
            return ""
        known_items = sorted(
            {self.raw_normalize_item_name(item) for item in KNOWN_PASSIVE_ITEMS},
            key=len,
            reverse=True,
        )
        for item in known_items:
            if normalized == item or normalized.startswith(f"{item} "):
                return item

        details = getattr(self, "passive_item_details", None)
        if not details:
            details = {
                self.raw_normalize_item_name(name): self.clean_item_detail(detail, name)
                for name, detail in DEFAULT_PASSIVE_ITEM_DETAILS.items()
            }
        detail_matches = []
        for item, detail in details.items():
            item_name = self.raw_normalize_item_name(item)
            detail_text = self.raw_normalize_item_name(detail)
            if len(normalized) >= 12 and detail_text and normalized in detail_text:
                detail_matches.append(item_name)
        if len(set(detail_matches)) == 1:
            return detail_matches[0]
        return normalized

    def normalize_pokemon_name(self, name):
        return " ".join(
            "".join(ch.lower() if ch.isalnum() else " " for ch in str(name or "")).split()
        )

    def pokemon_group_name_set(self, raw_text):
        normalized = f" {self.normalize_pokemon_name(raw_text)} "
        known_names = set()
        for raw_line in EVOLUTION_CHAIN_TEXT.splitlines():
            for part in raw_line.split(">"):
                name = self.normalize_pokemon_name(part)
                if name:
                    known_names.add(name)
        known_names.update(self.normalize_pokemon_name(name) for name in LEGENDARY_POKEMON_NAMES)
        return {
            name for name in known_names
            if name and f" {name} " in normalized
        }

    def parse_type_whitelist(self, text):
        raw_values = re.split(r"[,;\n]+", str(text or ""))
        selected = set()
        valid = set(POKEMON_TYPE_NAMES)
        for raw_value in raw_values:
            value = self.normalize_pokemon_name(raw_value.replace("type", ""))
            if value in valid:
                selected.add(value)
        return selected

    def parse_generation_whitelist(self, text):
        aliases = {
            "1": "kanto", "gen 1": "kanto", "generation 1": "kanto", "kanto": "kanto",
            "2": "johto", "gen 2": "johto", "generation 2": "johto", "johto": "johto",
            "3": "hoenn", "gen 3": "hoenn", "generation 3": "hoenn", "hoenn": "hoenn",
            "4": "sinnoh", "gen 4": "sinnoh", "generation 4": "sinnoh", "sinnoh": "sinnoh",
            "5": "unova", "gen 5": "unova", "generation 5": "unova", "unova": "unova",
            "6": "kalos", "gen 6": "kalos", "generation 6": "kalos", "kalos": "kalos",
            "7": "alola", "gen 7": "alola", "generation 7": "alola", "alola": "alola",
            "8": "galar", "gen 8": "galar", "generation 8": "galar", "galar": "galar",
            "9": "paldea", "gen 9": "paldea", "generation 9": "paldea", "paldea": "paldea",
        }
        selected = set()
        for raw_value in re.split(r"[,;\n]+", str(text or "")):
            value = self.normalize_pokemon_name(raw_value)
            if value in aliases:
                selected.add(aliases[value])
        return selected

    def names_for_type_filters(self, type_names):
        names = set()
        for type_name in type_names or []:
            names.update(self.pokemon_group_name_set(POKEMON_TYPE_NAME_GROUPS.get(type_name, "")))
        return names

    def names_for_generation_filters(self, generation_names):
        names = set()
        for generation_name in generation_names or []:
            names.update(self.pokemon_group_name_set(POKEMON_GENERATION_NAME_GROUPS.get(generation_name, "")))
        return names

    def pokemon_filters_enabled(self):
        return bool(
            self.current_ignore_pokemon
            or self.current_shiny_only_pokemon
            or self.current_manual_target_pokemon_list
            or self.current_type_whitelist
            or self.current_generation_whitelist
        )

    def pokemon_filter_payload(self):
        party_count = min(int((self.party_summary() or {}).get("count") or 0), 6)
        return {
            "ignorePokemon": bool(getattr(self, "current_ignore_pokemon", False)),
            "shinyOnly": bool(getattr(self, "current_shiny_only_pokemon", False)),
            "manualNames": list(getattr(self, "current_manual_target_pokemon_list", []) or []),
            "typeNames": list(getattr(self, "current_type_filter_names", set()) or []),
            "generationNames": list(getattr(self, "current_generation_filter_names", set()) or []),
            "typeWhitelist": list(getattr(self, "current_type_whitelist", set()) or []),
            "typeMode": getattr(self, "current_type_filter_mode", POKEMON_FILTER_PRIORITIZE),
            "whitelistMode": getattr(self, "current_whitelist_filter_mode", POKEMON_WHITELIST_ONLY),
            "generationWhitelist": list(getattr(self, "current_generation_whitelist", set()) or []),
            "smartTraitChoice": bool(getattr(self, "current_smart_trait_choice", True)),
            "partyCount": party_count,
            "startShinyGate": bool(
                getattr(self, "current_start_shiny_filter_reroll", False)
                and not getattr(self, "start_shiny_filter_acquired", False)
            ),
        }

    def pokemon_name_allowed_by_filters(self, name, shiny=False):
        key = self.normalize_pokemon_name(name)
        if getattr(self, "current_ignore_pokemon", False):
            return False
        if getattr(self, "current_shiny_only_pokemon", False) and not shiny:
            return False
        manual_names = set(getattr(self, "current_manual_target_pokemon_list", []) or [])
        whitelist_mode = getattr(self, "current_whitelist_filter_mode", POKEMON_WHITELIST_ONLY)
        if manual_names and whitelist_mode == POKEMON_WHITELIST_ONLY and key not in manual_names:
            return False
        if manual_names and whitelist_mode == POKEMON_WHITELIST_ONLY_OR_SHINY and key not in manual_names and not shiny:
            return False
        if (
            getattr(self, "current_type_whitelist", set())
            and getattr(self, "current_type_filter_mode", POKEMON_FILTER_PRIORITIZE) == POKEMON_FILTER_ONLY
            and key not in getattr(self, "current_type_filter_names", set())
        ):
            return False
        if getattr(self, "current_generation_whitelist", set()) and key not in getattr(self, "current_generation_filter_names", set()):
            return False
        return True

    def evolution_predecessor_map(self):
        cached = getattr(self, "_evolution_predecessor_map", None)
        if cached is not None:
            return cached
        predecessor_map = {}
        for raw_line in EVOLUTION_CHAIN_TEXT.splitlines():
            chain = [
                self.normalize_pokemon_name(part)
                for part in raw_line.split(">")
                if self.normalize_pokemon_name(part)
            ]
            for index, name in enumerate(chain):
                if index <= 0:
                    predecessor_map.setdefault(name, set())
                    continue
                predecessor_map.setdefault(name, set()).update(chain[:index])
        self._evolution_predecessor_map = predecessor_map
        return predecessor_map

    def evolution_aliases_for_target(self, name, aliases=None):
        result = []
        for alias in list(aliases or []) + [name]:
            key = self.normalize_pokemon_name(alias)
            if key and key not in result:
                result.append(key)
        for prevo in sorted(self.evolution_predecessor_map().get(self.normalize_pokemon_name(name), set())):
            if prevo and prevo not in result:
                result.append(prevo)
        return result

    def current_starter_key(self):
        thread_local = getattr(self, "thread_local", None)
        if thread_local is not None and getattr(thread_local, "use_local", False):
            starter = getattr(self, "current_starter_name", "") or STARTER_NAME
        else:
            starter = self.starter_var.get() or getattr(self, "current_starter_name", "") or STARTER_NAME
        return self.normalize_pokemon_name(starter)

    def current_starter_label(self):
        key = self.current_starter_key()
        return key.title() if key else STARTER_NAME.title()

    def active_regular_item_priority(self):
        key = self.current_starter_key()
        if key and key in self.regular_item_priority_by_starter:
            priority = self.regular_item_priority_by_starter[key]
        else:
            priority = self.regular_item_priority
        if getattr(self, "current_no_tm_move_tutor", False):
            return [
                item for item in priority
                if self.normalize_item_name(item) != "tm"
            ]
        return priority

    def active_regular_item_ignore(self):
        priority_names = {
            self.normalize_item_name(name)
            for name in list(self.active_regular_item_priority()) + list(self.active_combat_held_item_priority())
        }
        return [
            item for item in self.regular_item_ignore
            if self.normalize_item_name(item) not in priority_names
        ]

    def active_combat_held_item_priority(self):
        items = list(getattr(self, "combat_held_item_priority", []) or [])
        legacy_item = self.normalize_item_name(getattr(self, "current_combat_held_item", ""))
        if legacy_item and legacy_item not in {self.normalize_item_name(item) for item in items}:
            items.insert(0, legacy_item)
        return self.parse_priority_text(items, ())

    def active_restore_held_item(self):
        consumables = {self.normalize_item_name(item) for item in CONSUMABLE_ITEM_ALIASES}
        combat_items = {self.normalize_item_name(item) for item in self.active_combat_held_item_priority()}
        for item in self.active_regular_item_priority():
            normalized = self.normalize_item_name(item)
            if normalized and normalized not in consumables and normalized not in combat_items:
                return item
        return ""

    def strip_item_detail(self, text):
        text = str(text or "").strip()
        if text.endswith("]") and "[" in text:
            return text.rsplit("[", 1)[0].strip()
        return text

    def clean_item_detail(self, detail, name=""):
        detail = " ".join(str(detail or "").replace("\n", " ").split())
        if name:
            normalized_name = self.raw_normalize_item_name(name)
            normalized_detail = self.raw_normalize_item_name(detail)
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

    def passive_item_type_group(self, name):
        normalized = self.normalize_item_name(name)
        detail = self.passive_item_details.get(normalized, "") if hasattr(self, "passive_item_details") else ""

        def plain_text(value):
            text = str(value or "").lower()
            text = text.replace("pokémon", "pokemon").replace("pok\u00e9mon", "pokemon")
            text = text.replace("sp.atk", "sp atk").replace("sp.def", "sp def")
            return re.sub(r"[^a-z0-9]+", " ", text)

        def find_type(source, allow_bare_type=False):
            text = plain_text(source)
            if not text:
                return None
            matches = []
            for type_name in POKEMON_TYPE_NAMES:
                patterns = [
                    rf"\b{type_name}\s+pokemon\b",
                    rf"\b{type_name}\s+type\b",
                    rf"\b{type_name}\s+types\b",
                    rf"\b{type_name}\s+trait\b",
                    rf"\b{type_name}\s+traits\b",
                    rf"\b{type_name}\s+attack\b",
                    rf"\b{type_name}\s+attacks\b",
                    rf"\b{type_name}\s+move\b",
                    rf"\b{type_name}\s+moves\b",
                    rf"\b{type_name}\s+ally\b",
                    rf"\b{type_name}\s+allies\b",
                ]
                if allow_bare_type:
                    patterns.append(rf"\b{type_name}\b")
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        matches.append((match.start(), type_name))
                        break
            if not matches:
                return None
            matches.sort(key=lambda item: item[0])
            return f"{matches[0][1].title()} type"

        return find_type(detail, allow_bare_type=True) or "General"

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

    def load_unknown_regular_items(self):
        try:
            with open(UNKNOWN_REGULAR_ITEMS_PATH, "r", encoding="utf-8") as items_file:
                data = json.load(items_file)
        except Exception:
            return set()
        if not isinstance(data, list):
            return set()
        known_items = {self.normalize_item_name(item) for item in KNOWN_PASSIVE_ITEMS}
        default_priority = {self.normalize_item_name(item) for item in REGULAR_ITEM_PRIORITY}
        return {
            self.normalize_item_name(item)
            for item in data
            if self.normalize_item_name(item)
            and self.normalize_item_name(item) not in known_items
            and self.normalize_item_name(item) not in default_priority
        }

    def record_unknown_regular_items(self, names):
        priority_names = {
            self.normalize_item_name(name)
            for name in list(self.active_regular_item_priority()) + list(self.active_combat_held_item_priority())
        }
        new_items = []
        with self.unknown_regular_items_lock:
            for name in names or []:
                normalized = self.normalize_item_name(name)
                if not normalized or normalized in priority_names or normalized in self.unknown_regular_items:
                    continue
                self.unknown_regular_items.add(normalized)
                new_items.append(normalized)
            if not new_items:
                return
            try:
                with open(UNKNOWN_REGULAR_ITEMS_PATH, "w", encoding="utf-8") as items_file:
                    json.dump(sorted(self.unknown_regular_items), items_file, indent=2)
            except Exception as exc:
                self.log(f"Could not save unknown held items: {exc}")
                return
        self.merge_unknowns_into_regular_ignore()
        self.log("Unknown held item(s) recorded: " + ", ".join(sorted(new_items)))

    def merge_unknowns_into_regular_ignore(self):
        try:
            priority_names = {
                self.normalize_item_name(x)
                for x in list(self.active_regular_item_priority()) + list(self.active_combat_held_item_priority())
            }
            self.regular_item_ignore = [
                item for item in self.regular_item_ignore
                if self.normalize_item_name(item) not in priority_names
            ]
            have = {self.normalize_item_name(x) for x in self.regular_item_ignore}
            for item in sorted(self.unknown_regular_items):
                norm = self.normalize_item_name(item)
                if norm and norm not in priority_names and norm not in have:
                    self.regular_item_ignore.append(item)
                    have.add(norm)
        except Exception:
            pass

    def save_settings(self):
        settings = self.build_settings_payload()
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as settings_file:
                json.dump(settings, settings_file, indent=2)
        except Exception as exc:
            self.log(f"Could not save settings: {exc}")

    def export_configuration(self):
        self.save_settings()
        default_name = f"pokelike-bot-config-{time.strftime('%Y%m%d-%H%M%S')}.json"
        path = filedialog.asksaveasfilename(
            parent=self.settings_window or self,
            title="Export configuration",
            initialfile=default_name,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        payload = {
            "config_format": "pokelike-bot-config",
            "config_version": 1,
            "app": APP_NAME,
            "app_version": APP_VERSION,
            "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "settings": self.build_settings_payload(),
        }
        try:
            with open(path, "w", encoding="utf-8") as config_file:
                json.dump(payload, config_file, indent=2)
            self.log(f"Configuration exported: {path}")
            messagebox.showinfo(APP_NAME, "Configuration exported.", parent=self.settings_window or self)
        except Exception as exc:
            self.log(f"Could not export configuration: {exc}")
            messagebox.showerror(APP_NAME, f"Could not export configuration:\n\n{exc}", parent=self.settings_window or self)

    def import_configuration(self):
        path = filedialog.askopenfilename(
            parent=self.settings_window or self,
            title="Import configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as config_file:
                payload = json.load(config_file)
        except Exception as exc:
            self.log(f"Could not read configuration: {exc}")
            messagebox.showerror(APP_NAME, f"Could not read configuration:\n\n{exc}", parent=self.settings_window or self)
            return
        if not messagebox.askyesno(
            APP_NAME,
            "Import this configuration and replace the current bot settings?",
            parent=self.settings_window or self,
        ):
            return
        if not self.apply_settings_payload_to_ui(payload):
            messagebox.showerror(APP_NAME, "This file does not contain a valid PokeLike Bot configuration.", parent=self.settings_window or self)
            return
        self.save_settings()
        self.log(f"Configuration imported: {path}")
        messagebox.showinfo(APP_NAME, "Configuration imported.", parent=self.settings_window or self)

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
        brand_actions.grid_columnconfigure((0, 1, 2), weight=0)
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
        website_button.grid(row=0, column=1, padx=(0, 12), sticky="e")
        website_button.bind("<Button-1>", self.open_brand_link)

        github_button = ctk.CTkLabel(
            brand_actions,
            text="" if self.github_icon else "GitHub",
            image=self.github_icon,
            width=48,
            height=48,
            cursor="hand2",
        )
        github_button.grid(row=0, column=2, sticky="e")
        github_button.bind("<Button-1>", lambda _event: self.open_github_link())

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
        self.wallet_gold_label = self.create_stat(controls, "Gold wallet", "--", 2, 1)
        self.money_label = self.create_stat(controls, "Gold earned / h", "0 (0/h)", 2, 2)
        self.money_per_hour_label = self.money_label

        setup_box = ctk.CTkFrame(controls, fg_color="transparent")
        setup_box.grid(row=3, column=0, columnspan=3, padx=12, pady=(0, 8), sticky="ew")
        setup_box.grid_columnconfigure(1, weight=1)
        setup_box.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(setup_box, text="Mode", text_color="gray70", width=76, anchor="w").grid(
            row=0, column=0, padx=(0, 8), sticky="w"
        )
        self.mode_selector = ctk.CTkOptionMenu(
            setup_box,
            values=[
                MODE_FULL_RUN,
                MODE_SHINY_CHARM_REROLL,
                MODE_SHINY_POKEMON_REROLL,
                MODE_NORMAL_POKEMON_REROLL,
                MODE_COMPLETE_POKEDEX,
                MODE_POKEGOLD_FARM,
                MODE_SHINY_SHOP_REROLL,
                MODE_LEGENDARY_SHOP_REROLL,
            ],
            variable=self.mode_var,
            command=lambda _value: self.update_log_panel_title(_value),
        )
        self.mode_selector.grid(row=0, column=1, padx=(0, 18), sticky="ew")

        ctk.CTkLabel(setup_box, text="Stage", text_color="gray70").grid(row=0, column=2, padx=(0, 8), sticky="w")
        self.run_target_selector = ctk.CTkOptionMenu(
            setup_box,
            values=list(RUN_TARGET_OPTIONS),
            variable=self.run_target_var,
        )
        self.run_target_selector.grid(row=0, column=3, padx=(0, 0), sticky="ew")

        ctk.CTkLabel(setup_box, text="Starter", text_color="gray70", width=76, anchor="w").grid(
            row=1, column=0, padx=(0, 8), pady=(10, 0), sticky="w"
        )
        self.starter_entry = ctk.CTkEntry(setup_box, textvariable=self.starter_var, placeholder_text="Dratini")
        self.starter_entry.grid(row=1, column=1, padx=(0, 18), pady=(10, 0), sticky="ew")

        ctk.CTkLabel(setup_box, text="Pokemon whitelist", text_color="gray70").grid(
            row=1, column=2, padx=(0, 8), pady=(10, 0), sticky="w"
        )
        self.target_pokemon_entry = ctk.CTkEntry(setup_box, textvariable=self.target_pokemon_var, placeholder_text="Bagon, Ralts, Riolu")
        self.target_pokemon_entry.grid(row=1, column=3, pady=(10, 0), sticky="ew")

        ctk.CTkLabel(setup_box, text="Shop ignore list", text_color="gray70", width=76, anchor="w").grid(
            row=2, column=0, padx=(0, 8), pady=(10, 0), sticky="w"
        )
        self.shop_ignore_pokemon_entry = ctk.CTkEntry(
            setup_box,
            textvariable=self.shop_ignore_pokemon_var,
            placeholder_text="Moltres, Zapdos, Articuno",
        )
        self.shop_ignore_pokemon_entry.grid(row=2, column=1, columnspan=3, pady=(10, 0), sticky="ew")

        self.dex_missing_summary_label = ctk.CTkLabel(
            setup_box,
            textvariable=self.dex_missing_summary_var,
            text_color="gray70",
            anchor="w",
        )
        self.dex_missing_summary_label.grid(row=3, column=0, columnspan=4, pady=(8, 0), sticky="ew")

        browser_box = ctk.CTkFrame(controls, fg_color="transparent")
        browser_box.grid(row=4, column=0, columnspan=3, padx=12, pady=(0, 8), sticky="ew")
        browser_box.grid_columnconfigure(0, weight=1)
        browser_box.grid_columnconfigure(1, weight=1)
        browser_box.grid_columnconfigure(3, weight=0)
        self.manual_start_checkbox = ctk.CTkCheckBox(
            browser_box,
            text="Use current run screen on first attempt",
            variable=self.manual_start_var,
        )
        self.manual_start_checkbox.grid(row=0, column=0, padx=(0, 12), sticky="w")
        self.headless_checkbox = ctk.CTkCheckBox(
            browser_box,
            text="Run Chrome hidden (headless)",
            variable=self.headless_var,
        )
        self.headless_checkbox.grid(row=0, column=1, padx=(0, 12), sticky="w")
        ctk.CTkLabel(browser_box, text="Browsers", text_color="gray70").grid(
            row=0, column=2, padx=(8, 8), sticky="e"
        )
        self.browser_count_entry = ctk.CTkEntry(browser_box, textvariable=self.browser_count_var, width=70)
        self.browser_count_entry.grid(row=0, column=3, padx=(0, 12), sticky="e")
        ctk.CTkLabel(browser_box, text="Restart Chrome (min)", text_color="gray70").grid(
            row=0, column=4, padx=(8, 8), sticky="e"
        )
        self.chrome_restart_entry = ctk.CTkEntry(
            browser_box,
            textvariable=self.chrome_restart_minutes_var,
            width=70,
            placeholder_text="0",
        )
        self.chrome_restart_entry.grid(row=0, column=5, sticky="e")

        button_box = ctk.CTkFrame(controls, fg_color="transparent")
        button_box.grid(row=5, column=0, columnspan=3, padx=12, pady=(2, 14), sticky="ew")
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
            fg_color="#173a63",
            hover_color="#245181",
            height=38,
        )
        self.stop_button.grid(row=0, column=2, padx=(6, 0), sticky="ew")

        self.force_cloud_save_button = ctk.CTkButton(
            button_box,
            text="Force Cloud Save",
            command=self.force_cloud_save_from_ui,
            height=38,
        )
        self.force_cloud_save_button.grid(row=0, column=3, padx=(12, 0), sticky="ew")

        self.settings_button = ctk.CTkButton(
            button_box,
            text="Settings",
            command=self.open_settings_window,
            height=38,
        )
        self.settings_button.grid(row=1, column=0, padx=(0, 6), pady=(8, 0), sticky="ew")

        self.priority_button = ctk.CTkButton(
            button_box,
            text="Item priorities",
            command=self.open_priority_window,
            height=38,
        )
        self.priority_button.grid(row=1, column=1, padx=6, pady=(8, 0), sticky="ew")

        self.run_history_button = ctk.CTkButton(
            button_box,
            text="Run history",
            command=self.open_run_history_window,
            height=38,
        )
        self.run_history_button.grid(row=1, column=2, columnspan=2, padx=(6, 0), pady=(8, 0), sticky="ew")

        self.log_box = ctk.CTkFrame(controls, fg_color="transparent", corner_radius=0)
        self.log_box.grid(row=6, column=0, columnspan=3, padx=12, pady=(0, 14), sticky="ew")
        self.log_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self.log_box,
            textvariable=self.shop_shiny_rate_var,
            text_color="gray70",
            anchor="w",
        ).grid(row=0, column=0, padx=8, pady=(8, 0), sticky="ew")
        self.gui_log_text = ctk.CTkTextbox(
            self.log_box,
            height=72,
            wrap="word",
            font=ctk.CTkFont(size=12),
        )
        self.gui_log_text.grid(row=1, column=0, padx=8, pady=8, sticky="ew")
        self.gui_log_text.configure(state="disabled")
        self.shop_roll_log_text = self.gui_log_text
        self.update_log_panel_title()

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

    def configure_settings_controls(self, state):
        live_controls = []
        for widget in getattr(self, "settings_controls", []):
            try:
                if widget.winfo_exists():
                    widget.configure(state=state)
                    live_controls.append(widget)
            except Exception:
                pass
        self.settings_controls = live_controls

    def update_dex_missing_summary(self, counts=None):
        counts = counts or {}
        self.current_dex_missing_counts = counts
        normal = counts.get("normal") or {}
        shiny = counts.get("shiny") or {}
        text = (
            "Dex missing: "
            f"Normal {int(normal.get('total') or 0)} [{int(normal.get('legendary') or 0)} legendary] | "
            f"Shiny {int(shiny.get('total') or 0)} [{int(shiny.get('legendary') or 0)} legendary]"
        )
        self.safe_ui(lambda: self.dex_missing_summary_var.set(text))

    def refresh_dex_targets_from_ui(self):
        if self.dex_preload_thread and self.dex_preload_thread.is_alive():
            return
        drivers = self.get_live_drivers()
        if not drivers:
            self.log("Dex targets: open a browser first, then press Refresh Dex.")
            return
        mode = (
            self.full_run_dex_priority_var.get()
            if self.mode_var.get() == MODE_FULL_RUN
            else DEX_TARGET_BOTH
            if self.mode_var.get() == MODE_COMPLETE_POKEDEX
            else self.dex_target_var.get()
        )
        if mode not in DEX_TARGET_OPTIONS or mode == DEX_TARGET_OFF:
            self.log("Dex targets: choose a Dex target mode or Full run Dex priority in Settings before refreshing.")
            return
        self.force_cloud_save_button.configure(state="disabled")
        self.dex_preload_thread = threading.Thread(
            target=self.refresh_dex_targets_worker,
            args=(drivers[0], mode),
            daemon=True,
        )
        self.dex_preload_thread.start()

    def refresh_dex_targets_worker(self, driver, target_mode):
        self.thread_local.use_local = True
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        try:
            targets = self.collect_missing_dex_targets(target_mode)
            manual_targets = self.parse_pokemon_target_list(self.target_pokemon_var.get())
            self.current_dex_target_mode = target_mode
            self.current_manual_target_pokemon_list = manual_targets
            self.current_target_pokemon_list = self.build_current_pokemon_targets(manual_targets, targets)
            self.current_target_pokemon = ", ".join(self.current_target_pokemon_list)
            if targets:
                self.log(f"Dex targets: refresh complete; {len(targets)} missing target(s) available.")
            else:
                self.log("Dex targets: refresh completed, but no missing targets were found.")
        except Exception as exc:
            self.log(f"Dex targets: refresh failed ({exc}).")
        finally:
            self.clear_thread_driver()
            self.safe_ui(lambda: self.force_cloud_save_button.configure(state="normal"))

    def force_cloud_save_from_ui(self):
        if self.dex_preload_thread and self.dex_preload_thread.is_alive():
            return
        drivers = self.get_live_drivers()
        if not drivers:
            self.log("Force cloud save: open a browser first.")
            return
        self.force_cloud_save_button.configure(state="disabled")
        self.dex_preload_thread = threading.Thread(
            target=self.force_cloud_save_worker,
            args=(drivers[0],),
            daemon=True,
        )
        self.dex_preload_thread.start()

    def force_cloud_save_worker(self, driver):
        self.thread_local.use_local = True
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        try:
            self.log("Force cloud save: opening menu and clicking Force Upload to Cloud.")
            if self.force_upload_save_data(driver):
                self.close_account_modal_if_visible(driver)
                self.restore_legendary_shop_cloud_guard(driver)
                self.log("Force cloud save: upload completed.")
            else:
                self.log("Force cloud save: upload did not complete.")
        except Exception as exc:
            self.log(f"Force cloud save: upload failed ({exc}).")
        finally:
            self.clear_thread_driver()
            self.safe_ui(lambda: self.force_cloud_save_button.configure(state="normal"))

    def open_settings_window(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.bring_popup_to_front(self.settings_window)
            return

        window = ctk.CTkToplevel(self)
        window.title("Settings")
        window.geometry("760x520")
        window.minsize(680, 460)
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(0, weight=1)
        self.settings_window = window
        self.settings_controls = []
        self.prepare_popup_window(window)

        content = ctk.CTkScrollableFrame(window, corner_radius=12)
        content.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        def register(widget):
            self.settings_controls.append(widget)
            return widget

        run_box = ctk.CTkFrame(content, corner_radius=10, fg_color="#111827")
        run_box.grid(row=0, column=0, padx=4, pady=(4, 10), sticky="ew")
        run_box.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(run_box, text="Run Settings", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(12, 8), sticky="w"
        )
        ctk.CTkLabel(run_box, text="Dex targets", text_color="gray70").grid(
            row=1, column=0, padx=12, pady=6, sticky="w"
        )
        self.dex_target_selector = register(ctk.CTkOptionMenu(
            run_box,
            values=list(DEX_TARGET_OPTIONS),
            variable=self.dex_target_var,
        ))
        self.dex_target_selector.grid(row=1, column=1, padx=12, pady=6, sticky="ew")

        ctk.CTkLabel(run_box, text="Full run Dex priority", text_color="gray70").grid(
            row=2, column=0, padx=12, pady=6, sticky="w"
        )
        self.full_run_dex_priority_selector = register(ctk.CTkOptionMenu(
            run_box,
            values=list(FULL_RUN_DEX_PRIORITY_OPTIONS),
            variable=self.full_run_dex_priority_var,
        ))
        self.full_run_dex_priority_selector.grid(row=2, column=1, padx=12, pady=6, sticky="ew")

        filters_box = ctk.CTkFrame(run_box, corner_radius=8, fg_color="#0b1220")
        filters_box.grid(row=3, column=0, columnspan=2, padx=12, pady=6, sticky="ew")
        filters_box.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(filters_box, text="Full-run filters", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=10, pady=(10, 4), sticky="w"
        )
        register(ctk.CTkCheckBox(
            filters_box,
            text="Ignore all Pokemon",
            variable=self.ignore_pokemon_var,
        )).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        register(ctk.CTkCheckBox(
            filters_box,
            text="Avoid Pokecenter",
            variable=self.ignore_pokecenter_var,
        )).grid(row=1, column=1, padx=10, pady=5, sticky="w")
        register(ctk.CTkCheckBox(
            filters_box,
            text="Only take shiny Pokemon",
            variable=self.shiny_only_pokemon_var,
        )).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        register(ctk.CTkCheckBox(
            filters_box,
            text="No TMs or move tutor",
            variable=self.no_tm_move_tutor_var,
        )).grid(row=2, column=1, padx=10, pady=5, sticky="w")
        register(ctk.CTkCheckBox(
            filters_box,
            text="Reroll start for shiny matching filters",
            variable=self.start_shiny_filter_reroll_var,
        )).grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        register(ctk.CTkCheckBox(
            filters_box,
            text="Swap combat item for bosses",
            variable=self.boss_combat_item_swap_var,
        )).grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        register(ctk.CTkCheckBox(
            filters_box,
            text="Prioritize catches while party is under 6",
            variable=self.prioritize_party_fill_var,
        )).grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        register(ctk.CTkCheckBox(
            filters_box,
            text="Delay party-fill catches until map 3",
            variable=self.delay_party_fill_var,
        )).grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        register(ctk.CTkCheckBox(
            filters_box,
            text="Smart type ability choice",
            variable=self.smart_trait_choice_var,
        )).grid(row=7, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(filters_box, text="Whitelist mode", text_color="gray70").grid(
            row=8, column=0, padx=10, pady=5, sticky="w"
        )
        self.whitelist_filter_mode_selector = register(ctk.CTkOptionMenu(
            filters_box,
            values=list(POKEMON_WHITELIST_OPTIONS),
            variable=self.whitelist_filter_mode_var,
        ))
        self.whitelist_filter_mode_selector.grid(row=8, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(filters_box, text="Type mode", text_color="gray70").grid(
            row=10, column=0, padx=10, pady=5, sticky="w"
        )
        self.type_filter_mode_selector = register(ctk.CTkOptionMenu(
            filters_box,
            values=list(POKEMON_FILTER_OPTIONS),
            variable=self.type_filter_mode_var,
        ))
        self.type_filter_mode_selector.grid(row=10, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(filters_box, text="Type whitelist", text_color="gray70").grid(
            row=11, column=0, padx=10, pady=5, sticky="w"
        )
        self.type_whitelist_entry = register(ctk.CTkEntry(
            filters_box,
            textvariable=self.type_whitelist_var,
            placeholder_text="Dragon, Fire, Fairy",
        ))
        self.type_whitelist_entry.grid(row=11, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(filters_box, text="Generation whitelist", text_color="gray70").grid(
            row=12, column=0, padx=10, pady=(5, 10), sticky="w"
        )
        self.generation_whitelist_entry = register(ctk.CTkEntry(
            filters_box,
            textvariable=self.generation_whitelist_var,
            placeholder_text="Kanto, Hoenn or Gen 1, Gen 3",
        ))
        self.generation_whitelist_entry.grid(row=12, column=1, padx=10, pady=(5, 10), sticky="ew")

        ctk.CTkLabel(run_box, text="After reroll", text_color="gray70").grid(
            row=4, column=0, padx=12, pady=6, sticky="w"
        )
        self.reroll_completion_selector = register(ctk.CTkOptionMenu(
            run_box,
            values=list(REROLL_COMPLETION_OPTIONS),
            variable=self.reroll_completion_var,
        ))
        self.reroll_completion_selector.grid(row=4, column=1, padx=12, pady=6, sticky="ew")

        ctk.CTkLabel(run_box, text="Shop after hit", text_color="gray70").grid(
            row=5, column=0, padx=12, pady=6, sticky="w"
        )
        self.shop_reroll_after_hit_selector = register(ctk.CTkOptionMenu(
            run_box,
            values=list(SHOP_REROLL_AFTER_HIT_OPTIONS),
            variable=self.shop_reroll_after_hit_var,
        ))
        self.shop_reroll_after_hit_selector.grid(row=5, column=1, padx=12, pady=6, sticky="ew")

        ctk.CTkLabel(run_box, text="Item reroll target", text_color="gray70").grid(
            row=6, column=0, padx=12, pady=(6, 12), sticky="w"
        )
        self.item_reroll_target_entry = register(ctk.CTkEntry(
            run_box,
            textvariable=self.item_reroll_target_var,
            placeholder_text="Legend Lure",
        ))
        self.item_reroll_target_entry.grid(row=6, column=1, padx=12, pady=(6, 12), sticky="ew")

        ctk.CTkLabel(run_box, text="Pokegold farm target", text_color="gray70").grid(
            row=7, column=0, padx=12, pady=(6, 12), sticky="w"
        )
        self.pokegold_farm_target_entry = register(ctk.CTkEntry(
            run_box,
            textvariable=self.pokegold_farm_target_var,
            placeholder_text="100000",
        ))
        self.pokegold_farm_target_entry.grid(row=7, column=1, padx=12, pady=(6, 12), sticky="ew")

        ctk.CTkLabel(run_box, text="Evolution choices", text_color="gray70").grid(
            row=8, column=0, padx=12, pady=(6, 12), sticky="w"
        )
        self.evolution_preference_entry = register(ctk.CTkEntry(
            run_box,
            textvariable=self.evolution_preference_var,
            placeholder_text="Flareon, Dustox",
        ))
        self.evolution_preference_entry.grid(row=8, column=1, padx=12, pady=(6, 12), sticky="ew")

        schedule_box = ctk.CTkFrame(content, corner_radius=10, fg_color="#111827")
        schedule_box.grid(row=1, column=0, padx=4, pady=10, sticky="ew")
        schedule_box.grid_columnconfigure(0, weight=1)
        schedule_top = ctk.CTkFrame(schedule_box, fg_color="transparent")
        schedule_top.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="ew")
        schedule_top.grid_columnconfigure(0, weight=1)
        self.schedule_checkbox = register(ctk.CTkCheckBox(
            schedule_top,
            text="Task schedule",
            variable=self.schedule_enabled_var,
            command=self.update_schedule_summary,
        ))
        self.schedule_checkbox.grid(row=0, column=0, sticky="w")
        self.schedule_button = register(ctk.CTkButton(
            schedule_top,
            text="Edit",
            command=self.open_schedule_window,
            width=76,
            height=30,
        ))
        self.schedule_button.grid(row=0, column=1, padx=(10, 0), sticky="e")
        self.schedule_summary_label = ctk.CTkLabel(
            schedule_box,
            text="",
            text_color="gray78",
            anchor="w",
            justify="left",
            wraplength=660,
        )
        self.schedule_summary_label.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="ew")
        self.update_schedule_summary()

        tools_box = ctk.CTkFrame(content, corner_radius=10, fg_color="#151f2c")
        tools_box.grid(row=2, column=0, padx=4, pady=10, sticky="ew")
        tools_box.grid_columnconfigure((0, 1, 2), weight=1)

        def close_window():
            self.save_settings()
            self.settings_window = None
            self.settings_controls = []
            self.schedule_summary_label = None
            window.destroy()

        register(ctk.CTkButton(
            tools_box,
            text="Import config",
            command=self.import_configuration,
            height=36,
        )).grid(row=0, column=0, padx=(12, 6), pady=12, sticky="ew")
        register(ctk.CTkButton(
            tools_box,
            text="Export config",
            command=self.export_configuration,
            height=36,
        )).grid(row=0, column=1, padx=6, pady=12, sticky="ew")
        register(ctk.CTkButton(
            tools_box,
            text="Save and close",
            command=close_window,
            height=36,
        )).grid(row=0, column=2, padx=(6, 12), pady=12, sticky="ew")
        if self.bot_thread is not None and self.bot_thread.is_alive():
            self.configure_settings_controls("disabled")
        window.protocol("WM_DELETE_WINDOW", close_window)

    def schedule_step_label(self, step):
        custom_name = " ".join(str(step.get("name") or "").strip().split())
        target = step.get("target", RUN_TARGET_DAILY)
        starter = " ".join(str(step.get("starter") or "").strip().split())
        goal = self.normalize_schedule_goal(step.get("goal", SCHEDULE_COMPLETION_WINS))
        count = int(step.get("count", 1))
        settings = step.get("settings") if isinstance(step.get("settings"), dict) else {}
        mode = settings.get("mode")
        if goal == SCHEDULE_COMPLETION_POKEGOLD:
            suffix = "Pokegold"
        elif goal == SCHEDULE_COMPLETION_SHOP_BUDGET:
            suffix = "until shop funds low"
        elif goal == SCHEDULE_COMPLETION_FOREVER:
            suffix = "forever"
        else:
            suffix = goal.lower()
        if goal == SCHEDULE_COMPLETION_ATTEMPTS and count == 1:
            suffix = "attempt"
        if goal == SCHEDULE_COMPLETION_WINS and count == 1:
            suffix = "completed run"
        if goal == SCHEDULE_COMPLETION_CHALLENGE:
            suffix = "challenge completion" if count == 1 else "challenge completions"
        starter_text = f" with {starter.title()}" if starter else ""
        settings_text = f" [{mode}]" if mode else ""
        prefix = f"{custom_name}: " if custom_name else ""
        if goal == SCHEDULE_COMPLETION_POKEGOLD:
            return f"{prefix}{target}{starter_text} until {count:,} {suffix}{settings_text}"
        if goal in {SCHEDULE_COMPLETION_SHOP_BUDGET, SCHEDULE_COMPLETION_FOREVER}:
            return f"{prefix}{target}{starter_text} {suffix}{settings_text}"
        return f"{prefix}{target}{starter_text} x{count} {suffix}{settings_text}"

    def update_schedule_summary(self):
        if not hasattr(self, "schedule_summary_label") or self.schedule_summary_label is None:
            return
        if not self.schedule_enabled_var.get():
            text = "Off"
        else:
            labels = [self.schedule_step_label(step) for step in self.task_schedule[:3]]
            extra = len(self.task_schedule) - len(labels)
            text = "  ->  ".join(labels)
            if extra > 0:
                text = f"{text}  (+{extra})"
        try:
            if self.schedule_summary_label.winfo_exists():
                self.schedule_summary_label.configure(text=text)
        except Exception:
            pass

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
            result_key = str(entry.get("result") or "").strip().lower()
            won = result_key == "win"
            card = ctk.CTkFrame(
                frame,
                corner_radius=10,
                fg_color="#132117" if won else "#111827",
                border_width=2 if won else 0,
                border_color="#facc15" if won else "#111827",
            )
            card.grid(row=row, column=0, padx=8, pady=6, sticky="ew")
            card.grid_columnconfigure(0, weight=1)
            result = entry.get("result", "").title() or "Run"
            title = (
                f"Run #{entry.get('run', 0)}  -  {result}  -  "
                f"{self.format_duration_seconds(entry.get('duration', 0))}  -  "
                f"{int(entry.get('money') or 0):,} Pokegold"
            )
            title_kwargs = {
                "text": title,
                "anchor": "w",
                "font": ctk.CTkFont(size=14, weight="bold"),
            }
            if won:
                title_kwargs["text_color"] = "#fde68a"
            ctk.CTkLabel(
                card,
                **title_kwargs,
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
        window.geometry("1180x620")
        window.minsize(1040, 500)
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
            text="Each task advances after attempts, completed runs, challenge completion, or earned Pokegold.",
            text_color="gray72",
            anchor="w",
        ).grid(row=0, column=1, padx=(0, 12), pady=12, sticky="ew")

        column_header = ctk.CTkFrame(window, fg_color="transparent")
        column_header.grid(row=1, column=0, padx=18, pady=(0, 4), sticky="ew")
        column_header.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(column_header, text="#", width=36, text_color="gray70").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(column_header, text="Name", width=150, text_color="gray70").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(column_header, text="Run target", text_color="gray70").grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(column_header, text="Starter", width=124, text_color="gray70").grid(row=0, column=3, sticky="w")
        ctk.CTkLabel(column_header, text="Advance after", width=126, text_color="gray70").grid(row=0, column=4, sticky="w")
        ctk.CTkLabel(column_header, text="Amount", width=90, text_color="gray70").grid(row=0, column=5, sticky="w")
        ctk.CTkLabel(column_header, text="Task settings", width=190, text_color="gray70").grid(row=0, column=6, sticky="w")

        list_frame = ctk.CTkScrollableFrame(window, corner_radius=12)
        list_frame.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="nsew")
        list_frame.grid_columnconfigure(2, weight=1)
        row_vars = []

        def sync_rows_from_widgets():
            steps = []
            for row in row_vars:
                goal = self.normalize_schedule_goal(row["goal"].get())
                raw_count = row["count"].get().strip()
                starter = row["starter"].get().strip()
                try:
                    count = int(raw_count)
                except Exception:
                    count = 1
                    if (
                        raw_count
                        and raw_count != "-"
                        and not starter
                        and goal in {SCHEDULE_COMPLETION_SHOP_BUDGET, SCHEDULE_COMPLETION_FOREVER}
                    ):
                        starter = raw_count
                max_count = 999999999 if goal in {SCHEDULE_COMPLETION_POKEGOLD, SCHEDULE_COMPLETION_FOREVER} else 9999
                steps.append({
                    "name": row["name"].get().strip(),
                    "target": row["target"].get(),
                    "starter": starter,
                    "goal": goal,
                    "count": max(1, min(count, max_count)),
                    "settings": dict(row.get("settings") or {}),
                })
            return self.parse_task_schedule(steps, DEFAULT_TASK_SCHEDULE)

        def redraw(rows=None):
            for child in list_frame.winfo_children():
                child.destroy()
            row_vars.clear()
            steps = rows if rows is not None else sync_rows_from_widgets()
            for index, step in enumerate(steps):
                name_var = ctk.StringVar(value=step.get("name", ""))
                target_var = ctk.StringVar(value=step["target"])
                starter_var = ctk.StringVar(value=step.get("starter", ""))
                goal_var = ctk.StringVar(value=step["goal"])
                count_text = "-" if step["goal"] in {SCHEDULE_COMPLETION_SHOP_BUDGET, SCHEDULE_COMPLETION_FOREVER} else str(step["count"])
                count_var = ctk.StringVar(value=count_text)
                settings = dict(step.get("settings") or {})
                row_vars.append({
                    "name": name_var,
                    "target": target_var,
                    "starter": starter_var,
                    "goal": goal_var,
                    "count": count_var,
                    "settings": settings,
                })

                ctk.CTkLabel(list_frame, text=str(index + 1), width=36).grid(
                    row=index, column=0, padx=(8, 6), pady=7, sticky="w"
                )
                ctk.CTkEntry(
                    list_frame,
                    textvariable=name_var,
                    width=148,
                    placeholder_text="Custom task",
                ).grid(row=index, column=1, padx=6, pady=7, sticky="ew")
                ctk.CTkOptionMenu(
                    list_frame,
                    values=list(RUN_TARGET_OPTIONS),
                    variable=target_var,
                ).grid(row=index, column=2, padx=6, pady=7, sticky="ew")
                ctk.CTkEntry(
                    list_frame,
                    textvariable=starter_var,
                    width=116,
                    placeholder_text="main starter",
                ).grid(row=index, column=3, padx=6, pady=7, sticky="ew")
                ctk.CTkOptionMenu(
                    list_frame,
                    values=list(SCHEDULE_COMPLETION_OPTIONS),
                    variable=goal_var,
                    width=116,
                ).grid(row=index, column=4, padx=6, pady=7, sticky="ew")
                ctk.CTkEntry(list_frame, textvariable=count_var, width=76).grid(
                    row=index, column=5, padx=6, pady=7, sticky="ew"
                )
                settings_label = "Saved" if settings else "Default"
                ctk.CTkLabel(list_frame, text=settings_label, width=58, text_color="gray74").grid(
                    row=index, column=6, padx=(6, 2), pady=7, sticky="w"
                )
                ctk.CTkButton(
                    list_frame,
                    text="Capture",
                    width=70,
                    command=lambda i=index: capture_row_settings(i),
                ).grid(row=index, column=7, padx=2, pady=7)
                ctk.CTkButton(
                    list_frame,
                    text="Clear",
                    width=54,
                    command=lambda i=index: clear_row_settings(i),
                ).grid(row=index, column=8, padx=(2, 8), pady=7)
                ctk.CTkButton(
                    list_frame,
                    text="Up",
                    width=54,
                    command=lambda i=index: move_row(i, -1),
                ).grid(row=index, column=9, padx=(8, 3), pady=7)
                ctk.CTkButton(
                    list_frame,
                    text="Down",
                    width=62,
                    command=lambda i=index: move_row(i, 1),
                ).grid(row=index, column=10, padx=3, pady=7)
                ctk.CTkButton(
                    list_frame,
                    text="Remove",
                    width=74,
                    fg_color="#7c2424",
                    hover_color="#963030",
                    command=lambda i=index: remove_row(i),
                ).grid(row=index, column=11, padx=(3, 8), pady=7)

        def capture_row_settings(index):
            steps = sync_rows_from_widgets()
            if 0 <= index < len(steps):
                steps[index]["settings"] = self.current_task_settings_snapshot()
                if not steps[index].get("name"):
                    steps[index]["name"] = steps[index]["target"]
                redraw(steps)

        def clear_row_settings(index):
            steps = sync_rows_from_widgets()
            if 0 <= index < len(steps):
                steps[index]["settings"] = {}
                redraw(steps)

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
            steps.append({
                "name": "New task",
                "target": "Story Classic - Kanto",
                "starter": "",
                "goal": SCHEDULE_COMPLETION_ATTEMPTS,
                "count": 1,
                "settings": {},
            })
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
        window.grid_rowconfigure((3, 5), weight=1)
        self.priority_window = window

        ctk.CTkLabel(
            window,
            text="Higher priority items are picked first. Expand a type, search for an item, then select it to move it up, down, or between lists.",
            text_color="gray70",
        ).grid(row=0, column=0, columnspan=2, padx=16, pady=(16, 10), sticky="w")

        toolbar = ctk.CTkFrame(window, fg_color="transparent")
        toolbar.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 10), sticky="ew")
        toolbar.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        ctk.CTkButton(
            toolbar,
            text="Up",
            command=lambda: move_selected_item(-1),
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(
            toolbar,
            text="Down",
            command=lambda: move_selected_item(1),
        ).grid(row=0, column=1, padx=6, sticky="ew")
        ctk.CTkButton(
            toolbar,
            text="To priority",
            command=lambda: move_selected_to_priority(),
        ).grid(row=0, column=2, padx=6, sticky="ew")
        ctk.CTkButton(
            toolbar,
            text="To never-pick",
            command=lambda: move_selected_to_ignore(),
        ).grid(row=0, column=3, padx=6, sticky="ew")
        ctk.CTkButton(
            toolbar,
            text="Combat",
            command=lambda: toggle_combat_item(),
        ).grid(row=0, column=4, padx=(6, 0), sticky="ew")

        starting_header = ctk.CTkFrame(window, fg_color="transparent")
        starting_header.grid(row=2, column=0, padx=(16, 8), pady=(0, 6), sticky="ew")
        starting_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(starting_header, text="Starting / passive item priority").grid(row=0, column=0, sticky="w")
        starter_key = self.current_starter_key()
        starter_label = self.current_starter_label()
        regular_header = ctk.CTkFrame(window, fg_color="transparent")
        regular_header.grid(row=2, column=1, padx=(8, 16), pady=(0, 6), sticky="ew")
        regular_header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            regular_header,
            text=f"Held-item reward priority for {starter_label}",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            regular_header,
            text="Load default",
            width=96,
            command=lambda: load_regular_default(),
        ).grid(row=0, column=1, padx=(6, 0), sticky="e")
        ctk.CTkButton(
            regular_header,
            text="Clear starter",
            width=104,
            command=lambda: clear_starter_regular_profile(),
        ).grid(row=0, column=2, padx=(6, 0), sticky="e")

        class PriorityBlockList:
            def __init__(block_self, parent, row, column, values, padx, rowspan=1, group_items=False):
                block_self.group_items = group_items
                block_self.items = list(values)
                block_self.selected_index = None
                block_self.search_var = ctk.StringVar(value="")
                block_self.collapsed_groups = set(POKEMON_TYPE_GROUPS) | {"General"}
                block_self.row_widgets = {}
                block_self.search_after_id = None
                block_self.outer = ctk.CTkFrame(parent, fg_color="transparent")
                block_self.outer.grid(row=row, column=column, rowspan=rowspan, padx=padx, pady=(0, 12), sticky="nsew")
                block_self.outer.grid_columnconfigure(0, weight=1)
                block_self.outer.grid_rowconfigure(1, weight=1)
                block_self.search_entry = ctk.CTkEntry(
                    block_self.outer,
                    textvariable=block_self.search_var,
                    placeholder_text="Search items",
                )
                block_self.search_entry.grid(row=0, column=0, padx=0, pady=(0, 8), sticky="ew")
                block_self.search_entry.bind("<KeyRelease>", block_self.schedule_search_render)
                block_self.frame = ctk.CTkScrollableFrame(block_self.outer, corner_radius=10)
                block_self.frame.grid(row=1, column=0, sticky="nsew")
                block_self.frame.grid_columnconfigure(0, weight=1)
                block_self.render()

            def normalize_block_item(block_self, value):
                return self.normalize_item_name(value)

            def item_group(block_self, value):
                return self.passive_item_type_group(value)

            def group_order(block_self, group):
                if group == "General":
                    return len(POKEMON_TYPE_GROUPS)
                try:
                    return POKEMON_TYPE_GROUPS.index(group)
                except ValueError:
                    return len(POKEMON_TYPE_GROUPS) + 1

            def grouped_items(block_self):
                if not block_self.group_items:
                    return [("", list(block_self.items))]
                groups = {group: [] for group in POKEMON_TYPE_GROUPS}
                groups["General"] = []
                query = block_self.search_var.get().strip().lower()
                for value in block_self.items:
                    if query:
                        label = self.item_label_with_detail(value).lower()
                        if query not in label and query not in self.normalize_item_name(value):
                            continue
                    group = block_self.item_group(value)
                    if group not in groups:
                        group = "General"
                    groups[group].append(value)
                names = list(POKEMON_TYPE_GROUPS) + ["General"]
                return [(name, groups[name]) for name in names]

            def split_label(block_self, value):
                label = self.item_label_with_detail(value)
                detail_start = label.find(" [")
                if detail_start >= 0 and label.rstrip().endswith("]"):
                    return label[:detail_start], label[detail_start + 2:-1]
                return label, ""

            def select(block_self, value):
                try:
                    block_self.selected_index = block_self.items.index(value)
                except ValueError:
                    block_self.selected_index = None
                for candidate in priority_block_lists:
                    if candidate is not block_self:
                        candidate.selected_index = None
                        candidate.update_selection_styles()
                block_self.update_selection_styles()

            def toggle_group(block_self, group):
                if group in block_self.collapsed_groups:
                    block_self.collapsed_groups.remove(group)
                else:
                    block_self.collapsed_groups.add(group)
                block_self.render()

            def schedule_search_render(block_self, _event=None):
                if block_self.search_after_id is not None:
                    try:
                        window.after_cancel(block_self.search_after_id)
                    except Exception:
                        pass
                block_self.search_after_id = window.after(120, block_self.render)

            def type_display(block_self, group):
                if not group:
                    return ""
                if group.endswith(" type"):
                    return group[:-5]
                return group

            def type_color(block_self, group):
                return POKEMON_TYPE_COLORS.get(group, POKEMON_TYPE_COLORS["General"])

            def is_combat_item(block_self, value):
                combat_items = getattr(window, "_combat_held_item_priority", self.combat_held_item_priority)
                combat_names = {self.normalize_item_name(item) for item in combat_items}
                return self.normalize_item_name(value) in combat_names

            def update_selection_styles(block_self):
                for value, block in list(block_self.row_widgets.items()):
                    selected = (
                        block_self.selected_index is not None
                        and block_self.selected_index < len(block_self.items)
                        and block_self.items[block_self.selected_index] == value
                    )
                    combat = block_self.is_combat_item(value)
                    try:
                        block.configure(
                            fg_color="#1f3a5f" if selected else "#3b1116" if combat else "#111827",
                            border_color="#38bdf8" if selected else "#f87171" if combat else "#263244",
                        )
                    except Exception:
                        pass

            def render(block_self):
                block_self.search_after_id = None
                query = block_self.search_var.get().strip()
                for child in block_self.frame.winfo_children():
                    child.destroy()
                block_self.row_widgets = {}
                if not block_self.items:
                    ctk.CTkLabel(block_self.frame, text="No items", text_color="gray55", anchor="w").grid(
                        row=0, column=0, padx=10, pady=10, sticky="ew"
                    )
                    return
                row = 0
                for group, values in block_self.grouped_items():
                    if group and not values:
                        continue
                    if group:
                        collapsed = not query and group in block_self.collapsed_groups
                        type_color = block_self.type_color(group)
                        ctk.CTkButton(
                            block_self.frame,
                            text=f"{'+' if collapsed else '-'} {block_self.type_display(group)} ({len(values)})",
                            height=28,
                            anchor="w",
                            fg_color="#172033",
                            hover_color="#223149",
                            text_color=type_color,
                            border_width=1,
                            border_color=type_color,
                            command=lambda g=group: block_self.toggle_group(g),
                        ).grid(row=row, column=0, padx=6, pady=(6, 2), sticky="ew")
                        row += 1
                        if collapsed:
                            continue
                    for value in values:
                        selected = (
                            block_self.selected_index is not None
                            and block_self.selected_index < len(block_self.items)
                            and block_self.items[block_self.selected_index] == value
                        )
                        block = ctk.CTkFrame(
                            block_self.frame,
                            corner_radius=8,
                            fg_color="#1f3a5f" if selected else "#3b1116" if block_self.is_combat_item(value) else "#111827",
                            border_width=1,
                            border_color="#38bdf8" if selected else "#f87171" if block_self.is_combat_item(value) else "#263244",
                        )
                        block.grid(row=row, column=0, padx=6, pady=(3, 2), sticky="ew")
                        block.grid_columnconfigure(0, weight=1)
                        name, detail = block_self.split_label(value)
                        name_label = ctk.CTkLabel(
                            block,
                            text=name,
                            text_color="#7dd3fc",
                            anchor="w",
                            font=ctk.CTkFont(weight="bold"),
                            cursor="hand2",
                        )
                        name_label.grid(row=0, column=0, padx=10, pady=(7, 0), sticky="ew")
                        widgets = [block, name_label]
                        if detail:
                            detail_label = ctk.CTkLabel(
                                block,
                                text=detail,
                                text_color="#c4b5fd",
                                anchor="w",
                                justify="left",
                                wraplength=350,
                                cursor="hand2",
                            )
                            detail_label.grid(row=1, column=0, padx=10, pady=(1, 8), sticky="ew")
                            widgets.append(detail_label)
                        else:
                            name_label.grid_configure(pady=(7, 8))
                        for widget in widgets:
                            widget.bind("<Button-1>", lambda _event, item=value: block_self.select(item))
                        block_self.row_widgets[value] = block
                        row += 1
                if row == 0:
                    ctk.CTkLabel(block_self.frame, text="No matches", text_color="gray55", anchor="w").grid(
                        row=0, column=0, padx=10, pady=10, sticky="ew"
                    )

            def get(block_self, start, end=None):
                if str(start).startswith("1.0") and str(end).startswith("end"):
                    return "\n".join(block_self.items)
                if block_self.selected_index is None or block_self.selected_index >= len(block_self.items):
                    return ""
                return block_self.items[block_self.selected_index]

            def delete(block_self, start, end=None):
                if str(start).startswith("1.0") and str(end).startswith("end"):
                    block_self.items = []
                    block_self.selected_index = None
                    block_self.render()

            def insert(block_self, index, text):
                block_self.items = self.parse_priority_text(text, ())
                block_self.selected_index = None
                block_self.render()

            def selected_items(block_self):
                if block_self.selected_index is None or block_self.selected_index >= len(block_self.items):
                    return []
                return [block_self.items[block_self.selected_index]]

            def move_selected(block_self, direction):
                if block_self.selected_index is None:
                    return
                index = block_self.selected_index
                new_index = index + direction
                if new_index < 0 or new_index >= len(block_self.items):
                    return
                block_self.items[index], block_self.items[new_index] = block_self.items[new_index], block_self.items[index]
                block_self.selected_index = new_index
                block_self.render()

            def tag_ranges(block_self, _tag):
                return None

            def index(block_self, mark):
                if str(mark).startswith("end"):
                    return f"{len(block_self.items) + 1}.0"
                line = (block_self.selected_index or 0) + 1
                return f"{line}.0"

            def bind(block_self, *_args, **_kwargs):
                return None

            def configure(block_self, *_args, **_kwargs):
                return None

            def tag_configure(block_self, *_args, **_kwargs):
                return None

            def tag_remove(block_self, *_args, **_kwargs):
                return None

            def tag_add(block_self, *_args, **_kwargs):
                return None

        priority_block_lists = []
        starting_text = PriorityBlockList(
            window,
            row=3,
            column=0,
            values=self.starting_item_priority,
            padx=(16, 8),
            group_items=False,
        )
        priority_block_lists.append(starting_text)

        regular_text = PriorityBlockList(
            window,
            row=3,
            column=1,
            values=self.active_regular_item_priority(),
            padx=(8, 16),
            group_items=False,
        )
        priority_block_lists.append(regular_text)

        window._combat_held_item_priority = list(self.combat_held_item_priority)
        regular_text.render()

        ignore_header = ctk.CTkFrame(window, fg_color="transparent")
        ignore_header.grid(row=4, column=0, padx=(16, 8), pady=(0, 6), sticky="ew")
        ctk.CTkLabel(ignore_header, text="Starting / passive never-pick list").pack(side="left")

        ignore_text = PriorityBlockList(
            window,
            row=5,
            column=0,
            values=self.starting_item_ignore,
            padx=(16, 8),
            group_items=True,
        )
        priority_block_lists.append(ignore_text)

        regular_ignore_header = ctk.CTkFrame(window, fg_color="transparent")
        regular_ignore_header.grid(row=4, column=1, padx=(8, 16), pady=(0, 6), sticky="ew")
        ctk.CTkLabel(regular_ignore_header, text="Held-item never-pick list").pack(side="left")

        regular_ignore_text = PriorityBlockList(
            window,
            row=5,
            column=1,
            values=self.regular_item_ignore,
            padx=(8, 16),
            group_items=True,
        )
        priority_block_lists.append(regular_ignore_text)

        styled_boxes = [starting_text, regular_text, ignore_text, regular_ignore_text]

        def refresh_priority_box(box):
            box.render()

        def bind_priority_box(box):
            box.update_selection_styles()

        for box in styled_boxes:
            bind_priority_box(box)

        def _selected_lines(box):
            return [ln.strip() for ln in box.selected_items() if ln.strip()]

        def replace_box_items(box, lines, selected_index=None):
            box.items = self.parse_priority_text(lines, ())
            box.selected_index = selected_index if selected_index is not None and box.items else None
            box.render()

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
            replace_box_items(src, src_lines)
            replace_box_items(dst, dst_lines, max(0, len(dst_lines) - 1))

        def selected_box():
            for box in priority_block_lists:
                if box.selected_items():
                    return box
            return None

        def move_selected_item(direction):
            box = selected_box()
            if box is not None:
                box.move_selected(direction)

        def move_selected_to_priority():
            box = selected_box()
            if box is ignore_text:
                move_lines(ignore_text, starting_text)
            elif box is regular_ignore_text:
                move_lines(regular_ignore_text, regular_text)

        def move_selected_to_ignore():
            box = selected_box()
            if box is starting_text:
                move_lines(starting_text, ignore_text)
            elif box is regular_text:
                move_lines(regular_text, regular_ignore_text)

        def toggle_combat_item():
            picks = _selected_lines(regular_text)
            if not picks:
                return
            combat_items = list(getattr(window, "_combat_held_item_priority", []))
            combat_names = {self.normalize_item_name(item) for item in combat_items}
            for item in picks:
                normalized = self.normalize_item_name(item)
                if normalized in combat_names:
                    combat_items = [
                        current for current in combat_items
                        if self.normalize_item_name(current) != normalized
                    ]
                    combat_names.discard(normalized)
                else:
                    combat_items.append(item)
                    combat_names.add(normalized)
            window._combat_held_item_priority = combat_items
            regular_text.update_selection_styles()

        button_row = ctk.CTkFrame(window, fg_color="transparent")
        button_row.grid(row=6, column=0, columnspan=2, padx=16, pady=(0, 16), sticky="ew")
        button_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def save_priorities(save_for_starter):
            self.starting_item_priority = self.parse_priority_text(
                starting_text.get("1.0", "end"),
                STARTING_ITEM_PRIORITY,
            )
            regular_priorities = self.parse_priority_text(
                regular_text.get("1.0", "end"),
                REGULAR_ITEM_PRIORITY,
            )
            if save_for_starter and starter_key:
                self.regular_item_priority_by_starter[starter_key] = regular_priorities
            else:
                self.regular_item_priority = regular_priorities
            combat_marked = {
                self.normalize_item_name(item)
                for item in getattr(window, "_combat_held_item_priority", [])
            }
            self.combat_held_item_priority = [
                item for item in regular_priorities
                if self.normalize_item_name(item) in combat_marked
            ]
            self.starting_item_ignore = self.parse_priority_text(
                ignore_text.get("1.0", "end"),
                STARTING_ITEM_IGNORE,
            )
            self.regular_item_ignore = self.parse_priority_text(
                regular_ignore_text.get("1.0", "end"),
                REGULAR_ITEM_IGNORE,
            )
            self.merge_unknowns_into_ignore()
            self.merge_unknowns_into_regular_ignore()
            self.save_settings()
            regular_target = f"{starter_label} held-item" if save_for_starter and starter_key else "default held-item"
            self.log(
                "Updated item priorities: "
                f"{len(self.starting_item_priority)} starting, "
                f"{len(regular_priorities)} {regular_target}, "
                f"{len(self.combat_held_item_priority)} combat held, "
                f"{len(self.starting_item_ignore)} passive ignored, "
                f"{len(self.regular_item_ignore)} held ignored."
            )
            close_window()

        def load_regular_default():
            replace_box_items(regular_text, self.regular_item_priority)

        def clear_starter_regular_profile():
            if starter_key and starter_key in self.regular_item_priority_by_starter:
                del self.regular_item_priority_by_starter[starter_key]
                self.save_settings()
                self.log(f"Cleared held-item priority profile for {starter_label}; using default list.")
            load_regular_default()

        def reset_priorities():
            replace_box_items(starting_text, STARTING_ITEM_PRIORITY)
            replace_box_items(regular_text, REGULAR_ITEM_PRIORITY)
            window._combat_held_item_priority = list(COMBAT_HELD_ITEM_PRIORITY)
            replace_box_items(ignore_text, STARTING_ITEM_IGNORE)
            replace_box_items(regular_ignore_text, REGULAR_ITEM_IGNORE)
            regular_text.update_selection_styles()

        def close_window():
            self.priority_window = None
            window.destroy()

        ctk.CTkButton(button_row, text="Save for starter", command=lambda: save_priorities(True)).grid(
            row=0, column=0, padx=(0, 8), sticky="ew"
        )
        ctk.CTkButton(button_row, text="Save default", command=lambda: save_priorities(False)).grid(
            row=0, column=1, padx=8, sticky="ew"
        )
        ctk.CTkButton(button_row, text="Reset defaults", command=reset_priorities).grid(
            row=0, column=2, padx=8, sticky="ew"
        )
        ctk.CTkButton(button_row, text="Cancel", command=close_window).grid(
            row=0, column=3, padx=(8, 0), sticky="ew"
        )
        window.protocol("WM_DELETE_WINDOW", close_window)
        self.bring_popup_to_front(window)

    def safe_ui(self, fn):
        self.after(0, fn)

    def log(self, message):
        print(message, flush=True)
        text = str(message)
        self.gui_log_lines.append(text)
        self.gui_log_lines = self.gui_log_lines[-80:]

        def update_log_panel():
            widget = getattr(self, "gui_log_text", None)
            if not widget:
                return
            try:
                widget.configure(state="normal")
                widget.delete("1.0", "end")
                widget.insert("1.0", "\n".join(self.gui_log_lines))
                widget.see("end")
                widget.configure(state="disabled")
            except Exception:
                pass

        try:
            self.safe_ui(update_log_panel)
        except Exception:
            pass
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(LOG_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass

    def append_shop_roll_log(self, message):
        self.shop_roll_log_lines.append(message)
        self.shop_roll_log_lines = self.shop_roll_log_lines[-3:]
        self.log(message)

    def update_shop_shiny_rate(self, rate_text):
        if not rate_text or not self.is_shop_reroll_mode():
            return
        self.safe_ui(lambda: self.shop_shiny_rate_var.set(f"Legendary shiny rate: {rate_text}"))

    def update_log_panel_title(self, mode=None):
        def apply_title():
            selected_mode = mode or self.mode_var.get()
            if selected_mode in {MODE_SHINY_SHOP_REROLL, MODE_LEGENDARY_SHOP_REROLL}:
                if not str(self.shop_shiny_rate_var.get() or "").startswith("Legendary shiny rate:"):
                    self.shop_shiny_rate_var.set("Legendary shiny rate: --")
            else:
                self.shop_shiny_rate_var.set("Log")

        self.safe_ui(apply_title)

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
            self.money_label.configure(text=f"{int(self.total_money_earned):,} ({self.format_money_per_hour()})")
            self.after(1000, self.update_runtime_label)

    def update_stats_labels(self):
        self.safe_ui(lambda: self.runs_label.configure(text=str(self.run_count)))
        self.safe_ui(lambda: self.rolls_label.configure(text=str(self.item_rolls_checked)))
        self.safe_ui(lambda: self.encounters_label.configure(text=str(self.total_encounters_checked)))
        self.safe_ui(lambda: self.target_seen_label.configure(text=str(self.target_encounters_seen)))
        last_shiny = " ".join(str(getattr(self, "last_shiny_pokemon_name", "") or "").split())
        shiny_text = str(self.total_shinies_seen)
        if last_shiny:
            shiny_text = f"{shiny_text} - {last_shiny.title()}"
        self.safe_ui(lambda: self.shinies_seen_label.configure(text=shiny_text))
        money_text = f"{int(self.total_money_earned):,} ({self.format_money_per_hour()})"
        self.safe_ui(lambda: self.money_label.configure(text=money_text))
        wallet = self.last_wallet_pokegold_total
        wallet_text = f"{int(wallet):,}" if wallet is not None else "0"
        self.safe_ui(lambda: self.wallet_gold_label.configure(text=wallet_text))
        self.safe_ui(self.update_dynamic_stat_cards)

    def update_dynamic_stat_cards(self):
        target_list = getattr(self, "current_target_pokemon_list", []) or []
        if self.is_shop_reroll_mode():
            self.rolls_label.master.winfo_children()[0].configure(text="Shop rolls")
            self.rolls_label.configure(text=str(self.run_count))
            self.target_seen_label.master.winfo_children()[0].configure(text="Targets obtained")
            self.target_seen_label.configure(text=str(getattr(self, "shop_targets_obtained", 0)))
        elif self.current_mode == MODE_FULL_RUN:
            self.rolls_label.master.winfo_children()[0].configure(text="Leaders / E4")
            self.rolls_label.configure(text=str(self.run_leaders_defeated))
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

    def active_schedule_step(self):
        if not self.schedule_active or self.schedule_index >= len(self.task_schedule):
            return None
        return self.task_schedule[self.schedule_index]

    def active_schedule_goal(self):
        step = self.active_schedule_step()
        if not step:
            return None
        return self.normalize_schedule_goal(step.get("goal", SCHEDULE_COMPLETION_WINS))

    def current_shop_budget_schedule_active(self):
        return self.is_shop_reroll_mode() and self.active_schedule_goal() == SCHEDULE_COMPLETION_SHOP_BUDGET

    def active_schedule_starter(self):
        if not self.schedule_active or self.schedule_index >= len(self.task_schedule):
            return None
        starter = " ".join(str(self.task_schedule[self.schedule_index].get("starter") or "").strip().split())
        if starter:
            return starter.lower()
        return (self.schedule_default_starter_name or STARTER_NAME).strip().lower()

    def apply_task_settings_snapshot(self, settings, update_runtime=True):
        settings = self.parse_task_settings_snapshot(settings)
        if not settings:
            return False
        changed = False

        def set_var(var, value):
            nonlocal changed
            if value is None:
                return
            text = str(value)
            if var.get() != text:
                var.set(text)
                changed = True

        def set_bool(var, value):
            nonlocal changed
            if not isinstance(value, bool):
                return
            if bool(var.get()) != value:
                var.set(value)
                changed = True

        set_var(self.mode_var, settings.get("mode"))
        set_bool(self.manual_start_var, settings.get("manual_start"))
        set_bool(self.headless_var, settings.get("headless"))
        set_var(self.run_target_var, settings.get("run_target"))
        set_var(self.starter_var, settings.get("starter"))
        set_var(self.target_pokemon_var, settings.get("shiny_whitelist"))
        set_var(self.shop_ignore_pokemon_var, settings.get("shop_ignore_pokemon"))
        set_var(self.evolution_preference_var, settings.get("evolution_preference"))
        set_var(self.combat_held_item_var, settings.get("combat_held_item"))
        set_var(self.dex_target_var, settings.get("dex_target_mode"))
        set_var(self.full_run_dex_priority_var, settings.get("full_run_dex_priority_mode"))
        set_var(self.reroll_completion_var, settings.get("reroll_completion_mode"))
        set_var(self.shop_reroll_after_hit_var, settings.get("shop_reroll_after_hit"))
        set_var(self.item_reroll_target_var, settings.get("item_reroll_target"))
        set_var(self.pokegold_farm_target_var, settings.get("pokegold_farm_target"))
        set_bool(self.ignore_pokemon_var, settings.get("ignore_pokemon"))
        set_bool(self.ignore_pokecenter_var, settings.get("ignore_pokecenter"))
        set_bool(self.shiny_only_pokemon_var, settings.get("shiny_only_pokemon"))
        set_bool(self.start_shiny_filter_reroll_var, settings.get("start_shiny_filter_reroll"))
        set_bool(self.no_tm_move_tutor_var, settings.get("no_tm_move_tutor"))
        set_bool(self.boss_combat_item_swap_var, settings.get("boss_combat_item_swap"))
        set_bool(self.prioritize_party_fill_var, settings.get("prioritize_party_fill"))
        set_bool(self.delay_party_fill_var, settings.get("delay_party_fill_until_map3"))
        set_bool(self.smart_trait_choice_var, settings.get("smart_trait_choice"))
        set_var(self.type_whitelist_var, settings.get("pokemon_type_whitelist"))
        set_var(self.type_filter_mode_var, settings.get("pokemon_type_filter_mode"))
        set_var(self.whitelist_filter_mode_var, settings.get("pokemon_whitelist_mode"))
        set_var(self.generation_whitelist_var, settings.get("pokemon_generation_whitelist"))

        for attr, key in [
            ("starting_item_priority", "starting_item_priority"),
            ("regular_item_priority", "regular_item_priority"),
            ("combat_held_item_priority", "combat_held_item_priority"),
            ("starting_item_ignore", "starting_item_ignore"),
            ("regular_item_ignore", "regular_item_ignore"),
        ]:
            if key in settings:
                setattr(self, attr, list(settings.get(key) or []))
                changed = True
        if "regular_item_priority_by_starter" in settings:
            self.regular_item_priority_by_starter = dict(settings.get("regular_item_priority_by_starter") or {})
            changed = True
        self.merge_unknowns_into_ignore()
        self.merge_unknowns_into_regular_ignore()

        if update_runtime:
            mode = self.mode_var.get()
            if mode:
                self.current_mode = mode
            self.current_run_target = self.run_target_var.get()
            self.current_run_target_info = self.parse_run_target(self.current_run_target)
            self.current_tower = self.current_run_target_info.get("name", self.current_run_target)
            self.current_starter_name = (self.starter_var.get().strip() or STARTER_NAME).lower()
            self.current_manual_target_pokemon_list = self.parse_pokemon_target_list(self.target_pokemon_var.get())
            self.current_evolution_preference_list = self.parse_pokemon_target_list(self.evolution_preference_var.get())
            self.current_target_pokemon_list = self.build_current_pokemon_targets(self.current_manual_target_pokemon_list, [])
            self.current_target_pokemon = ", ".join(self.current_target_pokemon_list)
            self.current_item_reroll_targets = self.parse_item_target_list()
            self.current_item_reroll_target = ", ".join(self.current_item_reroll_targets)
            self.current_pokegold_farm_target = self.parse_pokegold_farm_target()
            self.current_shop_reroll_after_hit = self.shop_reroll_after_hit_var.get()
            if self.current_shop_reroll_after_hit not in SHOP_REROLL_AFTER_HIT_OPTIONS:
                self.current_shop_reroll_after_hit = SHOP_REROLL_AFTER_HIT_STOP
            self.current_ignore_pokemon = bool(self.ignore_pokemon_var.get())
            self.current_ignore_pokecenter = bool(self.ignore_pokecenter_var.get())
            self.current_shiny_only_pokemon = bool(self.shiny_only_pokemon_var.get())
            self.current_no_tm_move_tutor = bool(self.no_tm_move_tutor_var.get())
            self.current_prioritize_party_fill = bool(self.prioritize_party_fill_var.get())
            self.current_delay_party_fill = bool(self.delay_party_fill_var.get())
            self.current_type_whitelist = self.parse_type_whitelist(self.type_whitelist_var.get())
            self.current_type_filter_mode = (
                self.type_filter_mode_var.get()
                if self.type_filter_mode_var.get() in POKEMON_FILTER_OPTIONS
                else POKEMON_FILTER_PRIORITIZE
            )
            self.current_whitelist_filter_mode = (
                self.whitelist_filter_mode_var.get()
                if self.whitelist_filter_mode_var.get() in POKEMON_WHITELIST_OPTIONS
                else POKEMON_WHITELIST_ONLY
            )
            self.current_generation_whitelist = self.parse_generation_whitelist(self.generation_whitelist_var.get())
            self.current_type_filter_names = self.names_for_type_filters(self.current_type_whitelist)
            self.current_generation_filter_names = self.names_for_generation_filters(self.current_generation_whitelist)
        return changed

    def apply_active_schedule_target(self):
        step = self.active_schedule_step()
        if step and self.apply_task_settings_snapshot(step.get("settings"), update_runtime=True):
            label = step.get("name") or step.get("target") or "task"
            self.log(f"Schedule applied saved settings for: {label}.")
        target = self.active_schedule_target()
        starter = self.active_schedule_starter()
        changed = False
        if not target:
            return False
        if target != self.current_run_target:
            self.current_run_target = target
            self.run_target_var.set(target)
            self.current_run_target_info = self.parse_run_target(target)
            self.current_tower = self.current_run_target_info.get("name", target)
            self.log(f"Schedule switched to: {target}")
            changed = True
        if starter and starter != self.current_starter_name:
            self.current_starter_name = starter
            self.starter_var.set(starter.title())
            self.log(f"Schedule starter switched to: {starter.title()}")
            changed = True
        return changed

    def advance_schedule_after_shop_budget(self):
        if not self.current_shop_budget_schedule_active():
            return False
        step = self.active_schedule_step() or {}
        label = step.get("name") or step.get("target") or "shop task"
        config = self.current_shop_egg_config()
        wallet = self.last_wallet_pokegold_total
        wallet_text = f"{int(wallet):,}" if wallet is not None else "unknown"
        self.log(
            f"Schedule task {self.schedule_index + 1}/{len(self.task_schedule)} {label}: "
            f"wallet {wallet_text}, below one more {config['label']} ({config['expected_price']:,}); advancing."
        )
        self.schedule_index += 1
        self.schedule_result_signature = None
        if self.schedule_index >= len(self.task_schedule):
            self.set_status("Schedule done")
            self.log("Task schedule completed.")
            self.stop_event.set()
            return False
        self.apply_active_schedule_target()
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
        goal = self.normalize_schedule_goal(step.get("goal", SCHEDULE_COMPLETION_WINS))
        if goal == SCHEDULE_COMPLETION_FOREVER:
            label = step.get("name") or step.get("target")
            self.log(
                f"Schedule task {self.schedule_index + 1}/{len(self.task_schedule)} "
                f"{label}: forever task continuing."
            )
            return "continue"
        if goal == SCHEDULE_COMPLETION_SHOP_BUDGET:
            return "continue"
        if goal == SCHEDULE_COMPLETION_POKEGOLD:
            self.schedule_progress[self.schedule_index] += max(0, int(self.run_money_earned or 0))
        else:
            should_count = (
                goal == SCHEDULE_COMPLETION_ATTEMPTS
                or (goal in {SCHEDULE_COMPLETION_WINS, SCHEDULE_COMPLETION_CHALLENGE} and won)
            )
            if should_count:
                self.schedule_progress[self.schedule_index] += 1
        progress = self.schedule_progress[self.schedule_index]
        needed = int(step.get("count", 1))
        progress_text = f"{progress:,}/{needed:,}" if goal == SCHEDULE_COMPLETION_POKEGOLD else f"{progress}/{needed}"
        label = step.get("name") or step.get("target")
        self.log(
            f"Schedule task {self.schedule_index + 1}/{len(self.task_schedule)} "
            f"{label}: {progress_text} {goal.lower()}."
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
            if self.headless_var.get():
                self.close_existing_drivers_for_headless_launch()
            drivers = self.launch_missing_drivers(count)
            self.prepare_drivers_concurrently(drivers)
            if not self.headless_var.get():
                self.arrange_browser_windows(screen_w=screen_w, screen_h=screen_h)
            self.windows_arranged = True
            if self.headless_var.get():
                self.log(f"{count} headless browser(s) opened on PokeLike. Press Start Bot when ready.")
            else:
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

    def close_existing_drivers_for_headless_launch(self):
        with self.drivers_lock:
            drivers = list(self.worker_drivers)
            self.worker_drivers = []
        if self._driver and self._driver not in drivers:
            drivers.append(self._driver)
        for driver in drivers:
            try:
                driver.quit()
            except Exception:
                pass
        self._driver = None
        self._wait = None
        self.driver = None
        self.wait = None

    def parse_browser_count(self):
        try:
            count = int(str(self.browser_count_var.get()).strip())
        except Exception:
            count = 1
        return max(1, min(count, MAX_BROWSER_COUNT))

    def parse_pokegold_farm_target(self, value=None):
        raw = self.pokegold_farm_target_var.get() if value is None else value
        digits = "".join(ch for ch in str(raw or "") if ch.isdigit())
        if not digits:
            return 100000
        return max(1, min(int(digits), 999999999))

    def parse_chrome_restart_minutes(self):
        raw = str(self.chrome_restart_minutes_var.get()).strip().lower()
        if raw in ["", "0", "off", "none", "disabled"]:
            return 0.0
        try:
            minutes = float(raw.replace(",", "."))
        except Exception:
            minutes = 0.0
        return max(0.0, min(minutes, 1440.0))

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

    def shop_reroll_window_rect(self):
        try:
            screen_w = max(800, self.winfo_screenwidth())
            screen_h = max(600, self.winfo_screenheight() - 80)
        except Exception:
            screen_w, screen_h = 1920, 1000
        try:
            self.update_idletasks()
            app_x = max(0, int(self.winfo_rootx()))
            app_y = max(0, int(self.winfo_rooty()))
            app_w = max(560, int(self.winfo_width()))
            app_h = max(420, int(self.winfo_height()))
        except Exception:
            app_x, app_y, app_w, app_h = 0, 20, 900, 700
        width = min(max(560, app_w), screen_w)
        height = min(max(420, app_h), screen_h)
        right_x = app_x + app_w + 12
        if right_x + width <= screen_w:
            x = right_x
        else:
            x = max(0, min(app_x, screen_w - width))
        y = max(0, min(app_y, screen_h - height))
        return {"x": x, "y": y, "width": width, "height": height}

    def prepare_legendary_shop_seed_profile(self, window_rect=None):
        base_driver = None
        try:
            base_driver = self.launch_driver(
                worker_id=1,
                make_active=True,
                window_rect=window_rect,
            )
            self.thread_local.use_local = True
            self.driver = base_driver
            self.wait = WebDriverWait(base_driver, 20)
            self.prepare_page()
            if self.stop_if_cloud_save_conflict_visible(base_driver):
                raise RuntimeError("Cloud save conflict visible while loading the shop base profile.")
            self.ensure_home_screen_for_shop()
            self.record_wallet_gold_if_visible(base_driver)
            self.log("Legendary shop reroll: loaded the main profile at the home/shop screen.")
        finally:
            self.clear_thread_driver()
            if base_driver:
                try:
                    base_driver.quit()
                except Exception:
                    pass
                self.remove_driver_reference(base_driver)

        seed_path = self.legendary_shop_seed_profile_path()
        self.safe_replace_profile_copy(SELENIUM_PROFILE_PATH, seed_path)
        self.log(f"Legendary shop reroll: saved clean pre-buy profile seed at {seed_path}.")
        return seed_path

    def add_shop_hit_to_ignore_list(self, result):
        key = self.normalize_pokemon_name(
            (result or {}).get("key") or (result or {}).get("name")
        )
        if not key:
            return ""
        current = self.parse_pokemon_target_list(self.shop_ignore_pokemon_var.get())
        if key not in current:
            current.append(key)
            text = ", ".join(name.title() for name in current)
            self.shop_ignore_pokemon_var.set(text)
            self.current_shop_ignore_pokemon_list = current
            step = self.active_schedule_step()
            if isinstance(step, dict):
                settings = step.get("settings")
                if isinstance(settings, dict) and settings.get("mode") in {MODE_SHINY_SHOP_REROLL, MODE_LEGENDARY_SHOP_REROLL}:
                    settings["shop_ignore_pokemon"] = text
            self.save_settings()
            self.log(f"Legendary shop reroll: added {key.title()} to the shop ignore list.")
        else:
            self.current_shop_ignore_pokemon_list = current
            self.log(f"Legendary shop reroll: {key.title()} is already on the shop ignore list.")
        return key

    def sync_uploaded_shop_hit_to_base_profile(self, driver, attempt_path):
        if not attempt_path or not os.path.isdir(attempt_path):
            self.log("Legendary shop reroll: cannot continue; uploaded hit profile path is missing.")
            return False
        try:
            driver.quit()
        except Exception:
            pass
        self.remove_driver_reference(driver)
        if self._driver is driver:
            self._driver = None
            self._wait = None
        if self.driver is driver:
            self.driver = None
            self.wait = None
        if self.winning_driver is driver:
            self.winning_driver = None
        time.sleep(0.5)
        try:
            self.safe_replace_profile_copy(attempt_path, SELENIUM_PROFILE_PATH)
        except Exception as exc:
            self.log(f"Legendary shop reroll: could not make uploaded hit the new shop base ({exc}).")
            return False
        self.log("Legendary shop reroll: uploaded hit profile is now the new shop base.")
        return True

    def play_post_shop_hit_safety_run(self, driver, hit_name, run_token=None):
        key = self.normalize_pokemon_name(hit_name)
        if not key:
            self.log("Legendary shop reroll: cannot run post-hit safety run; hit name is missing.")
            return False
        if not self.is_active_bot_run_token(run_token):
            return False
        saved_state = {
            "mode": self.current_mode,
            "run_target": self.current_run_target,
            "run_target_info": dict(self.current_run_target_info or {}),
            "tower": self.current_tower,
            "starter": self.current_starter_name,
            "dex_target_mode": self.current_dex_target_mode,
            "manual_first_attempt": self.manual_first_attempt,
            "shop_post_hit_safety_run_active": self.shop_post_hit_safety_run_active,
        }
        try:
            self.shop_post_hit_safety_run_active = True
            self.current_mode = MODE_FULL_RUN
            self.current_dex_target_mode = DEX_TARGET_OFF
            self.manual_first_attempt = False
            self.current_run_target = RUN_TARGET_CHALLENGE
            self.current_run_target_info = self.parse_run_target(RUN_TARGET_CHALLENGE)
            self.current_tower = "Challenge Mode"
            self.current_starter_name = key
            self.driver = driver
            self.wait = WebDriverWait(driver, 30)
            self.set_status("Post-hit safety run")
            self.log(
                f"Legendary shop reroll: playing Challenge Mode safety runs for up to "
                f"5 minutes or {SHOP_REROLL_POST_HIT_MAX_TRIES} try/tries, whichever comes first, "
                f"with {key.title()} as starter before the second cloud upload."
            )
            tries_started = 1
            self.reset_run_tracking(prefix="Post-hit ")
            self.start_challenge_run()
            self.log(f"Legendary shop reroll: post-hit safety try {tries_started}/{SHOP_REROLL_POST_HIT_MAX_TRIES} started.")
            deadline = time.time() + SHOP_REROLL_POST_HIT_RUN_SECONDS
            last_log_at = 0
            while (
                not self.stop_event.is_set()
                and time.time() < deadline
                and tries_started <= SHOP_REROLL_POST_HIT_MAX_TRIES
            ):
                if not self.is_active_bot_run_token(run_token):
                    return False
                if self.stop_if_cloud_save_conflict_visible(driver):
                    return False
                try:
                    completed = self.handle_active_screen()
                except Exception as exc:
                    self.log(f"Legendary shop reroll: post-hit safety run handler failed ({exc}).")
                    return False
                if self.stop_event.is_set():
                    return False
                if completed:
                    self.log(
                        f"Legendary shop reroll: post-hit safety try "
                        f"{tries_started}/{SHOP_REROLL_POST_HIT_MAX_TRIES} ended."
                    )
                    if tries_started >= SHOP_REROLL_POST_HIT_MAX_TRIES or time.time() >= deadline:
                        break
                    tries_started += 1
                    self.reset_run_tracking(prefix="Post-hit ")
                    self.start_challenge_run()
                    self.log(
                        f"Legendary shop reroll: post-hit safety try "
                        f"{tries_started}/{SHOP_REROLL_POST_HIT_MAX_TRIES} started."
                    )
                    continue
                now = time.time()
                if now - last_log_at >= 60:
                    remaining = max(0, int(deadline - now))
                    self.log(
                        f"Legendary shop reroll: post-hit safety run active; "
                        f"{remaining}s or {SHOP_REROLL_POST_HIT_MAX_TRIES - tries_started + 1} try/tries until second upload."
                    )
                    last_log_at = now
            if self.stop_event.is_set():
                return False
            if not self.is_active_bot_run_token(run_token):
                return False
            self.set_status("Post-hit upload")
            self.log("Legendary shop reroll: post-hit safety run finished; force-uploading cloud save again.")
            return self.force_upload_shop_hit(driver)
        finally:
            self.current_mode = saved_state["mode"]
            self.current_run_target = saved_state["run_target"]
            self.current_run_target_info = saved_state["run_target_info"]
            self.current_tower = saved_state["tower"]
            self.current_starter_name = saved_state["starter"]
            self.current_dex_target_mode = saved_state["dex_target_mode"]
            self.manual_first_attempt = saved_state["manual_first_attempt"]
            self.shop_post_hit_safety_run_active = saved_state["shop_post_hit_safety_run_active"]

    def install_legendary_shop_cloud_guard(self, driver):
        script = r"""
(() => {
    if (window.__pokelikeBotCloudGuardInstalled) return;
    window.__pokelikeBotCloudGuardInstalled = true;
    window.__pokelikeBotAllowCloudUpload = false;
    const blockedTerms = [
        'cloud', 'sync', 'save', 'upload', 'account-force-upload',
        'force-upload', 'save-data', 'savedata'
    ];
    const methodWrites = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);
    const urlText = (input) => {
        try {
            if (typeof input === 'string') return input;
            if (input && input.url) return input.url;
        } catch (e) {}
        return '';
    };
    const shouldBlock = (method, url, body) => {
        if (window.__pokelikeBotAllowCloudUpload) return false;
        const verb = String(method || 'GET').toUpperCase();
        const haystack = `${url || ''} ${body || ''}`.toLowerCase();
        return methodWrites.has(verb) && blockedTerms.some(term => haystack.includes(term));
    };
    const fakeResponse = () => new Response(JSON.stringify({ ok: true, blockedByPokeLikeBot: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
    });
    const originalFetch = window.fetch;
    if (typeof originalFetch === 'function') {
        window.fetch = function(input, init) {
            const method = (init && init.method) || (input && input.method) || 'GET';
            const body = init && init.body;
            const url = urlText(input);
            if (shouldBlock(method, url, body)) {
                console.warn('[PokeLike Bot] blocked automatic cloud save request', method, url);
                return Promise.resolve(fakeResponse());
            }
            return originalFetch.apply(this, arguments);
        };
    }
    const originalBeacon = navigator.sendBeacon && navigator.sendBeacon.bind(navigator);
    if (originalBeacon) {
        navigator.sendBeacon = function(url, data) {
            if (shouldBlock('POST', url, data)) {
                console.warn('[PokeLike Bot] blocked automatic cloud save beacon', url);
                return true;
            }
            return originalBeacon(url, data);
        };
    }
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url) {
        this.__pokelikeBotMethod = method || 'GET';
        this.__pokelikeBotUrl = url || '';
        return originalOpen.apply(this, arguments);
    };
    XMLHttpRequest.prototype.send = function(body) {
        if (shouldBlock(this.__pokelikeBotMethod, this.__pokelikeBotUrl, body)) {
            console.warn('[PokeLike Bot] blocked automatic cloud save XHR', this.__pokelikeBotMethod, this.__pokelikeBotUrl);
            try {
                Object.defineProperty(this, 'readyState', { value: 4, configurable: true });
                Object.defineProperty(this, 'status', { value: 200, configurable: true });
                Object.defineProperty(this, 'responseText', { value: '{"ok":true,"blockedByPokeLikeBot":true}', configurable: true });
                if (typeof this.onreadystatechange === 'function') this.onreadystatechange();
                if (typeof this.onload === 'function') this.onload();
            } catch (e) {}
            return;
        }
        return originalSend.apply(this, arguments);
    };
})();
"""
        try:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script})
            driver.execute_script(script)
        except Exception as exc:
            self.log(f"Legendary shop reroll: could not install cloud-upload guard: {exc}")

    def enable_legendary_shop_network_guard(self, driver):
        try:
            driver.execute_cdp_cmd("Network.enable", {})
            driver.execute_cdp_cmd("Network.setBlockedURLs", {
                "urls": [
                    "*cloud*",
                    "*sync*",
                    "*upload*",
                    "*save-data*",
                    "*savedata*",
                    "*force-upload*",
                ]
            })
            self.log("Legendary shop reroll: enabled network block for cloud/save upload URLs.")
        except Exception as exc:
            self.log(f"Legendary shop reroll: could not enable network cloud guard: {exc}")

    def disable_legendary_shop_network_guard(self, driver=None):
        try:
            (driver or self.driver).execute_cdp_cmd("Network.setBlockedURLs", {"urls": []})
        except Exception:
            pass

    def reset_legendary_shop_attempt_profile(self, seed_path, slot=None, attempt_id=None):
        attempt_path = self.legendary_shop_attempt_profile_path(slot=slot, attempt_id=attempt_id)
        self.safe_replace_profile_copy(seed_path, attempt_path)
        return attempt_path

    def preserve_legendary_shop_hit_profile(self, attempt_path, result):
        name = self.normalize_pokemon_name((result or {}).get("name") or (result or {}).get("key") or "legendary")
        shiny_label = "shiny" if (result or {}).get("shiny") else "normal"
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        target_path = f"{SELENIUM_PROFILE_PATH}-shop-hit-{timestamp}-{shiny_label}-{name or 'pokemon'}"
        try:
            self.safe_replace_profile_copy(attempt_path, target_path)
            self.log(f"Legendary shop reroll: preserved hit Chrome profile at {target_path}.")
        except Exception as exc:
            self.log(f"Legendary shop reroll: could not preserve hit Chrome profile: {exc}")
        return target_path

    def prepare_shop_attempt_browser(self, seed_path, slot, window_rect=None, attempt_id=None, run_token=None):
        attempt_path = self.reset_legendary_shop_attempt_profile(seed_path, slot=slot, attempt_id=attempt_id)
        worker_id = 1000 + int(attempt_id) if attempt_id is not None else 100 + int(slot)
        driver = None
        try:
            if not self.is_active_bot_run_token(run_token):
                self.cleanup_shop_attempt_profile(attempt_path)
                return None
            driver = self.launch_driver(
                worker_id=worker_id,
                make_active=True,
                profile_path_override=attempt_path,
                allow_reconnect=False,
                window_rect=window_rect,
            )
            if self.winning_driver is not None and driver is not self.winning_driver:
                self.close_shop_attempt_driver(driver, attempt_path)
                return None
            self.install_legendary_shop_cloud_guard(driver)
            self.thread_local.use_local = True
            self.thread_local.worker_id = worker_id
            self.driver = driver
            self.wait = WebDriverWait(driver, 20)
            self.prepare_page(cookie_timeout=0.25)
            if not self.is_active_bot_run_token(run_token):
                self.close_shop_attempt_driver(driver, attempt_path)
                return None
            self.ensure_home_screen_for_shop()
            self.ensure_legendary_shop_buy_ready(driver, timeout=10.0)
            if not self.is_active_bot_run_token(run_token):
                self.close_shop_attempt_driver(driver, attempt_path)
                return None
            self.enable_legendary_shop_network_guard(driver)
            if self.stop_event.is_set() or (self.winning_driver is not None and driver is not self.winning_driver):
                self.close_shop_attempt_driver(driver, attempt_path)
                return None
            return {
                "driver": driver,
                "attempt_path": attempt_path,
                "slot": slot,
                "worker_id": worker_id,
            }
        except Exception as exc:
            self.log(f"Legendary shop reroll: discarded failed prepared browser in slot {slot} ({exc}).")
            if driver is not None:
                self.close_shop_attempt_driver(driver, attempt_path)
            else:
                self.cleanup_shop_attempt_profile(attempt_path)
            return None
        finally:
            self.clear_thread_driver()

    def ensure_home_screen_for_shop(self):
        if not self.driver.current_url.startswith(POKELIKE_URL):
            self.prepare_page()
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
                el.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                el.click();
                el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            };
            const activeId = document.querySelector('.screen.active')?.id || '';
            if (activeId && !document.body.classList.contains('run-menu-in-run')) {
                return {ok: true, screen: activeId, alreadyHome: true};
            }
            const home = [...document.querySelectorAll('button, [role="button"]')]
                .filter(visible)
                .find(btn => {
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    const label = (btn.getAttribute('aria-label') || '').toLowerCase();
                    const menu = (btn.dataset?.menu || '').toLowerCase();
                    return menu === 'home' || label === 'home' || text === 'home';
                });
            if (!home && typeof window.goHomeFromMenu === 'function') {
                window.goHomeFromMenu();
                return {ok: true, method: 'function', screen: activeId};
            }
            if (!home) return {ok: false, screen: activeId};
            click(home);
            return {ok: true, method: 'button', screen: activeId};
            """
        )
        if not result.get("ok"):
            raise RuntimeError(f"Could not reach home screen for shop; current screen={result.get('screen') or 'unknown'}")
        if not result.get("alreadyHome"):
            try:
                WebDriverWait(self.driver, 1.2, poll_frequency=0.05).until(
                    lambda _: self.driver.execute_script(
                        """
                        const activeId = document.querySelector('.screen.active')?.id || '';
                        return !!activeId && !document.body.classList.contains('run-menu-in-run');
                        """
                    )
                )
            except Exception:
                time.sleep(0.15)
        return True

    def ensure_legendary_shop_buy_ready(self, driver=None, timeout=8.0):
        target_driver = driver or self.driver
        config = self.current_shop_egg_config()
        try:
            target_driver.execute_script(
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
                    if (!el) return false;
                    el.scrollIntoView({block: 'center', inline: 'center'});
                    el.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                    el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                    el.click();
                    el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                    el.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
                    return true;
                };
                if (typeof window.openShopModal === 'function') {
                    window.openShopModal();
                    return true;
                }
                const btn = [...document.querySelectorAll('button, [role="button"]')]
                    .filter(visible)
                    .find(el => {
                        const text = (el.innerText || el.textContent || '').toLowerCase();
                        const label = (el.getAttribute('aria-label') || el.dataset?.tip || '').toLowerCase();
                        const html = (el.outerHTML || '').toLowerCase();
                        return label.includes('mart') || text.includes('mart') || html.includes('pokemart');
                    });
                return click(btn);
                """
            )
        except Exception:
            pass

        def shop_ready(_):
            try:
                return target_driver.execute_script(
                    """
                    const eggType = arguments[0];
                    const visible = (el) => {
                        if (!el) return false;
                        const rect = el.getBoundingClientRect();
                        const style = getComputedStyle(el);
                        return rect.width > 0 && rect.height > 0
                            && style.display !== 'none'
                            && style.visibility !== 'hidden';
                    };
                    const buy = document.querySelector(`button.mart-buy[data-egg="${eggType}"], .mart-buy[data-egg="${eggType}"]`);
                    if (!visible(buy)) return false;
                    const wallet = [...document.querySelectorAll('.mart-wallet .mart-wallet-amount, .mart-wallet-amount')]
                        .filter(visible)[0];
                    return {
                        ready: true,
                        walletText: wallet ? (wallet.innerText || wallet.textContent || '').replace(/\\s+/g, ' ').trim() : ''
                    };
                    """,
                    config["egg_type"],
                )
            except Exception:
                return False

        result = WebDriverWait(target_driver, timeout, poll_frequency=0.05).until(shop_ready)
        wallet_text = result.get("walletText") if isinstance(result, dict) else ""
        if wallet_text:
            amount = int("".join(ch for ch in wallet_text if ch.isdigit()) or "0")
            if amount > 0 and self.last_wallet_pokegold_total != amount:
                self.last_wallet_pokegold_total = amount
                self.update_stats_labels()
                self.log(f"Gold wallet detected: {amount:,} (mart-wallet ready: {wallet_text}).")
        return True

    def focus_shop_purchase_browser(self, driver=None):
        target_driver = driver or self.driver
        if not target_driver:
            return False
        try:
            target_driver.execute_cdp_cmd("Page.bringToFront", {})
        except Exception:
            pass
        try:
            target_driver.execute_script("window.focus();")
        except Exception:
            pass
        try:
            rect = target_driver.get_window_rect()
            target_driver.set_window_rect(
                x=int(rect.get("x", 0)),
                y=int(rect.get("y", 0)),
                width=max(120, int(rect.get("width", 900))),
                height=max(120, int(rect.get("height", 700))),
            )
        except Exception:
            pass
        return True

    def click_legendary_shop_buy(self, allow_unavailable=False):
        config = self.current_shop_egg_config()
        self.ensure_legendary_shop_buy_ready(timeout=8.0)
        self.focus_shop_purchase_browser()
        result = self.driver.execute_script(
            """
            const eggType = arguments[0];
            const expectedPrice = arguments[1];
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
                el.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                el.click();
                el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            };
            const normalizeMoney = (text) => parseInt(String(text || '').replace(/[^0-9]/g, ''), 10) || 0;
            const readWallet = () => {
                const wallet = [...document.querySelectorAll('.mart-wallet .mart-wallet-amount, .mart-wallet-amount')]
                    .filter(visible)[0];
                if (!wallet) return {walletAmount: 0, walletText: ''};
                const walletText = (wallet.innerText || wallet.textContent || '').replace(/\\s+/g, ' ').trim();
                return {walletAmount: normalizeMoney(walletText), walletText};
            };
            const openShop = () => {
                if (typeof window.openShopModal === 'function') {
                    window.openShopModal();
                    return true;
                }
                const btn = [...document.querySelectorAll('button, [role="button"]')]
                    .filter(visible)
                    .find(el => {
                        const text = (el.innerText || el.textContent || '').toLowerCase();
                        const label = (el.getAttribute('aria-label') || el.dataset?.tip || '').toLowerCase();
                        const html = (el.outerHTML || '').toLowerCase();
                        return label.includes('mart') || text.includes('mart') || html.includes('pokemart');
                    });
                if (!btn) return false;
                click(btn);
                return true;
            };
            openShop();
            const started = Date.now();
            while (Date.now() - started < 2500) {
                const exactBuy = document.querySelector(`button.mart-buy[data-egg="${eggType}"], .mart-buy[data-egg="${eggType}"]`);
                const buy = exactBuy && visible(exactBuy) ? exactBuy : [...document.querySelectorAll('button.mart-buy, .mart-buy, button')]
                    .filter(visible)
                    .find(btn => {
                        const text = (btn.innerText || btn.textContent || '').toLowerCase();
                        const egg = (btn.dataset?.egg || '').toLowerCase();
                        return egg === eggType
                            || (text.includes('buy') && text.includes(expectedPrice.toLocaleString('de-DE')))
                            || (text.includes('buy') && text.includes(String(expectedPrice)) && text.includes(eggType));
                    });
                if (buy) {
                    const text = buy.innerText || buy.textContent || '';
                    const price = normalizeMoney(text);
                    const wallet = readWallet();
                    if (price && price !== expectedPrice) return {clicked: false, reason: `unexpected price ${price}`, text, ...wallet};
                    if (buy.disabled || buy.getAttribute('aria-disabled') === 'true') {
                        return {clicked: false, reason: `${eggType} buy button disabled`, text, ...wallet};
                    }
                    const eggBlock = buy.closest('.mart-egg') || buy.parentElement;
                    const desc = eggBlock ? eggBlock.querySelector('.mart-egg-desc') : null;
                    const descText = desc ? (desc.innerText || desc.textContent || '') : '';
                    const rateMatch = descText.match(/([0-9]+(?:[.,][0-9]+)?\\s*%)(?:\\s+chance\\s+to\\s+be\\s+shiny)?/i)
                        || descText.match(/now\\s+([0-9]+(?:[.,][0-9]+)?\\s*%)/i);
                    const shinyRate = rateMatch ? rateMatch[1].replace(',', '.') : '';
                    click(buy);
                    return {clicked: true, text, price, shinyRate, descText, ...wallet};
                }
            }
            return {clicked: false, reason: `${eggType} buy button not found`};
            """,
            config["egg_type"],
            config["expected_price"],
        )
        wallet_amount = int(result.get("walletAmount") or 0)
        if wallet_amount > 0:
            if self.last_wallet_pokegold_total != wallet_amount:
                self.last_wallet_pokegold_total = wallet_amount
                self.update_stats_labels()
                self.log(
                    f"Gold wallet detected: {wallet_amount:,} "
                    f"(mart-wallet before buy: {result.get('walletText') or ''})."
                )
        if not result.get("clicked"):
            if allow_unavailable:
                self.log(f"{config['mode_label']}: cannot buy more {config['label']} ({result.get('reason') or 'unavailable'}).")
                return False
            raise RuntimeError(f"Could not buy {config['label']}: {result.get('reason') or 'unknown'}")
        if result.get("shinyRate"):
            self.update_shop_shiny_rate(result.get("shinyRate"))
        self.log(f"{config['mode_label']}: clicked buy ({result.get('text') or config['label']}).")
        time.sleep(0.12)
        return True

    def legendary_shop_party_summary(self):
        result = self.driver.execute_script(
            """
            const normalize = (text) => String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const visible = (el) => {
                if (!el) return false;
                const rect = el.getBoundingClientRect();
                const style = getComputedStyle(el);
                return rect.width > 0 && rect.height > 0
                    && style.display !== 'none'
                    && style.visibility !== 'hidden';
            };
            const roots = ['#team-bar', '#catch-team-bar', '#item-team-bar', '#passive-team-bar', '#gameover-team', '#win-team'];
            const cards = roots.flatMap(selector => [...document.querySelectorAll(`${selector} .team-slot, ${selector} .poke-card`)])
                .filter(visible);
            const slots = cards.map((card, index) => {
                const img = card.querySelector('img');
                const src = img?.src || '';
                const name = (
                    card.querySelector('.team-slot-name, .poke-name, .dex-name')?.innerText
                    || img?.getAttribute('alt')
                    || card.innerText
                    || ''
                ).trim().replace(/\\s+/g, ' ').slice(0, 80);
                const text = (card.innerText || card.textContent || '').toLowerCase();
                const shiny = card.classList.contains('pc-dex-card--shiny')
                    || card.classList.contains('shiny')
                    || !!card.querySelector('.pc-shiny-star, .shiny-star')
                    || src.includes('/shiny/')
                    || text.includes('shiny');
                return {index, name, key: normalize(name), shiny, src};
            }).filter(slot => slot.key);
            return {count: slots.length, slots};
            """
        )
        return result if isinstance(result, dict) else {"count": 0, "slots": []}

    def legendary_shop_visible_result_cards(self):
        result = self.driver.execute_script(
            """
            const normalize = (text) => String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const visible = (el) => {
                if (!el) return false;
                const rect = el.getBoundingClientRect();
                const style = getComputedStyle(el);
                return rect.width > 0 && rect.height > 0
                    && style.display !== 'none'
                    && style.visibility !== 'hidden';
            };
            const shopRoots = [...document.querySelectorAll(
                '[id*="shop" i], [class*="shop" i], [id*="mart" i], [class*="mart" i], [role="dialog"], .modal, .modal-content'
            )].filter(visible);
            if (!shopRoots.length) return [];
            const cards = shopRoots.flatMap(root => [...root.querySelectorAll('.poke-card, .dex-card, [class*="pokemon" i]')])
                .filter(visible)
                .map((card, index) => {
                    const img = card.querySelector('img');
                    const src = img?.src || '';
                    const name = (
                        card.querySelector('.poke-name, .dex-name, .team-slot-name, [class*="name" i]')?.innerText
                        || img?.getAttribute('alt')
                        || card.innerText
                        || ''
                    ).trim().replace(/\\s+/g, ' ').slice(0, 80);
                    const text = (card.innerText || card.textContent || '').toLowerCase();
                    const shiny = card.classList.contains('pc-dex-card--shiny')
                        || card.classList.contains('shiny')
                        || !!card.querySelector('.pc-shiny-star, .shiny-star')
                        || src.includes('/shiny/')
                        || text.includes('shiny');
                    return {index, name, key: normalize(name), shiny, src, text: text.slice(0, 240)};
                })
                .filter(card => card.key);
            return cards;
            """
        )
        return result if isinstance(result, list) else []

    def legendary_shop_egg_result(self):
        result = self.driver.execute_script(
            """
            const normalize = (text) => String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const visible = (el) => {
                if (!el) return false;
                const rect = el.getBoundingClientRect();
                const style = getComputedStyle(el);
                return rect.width > 0 && rect.height > 0
                    && style.display !== 'none'
                    && style.visibility !== 'hidden';
            };
            const overlay = document.querySelector('#egg-overlay');
            if (!overlay || !visible(overlay)) return {found: false};
            const sprite = overlay.querySelector('.egg-reveal-sprite.egg-revealed, .egg-reveal-sprite');
            const rawName = (
                overlay.querySelector('.egg-result .egg-name')?.innerText
                || overlay.querySelector('.egg-name')?.innerText
                || sprite?.getAttribute('alt')
                || ''
            ).replace(/[★✨]/g, '').trim().replace(/\\s+/g, ' ');
            const src = sprite?.src || sprite?.getAttribute('src') || '';
            const dexMatch = String(src || '').match(/\\/(\\d+)\\.png(?:$|[?#])/);
            const shiny = !!sprite && (
                sprite.classList.contains('shiny')
                || src.includes('/shiny/')
                || /[★☆✨✦✧]/.test(overlay.innerText || '')
                || (overlay.innerText || '').toLowerCase().includes('shiny')
            );
            const duplicateText = overlay.querySelector('.egg-dup')?.innerText || '';
            return {
                found: (!!rawName || (sprite && sprite.classList.contains('egg-revealed'))) && (!!sprite || !!rawName),
                name: rawName,
                key: normalize(rawName),
                shiny,
                src,
                dex: dexMatch ? dexMatch[1] : '',
                duplicateText,
                spriteClasses: sprite ? [...sprite.classList].join(' ') : '',
                text: (overlay.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 240)
            };
            """
        )
        if not isinstance(result, dict):
            return {"found": False}
        shiny_mark_codes = {0x2605, 0x2606, 0x2728, 0x2726, 0x2727}

        def has_shiny_mark(value):
            return any(ord(ch) in shiny_mark_codes for ch in str(value or ""))

        def strip_shiny_marks(value):
            return "".join(ch for ch in str(value or "") if ord(ch) not in shiny_mark_codes).strip()

        if has_shiny_mark(result.get("name")) or has_shiny_mark(result.get("text")):
            result["shiny"] = True
            result["shinyEvidence"] = result.get("shinyEvidence") or "sparkle"
        if result.get("shiny") and not result.get("shinyEvidence"):
            src = str(result.get("src") or "").lower()
            classes = str(result.get("spriteClasses") or "").lower()
            text = str(result.get("text") or "").lower()
            if "shiny" in classes:
                result["shinyEvidence"] = "class"
            elif "/shiny/" in src:
                result["shinyEvidence"] = "src"
            elif "shiny" in text:
                result["shinyEvidence"] = "text"
            else:
                result["shinyEvidence"] = "unknown"
        if result.get("name"):
            result["name"] = strip_shiny_marks(result.get("name"))
            result["key"] = self.normalize_pokemon_name(result.get("name"))
        return result

    def shop_reroll_is_hit(self, name, shiny):
        if not shiny:
            return False
        name_key = self.normalize_pokemon_name(name)
        ignored = set(getattr(self, "current_shop_ignore_pokemon_list", []) or [])
        if name_key and name_key in ignored:
            return False
        target_names = set(getattr(self, "current_target_pokemon_list", []) or [])
        if not target_names:
            return True
        return bool(name_key and name_key in target_names)

    def legendary_shop_result_after_buy(self, before_party):
        before_slots = before_party.get("slots", []) if isinstance(before_party, dict) else []
        before_signature_counts = {}
        for slot in before_slots:
            key = f"{slot.get('key') or self.normalize_pokemon_name(slot.get('name'))}:{bool(slot.get('shiny'))}"
            before_signature_counts[key] = before_signature_counts.get(key, 0) + 1
        deadline = time.time() + 3.0
        last_party = {"count": 0, "slots": []}
        while time.time() < deadline:
            egg_result = self.legendary_shop_egg_result()
            if egg_result.get("found"):
                name_key = self.normalize_pokemon_name(egg_result.get("name") or egg_result.get("key"))
                hit = self.shop_reroll_is_hit(name_key, bool(egg_result.get("shiny")))
                return {
                    "found": True,
                    "hit": hit,
                    "name": (
                        egg_result.get("name")
                        or (f"Dex #{egg_result.get('dex')}" if egg_result.get("dex") else "Pokemon")
                    ),
                    "key": name_key,
                    "shiny": bool(egg_result.get("shiny")),
                    "dex": egg_result.get("dex") or "",
                    "duplicateText": egg_result.get("duplicateText") or "",
                    "shinyEvidence": egg_result.get("shinyEvidence") or "",
                    "party": last_party,
                }
            party = self.legendary_shop_party_summary()
            last_party = party
            slots = party.get("slots", []) if isinstance(party, dict) else []
            after_counts = {}
            new_slots = []
            for slot in slots:
                key = f"{slot.get('key') or self.normalize_pokemon_name(slot.get('name'))}:{bool(slot.get('shiny'))}"
                after_counts[key] = after_counts.get(key, 0) + 1
                if after_counts[key] > before_signature_counts.get(key, 0):
                    new_slots.append(slot)
            if new_slots:
                candidate = new_slots[-1]
                name_key = self.normalize_pokemon_name(candidate.get("name") or candidate.get("key"))
                hit = self.shop_reroll_is_hit(name_key, bool(candidate.get("shiny")))
                return {
                    "found": True,
                    "hit": hit,
                    "name": candidate.get("name") or name_key.title(),
                    "key": name_key,
                    "shiny": bool(candidate.get("shiny")),
                    "party": party,
                }
            result_cards = self.legendary_shop_visible_result_cards()
            if result_cards:
                candidate = result_cards[-1]
                name_key = self.normalize_pokemon_name(candidate.get("name") or candidate.get("key"))
                hit = self.shop_reroll_is_hit(name_key, bool(candidate.get("shiny")))
                if candidate.get("shiny") or name_key in set(getattr(self, "current_target_pokemon_list", []) or []):
                    return {
                        "found": True,
                        "hit": hit,
                        "name": candidate.get("name") or name_key.title(),
                        "key": name_key,
                        "shiny": bool(candidate.get("shiny")),
                        "party": party,
                    }
            time.sleep(0.08)
        slots = last_party.get("slots", []) if isinstance(last_party, dict) else []
        candidate = slots[-1] if slots else {}
        name_key = self.normalize_pokemon_name(candidate.get("name") or candidate.get("key"))
        return {
            "found": bool(candidate),
            "hit": self.shop_reroll_is_hit(name_key, bool(candidate.get("shiny"))),
            "name": candidate.get("name") or name_key.title() if candidate else "",
            "key": name_key,
            "shiny": bool(candidate.get("shiny")),
            "party": last_party,
        }

    def accept_force_upload_confirmation(self, driver, timeout=5.0, action_label="force-upload"):
        deadline = time.time() + float(timeout)
        last_exc = None
        while time.time() < deadline:
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                alert.accept()
                self.log(f"Legendary shop reroll: accepted {action_label} confirmation ({alert_text}).")
                return True
            except Exception as exc:
                last_exc = exc
                try:
                    alert = WebDriverWait(driver, 0.5).until(EC.alert_is_present())
                    alert_text = alert.text
                    alert.accept()
                    self.log(f"Legendary shop reroll: accepted {action_label} confirmation ({alert_text}).")
                    return True
                except Exception as wait_exc:
                    last_exc = wait_exc
                    time.sleep(0.1)
        self.log(f"Legendary shop reroll: {action_label} confirmation was not available ({last_exc}).")
        return False

    def dismiss_shop_egg_result_overlay(self, driver=None):
        target_driver = driver or self.driver
        try:
            result = target_driver.execute_script(
                """
                const visible = (el) => {
                    if (!el) return false;
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0
                        && style.display !== 'none'
                        && style.visibility !== 'hidden';
                };
                const sprite = [...document.querySelectorAll(
                    'img.egg-reveal-sprite.egg-revealed, .egg-reveal-sprite.egg-revealed, #egg-overlay img'
                )].find(visible);
                const overlay = document.querySelector('#egg-overlay');
                if (!sprite && !visible(overlay)) return {clicked: false, reason: 'no egg reveal'};
                const target = sprite || overlay;
                target.scrollIntoView({block: 'center', inline: 'center'});
                const rect = target.getBoundingClientRect();
                const x = Math.floor(rect.left + rect.width / 2);
                const y = Math.floor(rect.top + rect.height / 2);
                for (const type of ['pointerdown', 'mousedown', 'mouseup', 'pointerup', 'click']) {
                    target.dispatchEvent(new MouseEvent(type, {
                        bubbles: true,
                        cancelable: true,
                        clientX: x,
                        clientY: y,
                        screenX: x,
                        screenY: y,
                        button: 0,
                    }));
                }
                return {clicked: true, target: sprite ? 'egg reveal sprite' : 'egg overlay'};
                """
            )
        except Exception as exc:
            self.log(f"Legendary shop reroll: could not dismiss egg result overlay ({exc}).")
            return False
        if isinstance(result, dict) and result.get("clicked"):
            self.log(f"Legendary shop reroll: clicked {result.get('target') or 'egg reveal'} before force upload.")
            time.sleep(0.4)
            return True
        return False

    def dismiss_pending_pokemon_reward_before_force_upload(self, driver=None):
        target_driver = driver or self.driver
        if not target_driver:
            return False
        clicked_any = False
        for _ in range(8):
            if self.stop_if_cloud_save_conflict_visible(target_driver):
                return False
            try:
                result = target_driver.execute_script(
                    """
                    const visible = (el) => {
                        if (!el) return false;
                        const rect = el.getBoundingClientRect();
                        const style = getComputedStyle(el);
                        return rect.width > 0 && rect.height > 0
                            && style.display !== 'none'
                            && style.visibility !== 'hidden';
                    };
                    const normalize = (text) => String(text || '').toLowerCase().replace(/\\s+/g, ' ').trim();
                    const click = (el) => {
                        if (!el) return false;
                        el.scrollIntoView({block: 'center', inline: 'center'});
                        const rect = el.getBoundingClientRect();
                        const x = Math.max(1, rect.left + rect.width / 2);
                        const y = Math.max(1, rect.top + rect.height / 2);
                        const target = document.elementFromPoint(x, y) || el;
                        for (const node of [...new Set([target, el])]) {
                            node.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true, cancelable: true, clientX: x, clientY: y}));
                            node.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, clientX: x, clientY: y}));
                            node.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, clientX: x, clientY: y}));
                            node.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, clientX: x, clientY: y}));
                            node.dispatchEvent(new MouseEvent('pointerup', {bubbles: true, cancelable: true, clientX: x, clientY: y}));
                        }
                        if (typeof el.click === 'function') el.click();
                        return true;
                    };
                    const active = document.querySelector('.screen.active') || document.body;
                    const activeId = active?.id || '';
                    const buttons = [...active.querySelectorAll('button, [role="button"], .btn-primary, .btn-secondary, [onclick]')]
                        .filter(visible);
                    const action = buttons.find(btn => {
                        const text = normalize(`${btn.innerText || btn.textContent || ''} ${btn.getAttribute('aria-label') || ''} ${btn.title || ''}`);
                        const id = normalize(btn.id || '');
                        return id === 'btn-take-shiny'
                            || id === 'btn-add-to-team'
                            || (text.includes('add ') && text.includes(' to team'))
                            || text.includes('take this pokemon')
                            || text.includes('take this pok')
                            || text.includes('take pokemon')
                            || /^take .+!$/.test(text);
                    });
                    if (action) {
                        click(action);
                        return {
                            clicked: true,
                            target: normalize(action.innerText || action.textContent || action.getAttribute('aria-label') || action.title || 'pokemon reward action'),
                            screen: activeId
                        };
                    }
                    const incomingSelectors = [
                        '#egg-overlay img',
                        '#egg-overlay .egg-reveal-sprite',
                        '.egg-result img',
                        '.egg-result .poke-card',
                        '.egg-result [role="button"]',
                        '#shop-modal .poke-card',
                        '#shop-modal .dex-card',
                        '#shop-modal img[src*="/pokemon/"]',
                        '#mart-modal .poke-card',
                        '#mart-modal .dex-card',
                        '#mart-modal img[src*="/pokemon/"]',
                        '.game-modal--menu .poke-card',
                        '.game-modal--menu .dex-card',
                        '.game-modal--menu img[src*="/pokemon/"]',
                        '#swap-incoming .poke-card',
                        '#swap-incoming [role="button"]',
                        '#swap-incoming [data-shortcut]',
                        '#swap-incoming img[src*="/pokemon/"]',
                        '.screen.active #shiny-content .poke-card',
                        '.screen.active #shiny-content img[src*="/pokemon/"]',
                        '.screen.active .reward-pokemon .poke-card',
                        '.screen.active .reward-pokemon img[src*="/pokemon/"]'
                    ];
                    const incoming = incomingSelectors
                        .flatMap(selector => [...document.querySelectorAll(selector)])
                        .find(visible);
                    if (incoming) {
                        click(incoming.closest('.poke-card, .dex-card, [role="button"], [data-shortcut]') || incoming);
                        return {
                            clicked: true,
                            target: 'incoming pokemon',
                            screen: activeId
                        };
                    }
                    return {clicked: false, screen: activeId};
                    """
                )
            except Exception as exc:
                self.log(f"Legendary shop reroll: could not clear Pokemon reward before force upload ({exc}).")
                return clicked_any
            if not isinstance(result, dict) or not result.get("clicked"):
                return clicked_any
            clicked_any = True
            self.log(
                f"Legendary shop reroll: clicked {result.get('target') or 'Pokemon reward'} "
                "before force upload."
            )
            time.sleep(0.7)
        return clicked_any

    def dismiss_shop_menu_before_force_upload(self, driver=None):
        target_driver = driver or self.driver
        try:
            result = target_driver.execute_script(
                """
                const visible = (el) => {
                    if (!el) return false;
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0
                        && style.display !== 'none'
                        && style.visibility !== 'hidden';
                };
                const shop = [...document.querySelectorAll(
                    '#shop-modal, #mart-modal, .game-modal--menu, [id*="mart" i], [id*="shop" i], '
                    + '[class*="mart" i], [class*="shop" i], [role="dialog"], .modal'
                )].find(visible);
                if (!shop) return {clicked: false, reason: 'no visible shop dialog'};

                const close = [...shop.querySelectorAll('button.btn-icon-close, button[aria-label="Close"], button')]
                    .filter(visible)
                    .find(btn => {
                        const label = (btn.getAttribute('aria-label') || '').trim().toLowerCase();
                        const cls = (btn.className || '').toString().toLowerCase();
                        return label === 'close' || cls.includes('btn-icon-close') || !!btn.querySelector('.btn-close-glyph');
                    });
                if (!close) return {clicked: false, reason: 'shop close button not visible'};

                close.scrollIntoView({block: 'center', inline: 'center'});
                const rect = close.getBoundingClientRect();
                const x = Math.floor(rect.left + rect.width / 2);
                const y = Math.floor(rect.top + rect.height / 2);
                for (const type of ['pointerdown', 'mousedown', 'mouseup', 'pointerup', 'click']) {
                    close.dispatchEvent(new MouseEvent(type, {
                        bubbles: true,
                        cancelable: true,
                        clientX: x,
                        clientY: y,
                        screenX: x,
                        screenY: y,
                        button: 0,
                    }));
                }
                return {
                    clicked: true,
                    targetText: close.getAttribute('aria-label') || close.title || (close.innerText || close.textContent || '').trim().slice(0, 80)
                };
                """
            )
        except Exception as exc:
            self.log(f"Legendary shop reroll: could not dismiss shop menu before force upload ({exc}).")
            return False
        if isinstance(result, dict) and result.get("clicked"):
            self.log("Legendary shop reroll: dismissed shop menu before force upload.")
            try:
                WebDriverWait(target_driver, 1.5, poll_frequency=0.05).until(
                    lambda _: target_driver.execute_script(
                        """
                        const shop = document.querySelector('#shop-modal, #mart-modal, .game-modal--menu');
                        if (shop) {
                            const shopRect = shop.getBoundingClientRect();
                            const shopStyle = getComputedStyle(shop);
                            if (shopRect.width > 0 && shopRect.height > 0
                                && shopStyle.display !== 'none'
                                && shopStyle.visibility !== 'hidden') {
                                return false;
                            }
                        }
                        const toggle = document.querySelector('#run-menu-toggle, .run-menu-toggle')
                            || [...document.querySelectorAll('button, [role="button"]')].find(el => {
                                const menu = (el.dataset?.menu || '').toLowerCase();
                                const label = (el.getAttribute('aria-label') || '').trim().toLowerCase();
                                const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                                const onclick = String(el.getAttribute('onclick') || '').toLowerCase();
                                return menu === 'menu' || label === 'open menu' || text === 'menu' || onclick.includes('openappmenumodal');
                            });
                        if (!toggle) return false;
                        const rect = toggle.getBoundingClientRect();
                        const style = getComputedStyle(toggle);
                        return rect.width > 0 && rect.height > 0
                            && style.display !== 'none'
                            && style.visibility !== 'hidden';
                        """
                    )
                )
                return True
            except Exception:
                try:
                    state = target_driver.execute_script(
                        """
                        const visible = (el) => {
                            if (!el) return false;
                            const rect = el.getBoundingClientRect();
                            const style = getComputedStyle(el);
                            return rect.width > 0 && rect.height > 0
                                && style.display !== 'none'
                                && style.visibility !== 'hidden';
                        };
                        const shop = document.querySelector('#shop-modal, #mart-modal, .game-modal--menu');
                        const toggle = document.querySelector('#run-menu-toggle, .run-menu-toggle')
                            || [...document.querySelectorAll('button, [role="button"]')].find(el => {
                                const menu = (el.dataset?.menu || '').toLowerCase();
                                const label = (el.getAttribute('aria-label') || '').trim().toLowerCase();
                                const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                                const onclick = String(el.getAttribute('onclick') || '').toLowerCase();
                                return menu === 'menu' || label === 'open menu' || text === 'menu' || onclick.includes('openappmenumodal');
                            });
                        return {
                            shopVisible: visible(shop),
                            toggleVisible: visible(toggle),
                            activeScreen: document.querySelector('.screen.active')?.id || '',
                            bodyClass: document.body.className || '',
                            url: location.href,
                        };
                        """
                    )
                except Exception:
                    state = {}
                self.log(
                    "Legendary shop reroll: shop close clicked, but run menu toggle was not ready "
                    f"(shopVisible={state.get('shopVisible')}, toggleVisible={state.get('toggleVisible')}, "
                    f"screen={state.get('activeScreen') or 'unknown'})."
                )
                return False
        return False

    def force_upload_save_data(self, driver=None):
        target_driver = driver or self.driver
        self.disable_legendary_shop_network_guard(target_driver)
        try:
            target_driver.execute_script("window.__pokelikeBotAllowCloudUpload = true;")
        except Exception:
            pass
        self.install_cloud_upload_tracker(target_driver)
        for _attempt in range(3):
            if self.dismiss_shop_menu_before_force_upload(target_driver):
                break
            try:
                ready = target_driver.execute_script(
                    """
                    const visible = (el) => {
                        if (!el) return false;
                        const rect = el.getBoundingClientRect();
                        const style = getComputedStyle(el);
                        return rect.width > 0 && rect.height > 0
                            && style.display !== 'none'
                            && style.visibility !== 'hidden';
                    };
                    const shop = document.querySelector('#shop-modal, #mart-modal, .game-modal--menu');
                    const toggle = document.querySelector('#run-menu-toggle, .run-menu-toggle')
                        || [...document.querySelectorAll('button, [role="button"]')].find(el => {
                            const menu = (el.dataset?.menu || '').toLowerCase();
                            const label = (el.getAttribute('aria-label') || '').trim().toLowerCase();
                            const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                            const onclick = String(el.getAttribute('onclick') || '').toLowerCase();
                            return menu === 'menu' || label === 'open menu' || text === 'menu' || onclick.includes('openappmenumodal');
                        });
                    return !visible(shop) && visible(toggle);
                    """
                )
                if ready:
                    break
            except Exception:
                pass
            time.sleep(0.4)
        result = None
        try:
            result = target_driver.execute_async_script(
                """
                const done = arguments[arguments.length - 1];
                const visible = (el) => {
                    if (!el) return false;
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0
                        && style.display !== 'none'
                        && style.visibility !== 'hidden';
                };
                const click = (el) => {
                    if (!el) return false;
                    el.scrollIntoView({block: 'center', inline: 'center'});
                    el.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                    el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                    el.click();
                    el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                    el.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
                    return true;
                };
                const findAccount = () => document.querySelector('#btn-cloud-sync')
                    || [...document.querySelectorAll('button, [role="button"]')].filter(visible).find(el => {
                        const text = `${el.innerText || el.textContent || ''} ${el.getAttribute('aria-label') || ''} ${el.title || ''}`.toLowerCase();
                        const menu = (el.dataset?.menu || '').toLowerCase();
                        const id = (el.id || '').toLowerCase();
                        return menu === 'account' || id.includes('cloud') || text.includes('cloud save');
                    });
                const findMenuOpener = () => document.querySelector('#run-menu-toggle, .run-menu-toggle')
                    || [...document.querySelectorAll('button, [role="button"]')].filter(visible).find(el => {
                        const menu = (el.dataset?.menu || '').toLowerCase();
                        const label = (el.getAttribute('aria-label') || '').trim().toLowerCase();
                        const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                        const onclick = String(el.getAttribute('onclick') || '').toLowerCase();
                        return menu === 'menu' || label === 'open menu' || text === 'menu' || onclick.includes('openappmenumodal');
                    });
                const started = Date.now();
                let menuClicked = false;
                const waitAndClick = () => {
                    const account = findAccount();
                    if (visible(account)) {
                        click(account);
                        done({
                            clicked: true,
                            step: 'account',
                            text: account.innerText || account.textContent || account.title || account.getAttribute('aria-label') || ''
                        });
                        return;
                    }
                    const toggle = findMenuOpener();
                    if (!menuClicked && visible(toggle)) {
                        click(toggle);
                        menuClicked = true;
                        setTimeout(waitAndClick, 120);
                        return;
                    }
                    if (Date.now() - started >= 7000) {
                        done({
                            clicked: false,
                            step: menuClicked ? 'account' : 'menu-toggle',
                            reason: menuClicked
                                ? 'cloud sync button not visible after opening run menu'
                                : 'run menu toggle not visible',
                            activeScreen: document.querySelector('.screen.active')?.id || '',
                            bodyClass: document.body.className || '',
                            shopVisible: visible(document.querySelector('#shop-modal, #mart-modal, .game-modal--menu')),
                        });
                        return;
                    }
                    setTimeout(waitAndClick, 80);
                };
                waitAndClick();
                """
            )
        except Exception as exc:
            self.log(f"Legendary shop reroll: could not open account menu for force upload ({exc}).")
            result = {}
        if not isinstance(result, dict) or not result.get("clicked"):
            reason = result.get("reason") if isinstance(result, dict) else ""
            step = result.get("step") if isinstance(result, dict) else ""
            state_bits = []
            if isinstance(result, dict):
                if result.get("activeScreen"):
                    state_bits.append(f"screen={result.get('activeScreen')}")
                if result.get("shopVisible") is not None:
                    state_bits.append(f"shopVisible={result.get('shopVisible')}")
            state_detail = f"; {', '.join(state_bits)}" if state_bits else ""
            detail = f" ({step}: {reason}{state_detail})" if step or reason or state_detail else ""
            self.log(f"Legendary shop reroll: target found, but account/cloud menu was not found{detail}.")
            return False
        clicked_upload = False
        upload_text = ""
        deadline = time.time() + 5.0
        while time.time() < deadline and not clicked_upload:
            try:
                upload_result = target_driver.execute_script(
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
                        el.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                        el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                        el.click();
                        el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                        el.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
                    };
                    const textFor = (el) => `${el.innerText || el.textContent || ''} ${el.getAttribute('aria-label') || ''} ${el.title || ''}`.toLowerCase();
                    const button = document.querySelector('#account-force-upload-btn')
                        || [...document.querySelectorAll('button, [role="button"]')].filter(visible).find(el => {
                            const text = textFor(el);
                            return (text.includes('force') && text.includes('upload'))
                                || (text.includes('upload') && text.includes('save'));
                        });
                    if (!button || !visible(button)) return {clicked: false};
                    const text = button.innerText || button.textContent || button.title || '';
                    click(button);
                    return {clicked: true, text};
                    """
                )
                if isinstance(upload_result, dict) and upload_result.get("clicked"):
                    clicked_upload = True
                    upload_text = upload_result.get("text") or "Force Upload to Cloud"
                    break
            except Exception as exc:
                if self.accept_force_upload_confirmation(target_driver, timeout=5.0):
                    return self.wait_for_cloud_upload_completion(target_driver)
                self.log(f"Legendary shop reroll: force-upload click was interrupted ({exc}).")
                return False
            time.sleep(0.1)
        if clicked_upload:
            self.log(f"Legendary shop reroll: force upload clicked ({upload_text}).")
            if self.accept_force_upload_confirmation(target_driver, timeout=5.0):
                return self.wait_for_cloud_upload_completion(target_driver)
            return False
        self.log("Legendary shop reroll: target found, but force upload save data button was not found.")
        return False

    def install_cloud_upload_tracker(self, driver=None):
        target_driver = driver or self.driver
        try:
            target_driver.execute_script(
                """
                (() => {
                    const matches = (url) => {
                        const text = String(url || '').toLowerCase();
                        return ['cloud', 'sync', 'save', 'upload', 'force-upload', 'savedata', 'save-data']
                            .some(term => text.includes(term));
                    };
                    window.__pokelikeBotUploadTracker = {
                        pending: 0,
                        seen: 0,
                        completed: 0,
                        failed: 0,
                        lastUrl: '',
                        lastDoneAt: 0,
                        startedAt: Date.now(),
                    };
                    if (!window.__pokelikeBotUploadTrackerInstalled) {
                        window.__pokelikeBotUploadTrackerInstalled = true;
                        const originalFetch = window.fetch;
                        if (typeof originalFetch === 'function') {
                            window.fetch = function(input, init) {
                                const url = typeof input === 'string' ? input : (input && input.url) || '';
                                const tracked = matches(url);
                                const tracker = window.__pokelikeBotUploadTracker;
                                if (tracked && tracker) {
                                    tracker.pending += 1;
                                    tracker.seen += 1;
                                    tracker.lastUrl = url;
                                }
                                return originalFetch.apply(this, arguments).then(
                                    response => {
                                        if (tracked && tracker) {
                                            tracker.completed += 1;
                                            tracker.pending = Math.max(0, tracker.pending - 1);
                                            tracker.lastDoneAt = Date.now();
                                        }
                                        return response;
                                    },
                                    error => {
                                        if (tracked && tracker) {
                                            tracker.failed += 1;
                                            tracker.pending = Math.max(0, tracker.pending - 1);
                                            tracker.lastDoneAt = Date.now();
                                        }
                                        throw error;
                                    }
                                );
                            };
                        }
                        const OriginalXHR = window.XMLHttpRequest;
                        if (OriginalXHR) {
                            window.XMLHttpRequest = function() {
                                const xhr = new OriginalXHR();
                                let tracked = false;
                                const originalOpen = xhr.open;
                                xhr.open = function(method, url) {
                                    tracked = matches(url);
                                    if (tracked && window.__pokelikeBotUploadTracker) {
                                        window.__pokelikeBotUploadTracker.pending += 1;
                                        window.__pokelikeBotUploadTracker.seen += 1;
                                        window.__pokelikeBotUploadTracker.lastUrl = url;
                                    }
                                    return originalOpen.apply(xhr, arguments);
                                };
                                xhr.addEventListener('loadend', () => {
                                    const tracker = window.__pokelikeBotUploadTracker;
                                    if (tracked && tracker) {
                                        if (xhr.status >= 200 && xhr.status < 400) tracker.completed += 1;
                                        else tracker.failed += 1;
                                        tracker.pending = Math.max(0, tracker.pending - 1);
                                        tracker.lastDoneAt = Date.now();
                                    }
                                });
                                return xhr;
                            };
                        }
                        const originalBeacon = navigator.sendBeacon && navigator.sendBeacon.bind(navigator);
                        if (originalBeacon) {
                            navigator.sendBeacon = function(url, data) {
                                const tracked = matches(url);
                                const tracker = window.__pokelikeBotUploadTracker;
                                if (tracked && tracker) {
                                    tracker.seen += 1;
                                    tracker.completed += 1;
                                    tracker.lastUrl = String(url || '');
                                    tracker.lastDoneAt = Date.now();
                                }
                                return originalBeacon(url, data);
                            };
                        }
                    }
                })();
                """
            )
        except Exception as exc:
            self.log(f"Legendary shop reroll: could not install cloud upload tracker ({exc}).")

    def wait_for_cloud_upload_completion(self, driver=None, timeout=35.0):
        target_driver = driver or self.driver
        deadline = time.time() + float(timeout)
        last_state = None
        while time.time() < deadline:
            try:
                state = target_driver.execute_script(
                    """
                    const visible = (el) => {
                        if (!el) return false;
                        const rect = el.getBoundingClientRect();
                        const style = getComputedStyle(el);
                        return rect.width > 0 && rect.height > 0
                            && style.display !== 'none'
                            && style.visibility !== 'hidden';
                    };
                    const tracker = window.__pokelikeBotUploadTracker || {};
                    const text = [...document.querySelectorAll('.toast, .notification, .alert, .modal, [role="status"], [aria-live], button, [role="button"]')]
                        .filter(visible)
                        .map(el => `${el.innerText || el.textContent || ''} ${el.getAttribute('aria-label') || ''} ${el.title || ''}`)
                        .join(' ')
                        .replace(/\\s+/g, ' ')
                        .toLowerCase();
                    const successText = /(upload(ed)?|sync(ed)?|save(d)?)\\s+(complete|success|successful|done)|cloud\\s+(save|sync)\\s+(complete|success|successful|done)|saved\\s+to\\s+cloud/.test(text);
                    const now = Date.now();
                    return {
                        pending: Number(tracker.pending || 0),
                        seen: Number(tracker.seen || 0),
                        completed: Number(tracker.completed || 0),
                        failed: Number(tracker.failed || 0),
                        lastDoneAgo: tracker.lastDoneAt ? now - Number(tracker.lastDoneAt) : null,
                        successText,
                        text: text.slice(0, 240),
                        lastUrl: String(tracker.lastUrl || '').slice(0, 160),
                    };
                    """
                )
            except Exception:
                state = {}
            last_state = state if isinstance(state, dict) else {}
            if last_state.get("successText"):
                self.log("Legendary shop reroll: cloud upload completion text detected.")
                time.sleep(1.0)
                return True
            seen = int(last_state.get("seen") or 0)
            pending = int(last_state.get("pending") or 0)
            completed = int(last_state.get("completed") or 0)
            failed = int(last_state.get("failed") or 0)
            last_done_ago = last_state.get("lastDoneAgo")
            if seen > 0 and pending == 0 and completed > 0 and failed == 0 and last_done_ago is not None and last_done_ago >= 3000:
                self.log(
                    "Legendary shop reroll: cloud upload network request completed "
                    f"({completed} request(s); last={last_state.get('lastUrl') or 'unknown'})."
                )
                time.sleep(1.5)
                return True
            time.sleep(0.25)
        self.log(
            "Legendary shop reroll: cloud upload was clicked, but completion was not confirmed "
            f"(state={last_state})."
        )
        return False

    def close_account_modal_if_visible(self, driver=None):
        target_driver = driver or self.driver
        result = target_driver.execute_script(
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
                el.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                el.click();
                el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            };
            const close = [...document.querySelectorAll('button.btn-icon-close, button[aria-label="Close"], button')]
                .filter(visible)
                .find(btn => {
                    const label = (btn.getAttribute('aria-label') || '').trim().toLowerCase();
                    const cls = (btn.className || '').toString().toLowerCase();
                    const glyph = !!btn.querySelector('.btn-close-glyph');
                    return label === 'close' || cls.includes('btn-icon-close') || glyph;
                });
            if (!close) return false;
            click(close);
            return true;
            """
        )
        if result:
            self.log("Legendary shop reroll: closed account menu after force upload.")
            time.sleep(0.4)
        return bool(result)

    def restore_legendary_shop_cloud_guard(self, driver=None):
        target_driver = driver or self.driver
        try:
            target_driver.execute_script("window.__pokelikeBotAllowCloudUpload = false;")
        except Exception:
            pass
        self.enable_legendary_shop_network_guard(target_driver)

    def prepare_winning_shop_browser_for_cloud_upload(self, driver):
        self.winning_driver = driver
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)
        self._driver = driver
        self._wait = WebDriverWait(driver, 30)
        with self.drivers_lock:
            self.worker_drivers = [driver]
        self.disable_legendary_shop_network_guard(driver)
        try:
            driver.execute_script("window.__pokelikeBotAllowCloudUpload = true;")
        except Exception:
            pass
        self.log("Legendary shop reroll: winning browser is isolated and cloud upload is unblocked.")

    def maximize_browser_for_shop_cloud_menu(self, driver):
        restore_rect = None
        try:
            restore_rect = driver.get_window_rect()
        except Exception:
            try:
                restore_rect = self.shop_reroll_window_rect()
            except Exception:
                restore_rect = None
        try:
            driver.maximize_window()
            self.log("Legendary shop reroll: maximized browser for cloud save menu.")
            time.sleep(0.5)
        except Exception as exc:
            self.log(f"Legendary shop reroll: could not maximize browser for cloud save menu ({exc}).")
        return restore_rect

    def restore_browser_after_shop_cloud_menu(self, driver, restore_rect):
        if not restore_rect:
            return
        try:
            self.apply_browser_window_rect(driver, restore_rect)
            self.log("Legendary shop reroll: restored browser size after cloud save menu.")
            time.sleep(0.2)
        except Exception as exc:
            self.log(f"Legendary shop reroll: could not restore browser size after cloud save menu ({exc}).")

    def record_shop_reroll_result(self, config, attempt_number, result):
        if result.get("found"):
            with self.stats_lock:
                self.total_encounters_checked += 1
                if result.get("shiny"):
                    self.total_shinies_seen += 1
                    self.last_shiny_pokemon_name = result.get("name") or "Pokemon"
                if result.get("hit"):
                    self.target_encounters_seen += 1
            self.update_stats_labels()
            label = "shiny" if result.get("shiny") else "normal"
            evidence = (
                f" ({result.get('shinyEvidence')})"
                if result.get("shiny") and result.get("shinyEvidence")
                else ""
            )
            message = (
                f"{config['mode_label']} attempt #{attempt_number}: rolled {label}{evidence} "
                f"{result.get('name') or 'Pokemon'}."
            )
            self.log(message)
            self.append_shop_roll_log(message)
        else:
            self.log(f"{config['mode_label']} attempt #{attempt_number}: could not identify the purchased Pokemon.")

    def force_upload_shop_hit(self, driver):
        if not self.should_allow_automated_shop_upload():
            self.log("Legendary shop reroll: refused automated cloud upload outside shop reroll flow.")
            return False
        self.log("Legendary shop reroll: starting cloud upload for winning browser.")
        self.prepare_winning_shop_browser_for_cloud_upload(driver)
        self.log("Legendary shop reroll: dismissing shop result overlay before cloud upload.")
        self.dismiss_shop_egg_result_overlay(driver)
        self.dismiss_pending_pokemon_reward_before_force_upload(driver)
        self.log("Legendary shop reroll: opening cloud save menu for force upload.")
        restore_rect = self.maximize_browser_for_shop_cloud_menu(driver)
        try:
            uploaded = self.force_upload_save_data(driver)
            if not uploaded:
                self.log("Legendary shop reroll: target found, but cloud force upload did not complete.")
                return False
            self.close_account_modal_if_visible(driver)
            self.restore_legendary_shop_cloud_guard(driver)
            return True
        finally:
            self.restore_browser_after_shop_cloud_menu(driver, restore_rect)

    def reopen_headless_shop_hit_visible_if_needed(self, driver, attempt_path, worker_id, window_rect=None):
        try:
            headless = bool(self.headless_var.get())
        except Exception:
            headless = False
        if not headless or not attempt_path:
            return driver
        try:
            driver.quit()
        except Exception:
            pass
        self.remove_driver_reference(driver)
        time.sleep(0.35)
        visible_driver = self.launch_driver(
            worker_id=worker_id,
            make_active=True,
            profile_path_override=attempt_path,
            allow_reconnect=False,
            window_rect=window_rect,
            force_headless=False,
        )
        self.install_legendary_shop_cloud_guard(visible_driver)
        self.thread_local.use_local = True
        self.thread_local.worker_id = worker_id
        self.driver = visible_driver
        self.wait = WebDriverWait(visible_driver, 30)
        self.prepare_page(cookie_timeout=0.25)
        self.ensure_home_screen_for_shop()
        self.enable_legendary_shop_network_guard(visible_driver)
        self.winning_driver = visible_driver
        self._driver = visible_driver
        self._wait = WebDriverWait(visible_driver, 30)
        with self.drivers_lock:
            self.worker_drivers = [visible_driver]
        self.log("Legendary shop reroll: reopened winning headless profile in a visible browser for cloud upload.")
        return visible_driver

    def run_legendary_shop_attempt(
        self,
        seed_path,
        attempt_number,
        prepared=None,
        window_rect=None,
        close_miss_driver=True,
        before_hit_upload=None,
        run_token=None,
    ):
        config = self.current_shop_egg_config()
        attempt_path = None
        driver = None
        try:
            if not self.is_active_bot_run_token(run_token):
                return "stale"
            if prepared:
                driver = prepared["driver"]
                attempt_path = prepared["attempt_path"]
                worker_id = prepared.get("worker_id", 1)
            else:
                attempt_path = self.reset_legendary_shop_attempt_profile(seed_path, attempt_id=attempt_number)
                worker_id = 1
                driver = self.launch_driver(
                    worker_id=worker_id,
                    make_active=True,
                    profile_path_override=attempt_path,
                    allow_reconnect=False,
                    window_rect=window_rect,
                )
                self.install_legendary_shop_cloud_guard(driver)
            self.thread_local.use_local = True
            self.thread_local.worker_id = worker_id
            self.driver = driver
            self.wait = WebDriverWait(driver, 20)
            if not self.is_active_bot_run_token(run_token):
                return "stale"
            if not prepared:
                self.prepare_page(cookie_timeout=0.25)
                self.ensure_home_screen_for_shop()
                self.ensure_legendary_shop_buy_ready(driver, timeout=10.0)
                self.enable_legendary_shop_network_guard(driver)
            if not self.is_active_bot_run_token(run_token):
                return "stale"
            if self.stop_if_cloud_save_conflict_visible(driver):
                return "stop"
            self.record_wallet_gold_if_visible(driver)
            before_party = self.legendary_shop_party_summary()
            if not self.click_legendary_shop_buy(allow_unavailable=self.current_shop_budget_schedule_active()):
                if self.current_shop_budget_schedule_active():
                    return "shop_budget_done"
                return "stop"
            if self.stop_if_cloud_save_conflict_visible(driver):
                return "stop"
            self.record_wallet_gold_if_visible(driver)
            result = self.legendary_shop_result_after_buy(before_party)
            if self.stop_if_cloud_save_conflict_visible(driver):
                return "stop"
            self.record_wallet_gold_if_visible(driver)
            self.record_shop_reroll_result(config, attempt_number, result)
            if result.get("hit"):
                if not self.is_active_bot_run_token(run_token):
                    return "stale"
                self.set_status("Target found")
                self.winning_driver = driver
                self._driver = driver
                self._wait = WebDriverWait(driver, 30)
                self.driver = driver
                self.wait = WebDriverWait(driver, 30)
                if callable(before_hit_upload):
                    before_hit_upload(driver)
                else:
                    self.close_other_drivers(driver)
                driver = self.reopen_headless_shop_hit_visible_if_needed(driver, attempt_path, worker_id, window_rect=window_rect)
                self.driver = driver
                self.wait = WebDriverWait(driver, 30)
                if not self.force_upload_shop_hit(driver):
                    if not self.is_active_bot_run_token(run_token):
                        return "stale"
                    self.stop_event.set()
                    self.set_status("Upload failed")
                    self.log("Legendary shop reroll: stopped on winning browser because target upload failed.")
                    return True
                if not self.is_active_bot_run_token(run_token):
                    self.log(f"{config['mode_label']}: stale shop upload finished after a newer run started; leaving the current run untouched.")
                    return "stale"
                with self.stats_lock:
                    self.run_count = attempt_number
                self.update_stats_labels()
                if self.should_continue_shop_reroll_after_hit():
                    uploaded_name = self.add_shop_hit_to_ignore_list(result)
                    with self.stats_lock:
                        self.shop_targets_obtained += 1
                    self.update_stats_labels()
                    if not self.play_post_shop_hit_safety_run(driver, uploaded_name or result.get("name"), run_token=run_token):
                        if not self.is_active_bot_run_token(run_token):
                            return "stale"
                        if not self.stop_event.is_set():
                            self.stop_event.set()
                            self.set_status("Post-hit run failed")
                        self.log("Legendary shop reroll: stopped because the post-hit safety run or second upload failed.")
                        return "stop"
                    if not self.sync_uploaded_shop_hit_to_base_profile(driver, attempt_path):
                        if not self.is_active_bot_run_token(run_token):
                            return "stale"
                        self.stop_event.set()
                        self.set_status("Profile sync failed")
                        self.log("Legendary shop reroll: stopped because the uploaded hit could not become the new shop base.")
                        return "stop"
                    self.set_status("Target uploaded")
                    label = uploaded_name.title() if uploaded_name else "uploaded hit"
                    self.log(
                        f"{config['mode_label']}: {label} uploaded and ignored; "
                        "restarting the shop reroller from the new cloud-synced base."
                    )
                    return "continue"
                if not self.is_active_bot_run_token(run_token):
                    self.log(f"{config['mode_label']}: stale shop upload finished after a newer run started; leaving the current run untouched.")
                    return "stale"
                self.stop_event.set()
                self.set_status("Target uploaded")
                self.log(f"{config['mode_label']}: target uploaded; stopping immediately with the winning browser open.")
                return "stop"
            return False
        finally:
            self.clear_thread_driver()
            if close_miss_driver and driver is not None and self.winning_driver is not driver:
                self.close_shop_attempt_driver(driver, attempt_path)

    def cleanup_shop_attempt_profile(self, attempt_path):
        if not attempt_path:
            return
        try:
            marker = f"{SELENIUM_PROFILE_PATH}-shop-attempt"
            if os.path.abspath(attempt_path).startswith(os.path.abspath(marker)):
                shutil.rmtree(attempt_path, ignore_errors=True)
        except Exception:
            pass

    def close_shop_attempt_driver(self, driver, attempt_path=None):
        if driver is not None and driver is self.winning_driver:
            self.log("Legendary shop reroll: refused to close the winning browser during cloud upload.")
            return
        try:
            driver.quit()
        except Exception:
            pass
        self.remove_driver_reference(driver)
        self.cleanup_shop_attempt_profile(attempt_path)

    def close_shop_attempt_driver_async(self, driver, attempt_path=None):
        if driver is None:
            self.cleanup_shop_attempt_profile(attempt_path)
            return
        try:
            self.remove_driver_reference(driver)
        except Exception:
            pass
        threading.Thread(
            target=self.close_shop_attempt_driver,
            args=(driver, attempt_path),
            daemon=True,
        ).start()

    def run_legendary_shop_reroll(self):
        config = self.current_shop_egg_config()
        shop_run_token = self.active_bot_run_token
        self.last_wallet_pokegold_total = 0
        self.update_stats_labels()
        ignored = list(getattr(self, "current_shop_ignore_pokemon_list", []) or [])
        if not self.current_target_pokemon_list:
            self.log(f"{config['mode_label']}: no Pokemon whitelist set; any non-ignored shiny roll is a hit.")
        else:
            self.log(
                f"{config['mode_label']} target whitelist: "
                + ", ".join(name.title() for name in self.current_target_pokemon_list)
            )
        if ignored:
            self.log(f"{config['mode_label']} ignore list: " + ", ".join(name.title() for name in ignored))
        self.browser_count = 1
        self.browser_count_var.set("1")
        window_rect = self.shop_reroll_window_rect()
        self.log(
            f"{config['mode_label']}: using Chrome window "
            f"{window_rect['width']}x{window_rect['height']} for shop reroll."
        )
        seed_path = self.prepare_legendary_shop_seed_profile(window_rect=window_rect)
        attempt_number = 0
        reroll_slot_count = max(1, min(SHOP_REROLL_PREWARM_COUNT, SHOP_REROLL_MAX_PARALLEL_ATTEMPTS))
        loading_browser_count = max(0, min(SHOP_REROLL_LOADING_BROWSER_COUNT, SHOP_REROLL_MAX_PARALLEL_ATTEMPTS))
        pipeline_count = reroll_slot_count + loading_browser_count
        self.log(
            f"{config['mode_label']}: pipeline has {pipeline_count} foreground browser slot(s); "
            "each browser rolls only after the shop buy button is confirmed clickable."
        )
        prep_executor = ThreadPoolExecutor(max_workers=pipeline_count)
        attempt_executor = ThreadPoolExecutor(max_workers=pipeline_count)
        try:
            futures = {}
            attempt_futures = {}
            attempt_lock = threading.Lock()
            next_prepare_id = 1

            def queue_attempt_browser(slot):
                nonlocal next_prepare_id
                attempt_id = next_prepare_id
                next_prepare_id += 1
                futures[
                    prep_executor.submit(
                        self.prepare_shop_attempt_browser,
                        seed_path,
                        slot,
                        window_rect,
                        attempt_id,
                        shop_run_token,
                    )
                ] = slot

            for slot in range(1, pipeline_count + 1):
                queue_attempt_browser(slot)

            def next_attempt_number():
                nonlocal attempt_number
                with attempt_lock:
                    attempt_number += 1
                    number = attempt_number
                with self.stats_lock:
                    self.run_count = number
                self.update_stats_labels()
                return number

            def run_prepared_shop_attempt(prepared, number):
                if not self.is_active_bot_run_token(shop_run_token):
                    return {"outcome": "stale", "prepared": prepared, "attempt_number": number, "closed": False}
                try:
                    outcome = self.run_legendary_shop_attempt(
                        seed_path,
                        number,
                        prepared=prepared,
                        window_rect=window_rect,
                        close_miss_driver=False,
                        before_hit_upload=close_non_winning_shop_browsers_before_upload,
                        run_token=shop_run_token,
                    )
                except Exception as exc:
                    self.close_shop_attempt_driver_async(
                        prepared.get("driver") if isinstance(prepared, dict) else None,
                        prepared.get("attempt_path") if isinstance(prepared, dict) else None,
                    )
                    self.log(f"{config['mode_label']} attempt #{number}: browser failed ({exc}); closing it and continuing.")
                    return {"outcome": False, "prepared": prepared, "attempt_number": number, "closed": True}
                return {"outcome": outcome, "prepared": prepared, "attempt_number": number, "closed": False}

            def submit_prepared_attempt(prepared):
                number = next_attempt_number()
                future = attempt_executor.submit(run_prepared_shop_attempt, prepared, number)
                attempt_futures[future] = number

            def process_ready_prepare(future):
                slot = futures.pop(future)
                try:
                    prepared = future.result()
                except Exception as exc:
                    self.log(f"{config['mode_label']}: browser slot {slot} failed before buy button became clickable ({exc}); replacing it.")
                    if not self.stop_event.is_set() and self.winning_driver is None and self.is_active_bot_run_token(shop_run_token):
                        queue_attempt_browser(slot)
                    return
                if not prepared:
                    if not self.stop_event.is_set() and self.winning_driver is None and self.is_active_bot_run_token(shop_run_token):
                        queue_attempt_browser(slot)
                    return
                if not self.stop_event.is_set() and self.winning_driver is None and self.is_active_bot_run_token(shop_run_token):
                    submit_prepared_attempt(prepared)
                else:
                    self.close_shop_attempt_driver(prepared.get("driver"), prepared.get("attempt_path"))

            def close_non_winning_shop_browsers_before_upload(winning_driver):
                closed = 0
                canceled = 0
                for pending_future in list(futures):
                    if pending_future.cancel():
                        canceled += 1
                        futures.pop(pending_future, None)
                        continue
                    if not pending_future.done():
                        continue
                    futures.pop(pending_future, None)
                    try:
                        spare = pending_future.result(timeout=0)
                        spare_driver = spare.get("driver") if isinstance(spare, dict) else None
                        if spare_driver is not None and spare_driver is not winning_driver:
                            self.close_shop_attempt_driver_async(spare_driver, spare.get("attempt_path"))
                            closed += 1
                    except Exception:
                        pass
                for pending_future in list(attempt_futures):
                    if pending_future.cancel():
                        canceled += 1
                        attempt_futures.pop(pending_future, None)
                with self.drivers_lock:
                    live_drivers = list(self.worker_drivers)
                    self.worker_drivers = [winning_driver]
                for candidate in live_drivers:
                    if candidate is winning_driver:
                        continue
                    self.remove_driver_reference(candidate)
                    threading.Thread(
                        target=self.close_shop_attempt_driver,
                        args=(candidate, None),
                        daemon=True,
                    ).start()
                    closed += 1
                with self.drivers_lock:
                    self.worker_drivers = [winning_driver]
                self._driver = winning_driver
                self._wait = WebDriverWait(winning_driver, 30)
                self.driver = winning_driver
                self.wait = WebDriverWait(winning_driver, 30)
                self.disable_legendary_shop_network_guard(winning_driver)
                try:
                    winning_driver.execute_script("window.__pokelikeBotAllowCloudUpload = true;")
                except Exception:
                    pass
                if closed or canceled:
                    self.log(
                        f"{config['mode_label']}: closed {closed} non-winning browser(s) "
                        f"and canceled {canceled} queued browser(s) before cloud upload; winning browser upload is unblocked."
                    )
                else:
                    self.log(f"{config['mode_label']}: no non-winning browsers were open before cloud upload; winning browser upload is unblocked.")

            while not self.stop_event.is_set() and self.is_active_bot_run_token(shop_run_token):
                ready_preps = [future for future in list(futures) if future.done()]
                for future in ready_preps:
                    process_ready_prepare(future)

                done_attempts = [future for future in list(attempt_futures) if future.done()]
                if not done_attempts:
                    wait_set = list(futures) + list(attempt_futures)
                    if not wait_set:
                        break
                    done_any, _pending = wait(wait_set, return_when=FIRST_COMPLETED, timeout=0.25)
                    if not done_any:
                        continue
                    ready_preps = [future for future in done_any if future in futures]
                    if ready_preps:
                        for future in ready_preps:
                            process_ready_prepare(future)
                    continue

                for future in done_attempts:
                    attempt_futures.pop(future, None)
                    try:
                        attempt_result = future.result()
                    except Exception as exc:
                        self.log(f"{config['mode_label']}: attempt worker failed ({exc}); continuing.")
                        continue
                    outcome = attempt_result.get("outcome") if isinstance(attempt_result, dict) else False
                    prepared = attempt_result.get("prepared") if isinstance(attempt_result, dict) else None
                    if outcome == "stale" or not self.is_active_bot_run_token(shop_run_token):
                        return
                    if outcome == "shop_budget_done":
                        for pending_future in list(futures):
                            pending_future.cancel()
                            futures.pop(pending_future, None)
                        for pending_future in list(attempt_futures):
                            pending_future.cancel()
                        if isinstance(prepared, dict):
                            self.close_shop_attempt_driver_async(prepared.get("driver"), prepared.get("attempt_path"))
                        if self.advance_schedule_after_shop_budget():
                            return "schedule_advance"
                        return "stop"
                    if outcome:
                        for pending_future in list(futures):
                            if pending_future.cancel():
                                futures.pop(pending_future, None)
                                continue
                            if not pending_future.done():
                                continue
                            futures.pop(pending_future, None)
                            try:
                                spare = pending_future.result()
                                spare_driver = spare.get("driver") if isinstance(spare, dict) else None
                                if spare_driver is not None and spare_driver is not self.winning_driver:
                                    self.close_shop_attempt_driver_async(spare_driver, spare.get("attempt_path"))
                            except Exception:
                                pass
                        for pending_future in list(attempt_futures):
                            pending_future.cancel()
                        if outcome == "continue" and not self.stop_event.is_set() and self.is_active_bot_run_token(shop_run_token):
                            prep_executor.shutdown(wait=False, cancel_futures=True)
                            attempt_executor.shutdown(wait=False, cancel_futures=True)
                            return self.run_legendary_shop_reroll()
                        if self.is_active_bot_run_token(shop_run_token):
                            self.stop_event.set()
                        return
                    if isinstance(prepared, dict) and not attempt_result.get("closed"):
                        self.close_shop_attempt_driver_async(prepared.get("driver"), prepared.get("attempt_path"))
                    if not self.stop_event.is_set() and self.winning_driver is None and isinstance(prepared, dict) and self.is_active_bot_run_token(shop_run_token):
                        queue_attempt_browser(prepared.get("slot") or 1)
                    self.log(f"{config['mode_label']}: miss; loading browsers keep feeding the next clickable shop purchase.")
                    continue
        finally:
            prep_executor.shutdown(wait=False, cancel_futures=True)
            attempt_executor.shutdown(wait=False, cancel_futures=True)

    def preload_dex_targets(self, driver, target_mode):
        self.thread_local.use_local = True
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        try:
            self.log(f"Dex targets: preloading {target_mode} from Pokédex in the background.")
            self.collect_missing_dex_targets(target_mode)
        except Exception as exc:
            self.log(f"Dex targets: background preload failed ({exc}).")
        finally:
            self.clear_thread_driver()

    def parse_item_target_list(self):
        targets = [
            name.strip().lower()
            for name in self.item_reroll_target_var.get().replace(";", ",").split(",")
            if name.strip()
        ]
        return targets or [DEFAULT_ITEM_REROLL_TARGET]

    def read_pokedex_modal_targets(self, target_mode):
        if target_mode == DEX_TARGET_OFF or not self.driver:
            return []
        try:
            result = self.driver.execute_async_script(
                """
                const mode = arguments[0];
                const legendaryNames = new Set(arguments[1].map(name => String(name || '').toLowerCase()));
                const done = arguments[arguments.length - 1];
                const wantsNormal = mode === 'Missing normal Dex' || mode === 'Missing normal + shiny Dex';
                const wantsShiny = mode === 'Missing shiny Dex' || mode === 'Missing normal + shiny Dex';
                const normalize = (text) => String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
                const title = (text) => normalize(text).replace(/\\b\\w/g, ch => ch.toUpperCase());
                const visible = (el) => {
                    if (!el) return false;
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0
                        && style.display !== 'none'
                        && style.visibility !== 'hidden';
                };
                const click = (el) => {
                    if (!el) return false;
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
                    return true;
                };
                const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                const waitFor = async (fn, timeout = 2500) => {
                    const end = Date.now() + timeout;
                    while (Date.now() < end) {
                        try {
                            const value = fn();
                            if (value) return value;
                        } catch (e) {}
                        await sleep(80);
                    }
                    return null;
                };
                const spriteId = (card) => {
                    const src = card.querySelector('img')?.getAttribute('src') || '';
                    const match = src.match(/pokemon\\/(?:shiny\\/)?(\\d+)\\.png/i);
                    if (match) return parseInt(match[1], 10) || 0;
                    const text = card.innerText || card.textContent || '';
                    const textMatch = text.match(/#\\s*(\\d+)/);
                    return textMatch ? parseInt(textMatch[1], 10) || 0 : 0;
                };
                const cardName = (card) => {
                    const raw = (
                        card.getAttribute('data-name')
                        || card.getAttribute('aria-label')
                        || card.querySelector('.dex-name')?.innerText
                        || card.querySelector('img[alt]')?.getAttribute('alt')
                        || ''
                    ).trim();
                    const norm = normalize(raw);
                    if (!norm || norm === 'unknown') return '';
                    return raw === '???' ? '' : title(raw);
                };
                const ensureOpen = async () => {
                    let modal = document.querySelector('#pokedex-modal');
                    if (!visible(modal)) {
                        if (typeof window.openPokedexModal === 'function') {
                            window.openPokedexModal();
                        } else {
                            const button = document.querySelector('button[data-menu="pokedex"], button[onclick*="openPokedexModal"], [data-tip*="Pok"]');
                            if (button) {
                                try { button.click(); } catch (e) { click(button); }
                            } else {
                                const menu = document.querySelector('#run-menu-toggle, .run-menu-toggle');
                                click(menu);
                                await sleep(120);
                                const openedButton = document.querySelector('button[data-menu="pokedex"], button[onclick*="openPokedexModal"], [data-tip*="Pok"]');
                                if (openedButton) {
                                    try { openedButton.click(); } catch (e) { click(openedButton); }
                                }
                            }
                        }
                    }
                    return await waitFor(() => {
                        const el = document.querySelector('#pokedex-modal');
                        return visible(el) && el.querySelector('#dex-grid-content') ? el : null;
                    });
                };
                const activeTab = () => (
                    document.querySelector('#pokedex-modal .dex-tab.active, .dex-tab.active')?.getAttribute('data-tab') || ''
                ).toLowerCase();
                const activeGen = () => (
                    document.querySelector('#pokedex-modal .dex-gen-filter-btn.active, .dex-gen-filter-btn.active')?.getAttribute('data-gen') || ''
                ).toLowerCase();
                const missingActive = () => {
                    const btn = document.querySelector('#dex-hide-caught-btn');
                    return !!btn && btn.classList.contains('active');
                };
                const gridSignature = () => {
                    const grid = document.querySelector('#dex-grid-content');
                    return grid ? String(grid.innerText || grid.textContent || '').replace(/\\s+/g, ' ').trim() : '';
                };
                const gridReady = () => {
                    const grid = document.querySelector('#dex-grid-content');
                    if (!visible(grid)) return false;
                    if (grid.querySelector('.dex-card')) return true;
                    return /no pok|no pokemon|no pokémon|match your filters/i.test(gridSignature());
                };
                const waitGridReady = async () => {
                    await waitFor(gridReady, 1800);
                    await sleep(120);
                };
                const selectTab = async (tabName) => {
                    const tab = [...document.querySelectorAll('#pokedex-modal .dex-tab, .dex-tab')]
                        .find(btn => (btn.getAttribute('data-tab') || '').toLowerCase() === tabName);
                    if (activeTab() !== tabName) click(tab);
                    await waitFor(() => {
                        return activeTab() === tabName;
                    }, 1200);
                    await waitGridReady();
                };
                const setMissingOnly = async (enabled) => {
                    const btn = document.querySelector('#dex-hide-caught-btn');
                    if (!btn) return;
                    if (missingActive() !== enabled) {
                        click(btn);
                        await waitFor(() => missingActive() === enabled, 1200);
                        await waitGridReady();
                    }
                };
                const selectAllGenerations = async () => {
                    const all = [...document.querySelectorAll('#pokedex-modal .dex-gen-filter-btn, .dex-gen-filter-btn')]
                        .find(btn => (btn.getAttribute('data-gen') || '').toLowerCase() === 'all');
                    if (all && activeGen() !== 'all') {
                        click(all);
                        await waitFor(() => activeGen() === 'all', 1200);
                        await waitGridReady();
                    }
                };
                const forceDexState = async (tabName, missing) => {
                    await selectTab(tabName);
                    await selectAllGenerations();
                    await setMissingOnly(missing);
                    await waitGridReady();
                    return {
                        tab: activeTab(),
                        gen: activeGen(),
                        missing: missingActive(),
                        cardCount: document.querySelectorAll('#dex-grid-content .dex-card').length,
                        empty: !!document.querySelector('#dex-grid-content .dex-empty'),
                        label: document.querySelector('#dex-count-label')?.innerText || '',
                    };
                };
                const readCards = () => [...document.querySelectorAll('#dex-grid-content .dex-card')]
                    .filter(visible)
                    .map(card => ({
                        id: spriteId(card),
                        name: cardName(card),
                        missing: card.classList.contains('dex-unknown')
                            || !card.querySelector('.dex-caught-badge')
                    }));
                const closeModal = async () => {
                    const modal = document.querySelector('#pokedex-modal');
                    if (!visible(modal)) return true;
                    const close = document.querySelector(
                        '#pokedex-modal .btn-icon-close, '
                        + '#pokedex-modal [aria-label="Close"], '
                        + '#pokedex-modal button[data-shortcut="Esc"], '
                        + '#pokedex-modal .btn-close-glyph'
                    );
                    if (close) click(close.closest('button') || close);
                    await waitFor(() => !visible(document.querySelector('#pokedex-modal')), 1200);
                    return !visible(document.querySelector('#pokedex-modal'));
                };
                (async () => {
                    const modal = await ensureOpen();
                    if (!modal) {
                        done({ok: false, reason: 'pokedex modal did not open', targets: []});
                        return;
                    }
                    const namesById = new Map();
                    const states = [];
                    const addNamesFromTab = async (tabName) => {
                        states.push({stage: `names:${tabName}`, ...(await forceDexState(tabName, false))});
                        for (const card of readCards()) {
                            if (card.id && card.name && card.name !== '???') namesById.set(card.id, card.name);
                        }
                    };
                    await addNamesFromTab('normal');
                    await addNamesFromTab('shiny');

                    const targets = [];
                    const readMissingTab = async (tabName, shiny, includeTargets) => {
                        const state = await forceDexState(tabName, true);
                        states.push({stage: `missing:${tabName}`, ...state});
                        if (!state.missing) {
                            return {
                                ...state,
                                found: 0,
                                totalMissing: 0,
                                legendaryMissing: 0,
                                filterFailed: true,
                            };
                        }
                        const before = targets.length;
                        let totalMissing = 0;
                        let legendaryMissing = 0;
                        for (const card of readCards()) {
                            if (!card.missing) continue;
                            totalMissing += 1;
                            const name = card.name || namesById.get(card.id) || '';
                            const key = normalize(name);
                            if (!key) continue;
                            if (legendaryNames.has(key)) {
                                legendaryMissing += 1;
                                continue;
                            }
                            if (includeTargets) {
                                targets.push({
                                    id: card.id || 0,
                                    name,
                                    key,
                                    shiny,
                                    source: 'pokedex-modal',
                                    aliases: [key]
                                });
                            }
                        }
                        return {
                            ...state,
                            found: targets.length - before,
                            totalMissing,
                            legendaryMissing,
                        };
                    };
                    const normalResult = await readMissingTab('normal', false, wantsNormal);
                    const shinyResult = await readMissingTab('shiny', true, wantsShiny);
                    if ((normalResult && normalResult.filterFailed) || (shinyResult && shinyResult.filterFailed)) {
                        const closed = await closeModal();
                        done({
                            ok: false,
                            reason: 'missing-only Pokedex filter did not activate',
                            targets: [],
                            states,
                            closed,
                        });
                        return;
                    }
                    const closed = await closeModal();
                    done({
                        ok: true,
                        targets,
                        namedSpecies: namesById.size,
                        mode,
                        states,
                        normalMissingFound: normalResult ? normalResult.found : null,
                        shinyMissingFound: shinyResult ? shinyResult.found : null,
                        missingCounts: {
                            normal: {
                                total: normalResult ? normalResult.totalMissing : 0,
                                legendary: normalResult ? normalResult.legendaryMissing : 0,
                            },
                            shiny: {
                                total: shinyResult ? shinyResult.totalMissing : 0,
                                legendary: shinyResult ? shinyResult.legendaryMissing : 0,
                            },
                        },
                        closed,
                    });
                })().catch(async error => {
                    let closed = false;
                    try { closed = await closeModal(); } catch (e) {}
                    done({ok: false, reason: String(error && error.message || error), targets: [], closed});
                });
                """,
                target_mode,
                [self.normalize_pokemon_name(name) for name in LEGENDARY_POKEMON_NAMES],
            )
        except Exception as exc:
            self.log(f"Dex targets: modal read failed ({exc}).")
            return None
        targets = result.get("targets") if isinstance(result, dict) else []
        if isinstance(result, dict):
            self.update_dex_missing_summary(result.get("missingCounts"))
        if not targets:
            reason = result.get("reason") if isinstance(result, dict) else ""
            states = result.get("states") if isinstance(result, dict) else []
            if states:
                state_text = " | ".join(
                    f"{state.get('stage')} tab={state.get('tab')} gen={state.get('gen')} "
                    f"missing={state.get('missing')} cards={state.get('cardCount')} empty={state.get('empty')}"
                    for state in states[-4:]
                )
                self.log(f"Dex targets: modal states: {state_text}.")
            if isinstance(result, dict) and "closed" in result:
                self.log(f"Dex targets: Pokedex modal closed={result.get('closed')}.")
            self.log(f"Dex targets: Pokédex modal returned no named targets{f' ({reason})' if reason else ''}.")
            return []
        self.log(
            f"Dex targets: read {len(targets)} missing target(s) from Pokédex modal "
            f"({int(result.get('namedSpecies') or 0)} named species cached)."
        )
        return targets

    def read_pokedex_data_targets(self, target_mode):
        if target_mode == DEX_TARGET_OFF or not self.driver:
            return None
        try:
            result = self.driver.execute_async_script(
                """
                const mode = arguments[0];
                const legendaryNames = new Set(arguments[1].map(name => String(name || '').toLowerCase()));
                const done = arguments[arguments.length - 1];
                const wantsNormal = mode === 'Missing normal Dex' || mode === 'Missing normal + shiny Dex';
                const wantsShiny = mode === 'Missing shiny Dex' || mode === 'Missing normal + shiny Dex';
                const normalize = (text) => String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
                const title = (text) => normalize(text).replace(/\\b\\w/g, ch => ch.toUpperCase());
                const pokemonImgRe = /pokemon\\/(?:shiny\\/)?(\\d+)\\.png/i;
                const speciesById = new Map();
                const speciesByName = new Map();
                const addSpecies = (id, name, raw) => {
                    id = parseInt(id, 10);
                    const norm = normalize(name);
                    if (!id || !norm || norm === 'unknown' || norm === '???') return;
                    const item = speciesByName.get(norm) || {id, name: title(norm), aliases: new Set([norm]), pre: new Set()};
                    item.id = item.id || id;
                    item.name = item.name || title(norm);
                    item.aliases.add(norm);
                    speciesById.set(id, item);
                    speciesByName.set(norm, item);
                    if (raw && typeof raw === 'object') {
                        for (const key of ['prevo', 'preEvolution', 'pre_evolution', 'baseSpecies', 'evolvesFrom', 'evolves_from']) {
                            const value = raw[key];
                            const parent = typeof value === 'object' ? (value && (value.name || value.species)) : value;
                            const pre = normalize(parent);
                            if (pre && pre !== norm) item.pre.add(pre);
                        }
                    }
                };
                const seenObjects = new Set();
                const inspectObject = (value, depth) => {
                    if (!value || typeof value !== 'object' || seenObjects.has(value) || depth > 5) return;
                    seenObjects.add(value);
                    if (Array.isArray(value)) {
                        if (value.length <= 2500) for (const item of value) inspectObject(item, depth + 1);
                        return;
                    }
                    const id = value.id ?? value.num ?? value.dex ?? value.dexNo ?? value.dexId
                        ?? value.nationalDex ?? value.national_dex ?? value.pokedexNumber;
                    const name = value.name ?? value.species ?? value.pokemon ?? value.label;
                    if (id && name) addSpecies(id, name, value);
                    for (const [key, child] of Object.entries(value)) {
                        if (depth >= 3) continue;
                        if (!/poke|species|dex|mon|data|list|all/i.test(key)) continue;
                        inspectObject(child, depth + 1);
                    }
                };
                for (const img of document.querySelectorAll('img[src*="/pokemon/"], img[src*="pokemon/"]')) {
                    const match = (img.getAttribute('src') || '').match(pokemonImgRe);
                    const alt = img.getAttribute('alt') || img.getAttribute('title') || '';
                    if (match && alt && alt !== '???') addSpecies(match[1], alt, null);
                }
                for (const key of Object.getOwnPropertyNames(window)) {
                    if (/poke|species|dex|mon|data/i.test(key)) {
                        try { inspectObject(window[key], 0); } catch (e) {}
                    }
                }

                const ownedNormal = new Set();
                const ownedShiny = new Set();
                const sourceNormal = new Set();
                const sourceShiny = new Set();
                const addOwned = (set, value) => {
                    if (value === null || value === undefined) return;
                    if (typeof value === 'number') {
                        set.add(String(value));
                        return;
                    }
                    if (typeof value === 'string') {
                        const norm = normalize(value);
                        if (norm) set.add(norm);
                        const num = value.match(/\\b\\d{1,4}\\b/);
                        if (num) set.add(String(parseInt(num[0], 10)));
                        return;
                    }
                    if (typeof value !== 'object') return;
                    const id = value.id ?? value.num ?? value.dex ?? value.dexNo ?? value.dexId
                        ?? value.nationalDex ?? value.pokedexNumber;
                    const name = value.name ?? value.species ?? value.pokemon;
                    if (id) set.add(String(parseInt(id, 10)));
                    if (name) set.add(normalize(name));
                };
                const inspectOwned = (key, value, depth = 0, kind = '') => {
                    const lowerKey = String(key || '').toLowerCase();
                    const isDex = /dex|caught|pokedex|halloffame|hall_of_fame|hof/.test(lowerKey);
                    if (lowerKey.includes('shiny')) kind = 'shiny';
                    else if (lowerKey.includes('normal')) kind = 'normal';
                    else if (isDex && !kind) kind = 'normal';
                    if (!kind && !isDex) return;
                    const set = kind === 'shiny' ? ownedShiny : ownedNormal;
                    const sources = kind === 'shiny' ? sourceShiny : sourceNormal;
                    sources.add(String(key || 'unknown'));
                    if (Array.isArray(value)) {
                        for (const item of value) addOwned(set, item);
                        return;
                    }
                    if (value && typeof value === 'object') {
                        for (const [childKey, childValue] of Object.entries(value)) {
                            const childLower = String(childKey || '').toLowerCase();
                            const childKind = childLower.includes('shiny')
                                ? 'shiny'
                                : childLower.includes('normal')
                                    ? 'normal'
                                    : kind;
                            (childKind === 'shiny' ? sourceShiny : sourceNormal).add(String(childKey || key || 'unknown'));
                            if (childValue === true || childValue === 1 || childValue === '1' || childValue === 'true') {
                                addOwned(childKind === 'shiny' ? ownedShiny : ownedNormal, childKey);
                            } else if (childValue && typeof childValue === 'object' && depth < 6) {
                                inspectOwned(childKey, childValue, depth + 1, childKind);
                            } else {
                                addOwned(childKind === 'shiny' ? ownedShiny : ownedNormal, childValue);
                            }
                        }
                    } else {
                        addOwned(set, value);
                    }
                };
                const inspectStorage = (storage) => {
                    for (let i = 0; i < storage.length; i += 1) {
                        const key = storage.key(i);
                        const raw = storage.getItem(key);
                        try {
                            const parsed = JSON.parse(raw);
                            inspectObject(parsed, 0);
                            inspectOwned(key, parsed);
                        } catch (e) {
                            inspectOwned(key, raw);
                        }
                    }
                };
                inspectStorage(localStorage);
                inspectStorage(sessionStorage);
                for (const key of Object.getOwnPropertyNames(window)) {
                    if (/dex|caught|pokedex|halloffame|hall_of_fame|hof/i.test(key)) {
                        try { inspectOwned(key, window[key]); } catch (e) {}
                    }
                }

                const readIndexedDb = async () => {
                    if (!window.indexedDB || typeof indexedDB.databases !== 'function') return;
                    let databases = [];
                    try { databases = await indexedDB.databases(); } catch (e) { return; }
                    for (const dbInfo of databases || []) {
                        const dbName = dbInfo && dbInfo.name;
                        if (!dbName || !/poke|game|save|local|dex/i.test(dbName)) continue;
                        await new Promise(resolve => {
                            const req = indexedDB.open(dbName);
                            let timer = setTimeout(resolve, 1200);
                            req.onerror = resolve;
                            req.onsuccess = () => {
                                const db = req.result;
                                const names = [...db.objectStoreNames].filter(name => /poke|dex|caught|save|state|game|hof/i.test(name));
                                if (!names.length) {
                                    db.close();
                                    clearTimeout(timer);
                                    resolve();
                                    return;
                                }
                                let pending = names.length;
                                const doneStore = () => {
                                    pending -= 1;
                                    if (pending <= 0) {
                                        db.close();
                                        clearTimeout(timer);
                                        resolve();
                                    }
                                };
                                for (const storeName of names) {
                                    try {
                                        const tx = db.transaction(storeName, 'readonly');
                                        const request = tx.objectStore(storeName).getAll();
                                        request.onsuccess = () => {
                                            inspectObject(request.result, 0);
                                            inspectOwned(`${dbName}:${storeName}`, request.result);
                                        };
                                        tx.oncomplete = doneStore;
                                        tx.onerror = doneStore;
                                        tx.onabort = doneStore;
                                    } catch (e) {
                                        doneStore();
                                    }
                                }
                            };
                        });
                    }
                };

                (async () => {
                    await Promise.race([readIndexedDb(), new Promise(resolve => setTimeout(resolve, 2500))]);
                    const haveNormalData = sourceNormal.size > 0 && ownedNormal.size > 0;
                    const haveShinyData = sourceShiny.size > 0 && ownedShiny.size > 0;
                    const allTargets = [];
                    const counts = {
                        normal: {total: 0, legendary: 0},
                        shiny: {total: 0, legendary: 0},
                    };
                    for (const item of speciesById.values()) {
                        const nameKey = normalize(item.name);
                        if (!item.id || !nameKey) continue;
                        const ownedKeys = [String(item.id), nameKey];
                        const isLegendary = legendaryNames.has(nameKey);
                        if (haveNormalData && !ownedKeys.some(key => ownedNormal.has(key))) {
                            counts.normal.total += 1;
                            if (isLegendary) counts.normal.legendary += 1;
                            else if (wantsNormal) allTargets.push({id: item.id, name: item.name, shiny: false, source: 'page-data'});
                        }
                        if (haveShinyData && !ownedKeys.some(key => ownedShiny.has(key))) {
                            counts.shiny.total += 1;
                            if (isLegendary) counts.shiny.legendary += 1;
                            else if (wantsShiny) allTargets.push({id: item.id, name: item.name, shiny: true, source: 'page-data'});
                        }
                    }
                    const unique = [];
                    const seen = new Set();
                    for (const target of allTargets) {
                        const key = `${normalize(target.name)}|${target.shiny}`;
                        if (seen.has(key)) continue;
                        seen.add(key);
                        const species = speciesByName.get(normalize(target.name));
                        const pre = species ? [...species.pre] : [];
                        unique.push({
                            id: target.id || 0,
                            name: target.name,
                            key: normalize(target.name),
                            shiny: !!target.shiny,
                            source: target.source,
                            aliases: [normalize(target.name), ...pre].filter(Boolean)
                        });
                    }
                    done({
                        ok: true,
                        targets: unique,
                        speciesCount: speciesById.size,
                        ownedNormal: ownedNormal.size,
                        ownedShiny: ownedShiny.size,
                        hasNormalDexData: haveNormalData,
                        hasShinyDexData: haveShinyData,
                        missingCounts: counts,
                    });
                })().catch(error => done({ok: false, reason: String(error && error.message || error), targets: []}));
                """,
                target_mode,
                [self.normalize_pokemon_name(name) for name in LEGENDARY_POKEMON_NAMES],
            )
        except Exception as exc:
            self.log(f"Dex targets: page-data read failed ({exc}).")
            return None
        if not isinstance(result, dict) or not result.get("ok"):
            reason = result.get("reason") if isinstance(result, dict) else ""
            self.log(f"Dex targets: page-data read did not complete{f' ({reason})' if reason else ''}.")
            return None
        self.update_dex_missing_summary(result.get("missingCounts"))
        has_required_data = (
            (target_mode == DEX_TARGET_NORMAL and result.get("hasNormalDexData"))
            or (target_mode == DEX_TARGET_SHINY and result.get("hasShinyDexData"))
            or (
                target_mode == DEX_TARGET_BOTH
                and result.get("hasNormalDexData")
                and result.get("hasShinyDexData")
            )
        )
        if not has_required_data or int(result.get("speciesCount") or 0) < 100:
            self.log(
                "Dex targets: page data incomplete "
                f"(species={int(result.get('speciesCount') or 0)}, "
                f"normalOwned={int(result.get('ownedNormal') or 0)}, "
                f"shinyOwned={int(result.get('ownedShiny') or 0)})."
            )
            return None

        clean_targets = []
        seen = set()
        legendary_keys = {self.normalize_pokemon_name(name) for name in LEGENDARY_POKEMON_NAMES}
        for target in result.get("targets") or []:
            if not isinstance(target, dict):
                continue
            key = self.normalize_pokemon_name(target.get("name") or target.get("key"))
            if not key or key in legendary_keys:
                continue
            shiny = bool(target.get("shiny"))
            marker = (key, shiny)
            if marker in seen:
                continue
            seen.add(marker)
            aliases = []
            for alias in self.evolution_aliases_for_target(key, target.get("aliases") or [key]):
                alias_key = self.normalize_pokemon_name(alias)
                if alias_key and alias_key not in aliases and alias_key not in legendary_keys:
                    aliases.append(alias_key)
            clean_targets.append({
                "name": key,
                "display": str(target.get("name") or key.title()),
                "shiny": shiny,
                "aliases": aliases or [key],
                "source": target.get("source") or "page-data",
            })
        if clean_targets:
            preview = ", ".join(target["display"] for target in clean_targets[:12])
            extra = len(clean_targets) - min(len(clean_targets), 12)
            suffix = f" (+{extra} more)" if extra else ""
            self.log(f"Dex targets loaded from page data ({target_mode}): {preview}{suffix}.")
        else:
            self.log(f"Dex targets: page data found no missing named entries for {target_mode}.")
        return clean_targets

    def read_pokedex_runtime_targets(self, target_mode):
        if target_mode == DEX_TARGET_OFF or not self.driver:
            return None
        try:
            result = self.driver.execute_async_script(
                """
                const mode = arguments[0];
                const legendaryNames = new Set(arguments[1].map(name => String(name || '').toLowerCase()));
                const done = arguments[arguments.length - 1];
                const wantsNormal = mode === 'Missing normal Dex' || mode === 'Missing normal + shiny Dex';
                const wantsShiny = mode === 'Missing shiny Dex' || mode === 'Missing normal + shiny Dex';
                const normalize = (text) => String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
                const title = (text) => normalize(text).replace(/\\b\\w/g, ch => ch.toUpperCase());
                const parseStorage = (key) => {
                    try { return JSON.parse(localStorage.getItem(key) || '{}') || {}; } catch (e) { return {}; }
                };
                const entryName = (entry) => {
                    if (!entry || typeof entry !== 'object') return '';
                    return entry.name || entry.species || entry.pokemon || entry.label || '';
                };
                const entryAliases = (entry) => {
                    const aliases = [];
                    if (!entry || typeof entry !== 'object') return aliases;
                    for (const key of ['prevo', 'preEvolution', 'pre_evolution', 'baseSpecies', 'evolvesFrom', 'evolves_from']) {
                        const value = entry[key];
                        if (typeof value === 'string') aliases.push(normalize(value));
                        else if (value && typeof value === 'object') aliases.push(normalize(value.name || value.species || value.label || ''));
                    }
                    return aliases.filter(Boolean);
                };
                const dexValue = (dex, id) => dex[String(id)] ?? dex[id];
                const isCaught = (value) => {
                    if (typeof window._isDexCaught === 'function') {
                        try { return !!window._isDexCaught(value); } catch (e) {}
                    }
                    if (typeof value === 'number') return value === 1;
                    if (value === true || value === '1' || value === 'true') return true;
                    return !!(value && typeof value === 'object' && value.caught);
                };
                (async () => {
                    const staticDex = typeof loadStaticPokedex === 'function'
                        ? await loadStaticPokedex()
                        : {};
                    const normalDex = typeof getPokedex === 'function'
                        ? getPokedex()
                        : parseStorage('poke_dex');
                    const shinyDex = typeof getShinyDex === 'function'
                        ? getShinyDex()
                        : parseStorage('poke_shiny_dex');
                    const staticIds = Object.keys(staticDex || {}).map(Number).filter(Number.isFinite);
                    const catchableIds = Array.from(new Set(
                        (Array.isArray(window.ALL_CATCHABLE_IDS) && window.ALL_CATCHABLE_IDS.length
                            ? window.ALL_CATCHABLE_IDS
                            : staticIds
                        ).map(Number).filter(Number.isFinite)
                    )).sort((a, b) => a - b);
                    const targets = [];
                    const counts = {
                        normal: {total: 0, legendary: 0},
                        shiny: {total: 0, legendary: 0},
                    };
                    let named = 0;
                    for (const id of catchableIds) {
                        const entry = staticDex[String(id)] || staticDex[id] || (
                            typeof getStaticPokedexEntry === 'function' ? getStaticPokedexEntry(id) : null
                        );
                        const rawName = entryName(entry);
                        const key = normalize(rawName);
                        if (!key || key === 'unknown') continue;
                        named += 1;
                        const isLegendary = legendaryNames.has(key);
                        if (!isCaught(dexValue(normalDex, id))) {
                            counts.normal.total += 1;
                            if (isLegendary) counts.normal.legendary += 1;
                            else if (wantsNormal) {
                                targets.push({
                                    id,
                                    name: rawName,
                                    key,
                                    shiny: false,
                                    source: 'runtime-dex',
                                    aliases: [key, ...entryAliases(entry)]
                                });
                            }
                        }
                        if (!dexValue(shinyDex, id)) {
                            counts.shiny.total += 1;
                            if (isLegendary) counts.shiny.legendary += 1;
                            else if (wantsShiny) {
                                targets.push({
                                    id,
                                    name: rawName,
                                    key,
                                    shiny: true,
                                    source: 'runtime-dex',
                                    aliases: [key, ...entryAliases(entry)]
                                });
                            }
                        }
                    }
                    done({
                        ok: true,
                        targets,
                        missingCounts: counts,
                        staticCount: Object.keys(staticDex || {}).length,
                        catchableCount: catchableIds.length,
                        namedSpecies: named,
                        normalOwned: Object.keys(normalDex || {}).length,
                        shinyOwned: Object.keys(shinyDex || {}).length,
                    });
                })().catch(error => done({ok: false, reason: String(error && error.message || error), targets: []}));
                """,
                target_mode,
                [self.normalize_pokemon_name(name) for name in LEGENDARY_POKEMON_NAMES],
            )
        except Exception as exc:
            self.log(f"Dex targets: runtime read failed ({exc}).")
            return None
        if not isinstance(result, dict) or not result.get("ok"):
            reason = result.get("reason") if isinstance(result, dict) else ""
            self.log(f"Dex targets: runtime read did not complete{f' ({reason})' if reason else ''}.")
            return None
        self.update_dex_missing_summary(result.get("missingCounts"))
        if int(result.get("staticCount") or 0) < 100 or int(result.get("catchableCount") or 0) < 100:
            self.log(
                "Dex targets: runtime data incomplete "
                f"(static={int(result.get('staticCount') or 0)}, "
                f"catchable={int(result.get('catchableCount') or 0)})."
            )
            return None
        clean_targets = []
        seen = set()
        legendary_keys = {self.normalize_pokemon_name(name) for name in LEGENDARY_POKEMON_NAMES}
        for target in result.get("targets") or []:
            if not isinstance(target, dict):
                continue
            key = self.normalize_pokemon_name(target.get("name") or target.get("key"))
            if not key or key in legendary_keys:
                continue
            shiny = bool(target.get("shiny"))
            marker = (key, shiny)
            if marker in seen:
                continue
            seen.add(marker)
            aliases = []
            for alias in self.evolution_aliases_for_target(key, target.get("aliases") or [key]):
                alias_key = self.normalize_pokemon_name(alias)
                if alias_key and alias_key not in aliases and alias_key not in legendary_keys:
                    aliases.append(alias_key)
            clean_targets.append({
                "name": key,
                "display": str(target.get("name") or key.title()),
                "shiny": shiny,
                "aliases": aliases or [key],
                "source": "runtime-dex",
            })
        preview = ", ".join(target["display"] for target in clean_targets[:12])
        extra = len(clean_targets) - min(len(clean_targets), 12)
        suffix = f" (+{extra} more)" if extra else ""
        if clean_targets:
            self.log(f"Dex targets loaded from runtime Dex ({target_mode}): {preview}{suffix}.")
        else:
            self.log(
                f"Dex targets: runtime Dex found no missing non-legendary entries for {target_mode} "
                f"(normalOwned={int(result.get('normalOwned') or 0)}, shinyOwned={int(result.get('shinyOwned') or 0)})."
            )
        return clean_targets

    def collect_missing_dex_targets(self, target_mode):
        if target_mode == DEX_TARGET_OFF or not self.driver:
            return []
        self.log("Dex targets: reading runtime Pokedex data in the background.")
        runtime_targets = self.read_pokedex_runtime_targets(target_mode)
        if runtime_targets is not None:
            self.cached_dex_targets[target_mode] = runtime_targets
            self.cached_dex_target_mode = target_mode
            return runtime_targets
        self.log("Dex targets: runtime Pokedex read failed; refusing to open the visual Pokedex modal.")
        return []
        try:
            result = self.driver.execute_script(
                """
                const mode = arguments[0];
                const legendaryNames = new Set(arguments[1].map(name => String(name || '').toLowerCase()));
                const wantsNormal = mode === 'Missing normal Dex' || mode === 'Missing normal + shiny Dex';
                const wantsShiny = mode === 'Missing shiny Dex' || mode === 'Missing normal + shiny Dex';
                const normalize = (text) => String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
                const title = (text) => normalize(text).replace(/\\b\\w/g, ch => ch.toUpperCase());
                const speciesById = new Map();
                const speciesByName = new Map();
                const addSpecies = (id, name, raw) => {
                    id = parseInt(id, 10);
                    const norm = normalize(name);
                    if (!id || !norm || norm === 'unknown' || norm === '???') return;
                    const item = speciesByName.get(norm) || {id, name: title(norm), aliases: new Set([norm]), pre: new Set(), raw: []};
                    item.id = item.id || id;
                    item.name = item.name || title(norm);
                    item.aliases.add(norm);
                    if (raw) item.raw.push(raw);
                    speciesById.set(id, item);
                    speciesByName.set(norm, item);
                };
                const pokemonImgRe = /pokemon\\/(?:shiny\\/)?(\\d+)\\.png/i;
                for (const img of document.querySelectorAll('img[src*="/pokemon/"], img[src*="pokemon/"]')) {
                    const match = (img.getAttribute('src') || '').match(pokemonImgRe);
                    const alt = img.getAttribute('alt') || img.getAttribute('title') || '';
                    if (match && alt && alt !== '???') addSpecies(match[1], alt, null);
                }
                const seenObjects = new Set();
                const inspectObject = (value, depth) => {
                    if (!value || typeof value !== 'object' || seenObjects.has(value) || depth > 3) return;
                    seenObjects.add(value);
                    if (Array.isArray(value)) {
                        if (value.length > 5 && value.length < 2000) {
                            for (const item of value) inspectObject(item, depth + 1);
                        }
                        return;
                    }
                    const id = value.id ?? value.num ?? value.dex ?? value.dexNo ?? value.nationalDex ?? value.national_dex;
                    const name = value.name ?? value.species ?? value.pokemon ?? value.label;
                    if (id && name) addSpecies(id, name, value);
                    for (const key of ['prevo', 'preEvolution', 'pre_evolution', 'baseSpecies']) {
                        if (value[key] && name) {
                            const norm = normalize(name);
                            const pre = normalize(value[key]);
                            const item = speciesByName.get(norm);
                            if (item && pre && pre !== norm) item.pre.add(pre);
                        }
                    }
                    for (const key of ['evolvesFrom', 'evolves_from']) {
                        const parent = value[key];
                        const parentName = typeof parent === 'object' ? (parent.name || parent.species) : parent;
                        if (parentName && name) {
                            const norm = normalize(name);
                            const pre = normalize(parentName);
                            const item = speciesByName.get(norm);
                            if (item && pre && pre !== norm) item.pre.add(pre);
                        }
                    }
                    for (const key of ['evolutions', 'evolvesTo', 'evolves_to']) {
                        const evos = Array.isArray(value[key]) ? value[key] : [];
                        for (const evo of evos) {
                            const evoName = normalize(typeof evo === 'object' ? (evo.name || evo.species) : evo);
                            const parent = normalize(name);
                            const child = speciesByName.get(evoName);
                            if (child && parent && parent !== evoName) child.pre.add(parent);
                        }
                    }
                    for (const [key, child] of Object.entries(value)) {
                        if (depth >= 2) continue;
                        if (!/poke|species|dex|mon/i.test(key)) continue;
                        inspectObject(child, depth + 1);
                    }
                };
                for (const key of Object.getOwnPropertyNames(window)) {
                    if (/poke|species|dex|mon/i.test(key)) {
                        try { inspectObject(window[key], 0); } catch (e) {}
                    }
                }

                const ownedNormal = new Set();
                const ownedShiny = new Set();
                const addOwned = (set, value) => {
                    if (value === null || value === undefined) return;
                    if (typeof value === 'number') { set.add(String(value)); return; }
                    if (typeof value === 'string') {
                        const norm = normalize(value);
                        if (norm) set.add(norm);
                        const num = value.match(/\\b\\d{1,4}\\b/);
                        if (num) set.add(String(parseInt(num[0], 10)));
                        return;
                    }
                    if (typeof value !== 'object') return;
                    const id = value.id ?? value.num ?? value.dex ?? value.dexNo ?? value.nationalDex;
                    const name = value.name ?? value.species ?? value.pokemon;
                    if (id) set.add(String(parseInt(id, 10)));
                    if (name) set.add(normalize(name));
                };
                const inspectOwned = (key, value) => {
                    const lowerKey = String(key || '').toLowerCase();
                    const isDex = lowerKey.includes('dex') || lowerKey.includes('caught') || lowerKey.includes('pokedex');
                    if (!isDex) return;
                    const set = lowerKey.includes('shiny') ? ownedShiny : ownedNormal;
                    if (Array.isArray(value)) value.forEach(item => addOwned(set, item));
                    else if (value && typeof value === 'object') {
                        for (const [childKey, childValue] of Object.entries(value)) {
                            if (childValue === true || childValue === 1 || childValue === '1' || childValue === 'true') addOwned(set, childKey);
                            else addOwned(set, childValue);
                        }
                    }
                };
                for (let i = 0; i < localStorage.length; i += 1) {
                    const key = localStorage.key(i);
                    const raw = localStorage.getItem(key);
                    try { inspectOwned(key, JSON.parse(raw)); } catch (e) { inspectOwned(key, raw); }
                }
                for (const key of Object.getOwnPropertyNames(window)) {
                    if (/dex|caught|pokedex/i.test(key)) {
                        try { inspectOwned(key, window[key]); } catch (e) {}
                    }
                }

                const modalTargets = [];
                const activeDexTab = document.querySelector('.dex-tab.active')?.getAttribute('data-tab') || '';
                for (const card of document.querySelectorAll('#dex-grid-content .dex-card')) {
                    const text = (card.innerText || card.textContent || '').trim();
                    const idMatch = text.match(/#\\s*(\\d+)/) || (card.querySelector('img')?.getAttribute('src') || '').match(pokemonImgRe);
                    const id = idMatch ? parseInt(idMatch[1], 10) : 0;
                    let name = card.querySelector('.dex-name')?.innerText || card.querySelector('img[alt]')?.getAttribute('alt') || '';
                    if ((!name || name === '???') && speciesById.has(id)) name = speciesById.get(id).name;
                    const isMissing = card.classList.contains('dex-unknown')
                        || !(card.querySelector('.dex-caught-badge') || /already in pok/i.test(card.innerHTML));
                    const shinyCard = activeDexTab === 'shiny' || (card.querySelector('img')?.getAttribute('src') || '').includes('/shiny/');
                    if (isMissing && name && name !== '???') {
                        modalTargets.push({id, name: title(name), shiny: shinyCard, source: 'modal'});
                    }
                }

                const allTargets = [];
                for (const entry of modalTargets) {
                    if ((entry.shiny && wantsShiny) || (!entry.shiny && wantsNormal)) allTargets.push(entry);
                }
                const haveNormalData = ownedNormal.size > 0;
                const haveShinyData = ownedShiny.size > 0;
                if (!allTargets.length && (haveNormalData || haveShinyData)) {
                    for (const item of speciesById.values()) {
                        const nameKey = normalize(item.name);
                        if (!nameKey || legendaryNames.has(nameKey)) continue;
                        const ownedKeys = [String(item.id), nameKey];
                        if (wantsNormal && haveNormalData && !ownedKeys.some(key => ownedNormal.has(key))) {
                            allTargets.push({id: item.id, name: item.name, shiny: false, source: 'storage'});
                        }
                        if (wantsShiny && haveShinyData && !ownedKeys.some(key => ownedShiny.has(key))) {
                            allTargets.push({id: item.id, name: item.name, shiny: true, source: 'storage'});
                        }
                    }
                }
                const unique = [];
                const seen = new Set();
                for (const target of allTargets) {
                    const key = `${normalize(target.name)}|${target.shiny}`;
                    if (seen.has(key)) continue;
                    seen.add(key);
                    const species = speciesByName.get(normalize(target.name));
                    const pre = species ? [...species.pre] : [];
                    unique.push({
                        id: target.id || 0,
                        name: target.name,
                        key: normalize(target.name),
                        shiny: !!target.shiny,
                        source: target.source,
                        aliases: [normalize(target.name), ...pre].filter(Boolean)
                    });
                }
                return {
                    targets: unique,
                    speciesCount: speciesById.size,
                    ownedNormal: ownedNormal.size,
                    ownedShiny: ownedShiny.size,
                    modalCount: modalTargets.length
                };
                """,
                target_mode,
                [self.normalize_pokemon_name(name) for name in LEGENDARY_POKEMON_NAMES],
            )
        except Exception as exc:
            self.log(f"Dex targets: could not read Pokédex data ({exc}).")
            return []
        targets = result.get("targets") if isinstance(result, dict) else []
        if not isinstance(targets, list):
            targets = []
        clean_targets = []
        seen = set()
        for target in targets:
            if not isinstance(target, dict):
                continue
            key = self.normalize_pokemon_name(target.get("name") or target.get("key"))
            if not key or key in {self.normalize_pokemon_name(name) for name in LEGENDARY_POKEMON_NAMES}:
                continue
            shiny = bool(target.get("shiny"))
            marker = (key, shiny)
            if marker in seen:
                continue
            seen.add(marker)
            aliases = []
            for alias in self.evolution_aliases_for_target(key, target.get("aliases") or [key]):
                alias_key = self.normalize_pokemon_name(alias)
                if alias_key and alias_key not in aliases and alias_key not in {self.normalize_pokemon_name(name) for name in LEGENDARY_POKEMON_NAMES}:
                    aliases.append(alias_key)
            clean_targets.append({
                "name": key,
                "display": str(target.get("name") or key.title()),
                "shiny": shiny,
                "aliases": aliases or [key],
                "source": target.get("source") or "unknown",
            })
        if clean_targets:
            preview = ", ".join(target["display"] for target in clean_targets[:12])
            extra = len(clean_targets) - min(len(clean_targets), 12)
            suffix = f" (+{extra} more)" if extra else ""
            self.log(f"Dex targets loaded ({target_mode}): {preview}{suffix}.")
        else:
            self.log(
                f"Dex targets: no named missing entries found for {target_mode}; "
                "using the manual Pokemon whitelist."
            )
        return clean_targets

    def missing_count(self, kind, legendary=False):
        counts = getattr(self, "current_dex_missing_counts", {}) or {}
        bucket = counts.get(kind) or {}
        key = "legendary" if legendary else "total"
        try:
            return int(bucket.get(key) or 0)
        except Exception:
            return 0

    def configure_complete_pokedex_phase(self, phase, target_mode, dex_targets=None):
        dex_targets = dex_targets or []
        labels = {
            "normal_regular": "normal non-legendary",
            "normal_legendary": "normal legendary",
            "shiny_regular": "shiny non-legendary",
            "shiny_legendary": "shiny legendary",
        }
        self.complete_pokedex_phase = phase
        self.complete_pokedex_phase_label = labels.get(phase, phase)
        self.current_dex_target_mode = target_mode
        self.current_reroll_completion_mode = REROLL_COMPLETE_CHAIN_FULL_RUNS
        self.current_item_reroll_targets = [COMPLETE_POKEDEX_ITEM_TARGET]
        self.current_item_reroll_target = COMPLETE_POKEDEX_ITEM_TARGET
        if phase in {"normal_regular", "shiny_regular"}:
            self.current_dex_targets = []
            self.current_target_pokemon_list = self.build_current_pokemon_targets(
                self.current_manual_target_pokemon_list,
                dex_targets,
            )
            self.current_target_pokemon = ", ".join(self.current_target_pokemon_list)
            self.log(
                "Complete Pokedex phase: "
                f"{self.complete_pokedex_phase_label}; rerolling for "
                f"{len(self.current_target_pokemon_list)} target alias(es)."
            )
        else:
            self.current_dex_targets = []
            self.current_dex_target_names = set()
            self.current_dex_target_by_name = {}
            self.current_primary_target_names = set()
            self.current_target_pokemon_list = []
            self.current_target_pokemon = ""
            self.log(
                "Complete Pokedex phase: "
                f"{self.complete_pokedex_phase_label}; rerolling for {COMPLETE_POKEDEX_ITEM_TARGET.title()}."
            )
        return True

    def prepare_complete_pokedex_phase(self, reason="", force_refresh=False):
        if not self.is_complete_pokedex_mode():
            return False
        if force_refresh:
            self.cached_dex_targets = {}
            self.cached_dex_target_mode = None
        suffix = f" after {reason}" if reason else ""
        self.log(f"Complete Pokedex: refreshing missing Dex state{suffix}.")

        normal_targets = self.collect_missing_dex_targets(DEX_TARGET_NORMAL)
        normal_legendary_missing = self.missing_count("normal", legendary=True)
        if normal_targets:
            return self.configure_complete_pokedex_phase(
                "normal_regular",
                DEX_TARGET_NORMAL,
                normal_targets,
            )
        if normal_legendary_missing > 0:
            return self.configure_complete_pokedex_phase(
                "normal_legendary",
                DEX_TARGET_NORMAL,
                [],
            )

        shiny_targets = self.collect_missing_dex_targets(DEX_TARGET_SHINY)
        shiny_legendary_missing = self.missing_count("shiny", legendary=True)
        if shiny_targets:
            return self.configure_complete_pokedex_phase(
                "shiny_regular",
                DEX_TARGET_SHINY,
                shiny_targets,
            )
        if shiny_legendary_missing > 0:
            return self.configure_complete_pokedex_phase(
                "shiny_legendary",
                DEX_TARGET_SHINY,
                [],
            )

        self.complete_pokedex_phase = "done"
        self.complete_pokedex_phase_label = "done"
        self.current_dex_target_mode = DEX_TARGET_BOTH
        self.current_target_pokemon_list = []
        self.current_target_pokemon = ""
        self.set_status("Target found")
        self.log("Complete Pokedex: no missing normal or shiny Dex entries remain.")
        return False

    def build_current_pokemon_targets(self, manual_targets, dex_targets):
        wanted_shiny = self.desired_reroll_shiny_state()
        usable_dex_targets = []
        if self.current_mode == MODE_FULL_RUN:
            usable_dex_targets = dex_targets
        elif self.is_pokemon_reroll_mode():
            usable_dex_targets = [target for target in dex_targets if bool(target.get("shiny")) == wanted_shiny]
        names = []
        primary = set()
        by_name = {}
        for target in usable_dex_targets:
            primary.add(target["name"])
            for alias in target.get("aliases") or [target["name"]]:
                key = self.normalize_pokemon_name(alias)
                if not key or key in {self.normalize_pokemon_name(name) for name in LEGENDARY_POKEMON_NAMES} or key in names:
                    continue
                names.append(key)
                by_name[key] = target
        for name in manual_targets:
            key = self.normalize_pokemon_name(name)
            if key and key not in names:
                names.append(key)
        self.current_dex_targets = usable_dex_targets
        self.current_dex_target_names = set(names)
        self.current_dex_target_by_name = by_name
        self.current_primary_target_names = primary or set(manual_targets)
        return names

    def ensure_dex_targets_ready(self, reason=""):
        if self.is_complete_pokedex_mode():
            if self.complete_pokedex_phase in {"normal_regular", "shiny_regular"} and self.current_target_pokemon_list:
                return True
            return self.prepare_complete_pokedex_phase(reason=reason)
        if self.current_dex_target_mode == DEX_TARGET_OFF:
            return False
        if self.current_dex_targets:
            return True
        if self.cached_dex_target_mode == self.current_dex_target_mode and self.cached_dex_targets.get(self.current_dex_target_mode):
            dex_targets = list(self.cached_dex_targets[self.current_dex_target_mode])
            self.current_target_pokemon_list = self.build_current_pokemon_targets(
                self.current_manual_target_pokemon_list,
                dex_targets,
            )
            self.current_target_pokemon = ", ".join(self.current_target_pokemon_list)
            self.log(f"Dex targets: loaded {len(dex_targets)} cached target(s).")
            return True
        suffix = f" after {reason}" if reason else ""
        self.log(f"Dex targets: retrieving Pokédex targets{suffix}.")
        dex_targets = self.collect_missing_dex_targets(self.current_dex_target_mode)
        self.current_target_pokemon_list = self.build_current_pokemon_targets(
            self.current_manual_target_pokemon_list,
            dex_targets,
        )
        self.current_target_pokemon = ", ".join(self.current_target_pokemon_list)
        return bool(dex_targets)

    def mark_reroll_target_acquired(self, name, shiny):
        key = self.normalize_pokemon_name(name)
        self.reroll_target_acquired = True
        self.reroll_acquired_target_name = key
        if key:
            self.reroll_chain_completed_targets.add(key)
        if self.current_reroll_completion_mode == REROLL_COMPLETE_STOP_NOW:
            return
        if key and key in self.current_target_pokemon_list:
            self.current_target_pokemon_list = [
                target for target in self.current_target_pokemon_list
                if target != key
            ]
        label = "shiny" if shiny else "normal"
        self.log(
            f"Reroll target secured: {label} {(key or name or 'Pokemon').title()}; "
            "continuing this run to completion."
        )

    def remove_acquired_target_from_active_list(self):
        key = self.normalize_pokemon_name(getattr(self, "reroll_acquired_target_name", ""))
        if not key:
            return
        remove_names = {key}
        target = self.current_dex_target_by_name.get(key)
        if target:
            remove_names.update(
                self.normalize_pokemon_name(alias)
                for alias in target.get("aliases", [])
                if self.normalize_pokemon_name(alias)
            )
            remove_names.add(self.normalize_pokemon_name(target.get("name")))
        self.current_target_pokemon_list = [
            name for name in self.current_target_pokemon_list
            if self.normalize_pokemon_name(name) not in remove_names
        ]
        self.current_target_pokemon = ", ".join(self.current_target_pokemon_list)
        if key in self.current_dex_target_by_name:
            target = self.current_dex_target_by_name.pop(key, None)
            if target:
                for alias in target.get("aliases", []):
                    self.current_dex_target_by_name.pop(self.normalize_pokemon_name(alias), None)
        self.current_dex_target_names = {
            name for name in self.current_dex_target_names
            if self.normalize_pokemon_name(name) not in remove_names
        }

    def start_bot(self):
        if self.schedule_enabled_var.get() and self.task_schedule:
            first_settings = self.task_schedule[0].get("settings") if isinstance(self.task_schedule[0], dict) else {}
            self.apply_task_settings_snapshot(first_settings, update_runtime=False)
        selected_mode = self.mode_var.get()
        manual_target_pokemon_list = self.parse_pokemon_target_list(self.target_pokemon_var.get())
        shop_ignore_pokemon_list = self.parse_pokemon_target_list(self.shop_ignore_pokemon_var.get())
        evolution_preference_list = self.parse_pokemon_target_list(self.evolution_preference_var.get())
        item_reroll_targets = self.parse_item_target_list()
        self.run_count = 0
        self.next_history_run_number = self.next_run_history_number()
        self.maps_reached = 0
        self.maps_started = 0
        self.item_rolls_checked = 0
        self.total_encounters_checked = 0
        self.target_encounters_seen = 0
        self.total_shinies_seen = 0
        self.last_shiny_pokemon_name = ""
        self.shop_targets_obtained = 0
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
        self.last_leader_signature = None
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
        self.start_shiny_filter_acquired = False
        self.schedule_active = bool(self.schedule_enabled_var.get())
        self.schedule_index = 0
        self.schedule_progress = [0 for _ in self.task_schedule]
        self.schedule_result_signature = None
        self.pending_replace_add_clicked = False
        self.pending_passive_item_name = ""
        self.pending_passive_item_priority = None
        self.start_time = time.time()
        self.begin_bot_run_token()
        self.stop_event.clear()
        self.current_mode = selected_mode
        self.update_log_panel_title()
        self.current_dex_target_mode = (
            self.full_run_dex_priority_var.get()
            if self.current_mode == MODE_FULL_RUN
            else DEX_TARGET_BOTH
            if self.current_mode == MODE_COMPLETE_POKEDEX
            else DEX_TARGET_OFF
            if self.is_shop_reroll_mode()
            else self.dex_target_var.get()
        )
        if self.current_dex_target_mode not in DEX_TARGET_OPTIONS:
            self.current_dex_target_mode = DEX_TARGET_OFF
        self.current_reroll_completion_mode = self.reroll_completion_var.get()
        if self.current_reroll_completion_mode not in REROLL_COMPLETION_OPTIONS:
            self.current_reroll_completion_mode = REROLL_COMPLETE_STOP_NOW
        self.current_shop_reroll_after_hit = self.shop_reroll_after_hit_var.get()
        if self.current_shop_reroll_after_hit not in SHOP_REROLL_AFTER_HIT_OPTIONS:
            self.current_shop_reroll_after_hit = SHOP_REROLL_AFTER_HIT_STOP
        self.shop_post_hit_safety_run_active = False
        self.reroll_target_acquired = False
        self.reroll_acquired_target_name = ""
        self.reroll_chain_completed_targets = set()
        self.complete_pokedex_phase = ""
        self.complete_pokedex_phase_label = ""
        self.current_pokegold_farm_target = self.parse_pokegold_farm_target()
        self.manual_first_attempt = bool(self.manual_start_var.get())
        self.schedule_default_starter_name = (self.starter_var.get().strip() or STARTER_NAME).lower()
        if self.schedule_active:
            self.browser_count_var.set("1")
            self.log("Task schedule enabled; using one browser so tasks advance in order.")
        self.current_run_target = self.run_target_var.get()
        if self.current_mode == MODE_COMPLETE_POKEDEX:
            self.current_run_target = RUN_TARGET_CHALLENGE
            self.run_target_var.set(RUN_TARGET_CHALLENGE)
            if self.schedule_active:
                self.schedule_active = False
                self.log("Complete Pokedex mode disables the task schedule and uses Challenge Mode.")
        if self.current_mode == MODE_POKEGOLD_FARM:
            self.current_run_target = RUN_TARGET_CHALLENGE
            self.run_target_var.set(RUN_TARGET_CHALLENGE)
        if self.is_shop_reroll_mode():
            self.browser_count_var.set("1")
            if self.schedule_active:
                self.log(f"{self.current_shop_egg_config()['mode_label']} uses one isolated browser for its schedule task.")
        self.run_target_var.set(self.current_run_target)
        self.current_run_target_info = self.parse_run_target(self.current_run_target)
        self.current_tower = self.current_run_target_info.get("name", self.current_run_target)
        self.current_starter_name = self.schedule_default_starter_name
        self.apply_active_schedule_target()
        self.current_manual_target_pokemon_list = manual_target_pokemon_list
        self.current_evolution_preference_list = evolution_preference_list
        self.current_ignore_pokemon = bool(self.ignore_pokemon_var.get())
        self.current_ignore_pokecenter = bool(self.ignore_pokecenter_var.get())
        self.current_shiny_only_pokemon = bool(self.shiny_only_pokemon_var.get())
        self.current_start_shiny_filter_reroll = bool(self.start_shiny_filter_reroll_var.get())
        self.current_no_tm_move_tutor = bool(self.no_tm_move_tutor_var.get())
        self.current_boss_combat_item_swap = bool(self.boss_combat_item_swap_var.get())
        self.current_combat_held_item = self.combat_held_item_var.get().strip()
        self.current_combat_held_items = self.active_combat_held_item_priority()
        self.current_prioritize_party_fill = bool(self.prioritize_party_fill_var.get())
        self.current_delay_party_fill = bool(self.delay_party_fill_var.get())
        self.current_smart_trait_choice = bool(self.smart_trait_choice_var.get())
        self.current_type_whitelist = self.parse_type_whitelist(self.type_whitelist_var.get())
        self.current_type_filter_mode = (
            self.type_filter_mode_var.get()
            if self.type_filter_mode_var.get() in POKEMON_FILTER_OPTIONS
            else POKEMON_FILTER_PRIORITIZE
        )
        self.current_whitelist_filter_mode = (
            self.whitelist_filter_mode_var.get()
            if self.whitelist_filter_mode_var.get() in POKEMON_WHITELIST_OPTIONS
            else POKEMON_WHITELIST_ONLY
        )
        self.current_generation_whitelist = self.parse_generation_whitelist(self.generation_whitelist_var.get())
        self.current_type_filter_names = self.names_for_type_filters(self.current_type_whitelist)
        self.current_generation_filter_names = self.names_for_generation_filters(self.current_generation_whitelist)
        self.current_dex_targets = []
        self.current_shop_ignore_pokemon_list = shop_ignore_pokemon_list
        self.current_target_pokemon_list = self.build_current_pokemon_targets(manual_target_pokemon_list, [])
        self.current_target_pokemon = ", ".join(self.current_target_pokemon_list)
        self.current_item_reroll_targets = item_reroll_targets
        self.current_item_reroll_target = ", ".join(item_reroll_targets)
        self.browser_count = self.parse_browser_count()
        if self.is_shop_reroll_mode():
            self.browser_count = 1
            self.browser_count_var.set("1")
        self.chrome_restart_minutes = self.parse_chrome_restart_minutes()
        self.winning_driver = None
        self.worker_errors = []
        self.save_settings()
        if self.chrome_restart_minutes > 0:
            self.log(
                f"Chrome restart enabled every {self.chrome_restart_minutes:g} minute(s); "
                "the bot will resume the visible saved run after relaunch."
            )
        if self.current_mode == MODE_ITEM_REROLL:
            self.log(
                "Item reroll target: "
                f"{self.current_item_reroll_target}; passive/item rolls are target-only."
            )
        if self.current_mode == MODE_COMPLETE_POKEDEX:
            self.log(
                "Complete Pokedex mode enabled: normal non-legendary, normal legendary, "
                "shiny non-legendary, then shiny legendary."
            )
        if self.current_mode == MODE_POKEGOLD_FARM:
            self.log(
                f"Farm Pokegold mode enabled: running Challenge Mode until "
                f"{self.current_pokegold_farm_target:,} Pokegold is earned this session."
            )
        if self.is_shop_reroll_mode():
            config = self.current_shop_egg_config()
            self.log(
                f"{config['mode_label']} mode enabled: buying {config['label']} in one isolated browser; "
                "force upload only after a shiny whitelist hit."
            )
        if self.current_dex_target_mode != DEX_TARGET_OFF:
            self.log(
                f"Dex target mode enabled: {self.current_dex_target_mode}. "
                "Targets will be read from the first loaded PokeLike browser."
            )
        if self.current_ignore_pokemon:
            self.log("Full-run filter enabled: ignoring Pokemon nodes and Pokemon rewards.")
        else:
            if self.current_shiny_only_pokemon:
                self.log("Full-run filter enabled: only shiny Pokemon will be accepted.")
            if self.current_type_whitelist:
                self.log(f"Full-run type whitelist: {', '.join(sorted(self.current_type_whitelist))}.")
            if self.current_generation_whitelist:
                self.log(f"Full-run generation whitelist: {', '.join(sorted(self.current_generation_whitelist))}.")
            if self.current_smart_trait_choice:
                self.log("Full-run filter enabled: smart type ability choice.")
            if self.current_start_shiny_filter_reroll:
                self.log("Full-run start gate enabled: rerolling until a shiny Pokemon matches active filters.")
        self.log("Full-run route rule: Pokecenter is lowest priority and only used when unavoidable.")
        if self.current_no_tm_move_tutor:
            self.log("Full-run filter enabled: skipping TMs and move tutor nodes.")
        if self.current_boss_combat_item_swap and self.current_combat_held_items:
            self.log(
                "Full-run boss item swap enabled: "
                f"{', '.join(self.current_combat_held_items)} for bosses, then restore top held priority."
            )
        if self.current_prioritize_party_fill:
            self.log("Full-run route option enabled: prioritizing catches while party is under 6.")
        if self.current_delay_party_fill:
            self.log("Full-run route option enabled: delaying party-fill catch priority until map 3.")

        self.start_button.configure(state="disabled")
        self.open_browser_button.configure(state="disabled")
        self.force_cloud_save_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.mode_selector.configure(state="disabled")
        self.run_target_selector.configure(state="disabled")
        self.settings_button.configure(state="disabled")
        self.priority_button.configure(state="disabled")
        self.starter_entry.configure(state="disabled")
        self.target_pokemon_entry.configure(state="disabled")
        self.shop_ignore_pokemon_entry.configure(state="disabled")
        self.manual_start_checkbox.configure(state="disabled")
        self.headless_checkbox.configure(state="disabled")
        self.browser_count_entry.configure(state="disabled")
        self.chrome_restart_entry.configure(state="disabled")
        self.configure_settings_controls("disabled")
        self.runtime_label.configure(text="00:00:00")
        self.money_label.configure(text="0 (0/h)")
        self.update_stats_labels()
        self.set_status("Running")
        self.update_runtime_label()

        self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        self.log("Stopping...")
        self.set_status("Stopping")
        self.invalidate_bot_run_token()
        self.stop_event.set()

        self.finish_ui()

    def finish_ui(self):
        self.safe_ui(lambda: self.runtime_label.configure(text=self.format_runtime()))
        self.safe_ui(lambda: self.open_browser_button.configure(state="normal"))
        self.safe_ui(lambda: self.force_cloud_save_button.configure(state="normal"))
        self.safe_ui(lambda: self.start_button.configure(state="normal"))
        self.safe_ui(lambda: self.stop_button.configure(state="disabled"))
        self.safe_ui(lambda: self.mode_selector.configure(state="normal"))
        self.safe_ui(lambda: self.run_target_selector.configure(state="normal"))
        self.safe_ui(lambda: self.settings_button.configure(state="normal"))
        self.safe_ui(lambda: self.priority_button.configure(state="normal"))
        self.safe_ui(lambda: self.starter_entry.configure(state="normal"))
        self.safe_ui(lambda: self.target_pokemon_entry.configure(state="normal"))
        self.safe_ui(lambda: self.shop_ignore_pokemon_entry.configure(state="normal"))
        self.safe_ui(lambda: self.manual_start_checkbox.configure(state="normal"))
        self.safe_ui(lambda: self.headless_checkbox.configure(state="normal"))
        self.safe_ui(lambda: self.browser_count_entry.configure(state="normal"))
        self.safe_ui(lambda: self.chrome_restart_entry.configure(state="normal"))
        self.safe_ui(lambda: self.configure_settings_controls("normal"))

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

    def chrome_profile_copy_ignore(self, _dir, names):
        ignored_names = {
            "SingletonCookie",
            "SingletonLock",
            "SingletonSocket",
            "LOCK",
            "lockfile",
            "Crashpad",
            "BrowserMetrics",
            "ShaderCache",
            "GrShaderCache",
            "DawnCache",
            "GPUCache",
            "Code Cache",
            "Cache",
        }
        ignored = set()
        for name in names:
            if name in ignored_names or name.startswith("BrowserMetrics"):
                ignored.add(name)
        return ignored

    def safe_replace_profile_copy(self, source_path, target_path):
        if not os.path.isdir(source_path):
            raise RuntimeError(f"Source Chrome profile does not exist: {source_path}")
        if os.path.abspath(source_path) == os.path.abspath(target_path):
            raise RuntimeError("Refusing to copy Chrome profile onto itself.")
        temp_path = f"{target_path}.tmp-{time.strftime('%Y%m%d-%H%M%S')}"
        if os.path.isdir(temp_path):
            shutil.rmtree(temp_path, ignore_errors=True)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copytree(source_path, temp_path, ignore=self.chrome_profile_copy_ignore)
        if os.path.isdir(target_path):
            shutil.rmtree(target_path, ignore_errors=True)
        os.replace(temp_path, target_path)

    def legendary_shop_seed_profile_path(self):
        return f"{SELENIUM_PROFILE_PATH}-shop-seed"

    def legendary_shop_attempt_profile_path(self, slot=None, attempt_id=None):
        if attempt_id is not None:
            suffix = f"-{int(slot or 1)}-{int(attempt_id)}"
        else:
            suffix = "" if slot is None else f"-{int(slot)}"
        return f"{SELENIUM_PROFILE_PATH}-shop-attempt{suffix}"

    def remove_driver_reference(self, driver):
        with self.drivers_lock:
            self.worker_drivers = [candidate for candidate in self.worker_drivers if candidate is not driver]
        if self._driver is driver:
            self._driver = None
            self._wait = None

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

    def chrome_debug_port_for_worker(self, worker_id):
        return CHROME_DEBUG_PORT_BASE + max(0, worker_id - 1)

    def mark_bot_browser_window(self, driver, worker_id):
        if self.headless_var.get():
            return
        marker = "PokeLike Bot" if worker_id <= 1 else f"PokeLike Bot {worker_id}"
        script = f"""
(() => {{
    const marker = {json.dumps(marker)};
    const applyMarker = () => {{
        if (!document.title || document.title.startsWith(marker + " - ")) {{
            return;
        }}
        document.title = marker + " - " + document.title;
    }};
    applyMarker();
    new MutationObserver(applyMarker).observe(
        document.querySelector("title") || document.documentElement,
        {{ childList: true, subtree: true, characterData: true }}
    );
}})();
"""
        try:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": script})
            driver.execute_script(script)
        except Exception as exc:
            self.log(f"Could not mark browser {worker_id} window title: {exc}")

    def try_reconnect_driver(self, worker_id, make_active=True):
        if self.headless_var.get():
            return None
        port = self.chrome_debug_port_for_worker(worker_id)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=0.35) as response:
                version_info = json.loads(response.read().decode("utf-8", errors="replace"))
            if not version_info.get("webSocketDebuggerUrl"):
                return None
        except Exception:
            return None

        options = webdriver.ChromeOptions()
        options.debugger_address = f"127.0.0.1:{port}"
        try:
            driver = webdriver.Chrome(
                service=Service(self.get_chromedriver_path()),
                options=options,
            )
        except Exception as manager_exc:
            self.log(f"Chrome reconnect via ChromeDriverManager failed, trying Selenium Manager fallback: {manager_exc}")
            try:
                driver = webdriver.Chrome(options=options)
            except Exception as selenium_exc:
                self.log(f"Could not reconnect to browser {worker_id} on port {port}: {selenium_exc}")
                return None

        try:
            _ = driver.current_url
        except Exception as exc:
            self.log(f"Reconnected browser {worker_id}, but it was not usable: {exc}")
            try:
                driver.quit()
            except Exception:
                pass
            return None

        self.mark_bot_browser_window(driver, worker_id)
        wait = WebDriverWait(driver, 30)
        if make_active:
            self.driver = driver
            self.wait = wait
        with self.drivers_lock:
            if driver not in self.worker_drivers:
                self.worker_drivers.append(driver)
        self.log(f"Reused existing Chrome window for browser {worker_id}.")
        return driver

    def launch_driver(
        self,
        worker_id=1,
        make_active=True,
        profile_path_override=None,
        allow_reconnect=True,
        window_rect=None,
        force_headless=None,
    ):
        if profile_path_override:
            profile_path = profile_path_override
        else:
            self.ensure_worker_profile(worker_id)
            profile_path = self.profile_path_for_worker(worker_id)
        os.makedirs(profile_path, exist_ok=True)

        if force_headless is None:
            try:
                headless = bool(self.headless_var.get())
            except Exception:
                headless = False
        else:
            headless = bool(force_headless)

        if allow_reconnect:
            existing_driver = self.try_reconnect_driver(worker_id, make_active=make_active)
            if existing_driver:
                self.apply_browser_window_rect(existing_driver, window_rect)
                return existing_driver

        def build_options(safe=False, active_profile_path=None):
            active_profile_path = active_profile_path or profile_path
            o = webdriver.ChromeOptions()
            o.add_argument(f"--user-data-dir={active_profile_path}")
            o.add_argument("--profile-directory=Default")
            o.add_argument("--no-first-run")
            o.add_argument("--no-default-browser-check")
            o.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            o.add_experimental_option("useAutomationExtension", False)
            o.add_experimental_option("detach", True)
            o.set_capability("unhandledPromptBehavior", "ignore")
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
                # exist"), we still launch. Keep the stable DevTools port so the
                # next app start can reuse this window.
                o.add_argument(f"--remote-debugging-port={self.chrome_debug_port_for_worker(worker_id)}")
                if not headless:
                    if window_rect:
                        o.add_argument(f"--window-size={int(window_rect['width'])},{int(window_rect['height'])}")
                        o.add_argument(f"--window-position={int(window_rect['x'])},{int(window_rect['y'])}")
                    else:
                        o.add_argument("--start-maximized")
                return o
            # Enhancements: keep the game's loop running while minimized/occluded,
            # and use a stable DevTools port so a restarted bot can reconnect.
            o.add_argument("--disable-blink-features=AutomationControlled")
            o.add_argument("--disable-background-timer-throttling")
            o.add_argument("--disable-backgrounding-occluded-windows")
            o.add_argument("--disable-renderer-backgrounding")
            o.add_argument(f"--remote-debugging-port={self.chrome_debug_port_for_worker(worker_id)}")
            if not headless:
                if window_rect:
                    o.add_argument(f"--window-size={int(window_rect['width'])},{int(window_rect['height'])}")
                    o.add_argument(f"--window-position={int(window_rect['x'])},{int(window_rect['y'])}")
                else:
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
        self.apply_browser_window_rect(driver, window_rect)
        self.mark_bot_browser_window(driver, worker_id)
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

    def apply_browser_window_rect(self, driver, window_rect):
        if not window_rect:
            return
        try:
            driver.set_window_rect(
                x=int(window_rect.get("x", 0)),
                y=int(window_rect.get("y", 0)),
                width=max(120, int(window_rect.get("width", 900))),
                height=max(120, int(window_rect.get("height", 700))),
            )
        except Exception:
            pass

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
        self.driver = keep_driver
        self.wait = WebDriverWait(keep_driver, 30)
        if self.winning_driver is keep_driver:
            self.disable_legendary_shop_network_guard(keep_driver)
            try:
                keep_driver.execute_script("window.__pokelikeBotAllowCloudUpload = true;")
            except Exception:
                pass

    def replace_current_worker_driver(self, worker_id):
        old_driver = self.driver
        try:
            old_driver.quit()
        except Exception:
            pass
        new_driver = self.launch_driver(worker_id=worker_id, make_active=True)
        with self.drivers_lock:
            self.worker_drivers = [
                new_driver if driver is old_driver else driver
                for driver in self.worker_drivers
                if driver is new_driver or driver is not old_driver
            ]
            if new_driver not in self.worker_drivers:
                self.worker_drivers.append(new_driver)
        self.thread_local.driver = new_driver
        self.thread_local.wait = WebDriverWait(new_driver, 30)
        return new_driver

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

    def cloud_save_conflict_visible(self, driver=None):
        target_driver = driver or self.driver
        if not target_driver:
            return None
        try:
            result = target_driver.execute_script(
                """
                const visible = (el) => {
                    if (!el) return false;
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0
                        && style.display !== 'none'
                        && style.visibility !== 'hidden';
                };
                const textFor = (el) => `${el.innerText || el.textContent || ''} ${el.getAttribute('aria-label') || ''} ${el.title || ''}`
                    .replace(/\\s+/g, ' ')
                    .trim();
                const nodes = [...document.querySelectorAll('button, [role="button"], .modal, .toast, .notification, .alert, [class*="modal" i], [class*="toast" i], [class*="notification" i]')]
                    .filter(visible);
                const hits = nodes
                    .map(textFor)
                    .filter(text => {
                        const lower = text.toLowerCase();
                        return lower.includes('keep local save') || lower.includes('load cloud');
                    });
                return hits.length ? {found: true, text: hits.slice(0, 3).join(' | ')} : {found: false};
                """
            )
        except Exception:
            return None
        if isinstance(result, dict) and result.get("found"):
            return result.get("text") or "cloud save conflict"
        return None

    def stop_if_cloud_save_conflict_visible(self, driver=None):
        text = self.cloud_save_conflict_visible(driver)
        if not text:
            return False
        self.stop_event.set()
        self.set_status("Cloud save conflict")
        self.log(f"Cloud save conflict visible; stopped without choosing local/cloud save ({text}).")
        return True

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

    def prepare_page(self, cookie_timeout=4):
        self.driver.get(POKELIKE_URL)
        self.wait.until(lambda _: self.driver.execute_script("return document.readyState") in ["interactive", "complete"])

        try:
            self.js_click(".qc-cmp2-summary-buttons button:last-child", timeout=cookie_timeout)
            self.log("Cookie prompt accepted.")
        except Exception:
            pass

    def click_visible_resume_button(self):
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
                el.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                el.click();
                el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            };
            const button = [...document.querySelectorAll('button, [role="button"]')]
                .filter(visible)
                .find(btn => {
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    const id = (btn.id || '').toLowerCase();
                    const cls = (btn.className || '').toString().toLowerCase();
                    return text.includes('resume')
                        || id.includes('continue')
                        || cls.includes('title-mode-resume');
                });
            if (!button) return {clicked: false};
            click(button);
            return {clicked: true, text: (button.innerText || button.textContent || '').trim()};
            """
        )
        if result.get("clicked"):
            self.log(f"Clicked title action: {result.get('text') or 'Resume'}")
            time.sleep(1.0)
            return True
        return False

    def click_resume_challenge_if_visible(self):
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
                el.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                el.click();
                el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                el.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            };
            const button = document.querySelector('#btn-continue-challenge')
                || [...document.querySelectorAll('button, [role="button"]')]
                    .filter(visible)
                    .find(btn => {
                        const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                        const cls = (btn.className || '').toString().toLowerCase();
                        return text.includes('resume challenge')
                            || cls.includes('title-mode-resume--challenge');
                    });
            if (!button || !visible(button)) return {clicked: false};
            click(button);
            return {clicked: true, text: (button.innerText || button.textContent || '').trim()};
            """
        )
        if result.get("clicked"):
            self.resumed_existing_challenge_run = True
            self.log(f"Existing Challenge run detected; clicked {result.get('text') or 'Resume Challenge'} and will finish it first.")
            time.sleep(1.0)
            return True
        return False

    def restart_chrome_if_due(self, worker_id):
        if not self.chrome_restart_minutes or self.chrome_restart_minutes <= 0:
            return False
        now = time.time()
        last_restart = getattr(self.thread_local, "last_chrome_restart_at", None) or self.run_started_at or now
        if now - last_restart < self.chrome_restart_minutes * 60:
            return False
        self.log(f"B{worker_id}: restarting Chrome after {self.chrome_restart_minutes:g} minute(s), then resuming run.")
        self.thread_local.last_chrome_restart_at = now
        self.replace_current_worker_driver(worker_id)
        self.prepare_page()
        for _ in range(8):
            if self.click_visible_resume_button():
                return True
            if self.active_screen_id() in [
                "map-screen", "battle-screen", "item-screen", "catch-screen", "badge-screen",
                "passive-screen", "stat-buff-screen", "swap-screen", "elite-prep-screen",
            ]:
                return True
            time.sleep(0.5)
        raise RuntimeError("Chrome restarted, but no Resume button or active run screen appeared.")

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

        if self.active_screen_id() in ["title-screen", "challenge-select"] and self.click_resume_challenge_if_visible():
            return

        if self.active_screen_id() in run_screens:
            reroll_mode = (
                self.current_mode == MODE_SHINY_CHARM_REROLL
                or self.is_pokemon_reroll_mode()
                or self.is_complete_pokedex_mode()
            )
            if not reroll_mode and self.should_use_full_run_logic():
                self.resumed_existing_challenge_run = True
                self.log(f"Existing run detected on {self.active_screen_id()}; finishing it before starting the configured run.")
                return
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
                    const timeoutMs = arguments[0];
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
                    while (Date.now() - started < timeoutMs) {
                        const button = findConfirm();
                        if (button && button.dataset?.menu !== 'reset') {
                            clickButton(button);
                            return true;
                        }
                    }
                    return false;
                    """,
                    160 if reroll_mode else 800,
                )
                if reroll_mode:
                    try:
                        WebDriverWait(self.driver, 0.2).until(
                            lambda _: self.active_screen_id() in ["title-screen", "challenge-select"]
                            or self.active_screen_id() in run_screens
                        )
                    except Exception:
                        pass
                else:
                    try:
                        WebDriverWait(self.driver, 1.5).until(
                            lambda _: self.active_screen_id() in ["title-screen", "challenge-select"]
                        )
                    except Exception:
                        pass
                self.log(f"In-game reset requested via {reset_result.get('method')}.")
            if self.active_screen_id() in run_screens:
                if reroll_mode:
                    self.log(f"Reset returned to run screen={self.active_screen_id()}; continuing reroll.")
                    return
                raise RuntimeError(f"Could not leave active run screen after reset; current screen={self.active_screen_id()}")
            return

        if self.active_screen_id() not in ["title-screen", "challenge-select"]:
            self.prepare_page()
            time.sleep(0.15)
            if self.active_screen_id() in ["title-screen", "challenge-select"] and self.click_resume_challenge_if_visible():
                return

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
        if not getattr(self, "shop_post_hit_safety_run_active", False):
            self.apply_active_schedule_target()
        self.reset_current_run_if_needed()

        if self.is_active_run_screen() and getattr(self, "resumed_existing_challenge_run", False):
            self.log(f"Using resumed existing Challenge run; screen={self.active_screen_id()}.")
            return False

        if (
            self.current_mode == MODE_SHINY_CHARM_REROLL
            or self.is_pokemon_reroll_mode()
            or self.is_complete_pokedex_mode()
        ) and self.is_active_run_screen():
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

        if target_only:
            target_aliases = getattr(self, "current_item_reroll_targets", None) or [DEFAULT_ITEM_REROLL_TARGET]
            for choice in choices:
                choice_text = f"{choice['name']} {choice.get('text', '')}".lower()
                if any(alias in choice_text for alias in target_aliases):
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
            const ignored = arguments[2].map(name => name.toLowerCase());
            const known = arguments[3].map(name => name.toLowerCase());
            const combatPriority = arguments[4].map(name => name.toLowerCase());
            const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
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
            const priorityIndex = (name) => {
                const norm = normalize(name);
                const idx = priority.findIndex(alias => norm.includes(alias));
                return idx < 0 ? null : idx;
            };
            const priorityMatches = (name) => {
                const norm = normalize(name);
                return priority.some(alias => norm.includes(alias));
            };
            const combatIndex = (name) => {
                const norm = normalize(name);
                const idx = combatPriority.findIndex(alias => norm.includes(alias));
                return idx < 0 ? null : idx;
            };
            const combatMatches = (name) => combatIndex(name) !== null;
            const ignoredMatches = (name) => {
                const norm = normalize(name);
                return !priorityMatches(name) && !combatMatches(name) && ignored.some(alias => norm.includes(alias));
            };
            const isRecognized = (name) => {
                const norm = normalize(name);
                if (!norm) return false;
                return priorityMatches(name)
                    || combatMatches(name)
                    || ignored.some(alias => norm.includes(alias))
                    || known.some(alias => norm.includes(alias));
            };
            const consumableIndex = (name) => {
                const norm = normalize(name);
                const idx = [...consumables].findIndex(alias => norm.includes(alias));
                return idx < 0 ? null : idx;
            };
            const choiceCards = [...document.querySelectorAll('#item-choices .item-card')]
                .filter(card => {
                    const rect = card.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                });
            const choices = choiceCards.map((card, index) => {
                const name = nameFor(card).replace(/\\s+/g, ' ').slice(0, 80);
                return {
                    index,
                    name,
                    priority: priorityIndex(name),
                    combatPriority: combatIndex(name),
                    consumable: consumableIndex(name) !== null,
                    consumablePriority: consumableIndex(name),
                    ignored: ignoredMatches(name),
                    recognized: isRecognized(name),
                    detail: detailFor(card)
                };
            });
            const itemDetails = choices
                .filter(choice => choice.name && choice.detail)
                .map(choice => ({name: choice.name, detail: choice.detail}));
            const ignoredNames = choices
                .filter(choice => choice.ignored)
                .map(choice => choice.name);
            const unrecognizedNames = choices
                .filter(choice => !choice.ignored && !choice.recognized)
                .map(choice => choice.name);
            const ownedRoots = ['#item-bar', '#elite-prep-items', '#item-team-bar', '#catch-team-bar', '#passive-team-bar'];
            const owned = ownedRoots.flatMap(selector => [...document.querySelectorAll(`${selector} img[alt], ${selector} img[title]`)])
                .concat([...document.querySelectorAll('.team-slot-item img[alt], .team-slot-item img[title], .battle-poke-item img[alt], .battle-poke-item img[title]')])
                .map(img => img.getAttribute('alt') || img.getAttribute('title') || '')
                .filter(Boolean);
            const ownedPriority = owned
                .map(priorityIndex)
                .filter(value => value !== null && !choices.some(choice => choice.consumable && choice.priority === value));
            const bestOwnedHeld = ownedPriority.length ? Math.min(...ownedPriority) : null;
            const ownedCombatPriority = owned
                .map(name => combatIndex(name))
                .filter(value => value !== null);
            const bestOwnedCombat = ownedCombatPriority.length ? Math.min(...ownedCombatPriority) : null;

            const consumableChoices = choices
                .filter(choice => !choice.ignored && choice.recognized && choice.consumable)
                .sort((a, b) => {
                    const ap = a.priority === null ? Number.POSITIVE_INFINITY : a.priority;
                    const bp = b.priority === null ? Number.POSITIVE_INFINITY : b.priority;
                    if (ap !== bp) return ap - bp;
                    return (a.consumablePriority ?? 999) - (b.consumablePriority ?? 999);
                });
            if (consumableChoices.length) {
                const choice = consumableChoices[0];
                return {take: true, index: choice.index, name: choice.name, reason: 'pickup', owned, offered: choices.map(choice => choice.name), ignoredNames, unrecognizedNames, itemDetails};
            }

            const combatChoices = choices
                .filter(choice =>
                    !choice.ignored
                    && choice.recognized
                    && !choice.consumable
                    && choice.combatPriority !== null
                    && (bestOwnedCombat === null || choice.combatPriority < bestOwnedCombat)
                )
                .sort((a, b) => a.combatPriority - b.combatPriority);
            if (combatChoices.length) {
                const choice = combatChoices[0];
                return {take: true, index: choice.index, name: choice.name, reason: 'combat', owned, offered: choices.map(choice => choice.name), ignoredNames, unrecognizedNames, itemDetails};
            }

            const ranked = choices
                .filter(choice => !choice.ignored && choice.recognized && !choice.consumable && choice.priority !== null)
                .sort((a, b) => a.priority - b.priority);
            for (const choice of ranked) {
                if (bestOwnedHeld === null || choice.priority < bestOwnedHeld) {
                    return {take: true, index: choice.index, name: choice.name, reason: 'upgrade', owned, offered: choices.map(choice => choice.name), ignoredNames, unrecognizedNames, itemDetails};
                }
            }
            return {take: false, owned, offered: choices.map(choice => choice.name), ignoredNames, unrecognizedNames, itemDetails};
            """,
            list(self.active_regular_item_priority()),
            [
                alias for alias in CONSUMABLE_ITEM_ALIASES
                if not (
                    getattr(self, "current_no_tm_move_tutor", False)
                    and self.normalize_item_name(alias) == "tm"
                )
            ],
            self.active_regular_item_ignore() + sorted(self.unknown_regular_items),
            list(KNOWN_PASSIVE_ITEMS),
            list(self.active_combat_held_item_priority()),
        )
        item_details = decision.get("itemDetails") or []
        ignored_names = decision.get("ignoredNames") or []
        unrecognized_names = decision.get("unrecognizedNames") or []
        if item_details:
            self.record_passive_item_details(item_details)
        if unrecognized_names:
            self.log("Unrecognized held item(s) -> don't pick: " + ", ".join(unrecognized_names))
            self.record_unknown_regular_items(unrecognized_names)
        if ignored_names:
            self.log("Ignored held item(s): " + ", ".join(ignored_names))
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
            const filters = arguments[0] || {};
            const ignorePokemon = !!filters.ignorePokemon;
            const shinyOnly = !!filters.shinyOnly;
            const manualNames = new Set((filters.manualNames || []).map(name => String(name).toLowerCase()));
            const typeNames = new Set((filters.typeNames || []).map(name => String(name).toLowerCase()));
            const generationNames = new Set((filters.generationNames || []).map(name => String(name).toLowerCase()));
            const typeWhitelist = new Set((filters.typeWhitelist || []).map(name => String(name).toLowerCase()));
            const generationWhitelist = new Set((filters.generationWhitelist || []).map(name => String(name).toLowerCase()));
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };
            const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const clickButton = (button) => {
                button.scrollIntoView({block: 'center', inline: 'center'});
                button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                button.click();
                button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
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
            const filters = arguments[0] || {};
            const ignorePokemon = !!filters.ignorePokemon;
            const manualNames = new Set((filters.manualNames || []).map(name => String(name).toLowerCase()));
            const typeNames = new Set((filters.typeNames || []).map(name => String(name).toLowerCase()));
            const generationNames = new Set((filters.generationNames || []).map(name => String(name).toLowerCase()));
            const typeWhitelist = new Set((filters.typeWhitelist || []).map(name => String(name).toLowerCase()));
            const generationWhitelist = new Set((filters.generationWhitelist || []).map(name => String(name).toLowerCase()));
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0
                    && getComputedStyle(el).display !== 'none'
                    && getComputedStyle(el).visibility !== 'hidden';
            };
            const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const click = (button) => {
                button.scrollIntoView({block: 'center', inline: 'center'});
                button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                button.click();
                button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            };
            const button = document.querySelector('#btn-take-shiny');
            if (!button || !visible(button)) return {clicked: false};
            const active = document.querySelector('.screen.active') || document;
            const screenText = (active.innerText || '').toLowerCase();
            const name = (
                active.querySelector('.poke-name, .dex-name, .catch-name')?.innerText
                || active.querySelector('img[alt]')?.getAttribute('alt')
                || ''
            ).trim();
            const key = normalize(name || button.innerText || screenText);
            const typeAllowed = !typeWhitelist.size
                || typeNames.has(key)
                || [...typeWhitelist].some(typeName => screenText.includes(`${typeName} type`) || screenText.includes(typeName));
            const generationAllowed = !generationWhitelist.size || generationNames.has(key);
            const manualAllowed = !manualNames.size || manualNames.has(key);
            if (ignorePokemon || !typeAllowed || !generationAllowed || !manualAllowed) {
                const skipButton = [...document.querySelectorAll('#btn-skip-shiny, button, [role="button"]')]
                    .filter(visible)
                    .find(btn => {
                        const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                        return text.includes('skip') || text.includes('decline');
                    });
                if (!skipButton) return {clicked: false, filteredOut: true, name};
                click(skipButton);
                return {clicked: true, skipped: true, filteredOut: true, text: (skipButton.innerText || skipButton.textContent || '').trim(), name};
            }
            click(button);
            return {clicked: true, text: (button.innerText || button.textContent || '').trim()};
            """,
            self.pokemon_filter_payload(),
        )
        if result.get("clicked"):
            if result.get("filteredOut"):
                self.log(f"Shiny reward skipped by filters: {result.get('name') or result.get('text') or 'Pokemon'}.")
                time.sleep(0.6)
                return True
            self.log(f"Shiny reward: {result.get('text') or 'Take shiny Pokemon'}")
            # This is always a shiny (#btn-take-shiny). Count it. Only reached if
            # handle_pokemon_reward_policy did not already take/count it this pass,
            # so there is no double count.
            if self.should_count_run_shiny_stats():
                with self.stats_lock:
                    self.total_shinies_seen += 1
                    self.last_shiny_pokemon_name = result.get("name") or "Pokemon"
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
            list(getattr(self, "current_item_reroll_targets", None) or [DEFAULT_ITEM_REROLL_TARGET]),
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

    def record_wallet_gold_if_visible(self, driver=None):
        target_driver = driver or self.driver
        if not target_driver:
            return False
        try:
            result = target_driver.execute_script(
                """
                const visible = (el) => {
                    if (!el) return false;
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0
                        && style.display !== 'none'
                        && style.visibility !== 'hidden';
                };
                const textFor = (el) => (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim();
                const parseAmount = (text) => {
                    const match = String(text || '').match(/([0-9][0-9.,]*)/);
                    return match ? (parseInt(match[1].replace(/[^0-9]/g, ''), 10) || 0) : 0;
                };
                const martWallet = [...document.querySelectorAll('.mart-wallet .mart-wallet-amount, .mart-wallet-amount')]
                    .filter(visible)[0];
                if (martWallet) {
                    const text = textFor(martWallet);
                    const amount = parseAmount(text);
                    if (amount > 0) {
                        return {found: true, amount, text, source: 'mart-wallet'};
                    }
                }
                return {found: false};
                """
            )
        except Exception:
            return False
        if not isinstance(result, dict) or not result.get("found"):
            return False
        amount = int(result.get("amount") or 0)
        if amount <= 0:
            return False
        if self.last_wallet_pokegold_total != amount:
            self.last_wallet_pokegold_total = amount
            self.update_stats_labels()
            self.log(
                f"Gold wallet detected: {amount:,} "
                f"({result.get('source') or 'wallet element'}: {result.get('text') or ''})."
            )
        return True

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
                const scoreValue = [...active.querySelectorAll('.run-score-value, [class*="score-value"]')]
                    .filter(visible)
                    .map(el => clean(el.innerText || el.textContent))
                    .find(text => /^[0-9][0-9.,]*$/.test(text));
                if (scoreValue) {
                    scoreText = `SCORE ${scoreValue}`;
                    score = parseInt(scoreValue.replace(/[^0-9]/g, ''), 10) || 0;
                }
                for (const text of scoreTexts) {
                    if (score) break;
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
            "leaders": int(self.run_leaders_defeated or 0),
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

    def normalize_trainer_name(self, value):
        text = str(value or "").lower()
        text = re.sub(r"[^a-z0-9]+", " ", text)
        text = re.sub(
            r"\b(wants to battle|would like to battle|challenge stage|map|trainer|pokemon|pokémon)\b",
            " ",
            text,
        )
        return " ".join(text.split())

    def known_leader_or_elite_name(self, text):
        normalized = self.normalize_trainer_name(text)
        if not normalized:
            return ""
        for name in sorted(LEADER_OR_ELITE_TRAINER_NAMES, key=len, reverse=True):
            leader = self.normalize_trainer_name(name)
            if not leader:
                continue
            if re.search(rf"(^| ){re.escape(leader)}($| )", normalized):
                return " ".join(part.capitalize() for part in leader.split())
        return ""

    def current_boss_trainer_info(self, include_map_info=False):
        try:
            return self.driver.execute_script(
                """
                const includeMapInfo = !!arguments[0];
                const visible = (el) => {
                    if (!el) return false;
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0
                        && style.display !== 'none'
                        && style.visibility !== 'hidden';
                };
                const text = (el) => (el ? (el.innerText || el.textContent || '').trim() : '');
                const attrText = (el) => {
                    if (!el) return '';
                    return [
                        el.getAttribute('alt'),
                        el.getAttribute('title'),
                        el.getAttribute('aria-label'),
                        el.getAttribute('src')
                    ].filter(Boolean).join(' ');
                };
                const active = document.querySelector('.screen.active');
                const screen = active?.id || '';
                const sources = [];
                const push = (source, value) => {
                    value = (value || '').trim();
                    if (value) sources.push({source, value});
                };
                push('battle-title', text(document.querySelector('#battle-title')));
                push('enemy-trainer-icon', attrText(document.querySelector('#enemy-trainer-icon')));
                if (screen === 'elite-prep-screen' || screen === 'badge-screen') {
                    push('elite-prep-enemy-name', text(document.querySelector('#elite-prep-enemy-name')));
                    push('elite-prep-title', text(document.querySelector('#elite-prep-title')));
                    push('elite-prep-sub', text(document.querySelector('#elite-prep-sub')));
                    push('elite-prep-enemy-trainer', attrText(document.querySelector('#elite-prep-enemy-trainer')));
                }
                if (includeMapInfo || screen === 'elite-prep-screen' || screen === 'badge-screen') {
                    push('map-info', text(document.querySelector('#map-info')));
                }
                return {screen, sources};
                """,
                include_map_info,
            ) or {"screen": "", "sources": []}
        except Exception:
            return {"screen": "", "sources": []}

    def record_leader_or_elite_if_visible(self, source="", include_map_info=False):
        info = self.current_boss_trainer_info(include_map_info=include_map_info)
        for item in info.get("sources") or []:
            name = self.known_leader_or_elite_name(item.get("value"))
            if not name:
                continue
            signature = f"{name.lower()}:{self.maps_started}:{self.maps_reached}"
            if signature == self.last_leader_signature:
                return False
            self.last_leader_signature = signature
            with self.stats_lock:
                self.run_leaders_defeated = int(self.run_leaders_defeated or 0) + 1
            if self.is_target_item_reroll_mode():
                self.awaiting_leader_item_roll = True
            self.log(f"Leader/E4 counted: {name} ({source or item.get('source') or 'trainer'}).")
            self.update_stats_labels()
            return True
        return False

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
            const filters = arguments[2] || {};
            const ignorePokemon = !!filters.ignorePokemon;
            const shinyOnly = !!filters.shinyOnly;
            const manualNames = new Set((filters.manualNames || []).map(name => String(name).toLowerCase()));
            const typeNames = new Set((filters.typeNames || []).map(name => String(name).toLowerCase()));
            const generationNames = new Set((filters.generationNames || []).map(name => String(name).toLowerCase()));
            const typeWhitelist = new Set((filters.typeWhitelist || []).map(name => String(name).toLowerCase()));
            const generationWhitelist = new Set((filters.generationWhitelist || []).map(name => String(name).toLowerCase()));
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0
                    && getComputedStyle(el).display !== 'none'
                    && getComputedStyle(el).visibility !== 'hidden';
            };
            const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const clickButton = (button) => {
                button.scrollIntoView({block: 'center', inline: 'center'});
                button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                button.click();
                button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            };
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
            const rewardName = (
                active.querySelector('.poke-name, .dex-name, .catch-name')?.innerText
                || active.querySelector('img[alt]')?.getAttribute('alt')
                || ''
            ).trim();
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
            const nameKey = normalize(rewardName || takeButton.innerText || rewardText);
            const typeAllowed = !typeWhitelist.size
                || typeNames.has(nameKey)
                || [...typeWhitelist].some(typeName => rewardText.includes(`${typeName} type`) || rewardText.includes(typeName));
            const generationAllowed = !generationWhitelist.size || generationNames.has(nameKey);
            const manualAllowed = !manualNames.size || manualNames.has(nameKey);
            const filterAllowed = !ignorePokemon
                && (!shinyOnly || rewardShiny)
                && manualAllowed
                && typeAllowed
                && generationAllowed;
            if (!filterAllowed) {
                const skipButton = buttons.find(btn => {
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    return btn.id === 'btn-skip-shiny' || text.includes('skip') || text.includes('decline');
                });
                if (!skipButton) return {clicked: false, blocked: true, filteredOut: true, rewardName, rewardShiny, rewardLegendary};
                clickButton(skipButton);
                return {clicked: true, skipped: true, filteredOut: true, text: (skipButton.innerText || skipButton.textContent || '').trim(), rewardName, rewardShiny, rewardLegendary};
            }
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
                clickButton(skipButton);
                return {clicked: true, skipped: true, text: (skipButton.innerText || skipButton.textContent || '').trim(), fullParty, rewardShiny, rewardLegendary};
            }
            clickButton(takeButton);
            return {clicked: true, skipped: false, text: (takeButton.innerText || takeButton.textContent || '').trim(), fullParty, rewardShiny, rewardLegendary, rewardName};
            """,
            party,
            list(LEGENDARY_POKEMON_NAMES),
            self.pokemon_filter_payload(),
        )
        if not result.get("clicked"):
            return False
        if result.get("skipped"):
            if result.get("filteredOut"):
                self.log(f"Pokemon reward skipped by filters: {result.get('rewardName') or result.get('text') or 'Pokemon'}.")
            elif result.get("rewardLegendary"):
                self.log("Legendary reward skipped: full team had no valid replacement.")
            else:
                self.log("Pokemon reward skipped: full shiny team and reward was not shiny.")
        else:
            if result.get("fullParty"):
                self.pending_team_replace = True
                self.pending_replace_allow_any = bool(result.get("rewardShiny"))
                self.pending_replace_add_clicked = False
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
            if result.get("rewardShiny") and self.should_count_run_shiny_stats():
                with self.stats_lock:
                    self.total_shinies_seen += 1
                    self.last_shiny_pokemon_name = result.get("rewardName") or "Pokemon"
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
            const addAlreadyClicked = !!arguments[3];
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
            const addButton = [...active.querySelectorAll([
                    '#swap-choices button',
                    '#swap-choices [role="button"]',
                    '#swap-choices .choice-card',
                    '#swap-choices .choice-cell',
                    '#swap-choices [onclick]',
                    'button',
                    '[role="button"]'
                ].join(','))]
                .filter(visible)
                .find(btn => {
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    return text.includes('add ') && text.includes(' to team');
                });
            if (addButton && !addAlreadyClicked) {
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
            const swapPromptText = normalize([
                active.querySelector('h2')?.innerText || '',
                active.querySelector('#swap-prompt')?.innerText || '',
                active.innerText || ''
            ].join(' '));
            const replacementPromptVisible = !!keepTeamButton && (
                candidates.length > 0
                || swapPromptText.includes('team full')
                || swapPromptText.includes('choose a pokemon to release')
                || swapPromptText.includes('choose a pok mon to release')
                || swapPromptText.includes('replace a pokemon')
                || swapPromptText.includes('replace a pok mon')
            );
            let selected = null;
            if (policy === 'legendary' || policy === 'legendary_shiny') {
                // A non-shiny legendary only ever releases a non-shiny, non-legendary
                // Pokémon — never sacrifice a shiny for a non-shiny legendary. If the
                // whole team is shiny, selected stays null -> keep team as-is.
                selected = candidates.find(candidate => !candidate.shiny && !candidate.legendary);
                // A shiny legendary may release a regular shiny only when no
                // normal non-legendary Pokemon can be released, keeping slot 0.
                if (!selected && policy === 'legendary_shiny') {
                    selected = candidates.find(candidate => candidate.index > 0 && candidate.shiny && !candidate.legendary);
                }
            } else if (policy === 'shiny') {
                // A shiny reward can replace any non-shiny Pokemon. Prefer
                // regular non-legendaries first, but do not keep a normal
                // legendary over a new shiny when no regular non-shiny exists.
                selected = candidates.find(candidate => !candidate.shiny && !candidate.legendary)
                    || candidates.find(candidate => !candidate.shiny);
            } else {
                selected = candidates.find(candidate => !candidate.shiny && !candidate.legendary)
                    || (allowAny ? candidates.find(candidate => !candidate.legendary) : null);
            }
            if (!selected) {
                if (addAlreadyClicked && !candidates.length) {
                    return {clicked: false, waitingReplacement: true, policy};
                }
                if (replacementPromptVisible && keepTeamButton) {
                    clickElement(keepTeamButton);
                    return {
                        clicked: true,
                        keptTeam: true,
                        count: candidates.length,
                        text: (keepTeamButton.innerText || keepTeamButton.textContent || '').trim(),
                        policy,
                        noValidReplacement: true
                    };
                }
                if (policy === 'add_only') {
                    const incomingCard = active.querySelector([
                        '#swap-incoming .poke-card',
                        '#swap-incoming [role="button"]',
                        '#swap-incoming [data-shortcut]',
                        '#swap-incoming img[src*="/pokemon/"]'
                    ].join(','));
                    const incomingClickTarget = incomingCard?.closest?.('.poke-card, [role="button"], [data-shortcut]') || incomingCard;
                    if (!incomingClickTarget || !visible(incomingClickTarget)) {
                        return {clicked: false, count: candidates.length, addOnlyMissing: true, policy};
                    }
                    incomingClickTarget.setAttribute('data-bot-swap-add-target', '1');
                    return {
                        clicked: true,
                        incomingClicked: true,
                        text: (incomingClickTarget.innerText || incomingClickTarget.textContent || '').trim(),
                        policy
                    };
                }
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
            self.pending_replace_add_clicked,
        )
        if not result.get("clicked"):
            return False
        if result.get("addClicked"):
            self.log(f"Team replace: clicked {result.get('text') or 'Add to team'}.")
            if result.get("policy") == "add_only":
                self.pending_team_replace = False
                self.pending_replace_allow_any = False
                self.pending_replace_policy = "default"
                self.pending_replace_add_clicked = False
            else:
                self.pending_replace_add_clicked = True
            time.sleep(0.6)
            return True
        if result.get("incomingClicked"):
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, '[data-bot-swap-add-target="1"]')
                self.browser_center_click(el, press_enter=True)
                self.log("Team replace: clicked incoming Pokemon to open Add to team control.")
                time.sleep(0.25)
                if self.active_screen_id() != "swap-screen":
                    self.pending_team_replace = False
                    self.pending_replace_allow_any = False
                    self.pending_replace_policy = "default"
                    self.pending_replace_add_clicked = False
            except Exception as exc:
                self.log(f"Team replace: incoming Pokemon click failed ({exc}).")
            finally:
                try:
                    self.driver.execute_script(
                        "document.querySelector('[data-bot-swap-add-target=\"1\"]')?.removeAttribute('data-bot-swap-add-target');"
                    )
                except Exception:
                    pass
            time.sleep(0.5)
            return True
        if result.get("keptTeam"):
            self.pending_team_replace = False
            self.pending_replace_allow_any = False
            self.pending_replace_policy = "default"
            self.pending_replace_add_clicked = False
            self.log(f"Team replace: kept team as-is ({result.get('policy') or 'default'} policy).")
            time.sleep(0.6)
            return True
        self.pending_team_replace = False
        self.pending_replace_allow_any = False
        self.pending_replace_policy = "default"
        self.pending_replace_add_clicked = False
        self.log(f"Team replace: replaced {result.get('name') or 'Pokemon'}.")
        time.sleep(0.6)
        return True

    def handle_event_pokemon_reward(self):
        result = self.driver.execute_script(
            """
            const filters = arguments[0] || {};
            const ignorePokemon = !!filters.ignorePokemon;
            const shinyOnly = !!filters.shinyOnly;
            const manualNames = new Set((filters.manualNames || []).map(name => String(name).toLowerCase()));
            const typeNames = new Set((filters.typeNames || []).map(name => String(name).toLowerCase()));
            const generationNames = new Set((filters.generationNames || []).map(name => String(name).toLowerCase()));
            const typeWhitelist = new Set((filters.typeWhitelist || []).map(name => String(name).toLowerCase()));
            const generationWhitelist = new Set((filters.generationWhitelist || []).map(name => String(name).toLowerCase()));
            const visible = (el) => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };
            const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
            const clickButton = (button) => {
                button.scrollIntoView({block: 'center', inline: 'center'});
                button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                button.click();
                button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
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
            const active = document.querySelector('.screen.active') || document;
            const screenText = (active.innerText || '').toLowerCase();
            const name = (
                active.querySelector('.poke-name, .dex-name, .catch-name')?.innerText
                || active.querySelector('img[alt]')?.getAttribute('alt')
                || ''
            ).trim();
            const key = normalize(name || button.innerText || screenText);
            const shiny = screenText.includes('shiny')
                || !!active.querySelector('.pc-shiny-star, .shiny-star, .shiny-badge, img[src*="/shiny/"]');
            const typeAllowed = !typeWhitelist.size
                || typeNames.has(key)
                || [...typeWhitelist].some(typeName => screenText.includes(`${typeName} type`) || screenText.includes(typeName));
            const generationAllowed = !generationWhitelist.size || generationNames.has(key);
            const manualAllowed = !manualNames.size || manualNames.has(key);
            const filterAllowed = !ignorePokemon
                && (!shinyOnly || shiny)
                && manualAllowed
                && typeAllowed
                && generationAllowed;
            if (!filterAllowed) {
                const skipButton = buttons.find(btn => {
                    const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                    return text.includes('skip') || text.includes('decline');
                });
                if (!skipButton) return {clicked: false, filteredOut: true, name};
                clickButton(skipButton);
                return {clicked: true, skipped: true, filteredOut: true, text: (skipButton.innerText || skipButton.textContent || '').trim(), name};
            }
            button.scrollIntoView({block: 'center', inline: 'center'});
            button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            button.click();
            button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
            return {clicked: true, text: (button.innerText || button.textContent || '').trim()};
            """,
            self.pokemon_filter_payload(),
        )
        if result.get("clicked"):
            if result.get("filteredOut"):
                self.log(f"Random event Pokemon reward skipped by filters: {result.get('name') or result.get('text') or 'Pokemon'}.")
            else:
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
            const normalizePokemonName = (value) => String(value || '')
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, ' ')
                .trim()
                .replace(/\\s+/g, ' ');
            const preferredNames = [...new Set((arguments[0] || []).map(normalizePokemonName).filter(Boolean))];
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
                'starter-screen', 'elite-prep-screen', 'battle-screen',
                'gameover-screen', 'win-screen'
            ];
            if (NON_EVO_SCREENS.includes(activeId) && !hasVisibleRoot && !hasEvolutionText) {
                return {clicked: false};
            }
            if (!hasVisibleRoot && !hasEvolutionText && !hasInlineChoices) {
                return {clicked: false};
            }
            const root = choiceRoots.find(visible) || document.querySelector('.screen.active') || document.body || document;
            const directChoiceCards = [
                ...document.querySelectorAll('#eevee-choices > *, #evo-choices > *, #evolution-choices > *')
            ].filter(visible).filter(el => {
                const text = (el.innerText || el.textContent || '').trim().toLowerCase();
                const id = (el.id || '').toLowerCase();
                const cls = (el.className || '').toString().toLowerCase();
                return text
                    && !!el.querySelector('img[src*="/pokemon/"]')
                    && !text.includes('cancel') && !text.includes('back') && !text.includes('skip')
                    && !id.includes('cancel') && !id.includes('back') && !id.includes('skip')
                    && !cls.includes('cancel') && !cls.includes('back') && !cls.includes('skip');
            });
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
            const choicePool = directChoiceCards.length ? directChoiceCards : candidates;
            const cardNames = (el) => {
                const names = [];
                const add = (value) => {
                    const normalized = normalizePokemonName(value);
                    if (normalized && !names.includes(normalized)) names.push(normalized);
                };
                el.querySelectorAll('.dex-name, .poke-name').forEach(node => add(node.innerText || node.textContent));
                el.querySelectorAll('img[alt]').forEach(img => add(img.getAttribute('alt')));
                ['data-evolution', 'data-evo', 'data-name', 'aria-label', 'title'].forEach(attr => add(el.getAttribute(attr)));
                const text = (el.innerText || el.textContent || '').trim();
                text.split(/\\n+/).forEach(add);
                add(text);
                return names;
            };
            const choiceMatchesPreference = (el) => {
                const names = cardNames(el);
                return preferredNames.find(preferred => names.some(name => name === preferred));
            };
            let preferredMatch = null;
            if (preferredNames.length) {
                preferredMatch = choicePool.find(choiceMatchesPreference)
                    || candidates.find(choiceMatchesPreference);
            }
            if (preferredNames.length && !preferredMatch) {
                return {
                    found: false,
                    blocked: true,
                    preferred: true,
                    choices: choicePool.map(el => cardNames(el)[0] || 'unknown').slice(0, 12),
                };
            }
            const card = preferredNames.length
                ? preferredMatch
                : (
                    choicePool[Math.floor(Math.random() * choicePool.length)]
                    || candidates.find(el => el.querySelector('img[src*="/pokemon/"], .dex-name, .poke-name'))
                    || candidates.find(el => !el.matches('button'))
                    || candidates[0]
                );
            if (!card) return {clicked: false};
            const name = (
                cardNames(card)[0]
                || card.querySelector('.dex-name, .poke-name')?.innerText
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
            return {found: true, name, preferred: preferredNames.length > 0};
            """,
            getattr(self, "current_evolution_preference_list", []) or [],
        )
        if result.get("blocked"):
            return True
        if not result.get("found"):
            return False
        name = result.get("name") or "random option"
        def choice_still_visible():
            try:
                return bool(self.driver.execute_script(
                    """
                    const visible = (el) => {
                        if (!el) return false;
                        const rect = el.getBoundingClientRect();
                        const style = getComputedStyle(el);
                        return rect.width > 0 && rect.height > 0
                            && style.display !== 'none'
                            && style.visibility !== 'hidden';
                    };
                    return ['#eevee-choice-overlay', '#evo-overlay', '#evo-choices', '#evolution-choices']
                        .some(selector => visible(document.querySelector(selector)));
                    """
                ))
            except Exception:
                return False

        def wait_for_choice_to_clear(timeout=1.2):
            deadline = time.time() + timeout
            while time.time() < deadline:
                if not choice_still_visible():
                    return True
                time.sleep(0.12)
            return not choice_still_visible()

        cleared = False
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, '[data-bot-evo-target="1"]')
            for attempt in range(3):
                self.browser_center_click(el, press_enter=(attempt == 2))
                if wait_for_choice_to_clear(0.8):
                    cleared = True
                    break
                try:
                    ActionChains(self.driver).move_to_element(el).pause(0.08).click().perform()
                    if wait_for_choice_to_clear(0.8):
                        cleared = True
                        break
                except Exception:
                    pass
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
                if wait_for_choice_to_clear(0.8):
                    cleared = True
                    break
        except Exception as exc:
            self.log(f"Evolution choice: native click failed ({exc}); trying fallback.")
            try:
                self.driver.execute_script(
                    "const el=document.querySelector('[data-bot-evo-target=\"1\"]');"
                    "if(el){el.dispatchEvent(new MouseEvent('mouseover',{bubbles:true}));"
                    "el.dispatchEvent(new MouseEvent('mouseenter',{bubbles:true}));"
                    "el.click();}"
                )
                cleared = wait_for_choice_to_clear(0.8)
            except Exception:
                cleared = False
        finally:
            try:
                self.driver.execute_script(
                    "document.querySelector('[data-bot-evo-target=\"1\"]')?.removeAttribute('data-bot-evo-target');"
                )
            except Exception:
                pass
        if cleared:
            self.log(f"Evolution choice: selected {name}.")
            time.sleep(0.6)
            return True
        self.log(f"Evolution choice: clicked {name}, but the choice overlay is still visible; retrying.")
        time.sleep(0.4)
        return True

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

    def visible_play_again_result_state(self):
        try:
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
                const normalize = (text) => String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
                const active = document.querySelector('.screen.active') || document.body;
                const buttons = [...document.querySelectorAll('#btn-retry, #btn-play-again, #btn-stage-again, button, [role="button"]')]
                    .filter(visible);
                const button = buttons.find(btn => {
                    const text = normalize(btn.innerText || btn.textContent || '');
                    const id = (btn.id || '').toLowerCase();
                    return id === 'btn-retry'
                        || id === 'btn-play-again'
                        || id === 'btn-stage-again'
                        || text.includes('play again');
                });
                if (!button) return {visible: false};
                const id = (button.id || '').toLowerCase();
                const text = normalize([
                    active.id || '',
                    active.innerText || active.textContent || '',
                    button.innerText || button.textContent || ''
                ].join(' '));
                let won = null;
                if (id === 'btn-stage-again' || text.includes('win screen') || text.includes('victory') || text.includes('champion') || text.includes('completed')) {
                    won = true;
                } else if (id === 'btn-retry' || text.includes('game over') || text.includes('defeat') || text.includes('lost')) {
                    won = false;
                }
                return {
                    visible: true,
                    won,
                    screen: won === false ? 'gameover-screen' : 'win-screen',
                    buttonId: id,
                    text: (button.innerText || button.textContent || '').trim()
                };
                """
            )
        except Exception:
            return {"visible": False}

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
                const cls = (btn.className || '').toString().toLowerCase();
                const aria = (btn.getAttribute('aria-label') || '').trim().toLowerCase();
                const tip = (btn.getAttribute('data-tip') || '').trim().toLowerCase();
                return id === 'btn-home'
                    || id === 'btn-stage-home'
                    || id === 'btn-title'
                    || btn.getAttribute('onclick') === 'goHomeFromMenu()'
                    || cls.includes('nav-in-run')
                    || aria === 'home'
                    || tip === 'home'
                    || text === 'home'
                    || text.includes('back home')
                    || text.includes('main menu');
            });
            if (button) {
                button.scrollIntoView({block: 'center', inline: 'center'});
                button.dispatchEvent(new MouseEvent('pointerdown', {bubbles: true}));
                button.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                button.click();
                button.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                button.dispatchEvent(new MouseEvent('pointerup', {bubbles: true}));
                return {clicked: true, text: (button.innerText || button.textContent || button.getAttribute('aria-label') || 'Home').trim()};
            }
            if (typeof window.goHomeFromMenu === 'function') {
                window.goHomeFromMenu();
                return {clicked: true, text: 'Home'};
            }
            return {clicked: false};
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

    def choose_passive_item(self, target_only=False, target_aliases=None, priority_items=None):
        target_aliases = target_aliases or getattr(self, "current_item_reroll_targets", None) or [DEFAULT_ITEM_REROLL_TARGET]
        priority_items = priority_items or list(self.starting_item_priority)
        result = self.driver.execute_script(
            """
            const priority = arguments[0].map(name => name.toLowerCase());
            const targetAliases = arguments[1].map(name => name.toLowerCase());
            const targetOnly = arguments[2];
            const ignored = arguments[3].map(name => name.toLowerCase());
            const forcedFirstPickAliases = ['shiny hunter'];
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
                return priority.some(alias => norm.includes(alias))
                    || forcedFirstPickAliases.some(alias => norm.includes(alias));
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
            const forcedFirstPick = visibleCards.find(card => {
                const norm = normalize(nameFor(card));
                return forcedFirstPickAliases.some(alias => norm.includes(alias));
            });
            if (forcedFirstPick) {
                const selectedName = nameFor(forcedFirstPick) || (forcedFirstPick.innerText || '').trim();
                const forcedNorm = normalize(selectedName);
                const forcedIsTarget = targetAliases.some(alias => forcedNorm.includes(normalize(alias)));
                if (!targetOnly || forcedIsTarget) {
                    clickCard(forcedFirstPick);
                    return {
                        clicked: true,
                        forcedFirstPick: true,
                        target: targetOnly && forcedIsTarget,
                        fallback: false,
                        priority: 0,
                        name: selectedName.replace(/\\s+/g, ' ').slice(0, 80),
                        names,
                        ignoredNames,
                        unrecognizedNames,
                        itemDetails
                    };
                }
            }
            const priorityIndex = (card) => {
                const norm = normalize(nameFor(card));
                const idx = priority.findIndex(alias => norm.includes(alias));
                return idx < 0 ? null : idx;
            };
            if (targetOnly) {
                let target = visibleCards.find(card => {
                    const norm = normalize(nameFor(card));
                    return targetAliases.some(alias => norm.includes(normalize(alias)));
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
                // Nothing preferred is pickable (all offers are unrecognized/ignored):
                // skip when possible; otherwise pick the first offer so full runs continue.
                const skip = [...document.querySelectorAll('#passive-choices .choice-skip-cell, .choice-skip-btn, #passive-choices button')]
                    .find(el => isVisible(el) && /skip/i.test(el.innerText || el.textContent || ''));
                if (skip) { clickCard(skip); return {clicked: true, skipped: true, name: 'skip', names, ignoredNames, unrecognizedNames, itemDetails}; }
                const lastResort = visibleCards[0];
                if (lastResort) {
                    const selectedName = nameFor(lastResort) || (lastResort.innerText || '').trim();
                    clickCard(lastResort);
                    return {
                        clicked: true,
                        target: false,
                        fallback: true,
                        lastResort: true,
                        priority: null,
                        name: selectedName.replace(/\\s+/g, ' ').slice(0, 80),
                        names,
                        ignoredNames,
                        unrecognizedNames,
                        itemDetails
                    };
                }
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
            list(priority_items),
            list(target_aliases),
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
            self.log("Passive choice: no clickable item found yet; waiting for the screen to finish loading.")
            return False
        if result.get("skipped"):
            # Everything offered was unrecognized/ignored — skipped the screen.
            return False
        if result.get("lastResort"):
            self.log(
                "Passive choice: all offers were ignored or unrecognized; "
                f"picked {result.get('name') or 'first visible item'} to continue the run."
            )
        # A passive item is offered once per map (start of each Tower/Challenge
        # map), so a successful pick marks entering a new map. Used by the
        # optional map-3 party-fill delay in pick_map_node().
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
        if result.get("forcedFirstPick"):
            self.log(f"Selected passive item: {result.get('name')} (forced Shiny Hunter first pick)")
        elif result.get("fallback"):
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

    def swap_team_count(self):
        try:
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
                const selectors = [
                    '#swap-team-list .team-slot',
                    '#swap-team-list .poke-card',
                    '#trade-team-list .team-slot',
                    '#trade-team-list .poke-card',
                    '.screen.active .team-slot'
                ];
                const seen = new Set();
                const slots = [];
                for (const selector of selectors) {
                    for (const slot of document.querySelectorAll(selector)) {
                        if (!visible(slot) || slot.closest('#swap-incoming') || seen.has(slot)) continue;
                        const img = slot.querySelector('img.team-sprite, img.poke-sprite, img[src*="/pokemon/"]');
                        if (!img || !visible(img)) continue;
                        const key = [
                            img.getAttribute('src') || img.src || '',
                            slot.querySelector('.team-slot-name, .poke-name, .battle-poke-name')?.innerText || '',
                            slots.length
                        ].join('|');
                        if (seen.has(key)) continue;
                        seen.add(slot);
                        seen.add(key);
                        slots.push(slot);
                    }
                }
                return slots.length;
                """
            )
            count = int(result or 0)
            if count > 0:
                return min(count, 6)
        except Exception:
            pass
        try:
            return min(int((self.party_summary() or {}).get("count") or 0), 6)
        except Exception:
            return 0

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

    def completed_primary_dex_target_in_party(self):
        if not self.should_complete_current_reroll_run():
            return False
        if self.is_complete_pokedex_mode():
            return False
        primary_targets = {
            self.normalize_pokemon_name(name)
            for name in getattr(self, "current_primary_target_names", set())
            if self.normalize_pokemon_name(name)
        }
        if not primary_targets:
            return False
        snapshot = list(getattr(self, "last_team_snapshot", []) or [])
        if not snapshot:
            try:
                party = self.party_summary()
                snapshot = party.get("slots", []) if isinstance(party, dict) else []
            except Exception:
                snapshot = []
        for slot in snapshot:
            name = self.normalize_pokemon_name(slot.get("name") if isinstance(slot, dict) else "")
            if name in primary_targets:
                self.set_status("Target found")
                self.log(f"Dex target evolved/owned in party: {name.title()}. Ending current reroll completion run early.")
                return True
        return False

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
        if not getattr(self, "current_prioritize_party_fill", True):
            prioritize_party_fill = False
        elif getattr(self, "current_delay_party_fill", False):
            # Optional legacy behavior: do not bias route selection toward
            # party-fill catches until map 3.
            prioritize_party_fill = self.maps_reached >= 2 or self.maps_started >= 3
        else:
            prioritize_party_fill = True
        avoid_pokemon = bool(getattr(self, "current_ignore_pokemon", False))
        avoid_pokecenter = True
        avoid_tm_move_tutor = bool(getattr(self, "current_no_tm_move_tutor", False))
        needs_move_tutor = self.main_move_upgrades_used < MAIN_MOVE_TARGET_USES and not avoid_tm_move_tutor
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
            penalty = 0
            if "poke-center" in kinds:
                penalty += 1000
            if avoid_pokemon and ({"legendary", "pokeball"} & kinds):
                penalty += 350
            if avoid_tm_move_tutor and "move-tutor" in kinds:
                penalty += 175
            if not avoid_pokemon and "legendary" in kinds:
                return penalty - 300
            if needs_move_tutor and "move-tutor" in kinds:
                return penalty - 200
            return penalty

        def score(node):
            kind = node.get("kind") or "other"
            if avoid_pokemon and kind in {"legendary", "pokeball"}:
                base = 500
            elif kind == "poke-center":
                base = 1000
            elif avoid_tm_move_tutor and kind == "move-tutor":
                base = 425
            elif kind == "legendary":
                base = 0
            elif needs_move_tutor and kind == "move-tutor":
                base = 1
            elif kind == "trainer":
                base = 2
            elif prioritize_party_fill and party_count < 6 and kind == "pokeball":
                base = 3
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
            elif kind == "trade":
                base = 8
            elif kind == "move-tutor":
                base = 99
            else:
                base = 10
            return (base + route_bonus(node), 0)

        # If the visible map has any route that avoids disabled content, filter to
        # that subset. Pokecenter is always lowest priority and only used when
        # every reachable route forces it.
        filtered_nodes = nodes
        without_center = [
            node for node in filtered_nodes
            if node.get("kind") != "poke-center" and "poke-center" not in reachable_kinds(node["index"])
        ]
        if without_center:
            filtered_nodes = without_center
        if avoid_pokemon:
            without_pokemon = [
                node for node in filtered_nodes
                if node.get("kind") not in {"legendary", "pokeball"}
                and not ({"legendary", "pokeball"} & reachable_kinds(node["index"]))
            ]
            if without_pokemon:
                filtered_nodes = without_pokemon
        if avoid_tm_move_tutor:
            without_move_tutor = [
                node for node in filtered_nodes
                if node.get("kind") != "move-tutor" and "move-tutor" not in reachable_kinds(node["index"])
            ]
            if without_move_tutor:
                filtered_nodes = without_move_tutor

        # Tie-break downward to make steady progress toward the leader.
        chosen = sorted(filtered_nodes, key=lambda node: (*score(node), -node["y"]))[0]
        if avoid_pokemon and chosen.get("kind") in {"legendary", "pokeball"}:
            self.log("Map route: Pokemon avoidance is enabled, but this map appears to force a Pokemon route.")
        elif chosen.get("kind") == "poke-center":
            self.log("Map route: Pokecenter is forced; no reachable route avoids it.")
        elif avoid_tm_move_tutor and chosen.get("kind") == "move-tutor":
            self.log("Map route: TM/move-tutor avoidance is enabled, but this map appears to force move tutor.")
        elif chosen.get("kind") == "legendary":
            self.log("Map route: prioritizing reachable legendary node.")
        elif route_bonus(chosen) <= -300:
            self.log("Map route: choosing path toward legendary node.")
        elif needs_move_tutor and (chosen.get("kind") == "move-tutor" or route_bonus(chosen) <= -200):
            self.log(f"Map route: choosing path toward move tutor ({self.main_move_upgrades_used}/{MAIN_MOVE_TARGET_USES}).")
        elif prioritize_party_fill and party_count < 6 and chosen.get("kind") == "pokeball":
            self.log(f"Map route: map {self.maps_reached + 1}; party has {party_count}/6 Pokemon; prioritizing pokeball catch node.")
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
                is_loss_continue = self.driver.execute_script(
                    """
                    const btn = document.querySelector('#btn-continue-battle');
                    if (!btn) return false;
                    const cls = (btn.className || '').toString().toLowerCase();
                    return cls.includes('battle-continue-loss');
                    """
                )
                self.js_click("#btn-continue-battle", timeout=0.4)
                if is_loss_continue and self.should_use_full_run_logic():
                    for _ in range(20):
                        time.sleep(0.15)
                        next_screen = self.active_screen_id()
                        if next_screen == "gameover-screen":
                            self.handle_completed_run_result(False, next_screen)
                            return
                        if next_screen == "win-screen":
                            self.handle_completed_run_result(True, next_screen)
                            return
                        if next_screen and next_screen != "battle-screen":
                            break
                time.sleep(0.18)
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
                self.js_click("#btn-auto-battle", timeout=0.4)

            time.sleep(0.12)

    def handle_move_tutor(self):
        skip_move_tutor = (
            bool(getattr(self, "current_no_tm_move_tutor", False))
            or (self.should_use_full_run_logic() and self.main_move_upgrades_used >= MAIN_MOVE_TARGET_USES)
        )
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
                || activeText.includes('learn move');
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
            let button = [...document.querySelectorAll('button[data-tutor], button')]
                .filter(visible)
                .find(btn => ((btn.innerText || btn.textContent || '').trim().toLowerCase()).includes('dragon pulse')) || null;
            let row = button ? button.closest('.equip-pokemon-row') : null;
            if (!button) {
                row = rows[0] || null;
                button = row ? row.querySelector('button[data-tutor], button') : null;
            }
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
                reason = "TM/move tutor disabled" if getattr(self, "current_no_tm_move_tutor", False) else result.get("reason") or f"main Pokemon already has {MAIN_MOVE_TARGET_USES} move upgrade(s)"
                self.log(f"Move tutor/TM skipped: {reason}.")
                return True
            if self.should_use_full_run_logic() and self.main_move_upgrades_used < MAIN_MOVE_TARGET_USES:
                self.main_move_upgrades_used += 1
            self.log(f"Move tutor: {result.get('pokemon') or 'first Pokemon'} {result.get('move')}")
            return True
        if result.get("blocked"):
            self.log(f"Move tutor/TM screen blocked: {result.get('reason')}")
        return False

    def handle_tm_item_equip(self):
        result = self.driver.execute_script(
            """
            const skipTm = !!arguments[0];
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
            const activeText = [
                modal?.innerText || modal?.textContent || '',
                active?.innerText || '',
                document.body.innerText || ''
            ].join('\\n').toLowerCase();
            const rows = [...document.querySelectorAll('#item-equip-modal .equip-pokemon-row, .equip-pokemon-row')]
                .filter(visible);
            const isTmContext = activeText.includes('tm ') || activeText.includes('technical machine');
            const isTutorContext = rows.some(row => !!row.querySelector('button[data-tutor]'))
                || !!document.querySelector('button[data-tutor]')
                || !!document.querySelector('#btn-skip-tutor')
                || activeText.includes('move tutor');
            if (!isTmContext || isTutorContext || !rows.length) return {clicked: false};
            if (skipTm) {
                const skipButton = [...document.querySelectorAll('button, [role="button"]')]
                    .filter(visible)
                    .find(btn => {
                        const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                        const id = (btn.id || '').toLowerCase();
                        return text.includes('skip') || text.includes('cancel') || text.includes('no thanks') || id.includes('skip') || id.includes('cancel');
                    });
                if (!skipButton) return {clicked: false, blocked: true, reason: 'TM disabled and no skip button was visible'};
                click(skipButton);
                return {clicked: true, skipped: true, reason: 'TM disabled'};
            }
            for (const row of rows) {
                const mastered = (row.innerText || row.textContent || '').toLowerCase();
                if (mastered.includes('already mastered') || mastered.includes('(mastered)') || mastered.includes('move slots full')) {
                    continue;
                }
                const button = [...row.querySelectorAll('button, [role="button"]')]
                    .filter(visible)
                    .find(btn => {
                        const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                        return text.includes('use') || text.includes('teach') || text.includes('learn') || text.includes('select');
                    });
                if (!button) continue;
                const pokemon = row.querySelector('.equip-poke-name')?.innerText || row.innerText || 'Pokemon';
                click(button);
                return {clicked: true, pokemon: pokemon.trim(), text: (button.innerText || button.textContent || '').trim()};
            }
            return {clicked: false, blocked: true, reason: 'no Pokemon could learn the TM'};
            """,
            bool(getattr(self, "current_no_tm_move_tutor", False)),
        )
        if result.get("clicked"):
            if result.get("skipped"):
                self.log(f"TM skipped: {result.get('reason') or 'disabled'}.")
                time.sleep(0.45)
                return True
            if self.should_use_full_run_logic() and self.main_move_upgrades_used < MAIN_MOVE_TARGET_USES:
                self.main_move_upgrades_used += 1
            self.log(f"TM used on {result.get('pokemon') or 'first Pokemon'}.")
            time.sleep(0.45)
            return True
        if result.get("blocked"):
            self.log(f"TM skipped: {result.get('reason')}.")
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
                || activeText.includes('learn move');
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

    def equip_visible_held_item_on_starter(self, item_name, label):
        item_name = str(item_name or "").strip()
        if not item_name:
            return False

        def click_item_badge():
            return self.driver.execute_script(
                """
                const targetName = String(arguments[0] || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
                const visible = (el) => {
                    if (!el) return false;
                    const rect = el.getBoundingClientRect();
                    const style = getComputedStyle(el);
                    return rect.width > 0 && rect.height > 0
                        && style.display !== 'none'
                        && style.visibility !== 'hidden';
                };
                const normalize = (text) => String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
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
                const roots = [
                    '#elite-prep-items .item-badge',
                    '#item-bar .item-badge',
                    '#item-team-bar .item-badge',
                    '#catch-team-bar .item-badge',
                    '#passive-team-bar .item-badge',
                    '.screen.active .item-badge'
                ].join(',');
                const badges = [...document.querySelectorAll(roots)].filter(visible);
                const badgeName = (badge) => normalize([
                    badge.innerText || badge.textContent || '',
                    badge.getAttribute('aria-label') || '',
                    badge.getAttribute('title') || '',
                    badge.dataset?.item || '',
                    badge.dataset?.name || '',
                    ...[...badge.querySelectorAll('img')].map(img => [
                        img.getAttribute('alt') || '',
                        img.getAttribute('title') || '',
                        img.getAttribute('src') || ''
                    ].join(' '))
                ].join(' '));
                const badge = badges.find(candidate => {
                    const name = badgeName(candidate);
                    return name && (name === targetName || name.includes(targetName) || targetName.includes(name));
                });
                if (!badge) {
                    return {clicked: false, reason: 'item badge not visible', visibleItems: badges.map(badgeName).filter(Boolean).slice(0, 12)};
                }
                click(badge);
                return {clicked: true};
                """,
                item_name,
            )

        def click_starter_row():
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
                const rows = [...document.querySelectorAll('#item-equip-modal .equip-pokemon-row, .equip-pokemon-row')]
                    .filter(visible)
                    .sort((a, b) => {
                        const ai = parseInt(a.getAttribute('data-idx') || '999', 10);
                        const bi = parseInt(b.getAttribute('data-idx') || '999', 10);
                        return ai - bi;
                    });
                const row = rows.find(candidate => (candidate.getAttribute('data-idx') || '') === '0') || rows[0];
                if (!row) return {clicked: false};
                const button = [...row.querySelectorAll('button, [role="button"]')]
                    .filter(visible)
                    .find(btn => {
                        const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                        return text.includes('equip') || text.includes('use') || text.includes('select') || text.includes('swap');
                    });
                const target = button || row;
                const pokemon = row.querySelector('.equip-poke-name')?.innerText || row.innerText || 'starter';
                click(target);
                return {clicked: true, pokemon: pokemon.trim(), targetText: (target.innerText || target.textContent || '').trim()};
                """
            )

        clicked_badge = click_item_badge()
        if not clicked_badge.get("clicked"):
            return False
        result = None
        deadline = time.time() + 1.2
        while time.time() < deadline and not self.stop_event.is_set():
            result = click_starter_row()
            if result.get("clicked"):
                break
            time.sleep(0.08)
        if not result or not result.get("clicked"):
            self.log(f"{label}: clicked {item_name}, but no starter equip row appeared.")
            return False
        self.log(f"{label}: equipped {item_name} on {result.get('pokemon') or 'starter'}.")
        time.sleep(0.45)
        return True

    def handle_boss_combat_item_swap(self):
        if not (
            self.should_use_full_run_logic()
            and getattr(self, "current_boss_combat_item_swap", False)
            and getattr(self, "current_combat_held_items", [])
        ):
            return False
        if getattr(self, "boss_combat_item_equipped", False):
            return False
        for item_name in self.current_combat_held_items:
            if self.equip_visible_held_item_on_starter(item_name, "Boss item swap"):
                self.boss_combat_item_equipped = True
                return True
        return False

    def restore_boss_combat_item_if_needed(self):
        if not getattr(self, "boss_combat_item_equipped", False):
            return False
        restore_item = self.active_restore_held_item()
        if not restore_item:
            return False
        if self.equip_visible_held_item_on_starter(restore_item, "Boss item restore"):
            self.boss_combat_item_equipped = False
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

    def use_sacred_ash_on_fainted_starter_if_available(self):
        if not self.should_use_full_run_logic():
            return False
        screen = self.active_screen_id()
        if screen in {"battle-screen", "badge-screen", "elite-prep-screen"}:
            return False
        if bool(getattr(self, "awaiting_leader_item_roll", False)):
            return False

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
            const normalize = (text) => String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
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
            const itemBadgeName = (badge) => normalize([
                badge.innerText || badge.textContent || '',
                badge.getAttribute('aria-label') || '',
                badge.getAttribute('title') || '',
                badge.dataset?.item || '',
                badge.dataset?.name || '',
                ...[...badge.querySelectorAll('img')].map(img => [
                    img.getAttribute('alt') || '',
                    img.getAttribute('title') || '',
                    img.getAttribute('src') || ''
                ].join(' '))
            ].join(' '));
            const sacredAsh = [...document.querySelectorAll([
                '#item-bar .item-badge',
                '#item-team-bar .item-badge',
                '#catch-team-bar .item-badge',
                '#passive-team-bar .item-badge',
                '.screen.active .item-badge'
            ].join(','))]
                .filter(visible)
                .find(badge => {
                    const name = itemBadgeName(badge);
                    return name.includes('sacred ash') || name.includes('sacred ash png');
                });
            if (!sacredAsh) return {clicked: false, reason: 'no sacred ash'};

            const teamSlots = [...document.querySelectorAll([
                '#team-bar .team-slot',
                '#map-team-bar .team-slot',
                '#catch-team-bar .team-slot',
                '#item-team-bar .team-slot',
                '#passive-team-bar .team-slot',
                '.screen.active .team-slot'
            ].join(','))]
                .filter(visible)
                .sort((a, b) => {
                    const ai = parseInt(a.getAttribute('data-idx') || a.dataset?.idx || '999', 10);
                    const bi = parseInt(b.getAttribute('data-idx') || b.dataset?.idx || '999', 10);
                    return ai - bi;
                });
            const starterSlot = teamSlots.find(slot => (slot.getAttribute('data-idx') || slot.dataset?.idx || '') === '0') || teamSlots[0];
            if (!starterSlot) return {clicked: false, reason: 'no starter slot'};
            const slotText = normalize(starterSlot.innerText || starterSlot.textContent || '');
            const slotClass = normalize(starterSlot.className || '');
            const hpText = [
                starterSlot.querySelector('.hp, .team-slot-hp, .poke-hp, [class*="hp"]')?.innerText || '',
                starterSlot.getAttribute('aria-label') || '',
                starterSlot.getAttribute('title') || ''
            ].join(' ');
            const hpZero = /(^|\\D)0\\s*\\/\\s*[1-9][0-9]*/.test(hpText);
            const fainted = slotText.includes('fainted')
                || slotText.includes('ko')
                || slotClass.includes('fainted')
                || slotClass.includes('ko')
                || starterSlot.classList.contains('fainted')
                || starterSlot.classList.contains('is-fainted')
                || !!starterSlot.querySelector('.fainted, .is-fainted, [class*="fainted"]')
                || hpZero;
            if (!fainted) return {clicked: false, reason: 'starter not fainted'};
            const starterName = (
                starterSlot.querySelector('.team-slot-name, .poke-name, .battle-poke-name')?.innerText
                || starterSlot.querySelector('img[alt]')?.getAttribute('alt')
                || 'starter'
            ).trim();
            click(sacredAsh);
            return {clicked: true, starterName};
            """
        )
        if not result.get("clicked"):
            return False

        def click_starter_row():
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
                        node.dispatchEvent(new MouseEvent('pointerup', {bubbles: true, clientX: x, clientY: y}));
                    }
                };
                const rows = [...document.querySelectorAll('#item-equip-modal .equip-pokemon-row, .equip-pokemon-row')]
                    .filter(visible)
                    .sort((a, b) => {
                        const ai = parseInt(a.getAttribute('data-idx') || '999', 10);
                        const bi = parseInt(b.getAttribute('data-idx') || '999', 10);
                        return ai - bi;
                    });
                const row = rows.find(candidate => (candidate.getAttribute('data-idx') || '') === '0') || rows[0];
                if (!row) return {clicked: false};
                const button = [...row.querySelectorAll('button, [role="button"]')]
                    .filter(visible)
                    .find(btn => {
                        const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                        return text.includes('use') || text.includes('select') || text.includes('revive') || text.includes('restore');
                    });
                const target = button || row;
                const pokemon = row.querySelector('.equip-poke-name')?.innerText || row.innerText || 'starter';
                click(target);
                return {clicked: true, pokemon: pokemon.trim()};
                """
            )

        used = None
        deadline = time.time() + 1.2
        while time.time() < deadline and not self.stop_event.is_set():
            used = click_starter_row()
            if used.get("clicked"):
                break
            time.sleep(0.08)
        if not used or not used.get("clicked"):
            self.log("Sacred Ash: clicked item, but no starter target picker appeared.")
            return False
        self.log(f"Sacred Ash: revived/restored {used.get('pokemon') or result.get('starterName') or 'starter'}.")
        time.sleep(0.45)
        return True

    def use_moon_stone_on_target_if_available(self):
        target_names = []
        if getattr(self, "reroll_acquired_target_name", ""):
            target_names.append(self.reroll_acquired_target_name)
        target_names.extend(list(getattr(self, "current_primary_target_names", set()) or []))
        target_names.extend(list(getattr(self, "current_target_pokemon_list", []) or []))
        target_names = [
            name for name in dict.fromkeys(self.normalize_pokemon_name(name) for name in target_names)
            if name
        ]
        if not target_names:
            return False
        result = self.driver.execute_script(
            """
            const targetNames = new Set(arguments[0].map(name => String(name || '').toLowerCase()));
            const normalize = (text) => String(text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
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
            const isMoonStoneText = (text) => {
                const norm = normalize(text);
                return norm.includes('moon stone') || norm.includes('moonstone');
            };
            const modalRows = [...document.querySelectorAll('#item-equip-modal .equip-pokemon-row, .equip-pokemon-row')]
                .filter(visible);
            if (modalRows.length) {
                const activeText = [
                    document.querySelector('#item-equip-modal')?.innerText || '',
                    document.querySelector('.screen.active')?.innerText || ''
                ].join(' ');
                if (!isMoonStoneText(activeText)) return {clicked: false};
                const rows = modalRows.map(row => {
                    const name = row.querySelector('.equip-poke-name')?.innerText
                        || row.querySelector('img[alt]')?.getAttribute('alt')
                        || row.innerText
                        || '';
                    const norm = normalize(name);
                    const button = [...row.querySelectorAll('button, [role="button"]')]
                        .filter(visible)
                        .find(btn => {
                            const text = normalize(btn.innerText || btn.textContent || '');
                            return text.includes('use') || text.includes('evolve') || text.includes('select');
                        });
                    return {row, name, norm, button};
                });
                const selected = rows.find(item => targetNames.has(item.norm))
                    || rows.find(item => [...targetNames].some(target => item.norm.includes(target) || target.includes(item.norm)));
                if (!selected) return {clicked: false, blocked: true, reason: 'target Pokemon not in Moon Stone picker'};
                click(selected.button || selected.row);
                return {clicked: true, pokemon: selected.name, phase: 'picker'};
            }
            const active = document.querySelector('.screen.active');
            if (active?.id && active.id !== 'item-screen' && active.id !== 'elite-prep-screen'
                && active.id !== 'map-screen' && active.id !== 'catch-screen'
                && active.id !== 'passive-screen') {
                return {clicked: false};
            }
            const badgeSelectors = [
                '#item-bar .item-badge',
                '#elite-prep-items .item-badge',
                '#item-team-bar .item-badge',
                '#catch-team-bar .item-badge',
                '#passive-team-bar .item-badge'
            ];
            const badge = [...document.querySelectorAll(badgeSelectors.join(','))]
                .filter(visible)
                .find(el => {
                    if (el.closest('#item-choices, .item-card, #passive-choices, .passive-card')) return false;
                    const text = [
                        el.innerText || el.textContent || '',
                        ...[...el.querySelectorAll('img')].map(img => `${img.getAttribute('alt') || ''} ${img.getAttribute('title') || ''} ${img.getAttribute('src') || ''}`)
                    ].join(' ');
                    return isMoonStoneText(text);
                });
            if (!badge) return {clicked: false};
            click(badge);
            return {clicked: true, pokemon: '', phase: 'badge'};
            """,
            target_names,
        )
        if result.get("clicked"):
            pokemon = " ".join(str(result.get("pokemon") or "").split())
            if pokemon:
                self.log(f"Moon Stone: used on {pokemon}.")
            else:
                self.log("Moon Stone: opened target picker.")
            time.sleep(0.45)
            return True
        if result.get("blocked"):
            self.log(f"Moon Stone skipped: {result.get('reason')}.")
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
                    if self.should_count_run_shiny_stats():
                        self.total_shinies_seen += len(shiny_names)
                        if shiny_names:
                            self.last_shiny_pokemon_name = shiny_names[-1]
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
            self.mark_reroll_target_acquired(result.get("name") or target_name, target_shiny)
            return self.current_reroll_completion_mode == REROLL_COMPLETE_STOP_NOW

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

    def click_catch_skip_if_available(self):
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
            const active = document.querySelector('#catch-screen.screen.active, #catch-screen, .screen.active') || document;
            const buttons = [...active.querySelectorAll([
                '#btn-flee',
                '#btn-skip-catch',
                '#btn-skip-pokemon',
                '.choice-skip-btn',
                '.choice-skip-cell',
                '[data-action="flee"]',
                '[data-action="skip"]',
                'button',
                '[role="button"]'
            ].join(','))].filter(visible);
            const button = buttons.find(btn => {
                const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                const id = (btn.id || '').toLowerCase();
                const cls = String(btn.className || '').toLowerCase();
                return id.includes('flee')
                    || id.includes('skip')
                    || cls.includes('flee')
                    || cls.includes('skip')
                    || text.includes('flee')
                    || text.includes('skip')
                    || text.includes('decline')
                    || text.includes('leave');
            });
            if (!button) {
                return {
                    clicked: false,
                    buttons: buttons.map(btn => (btn.innerText || btn.textContent || btn.id || '').trim()).filter(Boolean).slice(0, 8)
                };
            }
            button.scrollIntoView({block: 'center', inline: 'center'});
            const rect = button.getBoundingClientRect();
            const x = rect.left + rect.width / 2;
            const y = rect.top + rect.height / 2;
            const target = document.elementFromPoint(x, y) || button;
            for (const el of [...new Set([target, button])]) {
                el.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 1, pointerId: 1, pointerType: 'mouse', isPrimary: true}));
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 1}));
                el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0}));
                el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0}));
                el.dispatchEvent(new PointerEvent('pointerup', {bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0, buttons: 0, pointerId: 1, pointerType: 'mouse', isPrimary: true}));
            }
            if (typeof button.click === 'function') button.click();
            return {clicked: true, text: (button.innerText || button.textContent || button.id || 'flee').trim()};
            """
        )
        if result.get("clicked"):
            self.log(f"Catch screen: skipped/fled ({result.get('text') or 'skip'}).")
            time.sleep(0.6)
            return True
        self.log(f"Catch screen: no skip/flee button found. Visible actions: {result.get('buttons') or 'none'}.")
        return False

    def choose_priority_catch(self):
        def click_priority_choice(immediate_only=False):
            return self.driver.execute_script(
                """
                const immediateOnly = arguments[0];
                const priorityNames = arguments[1].map(name => name.toLowerCase());
                const legendaryNames = new Set(arguments[2].map(name => name.toLowerCase()));
                const dexPriorityNames = new Set(arguments[3].map(name => name.toLowerCase()));
                const dexTargetMode = arguments[4] || 'Off';
                const filters = arguments[5] || {};
                const allTypeNames = new Set((arguments[6] || []).map(name => String(name || '').toLowerCase()));
                const ignorePokemon = !!filters.ignorePokemon;
                const shinyOnly = !!filters.shinyOnly;
                const smartTraitChoice = !!filters.smartTraitChoice;
                const startShinyGate = !!filters.startShinyGate;
                const manualNames = new Set((filters.manualNames || []).map(name => String(name).toLowerCase()));
                const typeNames = new Set((filters.typeNames || []).map(name => String(name).toLowerCase()));
                const generationNames = new Set((filters.generationNames || []).map(name => String(name).toLowerCase()));
                const typeWhitelist = new Set((filters.typeWhitelist || []).map(name => String(name).toLowerCase()));
                const typeMode = filters.typeMode || 'Prioritize';
                const whitelistMode = filters.whitelistMode || 'Only whitelist';
                const generationWhitelist = new Set((filters.generationWhitelist || []).map(name => String(name).toLowerCase()));
                const partyCount = Math.min(Number(filters.partyCount || 0), 6);
                const matchAnyPriorityName = priorityNames.length === 0;
                const hardWhitelist = manualNames.size && (startShinyGate || whitelistMode !== 'Prioritize whitelist');
                const hardType = typeWhitelist.size && (startShinyGate || typeMode === 'Only');
                const filtersActive = ignorePokemon || shinyOnly || startShinyGate || hardWhitelist || hardType || generationWhitelist.size;
                const visible = (el) => {
                    const rect = el.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                };
                const normalize = (text) => (text || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
                const typeFromText = (text) => {
                    const norm = normalize(text);
                    return [...typeWhitelist].some(typeName =>
                        norm.includes(`${typeName} type`) || norm.split(' ').includes(typeName)
                    );
                };
                const visibleTraits = () => {
                    if (!smartTraitChoice) return [];
                    return [...document.querySelectorAll('#endless-trait-panel .trait-row, .map-panel-traits .trait-row')]
                        .filter(visible)
                        .map(row => {
                            const badge = row.querySelector('.type-badge');
                            const typeText = normalize(badge?.innerText || badge?.textContent || '');
                            const classText = String(badge?.className || '').toLowerCase();
                            const typeName = [...allTypeNames].find(typeName =>
                                typeText === typeName || classText.split(/\s+/).includes(`type-${typeName}`)
                            );
                            const countText = (row.querySelector('.trait-count')?.innerText || row.querySelector('.trait-count')?.textContent || '').trim();
                            const match = countText.match(/(\\d+)\\s*\\/\\s*(\\d+)(?:\\s*T(\\d+))?/i);
                            if (!typeName || !match) return null;
                            return {
                                typeName,
                                count: Number(match[1]) || 0,
                                needed: Number(match[2]) || 0,
                                tier: Number(match[3]) || 0,
                                inactive: row.classList.contains('trait-row-inactive'),
                                label: `${typeName} ${countText}`
                            };
                        })
                        .filter(trait => trait && trait.needed > 0);
                };
                const traitRows = visibleTraits();
                const whitelistTraitCount = traitRows
                    .filter(row => typeWhitelist.has(row.typeName))
                    .reduce((total, row) => total + Math.max(Number(row.count) || 0, 0), 0);
                const whitelistTargetFor = (detectedTypes, shiny) => {
                    if (!typeWhitelist.size) return 0;
                    const matchesWhitelist = [...detectedTypes].some(typeName => typeWhitelist.has(typeName));
                    return (whitelistTraitCount >= 5 || (matchesWhitelist && shiny)) ? 6 : 4;
                };
                const canStillHitWhitelistTarget = (detectedTypes, shiny) => {
                    if (!typeWhitelist.size) return true;
                    const matchesWhitelist = [...detectedTypes].some(typeName => typeWhitelist.has(typeName));
                    const contribution = matchesWhitelist ? (shiny ? 2 : 1) : 0;
                    const targetPoints = whitelistTargetFor(detectedTypes, shiny);
                    const projectedWhitelistPoints = Math.min(6, whitelistTraitCount + contribution);
                    const projectedPartyCount = Math.min(6, partyCount + 1);
                    const remainingSlots = Math.max(6 - projectedPartyCount, 0);
                    return projectedWhitelistPoints + remainingSlots >= targetPoints;
                };
                const typeSourcesFor = (card) => {
                    const directTypeBadges = [...card.querySelectorAll('.poke-types .type-badge, .dex-types .type-badge')];
                    if (directTypeBadges.length) return directTypeBadges;
                    return [
                        ...card.querySelectorAll('.type-badge:not(.move-type-badge), .poke-types [class*="type-"], .dex-types [class*="type-"]')
                    ];
                };
                const detectedTypesFor = (card) => {
                    const detected = new Set();
                    for (const el of typeSourcesFor(card)) {
                        const classText = String(el.className || '').toLowerCase();
                        const text = [
                            el.innerText || el.textContent || '',
                            el.getAttribute?.('aria-label') || '',
                            el.getAttribute?.('title') || '',
                            el.getAttribute?.('alt') || ''
                        ].join(' ');
                        const normText = normalize(text);
                        for (const typeName of allTypeNames) {
                            if (
                                classText.split(/\s+/).includes(`type-${typeName}`)
                                || normText === typeName
                                || normText.includes(`${typeName} type`)
                                || normText.split(' ').includes(typeName)
                            ) {
                                detected.add(typeName);
                            }
                        }
                    }
                    return detected;
                };
                const cards = [...new Set([...document.querySelectorAll('#catch-choices .poke-card, #catch-choices [role="button"], .catch-card')]
                    .map(el => el.closest('.poke-card, .catch-card') || el))]
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
                    const rawPriorityName = !matchAnyPriorityName && priorityNames.some(target =>
                        nameLower === target || alt === target || text.includes(target)
                    );
                    const dexPriorityName = [...dexPriorityNames].some(target =>
                        nameLower === target || alt === target || text.includes(target)
                    );
                    const manualPriorityName = rawPriorityName && !dexPriorityName;
                    const shiny = card.classList.contains('pc-dex-card--shiny')
                        || card.classList.contains('shiny')
                        || !!card.querySelector('.pc-shiny-star, .shiny-star')
                        || src.includes('/shiny/')
                        || text.includes('shiny');
                    const nameKey = normalize(name || alt);
                    const detectedTypes = detectedTypesFor(card);
                    const typeAllowed = !typeWhitelist.size
                        || typeNames.has(nameKey)
                        || [...detectedTypes].some(typeName => typeWhitelist.has(typeName))
                        || typeFromText(`${name} ${alt} ${text} ${src}`);
                    const generationAllowed = !generationWhitelist.size || generationNames.has(nameKey);
                    const manualMatched = manualNames.has(nameKey);
                    const manualAllowed = !manualNames.size
                        || (!startShinyGate && whitelistMode === 'Prioritize whitelist')
                        || manualMatched
                        || (whitelistMode === 'Only whitelist + shiny' && shiny);
                    const typeMatched = typeAllowed && typeWhitelist.size;
                    const reserveAllowed = canStillHitWhitelistTarget(detectedTypes, shiny);
                    const smartReserveCandidate = smartTraitChoice
                        && !startShinyGate
                        && shiny
                        && reserveAllowed;
                    const filterAllowed = !ignorePokemon
                        && (!shinyOnly || shiny)
                        && (!startShinyGate || shiny)
                        && manualAllowed
                        && (!hardType || typeAllowed || smartReserveCandidate)
                        && reserveAllowed
                        && generationAllowed;
                    const traitContribution = shiny ? 2 : 1;
                    let smartTraitScore = 0;
                    let smartTraitReason = '';
                    if (smartTraitChoice && detectedTypes.size) {
                        const reasons = [];
                        const whitelistMatches = [...detectedTypes].filter(typeName => typeWhitelist.has(typeName)).length;
                        const whitelistTargetPoints = whitelistTargetFor(detectedTypes, shiny);
                        if (whitelistMatches > 0 && whitelistTraitCount < whitelistTargetPoints) {
                            const contribution = shiny ? 2 : 1;
                            smartTraitScore += 900 + contribution * 180;
                            reasons.push(`whitelist trait target ${Math.min(6, whitelistTraitCount + contribution)}/${whitelistTargetPoints}`);
                        }
                        for (const typeName of detectedTypes) {
                            const trait = traitRows.find(row => row.typeName === typeName);
                            if (!trait) {
                                const newTraitScore = shiny ? 225 : 25;
                                smartTraitScore += newTraitScore;
                                reasons.push(shiny ? `new shiny ${typeName} trait` : `new ${typeName} trait`);
                                continue;
                            }
                            const remaining = Math.max(trait.needed - trait.count, 0);
                            let score = 100 + traitContribution * 40 + trait.tier * 80;
                            if (trait.inactive) score += 40;
                            let nextText = ' improves trait';
                            if (remaining > 0 && traitContribution >= remaining) {
                                score += 700 + trait.tier * 160;
                                nextText = ' completes next trait tier';
                            } else if (remaining > 0) {
                                score += Math.round((traitContribution / remaining) * 220);
                            } else {
                                score += 260 + trait.tier * 120;
                                nextText = ' reinforces active trait';
                            }
                            if (shiny) score += 140;
                            if (typeWhitelist.has(typeName)) score += 90;
                            smartTraitScore += score;
                            reasons.push(`${typeName}${nextText} (${trait.count}+${traitContribution}/${trait.needed}${trait.tier ? ` T${trait.tier}` : ''})`);
                        }
                        if (whitelistMatches > 0) {
                            smartTraitScore += whitelistMatches * 120;
                        }
                        smartTraitReason = reasons.slice(0, 2).join('; ');
                    }
                    const smartTraitAllowed = smartTraitChoice
                        && !startShinyGate
                        && !ignorePokemon
                        && shiny
                        && smartTraitScore > 0
                        && reserveAllowed
                        && manualAllowed
                        && generationAllowed;
                    const dexAllowed = !dexPriorityName
                        ? false
                        : dexTargetMode === 'Missing shiny Dex'
                            ? shiny
                            : dexTargetMode === 'Missing normal + shiny Dex'
                                ? true
                                : !shiny;
                    return {
                        card,
                        index,
                        name,
                        priorityName: manualPriorityName || dexAllowed,
                        manualPriorityName,
                        dexPriorityName: dexAllowed,
                        filterAllowed,
                        smartTraitAllowed,
                        reserveAllowed,
                        typePriority: typeMatched,
                        detectedTypes: [...detectedTypes],
                        smartTraitScore,
                        smartTraitReason,
                        shiny,
                        legendary: normalizedText.includes('legendary')
                            || [...legendaryNames].some(legendary => nameLower === legendary || alt === legendary || normalizedText.includes(legendary))
                    };
                };
                const infos = cards.map(infoFor);
                const targetCount = infos.filter(info => info.priorityName).length;
                const shinyNames = infos.filter(info => info.shiny).map(info => info.name || 'unknown');
                const names = infos.map(info => `${info.index + 1}:${info.name || 'unknown'} shiny=${info.shiny}`).join(' | ');
                const signature = infos.map(info => `${info.index}:${info.name || 'unknown'}:${info.shiny}`).join('|');
                const selectable = filtersActive
                    ? (ignorePokemon ? [] : infos.filter(info => info.filterAllowed || info.dexPriorityName || info.smartTraitAllowed))
                    : infos;
                if (!selectable.length) {
                    return {
                        clicked: false,
                        filteredOut: true,
                        reason: ignorePokemon ? 'ignore pokemon' : 'filters',
                        offered: infos.map(info => `${info.name || 'unknown'}:${!info.reserveAllowed ? 'reserve-full' : info.shiny ? 'shiny' : info.legendary ? 'legendary' : info.detectedTypes.length ? `type=${info.detectedTypes.join('/')}` : 'other'}`),
                        startShinyGate,
                        checked: infos.length,
                        targetCount,
                        shinyNames,
                        names,
                        signature
                    };
                }
                const selected = selectable.find(info => info.dexPriorityName)
                    || selectable.filter(info => info.smartTraitScore > 0).sort((a, b) => b.smartTraitScore - a.smartTraitScore)[0]
                    || selectable.find(info => info.shiny)
                    || selectable.find(info => info.legendary)
                    || selectable.find(info => info.priorityName)
                    || selectable.find(info => info.typePriority)
                    || selectable[0];
                const reason = selected.dexPriorityName ? 'dex target'
                    : startShinyGate ? 'start shiny filter'
                    : selected.smartTraitScore > 0 ? `smart trait: ${selected.smartTraitReason}`
                    : selected.shiny ? 'shiny'
                    : selected.legendary ? 'legendary'
                    : selected.priorityName ? 'pokemon list'
                    : selected.typePriority ? 'type'
                    : 'random';
                if (immediateOnly && reason !== 'dex target' && reason !== 'start shiny filter' && !reason.startsWith('smart trait:') && reason !== 'pokemon list' && reason !== 'shiny' && reason !== 'legendary' && reason !== 'type') {
                    return {
                        clicked: false,
                        deferred: true,
                        name: selected.name,
                        reason,
                        offered: infos.map(info => `${info.name || 'unknown'}:${!info.reserveAllowed ? 'reserve-full' : info.dexPriorityName ? 'dex' : info.smartTraitScore > 0 ? `trait=${info.smartTraitScore}` : info.priorityName ? 'list' : info.shiny ? 'shiny' : info.detectedTypes.length ? `type=${info.detectedTypes.join('/')}` : 'other'}`),
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
                    offered: infos.map(info => `${info.name || 'unknown'}:${!info.reserveAllowed ? 'reserve-full' : info.dexPriorityName ? 'dex' : info.smartTraitScore > 0 ? `trait=${info.smartTraitScore}` : info.priorityName ? 'list' : info.shiny ? 'shiny' : info.detectedTypes.length ? `type=${info.detectedTypes.join('/')}` : 'other'}`),
                    checked: infos.length,
                    targetCount,
                    shinyNames,
                    names,
                    signature,
                    startShinyGate
                };
                """,
                immediate_only,
                self.current_target_pokemon_list,
                [self.normalize_pokemon_name(name) for name in LEGENDARY_POKEMON_NAMES],
                list(getattr(self, "current_dex_target_names", set()) or []),
                self.current_dex_target_mode,
                self.pokemon_filter_payload(),
                list(POKEMON_TYPE_NAMES),
            )

        result = click_priority_choice(immediate_only=True)
        if result.get("filteredOut") and not self.catch_reroll_used and self.click_catch_rerolls_if_available():
            self.record_catch_scan(result, "full run filtered before reroll")
            time.sleep(0.4)
            result = click_priority_choice(immediate_only=False)
        if result.get("deferred") and not self.catch_reroll_used and self.click_catch_rerolls_if_available():
            self.record_catch_scan(result, "full run before reroll")
            time.sleep(0.4)
            result = click_priority_choice(immediate_only=False)
        elif result.get("deferred"):
            result = click_priority_choice(immediate_only=False)

        if result.get("clicked"):
            self.record_catch_scan(result, "full run")
            if result.get("startShinyGate"):
                self.start_shiny_filter_acquired = True
            if result.get("reason") == "legendary":
                self.record_legendary_encounter(f"catch:{result.get('signature')}:{result.get('name')}")
            self.log(f"Catch screen: selected {result.get('name') or 'Pokemon'} by {result.get('reason')} priority.")
            time.sleep(0.8)
            return False
        if result.get("filteredOut"):
            self.record_catch_scan(result, "full run filtered")
            if result.get("startShinyGate"):
                self.restart_attempt = True
                self.log(
                    "Start shiny filter missed after catch rerolls; restarting run. "
                    f"Offered: {result.get('offered') or result.get('names') or 'unknown'}."
                )
                return False
            self.log(
                "Catch screen: no Pokemon passed the active filters; fleeing and continuing run. "
                f"Offered: {result.get('offered') or result.get('names') or 'unknown'}."
            )
            self.click_catch_skip_if_available()
            return False
        self.log("Catch screen had no clickable Pokemon choices.")
        return False

    def handle_active_screen(self):
        if self.stop_if_cloud_save_conflict_visible():
            return True
        screen = self.active_screen_id()

        if self.should_use_full_run_logic():
            self.record_money_earned_if_visible()
        if screen not in ["gameover-screen", "win-screen"]:
            self.refresh_team_snapshot()
            if self.completed_primary_dex_target_in_party():
                return True
        if (
            self.should_use_full_run_logic()
            and screen not in ["gameover-screen", "win-screen"]
        ):
            result_state = self.visible_play_again_result_state() or {}
            if result_state.get("visible"):
                won = result_state.get("won")
                if won is not None:
                    self.record_run_history_result(bool(won), result_state.get("screen") or screen)
                if self.click_play_again_if_visible():
                    return False

        reward_screens = {
            "catch-screen",
            "shiny-screen",
            "swap-screen",
            "trade-screen",
            "passive-screen",
            "item-screen",
            "stat-buff-screen",
            "badge-screen",
            "elite-prep-screen",
        }
        equip_screens = {"item-screen", "elite-prep-screen"}
        move_tutor_screens = equip_screens | {"map-screen"}

        if self.handle_evolution_choice():
            return False

        if screen in equip_screens and self.handle_tm_item_equip():
            return False

        if screen in equip_screens and self.use_moon_stone_on_target_if_available():
            return False

        if screen in move_tutor_screens and self.handle_move_tutor():
            time.sleep(0.5)
            return False

        if screen == "elite-prep-screen" and self.handle_boss_combat_item_swap():
            return False

        if screen in equip_screens and self.handle_regular_item_equip():
            return False

        if (
            screen == "swap-screen"
            and self.pending_team_replace
            and self.pending_replace_policy in {"legendary", "legendary_shiny"}
            and self.swap_team_count() < 6
        ):
            self.pending_replace_allow_any = False
            self.pending_replace_add_clicked = False
            self.pending_replace_policy = "add_only"

        if screen in {"swap-screen", "catch-screen", "shiny-screen"} and self.handle_team_replace_choice():
            return False

        if self.pending_passive_item_name and self.handle_passive_replace_choice():
            return False

        if screen == "elite-prep-screen":
            self.record_leader_or_elite_if_visible("elite prep", include_map_info=True)

        if screen == "elite-prep-screen" and self.handle_final_fight_confirm():
            return False

        if screen in {"badge-screen", "item-screen", "map-screen"} and self.restore_boss_combat_item_if_needed():
            return False

        if screen in {"catch-screen", "shiny-screen", "swap-screen"} and self.handle_pokemon_reward_policy():
            return False

        if screen == "shiny-screen" and self.handle_take_shiny_reward():
            return False

        if screen in {"catch-screen", "shiny-screen"} and self.handle_event_pokemon_reward():
            return False

        if self.is_pokemon_reroll_mode() and not self.should_complete_current_reroll_run() and screen in [
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

        if self.should_use_full_run_logic() and screen in [
            "map-screen",
            "item-screen",
            "catch-screen",
            "passive-screen",
            "elite-prep-screen",
        ]:
            if self.use_sacred_ash_on_fainted_starter_if_available():
                return False
            if self.use_rare_candy_on_starter_if_available():
                return False
            if self.use_moon_stone_on_target_if_available():
                return False

        if screen == "map-screen":
            self.catch_reroll_used = False
            if self.is_pokemon_reroll_mode() and not self.should_complete_current_reroll_run():
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
            self.record_leader_or_elite_if_visible("battle")
            self.advance_battle()
            return False

        if screen == "elite-prep-screen":
            self.record_leader_or_elite_if_visible("elite prep", include_map_info=True)

        if screen == "item-screen":
            if self.is_pokemon_reroll_mode() and not self.should_complete_current_reroll_run():
                if self.visible_item_choice_context():
                    self.choose_item(target_only=False)
                    return False
                self.restart_attempt = True
                self.log("Reached non-starting item screen in Pokemon reroll mode. Restarting.")
                return False

            if self.awaiting_leader_item_roll:
                self.awaiting_leader_item_roll = False
                if self.is_target_item_reroll_mode():
                    found = self.choose_item(target_only=True)
                    if not found:
                        self.restart_attempt = True
                        self.log(
                            f"{self.current_item_reroll_target.title()} was not in the first leader item rolls. Restarting."
                        )
                    elif self.is_complete_pokedex_mode():
                        self.mark_reroll_target_acquired(COMPLETE_POKEDEX_ITEM_TARGET, False)
                        return False
                    return found
                reroll_mode = self.is_target_item_reroll_mode()
                found = self.choose_item(target_only=reroll_mode)
                if not found:
                    if reroll_mode:
                        self.restart_attempt = True
                        self.log(
                            f"{self.current_item_reroll_target.title()} was not in the first leader item rolls. Restarting."
                        )
                    else:
                        self.log("Shiny Charm was not in the first leader item rolls; continuing full run.")
                return found

            return self.choose_item(target_only=False)

        if screen == "catch-screen":
            if self.should_complete_current_reroll_run():
                return self.choose_priority_catch()
            if self.current_mode == MODE_SHINY_POKEMON_REROLL or (
                self.current_mode == MODE_COMPLETE_POKEDEX
                and self.complete_pokedex_phase == "shiny_regular"
            ):
                return self.handle_target_shiny_catch()
            if self.current_mode == MODE_NORMAL_POKEMON_REROLL or (
                self.current_mode == MODE_COMPLETE_POKEDEX
                and self.complete_pokedex_phase == "normal_regular"
            ):
                return self.handle_target_normal_catch()

            return self.choose_priority_catch()

        if screen == "swap-screen":
            # A legendary from a map node arrives directly on the swap screen
            # (no take/skip step), so pending_team_replace isn't set. If the
            # incoming Pokémon is a legendary, route it through the team-replace
            # handler: it clicks "Add X to team!" when there's room, or releases a
            # valid Pokémon when the team is full. Otherwise keep the team as-is.
            incoming = self.swap_incoming_info() or {}
            swap_party_count = self.swap_team_count()
            if self.pokemon_filters_enabled() and not self.pokemon_name_allowed_by_filters(
                incoming.get("name"),
                shiny=bool(incoming.get("shiny")),
            ):
                self.log(f"Team replace: skipped incoming Pokemon by filters ({incoming.get('name') or 'unknown'}).")
                self.js_click("#btn-cancel-swap")
                time.sleep(0.6)
                return False
            if (incoming.get("legendary") or incoming.get("hasAdd")) and swap_party_count < 6:
                self.pending_team_replace = True
                self.pending_replace_allow_any = False
                self.pending_replace_add_clicked = False
                self.pending_replace_policy = "add_only"
                if self.handle_team_replace_choice():
                    return False
                self.pending_team_replace = False
                self.pending_replace_allow_any = False
                self.pending_replace_add_clicked = False
                self.pending_replace_policy = "default"
                self.log("Team replace: waiting for Add to team control on underfilled team.")
                time.sleep(0.4)
                return False
            if incoming.get("legendary"):
                self.record_legendary_encounter(f"swap:{incoming.get('name')}:{self.active_screen_id()}")
                self.pending_team_replace = True
                self.pending_replace_allow_any = bool(incoming.get("shiny"))
                self.pending_replace_add_clicked = False
                self.pending_replace_policy = "legendary_shiny" if incoming.get("shiny") else "legendary"
                if self.handle_team_replace_choice():
                    return False
                self.pending_team_replace = False
                self.pending_replace_add_clicked = False
            self.js_click("#btn-cancel-swap")
            time.sleep(0.6)
            return False

        if screen == "trade-screen":
            self.js_click("#btn-skip-trade")
            time.sleep(0.6)
            return False

        if screen == "passive-screen":
            if self.is_target_item_reroll_mode():
                self.awaiting_leader_item_roll = False
                found = self.choose_passive_item(target_only=True)
                if not found:
                    self.restart_attempt = True
                    self.log(
                        f"{self.current_item_reroll_target.title()} was not in the passive rolls. Restarting."
                    )
                elif self.is_complete_pokedex_mode():
                    self.mark_reroll_target_acquired(COMPLETE_POKEDEX_ITEM_TARGET, False)
                    return False
                return found

            self.choose_passive_item()
            self.ensure_dex_targets_ready("starting item selection")
            time.sleep(0.25)
            return False

        if screen == "stat-buff-screen":
            self.js_click("#stat-buff-choices .stat-buff-card")
            time.sleep(0.6)
            return False

        if screen == "badge-screen":
            self.maps_reached += 1
            self.record_leader_or_elite_if_visible("badge", include_map_info=True)
            self.awaiting_leader_item_roll = True
            self.log("Badge screen reached.")
            self.update_stats_labels()
            self.js_click("#btn-next-map")
            time.sleep(1.0)
            return False

        if screen == "gameover-screen":
            return self.handle_completed_run_result(False, screen)

        if screen == "win-screen":
            return self.handle_completed_run_result(True, screen)

        time.sleep(0.5)
        return False

    def handle_completed_run_result(self, won, screen):
        self.record_money_earned_if_visible()
        self.record_run_history_result(won, screen)
        if getattr(self, "resumed_existing_challenge_run", False):
            self.resumed_existing_challenge_run = False
            if self.click_home_if_visible():
                self.restart_attempt = True
                self.log("Finished resumed Challenge run; returning Home to start the configured run.")
                return False
            raise RuntimeError("Finished resumed Challenge run, but Home was not available.")
        schedule_action = self.update_schedule_after_result(won, screen)
        if schedule_action == "done":
            return False
        if schedule_action == "advance":
            if self.click_home_if_visible():
                self.restart_attempt = True
                return False
            raise RuntimeError("Schedule needs the next task, but Home was not available on the result screen.")
        if (
            self.current_mode == MODE_POKEGOLD_FARM
            and not self.schedule_active
            and int(self.total_money_earned or 0) >= int(self.current_pokegold_farm_target or 1)
        ):
            self.set_status("Pokegold target reached")
            self.log(
                f"Farm Pokegold target reached: {int(self.total_money_earned or 0):,}/"
                f"{int(self.current_pokegold_farm_target or 1):,} Pokegold."
            )
            return True
        if self.is_complete_pokedex_mode():
            previous_phase = self.complete_pokedex_phase_label or self.complete_pokedex_phase or "current phase"
            self.reroll_target_acquired = False
            self.reroll_acquired_target_name = ""
            phase_ready = self.prepare_complete_pokedex_phase(
                reason=f"completed {previous_phase} run",
                force_refresh=True,
            )
            if not phase_ready or self.complete_pokedex_phase == "done":
                return True
            if self.click_play_again_if_visible():
                self.start_next_play_again_run()
                self.log(f"Complete Pokedex continuing with {self.complete_pokedex_phase_label} phase.")
                return False
            raise RuntimeError("Complete Pokedex needs the next run, but Play Again was not available.")
        if self.should_complete_current_reroll_run():
            acquired = (self.reroll_acquired_target_name or "target").title()
            if self.current_reroll_completion_mode == REROLL_COMPLETE_ONE_FULL_RUN:
                self.set_status("Target found")
                self.log(f"Completed one full run after reroll target {acquired}.")
                return True
            self.remove_acquired_target_from_active_list()
            if not self.current_target_pokemon_list:
                self.set_status("Target found")
                self.log("Reroll chain completed: no whitelist/Dex targets remain.")
                return True
            if self.click_play_again_if_visible():
                self.reroll_target_acquired = False
                self.reroll_acquired_target_name = ""
                self.start_next_play_again_run()
                self.log(f"Reroll chain continuing with remaining targets: {self.current_target_pokemon}.")
                return False
            raise RuntimeError("Reroll chain needs the next run, but Play Again was not available.")
        if self.click_play_again_if_visible():
            if self.should_use_full_run_logic():
                self.start_next_play_again_run()
            else:
                self.restart_attempt = True
            return False
        if self.is_pokemon_reroll_mode():
            self.restart_attempt = True
            if won:
                self.log("Run won without a whitelist hit. Starting another attempt.")
            else:
                self.log("Run ended without a whitelist hit. Starting another attempt.")
            return False
        if won:
            raise RuntimeError("Run reached win screen before target item appeared.")
        raise RuntimeError("Run ended and Play Again was not available.")

    def start_next_play_again_run(self):
        worker_id = getattr(self.thread_local, "worker_id", 1)
        worker_attempt = getattr(self.thread_local, "attempt_count", 0) + 1
        self.thread_local.attempt_count = worker_attempt
        prefix = f"B{worker_id} " if self.browser_count > 1 else ""
        return self.reset_run_tracking(prefix=prefix)

    def reset_run_tracking(self, prefix=""):
        with self.stats_lock:
            self.run_count += 1
            run_number = self.run_count
        self.update_stats_labels()
        self.awaiting_leader_item_roll = False
        self.restart_attempt = False
        self.catch_reroll_used = False
        self.start_shiny_filter_acquired = False
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
        self.last_leader_signature = None
        self.last_team_snapshot_signature = None
        self.last_team_snapshot = []
        self.last_passive_items_snapshot = []
        self.pending_team_replace = False
        self.pending_replace_allow_any = False
        self.pending_replace_policy = "default"
        self.pending_replace_add_clicked = False
        self.pending_passive_item_name = ""
        self.pending_passive_item_priority = None
        self.run_encounters_checked = 0
        self.run_target_encounters = 0
        self.log(f"========== {prefix}RUN #{run_number} ==========")
        return run_number

    def run_single_attempt(self):
        worker_id = getattr(self.thread_local, "worker_id", 1)
        worker_attempt = getattr(self.thread_local, "attempt_count", 0) + 1
        self.thread_local.attempt_count = worker_attempt
        prefix = f"B{worker_id} " if self.browser_count > 1 else ""
        run_number = self.reset_run_tracking(prefix=prefix)
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
            if self.stop_if_cloud_save_conflict_visible():
                return True
            self.restart_chrome_if_due(worker_id)
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

    def run_bot_worker(self, worker_id, driver, run_token=None):
        self.thread_local.use_local = True
        self.thread_local.worker_id = worker_id
        self.thread_local.attempt_count = 0
        self.thread_local.last_chrome_restart_at = time.time()
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)
        try:
            try:
                self.log(f"B{worker_id} ready: screen={self.active_screen_id() or 'unknown'}")
            except Exception as exc:
                self.log(f"B{worker_id} ready check failed: {exc}")
            recoveries = 0
            while not self.stop_event.is_set() and self.is_active_bot_run_token(run_token):
                try:
                    found = self.run_single_attempt()
                    recoveries = 0
                except Exception as e:
                    if not (self.is_pokemon_reroll_mode() or self.is_complete_pokedex_mode()) or self.stop_event.is_set():
                        raise
                    recoveries += 1
                    screen = "unknown"
                    try:
                        screen = self.active_screen_id()
                    except Exception:
                        pass
                    loop_name = "Complete Pokedex" if self.is_complete_pokedex_mode() else "Pokemon reroll"
                    self.log(f"Recovering {loop_name} loop after error on {screen}: {e}")
                    if recoveries >= 5:
                        raise RuntimeError(f"{loop_name} loop failed {recoveries} times in a row: {e}")
                    time.sleep(0.4)
                    continue
                if found:
                    if not self.is_active_bot_run_token(run_token):
                        break
                    driver = self.driver
                    self.winning_driver = driver
                    self.stop_event.set()
                    self.close_other_drivers(driver)
                    self.log(f"B{worker_id} found target. Final runtime: {self.format_runtime()}")
                    break
                if self.is_complete_pokedex_mode():
                    target_kind = self.complete_pokedex_phase_label or "dex"
                    self.log(f"B{worker_id}: Complete Pokedex has no {target_kind} hit yet. Restarting...")
                elif self.is_pokemon_reroll_mode():
                    target_kind = "shiny" if self.current_mode == MODE_SHINY_POKEMON_REROLL else "normal"
                    self.log(f"B{worker_id}: no whitelisted {target_kind} Pokemon found. Restarting...")
                elif self.current_mode == MODE_ITEM_REROLL:
                    self.log(f"B{worker_id}: no {self.current_item_reroll_target.title()} yet. Restarting...")
                else:
                    self.log(f"B{worker_id}: no Shiny Charm yet. Restarting...")

        except Exception as e:
            if not self.stop_event.is_set() and self.is_active_bot_run_token(run_token):
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
        run_token = self.active_bot_run_token
        try:
            if not self.is_active_bot_run_token(run_token):
                return
            if self.is_shop_reroll_mode():
                shop_outcome = self.run_legendary_shop_reroll()
                if shop_outcome != "schedule_advance" or not self.is_active_bot_run_token(run_token):
                    return

            live_before_launch = len(self.get_live_drivers())
            drivers = self.launch_missing_drivers(self.browser_count)
            if not self.headless_var.get() and (not self.windows_arranged or len(drivers) != live_before_launch):
                self.arrange_browser_windows()
                self.windows_arranged = True
            self.log(f"Running with {len(drivers)} browser window(s).")
            if self.is_complete_pokedex_mode() and drivers:
                self.thread_local.use_local = True
                self.driver = drivers[0]
                self.wait = WebDriverWait(drivers[0], 30)
                try:
                    if not self.prepare_complete_pokedex_phase(reason="startup", force_refresh=True):
                        self.stop_event.set()
                finally:
                    self.clear_thread_driver()
            elif self.current_dex_target_mode != DEX_TARGET_OFF and drivers:
                preload = getattr(self, "dex_preload_thread", None)
                if preload is not None and preload.is_alive():
                    self.log("Dex targets: waiting for background Pokédex preload to finish.")
                    preload.join(timeout=35.0)
                if (
                    self.cached_dex_target_mode == self.current_dex_target_mode
                    and self.cached_dex_targets.get(self.current_dex_target_mode)
                ):
                    dex_targets = list(self.cached_dex_targets[self.current_dex_target_mode])
                    self.log(f"Dex targets: using {len(dex_targets)} preloaded target(s).")
                    self.current_target_pokemon_list = self.build_current_pokemon_targets(
                        self.current_manual_target_pokemon_list,
                        dex_targets,
                    )
                    self.current_target_pokemon = ", ".join(self.current_target_pokemon_list)
                    if self.current_target_pokemon_list:
                        self.log(f"Active Pokemon target list: {self.current_target_pokemon}.")
                else:
                    self.log("Dex targets: will retrieve Pokédex data after the run starts and the page is ready.")

            if self.stop_event.is_set() or not self.is_active_bot_run_token(run_token):
                return

            for worker_id, driver in enumerate(drivers, start=1):
                thread = threading.Thread(target=self.run_bot_worker, args=(worker_id, driver, run_token), daemon=True)
                threads.append(thread)
                thread.start()

            while any(thread.is_alive() for thread in threads) and self.is_active_bot_run_token(run_token):
                for thread in threads:
                    thread.join(timeout=0.2)

            if self.is_active_bot_run_token(run_token) and self.status_var.get() not in ["Target found", "Error"]:
                self.set_status("Stopped")

        except Exception as e:
            if not self.stop_event.is_set() and self.is_active_bot_run_token(run_token):
                self.set_status("Error")
                self.log(f"ERROR: {e}")

        finally:
            if not self.is_active_bot_run_token(run_token):
                return
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
