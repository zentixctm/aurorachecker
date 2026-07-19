import re
import os

CHEAT_PATTERNS = {
    'KillAura': re.compile(r'\bKillAura\b', re.IGNORECASE),
    'Aimbot': re.compile(r'\bAimbot\b', re.IGNORECASE),
    'AutoClicker': re.compile(r'\bAutoClicker\b', re.IGNORECASE),
    'Reach': re.compile(r'\bReach\b', re.IGNORECASE),
    'ESP': re.compile(r'\bTargetESP\b|\bESP\b', re.IGNORECASE),
    'Velocity': re.compile(r'\bVelocity\b', re.IGNORECASE),
    'Hitbox': re.compile(r'\bHitbox\b', re.IGNORECASE),
    'Scaffold': re.compile(r'\bScaffold\b', re.IGNORECASE),
    'BowAura': re.compile(r'\bBowAura\b', re.IGNORECASE),
    'Speed': re.compile(r'\bSpeed\b', re.IGNORECASE),
    'Fly': re.compile(r'\bFly\b', re.IGNORECASE),
    'NoFall': re.compile(r'\bNoFall\b', re.IGNORECASE),
    'AntiVoid': re.compile(r'\bAntiVoid\b', re.IGNORECASE),
    'FastBreak': re.compile(r'\bFastBreak\b', re.IGNORECASE),
    'AutoArmor': re.compile(r'\bAutoArmor\b', re.IGNORECASE),
    'ChestStealer': re.compile(r'\bChestStealer\b|\bChestSteal\b', re.IGNORECASE),
    'Xray': re.compile(r'\bXray\b', re.IGNORECASE),
    'Tracers': re.compile(r'\bTracers\b', re.IGNORECASE),
    'Fullbright': re.compile(r'\bFullbright\b', re.IGNORECASE),
    'NoSlow': re.compile(r'\bNoSlow\b', re.IGNORECASE),
    'Jesus': re.compile(r'\bJesus\b', re.IGNORECASE),
    'Spider': re.compile(r'\bSpider\b', re.IGNORECASE),
    'Step': re.compile(r'\bStep\b', re.IGNORECASE),
    'Sprint': re.compile(r'\bSprint\b', re.IGNORECASE),
    'AutoTotem': re.compile(r'\bAutoTotem\b', re.IGNORECASE),
    'SelfDestruct': re.compile(r'\bSelfDestruct\b', re.IGNORECASE),
    'LogoutSpot': re.compile(r'\bLogoutSpot\b', re.IGNORECASE),
    'ItemESP': re.compile(r'\bItemESP\b', re.IGNORECASE),
    'PlayerESP': re.compile(r'\bPlayerESP\b', re.IGNORECASE),
    'StorageESP': re.compile(r'\bStorageESP\b', re.IGNORECASE),
    'Nametags': re.compile(r'\bNametags\b', re.IGNORECASE),
    'Clicker': re.compile(r'\bClicker\b', re.IGNORECASE),
    'AimAssist': re.compile(r'\bAimAssist\b', re.IGNORECASE),
    'TriggerBot': re.compile(r'\bTriggerBot\b', re.IGNORECASE),
    'AnchorTweaks': re.compile(r'\bAnchorTweaks\b|\banchor macro\b|\banchortweaks\b', re.IGNORECASE),
    'AutoDoubleHand': re.compile(r'\bAutoDoubleHand\b|\bautodoublehand\b', re.IGNORECASE),
    'AutoHitCrystal': re.compile(r'\bAutoHitCrystal\b|\bautohitcrystal\b', re.IGNORECASE),
    'JumpReset': re.compile(r'\bJumpReset\b', re.IGNORECASE),
    'LegitTotem': re.compile(r'\bLegitTotem\b|\blegittotem\b', re.IGNORECASE),
    'ShieldBreaker': re.compile(r'\bShieldBreaker\b|\bshield breaker\b', re.IGNORECASE),
    'AxeSpam': re.compile(r'\bAxeSpam\b|\baxe spam\b', re.IGNORECASE),
    'WebMacro': re.compile(r'\bWebMacro\b|\bweb macro\b', re.IGNORECASE),
    'FastPlace': re.compile(r'\bFastPlace\b', re.IGNORECASE),
    'WalskyOptimizer': re.compile(r'\bWalskyOptimizer\b|\bWalksyOptimizer\b|\bwalsky\.optimizer\b', re.IGNORECASE),
    'ShieldDisabler': re.compile(r'\bShieldDisabler\b', re.IGNORECASE),
    'SilentAim': re.compile(r'\bSilentAim\b', re.IGNORECASE),
    'AntiMissClick': re.compile(r'\bAntiMissClick\b', re.IGNORECASE),
    'LagReach': re.compile(r'\bLagReach\b', re.IGNORECASE),
    'PopSwitch': re.compile(r'\bPopSwitch\b', re.IGNORECASE),
    'SprintReset': re.compile(r'\bSprintReset\b', re.IGNORECASE),
    'AntiBot': re.compile(r'\bAntiBot\b', re.IGNORECASE),
    'ElytraSwap': re.compile(r'\bElytraSwap\b', re.IGNORECASE),
    'FastXP': re.compile(r'\bFastXP\b|\bFastExp\b', re.IGNORECASE),
    'Refill': re.compile(r'\bRefill\b', re.IGNORECASE),
    'NoJumpDelay': re.compile(r'\bNoJumpDelay\b', re.IGNORECASE),
    'AirAnchor': re.compile(r'\bAirAnchor\b', re.IGNORECASE),
    'FakeInv': re.compile(r'\bFakeInv\b', re.IGNORECASE),
    'PackSpoof': re.compile(r'\bPackSpoof\b', re.IGNORECASE),
    'Antiknockback': re.compile(r'\bAntiknockback\b', re.IGNORECASE),
    'catlean': re.compile(r'\bcatlean\b', re.IGNORECASE),
    'Argon': re.compile(r'\bArgon\b', re.IGNORECASE),
    'AuthBypass': re.compile(r'\bAuthBypass\b', re.IGNORECASE),
    'Asteria': re.compile(r'\bAsteria\b', re.IGNORECASE),
    'Prestige': re.compile(r'\bPrestige\b', re.IGNORECASE),
    'AutoEat': re.compile(r'\bAutoEat\b', re.IGNORECASE),
    'AutoMine': re.compile(r'\bAutoMine\b', re.IGNORECASE),
    'MaceSwap': re.compile(r'\bMaceSwap\b|\bAutoMace\b|\bMace Priority\b', re.IGNORECASE),
    'DoubleAnchor': re.compile(r'\bDoubleAnchor\b', re.IGNORECASE),
    'AutoTPA': re.compile(r'\bAutoTPA\b', re.IGNORECASE),
    'Xenon': re.compile(r'\bXenon\b', re.IGNORECASE),
    'gypsy': re.compile(r'\bgypsy\b', re.IGNORECASE),
    'dontPlaceCrystal': re.compile(r'\bdontPlaceCrystal\b', re.IGNORECASE),
    'dontBreakCrystal': re.compile(r'\bdontBreakCrystal\b', re.IGNORECASE),
    'canPlaceCrystalServer': re.compile(r'\bcanPlaceCrystalServer\b', re.IGNORECASE),
    'healPotSlot': re.compile(r'\bhealPotSlot\b', re.IGNORECASE),
    'speedPotSlot': re.compile(r'\bspeedPotSlot\b', re.IGNORECASE),
    'strengthPotSlot': re.compile(r'\bstrengthPotSlot\b', re.IGNORECASE),
    'hasGlowstone': re.compile(r'\bhasGlowstone\b', re.IGNORECASE),
    'HasAnchor': re.compile(r'\bHasAnchor\b', re.IGNORECASE),
    'preventSwordBlockBreaking': re.compile(r'\bpreventSwordBlockBreaking\b', re.IGNORECASE),
    'preventSwordBlockAttack': re.compile(r'\bpreventSwordBlockAttack\b', re.IGNORECASE),
    'swapBackToOriginalSlot': re.compile(r'\bswapBackToOriginalSlot\b', re.IGNORECASE),
    'autoCrystalPlaceClock': re.compile(r'\bautoCrystalPlaceClock\b', re.IGNORECASE),
    'setBlockBreakingCooldown': re.compile(r'\bsetBlockBreakingCooldown\b', re.IGNORECASE),
    'getBlockBreakingCooldown': re.compile(r'\bgetBlockBreakingCooldown\b', re.IGNORECASE),
    'blockBreakingCooldown': re.compile(r'\bblockBreakingCooldown\b', re.IGNORECASE),
    'onBlockBreaking': re.compile(r'\bonBlockBreaking\b', re.IGNORECASE),
    'setItemUseCooldown': re.compile(r'\bsetItemUseCooldown\b', re.IGNORECASE),
    'setSelectedSlot': re.compile(r'\bsetSelectedSlot\b', re.IGNORECASE),
    'invokeDoAttack': re.compile(r'\binvokeDoAttack\b', re.IGNORECASE),
    'invokeDoItemUse': re.compile(r'\binvokeDoItemUse\b', re.IGNORECASE),
    'invokeOnMouseButton': re.compile(r'\binvokeOnMouseButton\b', re.IGNORECASE),
    'onTickMovement': re.compile(r'\bonTickMovement\b', re.IGNORECASE),
    'onPushOutOfBlocks': re.compile(r'\bonPushOutOfBlocks\b', re.IGNORECASE),
    'onIsGlowing': re.compile(r'\bonIsGlowing\b', re.IGNORECASE),
    'Future': re.compile(r'\bFutureClient\b|\bFuture Client\b', re.IGNORECASE),
    'Meteor': re.compile(r'\bMeteorClient\b|\bMeteor Client\b', re.IGNORECASE),
    'Impact': re.compile(r'\bImpactClient\b|\bImpact Client\b', re.IGNORECASE),
    'Wurst': re.compile(r'\bWurstClient\b|\bWurst Client\b', re.IGNORECASE),
    'Phobos': re.compile(r'\bPhobos\b', re.IGNORECASE),
    'Freecam': re.compile(r'\bFreecam\b|\bFree Camera\b', re.IGNORECASE),
    'Nuker': re.compile(r'\bNuker\b', re.IGNORECASE),
    'Chams': re.compile(r'\bChams\b|\bWallhack\b', re.IGNORECASE),
    'NoRender': re.compile(r'\bNoRender\b', re.IGNORECASE),
    'WTap': re.compile(r'\bWTap\b|\bW-Tap\b', re.IGNORECASE),
    'STap': re.compile(r'\bSTap\b|\bS-Tap\b', re.IGNORECASE),
    'FastBow': re.compile(r'\bFastBow\b', re.IGNORECASE),
    'Offhand': re.compile(r'\bOffhand\b|\bOffhandCrystal\b', re.IGNORECASE),
    'Crystalaura': re.compile(r'\bCrystalaura\b|\bCrystal Aura\b', re.IGNORECASE),
    'AnchorAura': re.compile(r'\bAnchorAura\b|\bAnchor Aura\b', re.IGNORECASE),
    'BedAura': re.compile(r'\bBedAura\b|\bBed Aura\b', re.IGNORECASE),
    'Surround': re.compile(r'\bSurround\b|\bAutoObby\b', re.IGNORECASE),
    'AutoTrap': re.compile(r'\bAutoTrap\b', re.IGNORECASE),
    'SelfTrap': re.compile(r'\bSelfTrap\b', re.IGNORECASE),
    'AutoWalk': re.compile(r'\bAutoWalk\b', re.IGNORECASE),
    'InventoryWalk': re.compile(r'\bInventoryWalk\b|\bInvMove\b|\bInvWalk\b', re.IGNORECASE),
    'FastFall': re.compile(r'\bFastFall\b', re.IGNORECASE),
    'Glide': re.compile(r'\bGlide\b', re.IGNORECASE),
    'Blink': re.compile(r'\bBlink\b', re.IGNORECASE),
    'Phase': re.compile(r'\bPhase\b', re.IGNORECASE),
    'Clip': re.compile(r'\bClip\b|\bVClip\b|\bHClip\b', re.IGNORECASE),
    'PacketFly': re.compile(r'\bPacketFly\b|\bpfly\b', re.IGNORECASE),
    'BoatFly': re.compile(r'\bBoatFly\b', re.IGNORECASE),
    'EntitySpeed': re.compile(r'\bEntitySpeed\b|\bEntity Speed\b', re.IGNORECASE),
    'ElytraFly': re.compile(r'\bElytraFly\b|\bElytra Fly\b', re.IGNORECASE),
    'Parkour': re.compile(r'\bParkour\b', re.IGNORECASE),
    'NoPush': re.compile(r'\bNoPush\b|\bNoColli\b', re.IGNORECASE),
    'AutoTool': re.compile(r'\bAutoTool\b|\bAuto Tool\b', re.IGNORECASE),
    'InvClean': re.compile(r'\bInvClean\b|\bInvCleaner\b|\bInventory Cleaner\b', re.IGNORECASE),
    'AutoLog': re.compile(r'\bAutoLog\b|\bAutoDisconnect\b', re.IGNORECASE),
    'FastUse': re.compile(r'\bFastUse\b', re.IGNORECASE),
    'AntiAFK': re.compile(r'\bAntiAFK\b|\bAnti AFK\b', re.IGNORECASE),
    'Derp': re.compile(r'\bDerp\b|\bSpinBot\b', re.IGNORECASE),
    'Timer': re.compile(r'\bTimerModule\b|\bTimerSpeed\b', re.IGNORECASE),
    'PortalGodMode': re.compile(r'\bPortalGodMode\b|\bPortal God Mode\b', re.IGNORECASE),
    'FakePlayer': re.compile(r'\bFakePlayer\b|\bFake Player\b', re.IGNORECASE),
    'AutoReconnect': re.compile(r'\bAutoReconnect\b', re.IGNORECASE),
    'AutoRespawn': re.compile(r'\bAutoRespawn\b', re.IGNORECASE),
    'AntiVanish': re.compile(r'\bAntiVanish\b|\bAnti Vanish\b', re.IGNORECASE),
    'XCarry': re.compile(r'\bXCarry\b|\bMoreInventory\b', re.IGNORECASE),
    'NoEntityTrace': re.compile(r'\bNoEntityTrace\b|\bNoEntityTrees\b', re.IGNORECASE),
    'PacketCrasher': re.compile(r'\bPacketCrasher\b|\bServerCrasher\b', re.IGNORECASE),
    'CommandSpam': re.compile(r'\bCommandSpam\b|\bSpammer\b', re.IGNORECASE),
    'SignCrash': re.compile(r'\bSignCrash\b|\bBookCrash\b', re.IGNORECASE),
    'CoordExploit': re.compile(r'\bCoordExploit\b|\bCoord Finder\b', re.IGNORECASE),
    'Nursultan': re.compile(r'\bNursultan\b', re.IGNORECASE),
    'Expensive': re.compile(r'\bExpensive\b|\bExpensiveClient\b', re.IGNORECASE),
    'Neverhook': re.compile(r'\bNeverhook\b', re.IGNORECASE),
    'Celestia': re.compile(r'\bCelestia\b|\bCelestial\b', re.IGNORECASE),
    'Akrien': re.compile(r'\bAkrien\b', re.IGNORECASE),
    'Excellent': re.compile(r'\bExcellent\b|\bExcellentClient\b', re.IGNORECASE),
    'Wexside': re.compile(r'\bWexside\b', re.IGNORECASE),
    'Minced': re.compile(r'\bMinced\b', re.IGNORECASE),
    'WildClient': re.compile(r'\bWildClient\b|\bWild Client\b', re.IGNORECASE),
    'Fluger': re.compile(r'\bFluger\b', re.IGNORECASE),
    'Envy': re.compile(r'\bEnvyClient\b', re.IGNORECASE),
    'RiseClient': re.compile(r'\bRiseClient\b|\bRise Client\b', re.IGNORECASE),
    'Elysium': re.compile(r'\bElysium\b|\bElysiumClient\b', re.IGNORECASE),
    'Gamble': re.compile(r'\bGamble\b|\bGambleClient\b', re.IGNORECASE),
    'Phantom': re.compile(r'\bPhantom\b|\bPhantomClient\b', re.IGNORECASE),
    'Booster': re.compile(r'\bBooster\b|\bBoosterClient\b|\bBoosterHUD\b', re.IGNORECASE),
    'FDPClient': re.compile(r'\bFDPClient\b', re.IGNORECASE),
    'Salhack': re.compile(r'\bSalhack\b', re.IGNORECASE),
    'KamiBlue': re.compile(r'\bKamiBlue\b|\bKami Blue\b', re.IGNORECASE),
    'Aristois': re.compile(r'\bAristois\b', re.IGNORECASE),
    'Pyro': re.compile(r'\bPyro\b|\bPyroClient\b', re.IGNORECASE),
    'Rhack': re.compile(r'\bRhack\b|\bRusherhack\b', re.IGNORECASE),
    'Gamesense': re.compile(r'\bGamesense\b', re.IGNORECASE),
    'Konas': re.compile(r'\bKonas\b', re.IGNORECASE),
    'Seppuku': re.compile(r'\bSeppuku\b', re.IGNORECASE),
    'Xulu': re.compile(r'\bXulu\b', re.IGNORECASE),
    'Deadcode': re.compile(r'\bDeadcode\b|\bDead Code\b', re.IGNORECASE),
    'Ares': re.compile(r'\bAres\b|\bAresClient\b', re.IGNORECASE),
    'Huzuni': re.compile(r'\bHuzuni\b', re.IGNORECASE),
    'ZeroDay': re.compile(r'\bZeroDay\b', re.IGNORECASE),
    'ArmorHUD': re.compile(r'\bArmorHUD\b|\bArmor HUD\b', re.IGNORECASE),
    'Breadcrumbs': re.compile(r'\bBreadcrumbs\b', re.IGNORECASE),
    'Trajectories': re.compile(r'\bTrajectories\b', re.IGNORECASE),
    'NoFog': re.compile(r'\bNoFog\b', re.IGNORECASE),
    'AntiOverlay': re.compile(r'\bAntiOverlay\b', re.IGNORECASE),
    'AntiBlind': re.compile(r'\bAntiBlind\b|\bNoBlind\b', re.IGNORECASE),
    'AutoShield': re.compile(r'\bAutoShield\b', re.IGNORECASE),
    'AntiKB': re.compile(r'\bAntiKB\b|\bVelocity\b', re.IGNORECASE),
    'BedAura': re.compile(r'\bBedAura\b|\bAutoBed\b', re.IGNORECASE),
    'ObbyBypass': re.compile(r'\bObbyBypass\b|\bObby Bypass\b', re.IGNORECASE),
    'OffhandTotem': re.compile(r'\bOffhandTotem\b|\bSmartOffhand\b', re.IGNORECASE),
    'AutoSneak': re.compile(r'\bAutoSneak\b|\bFastSneak\b', re.IGNORECASE),
    'AirJump': re.compile(r'\bAirJump\b|\bInfiniteJump\b', re.IGNORECASE),
    'FastLadder': re.compile(r'\bFastLadder\b', re.IGNORECASE),
    'WaterSpeed': re.compile(r'\bWaterSpeed\b', re.IGNORECASE),
    'IceSpeed': re.compile(r'\bIceSpeed\b', re.IGNORECASE),
    'SlimeJump': re.compile(r'\bSlimeJump\b', re.IGNORECASE),
    'AutoSell': re.compile(r'\bAutoSell\b|\bAutoBuy\b', re.IGNORECASE),
    'LootYeeter': re.compile(r'\bLootYeeter\b', re.IGNORECASE),
    'ItemScroller': re.compile(r'\bItemScroller\b', re.IGNORECASE),
    'HWID': re.compile(r'\bHWID\b|\bHWIDBypass\b', re.IGNORECASE),
    'AntiLeak': re.compile(r'\bAntiLeak\b|\bLeaked\b', re.IGNORECASE),
    'Cracked': re.compile(r'\bCracked\b|\bCrackedClient\b', re.IGNORECASE),
}

BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp', '.svg',
    '.mp3', '.mp4', '.wav', '.ogg', '.flac',
    '.zip', '.rar', '.7z', '.tar', '.gz',
    '.dll', '.so', '.dylib', '.exe', '.jar',
    '.class', '.dex',
    '.ttf', '.otf', '.woff', '.woff2',
}


def check_cheats(all_strings: dict) -> dict:
    found = {}
    evidence = {}
    
    # 1. Check all file/class paths themselves first
    for path in all_strings.keys():
        filename = path.split('!')[-1]
        name_only = os.path.splitext(filename)[0]
        # Split CamelCase
        words = re.sub(r'([a-z])([A-Z])', r'\1 \2', name_only)
        words = re.sub(r'([a-zA-Z])([A-Z][a-z])', r'\1 \2', words)
        
        for name, pattern in CHEAT_PATTERNS.items():
            if name in found and found[name]:
                continue
            m = pattern.search(name_only) or pattern.search(words)
            if m:
                found[name] = True
                evidence.setdefault(name, []).append({
                    'file': path,
                    'matched': m.group(0),
                    'context': f"File/Class path matches cheat signature: {filename}"
                })

    # 2. Check the contents of the files
    for path, strings in all_strings.items():
        ext = os.path.splitext(path.split('!')[-1])[1].lower()
        if ext in BINARY_EXTENSIONS:
            continue
        for i, s in enumerate(strings):
            s_str = str(s)
            if len(s_str) < 3 or len(s_str) > 200:
                continue
            for name, pattern in CHEAT_PATTERNS.items():
                if name in found and found[name]:
                    continue
                m = pattern.search(s_str)
                if m:
                    found[name] = True
                    start_idx = max(0, i - 5)
                    end_idx = min(len(strings), i + 5)
                    context_str = "\n".join(str(strings[idx]) for idx in range(start_idx, end_idx))
                    evidence.setdefault(name, []).append({
                        'file': path,
                        'matched': m.group(0),
                        'context': context_str
                    })
    for name in CHEAT_PATTERNS:
        if name not in found:
            found[name] = False
    return {'positive': any(found.values()), 'matches': found, 'evidence': evidence}
