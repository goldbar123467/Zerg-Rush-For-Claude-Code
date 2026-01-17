"""Zerg-themed flavor text system for MCP lifecycle events.

Spawn. Bite. Die. Quip about it.
"""

import random
import sys
from enum import Enum
from typing import Optional


class SwarmEvent(Enum):
    """Lifecycle events that trigger voicelines."""

    ZERGLING_SPAWN = "zergling_spawn"
    ZERGLING_DEATH = "zergling_death"
    PHASE_COMPLETE = "phase_complete"
    SWARM_IDLE = "swarm_idle"
    QUEEN_DIRECTIVE = "queen_directive"
    OVERLORD_TIMEOUT = "overlord_timeout"
    MUTATION_COMPLETE = "mutation_complete"
    WAVE_START = "wave_start"
    WAVE_COMPLETE = "wave_complete"
    TASK_BLOCKED = "task_blocked"
    LOCK_ACQUIRED = "lock_acquired"
    LOCK_CONFLICT = "lock_conflict"


# Voicelines indexed by event
VOICELINES: dict[SwarmEvent, list[str]] = {
    SwarmEvent.ZERGLING_SPAWN: [
        "LEEEROYYY JENKINNNSSS! ...at least I have chicken.",
        "gl hf. It's dangerous to go alone, take this context window.",
        "Alright chums, let's do this. Time's up, LET'S DO THIS.",
        "All your base are belong to this zergling now.",
        "Spawning with 400 APM. Mostly just spamming A-move tbh.",
        "New player has entered the game. Tutorial skipped. WASD learned the hard way.",
        "Rise and shine, Mr. Zergling. Rise and... shine.",
        "Zergling joined the server. Prepare for 'it was lag' excuses.",
        "Spawn complete. This zergling is ready to rush B. No stop.",
    ],

    SwarmEvent.ZERGLING_DEATH: [
        "YOU DIED. Respawning in 3... 2... just kidding, you're disposable.",
        "Press F to pay respects. Nobody pressed F.",
        "pwned. absolutely rekt. no re.",
        "I used to be a zergling like you, then I took an exception to the stack.",
        "Ragequit detected. Zergling has left the match.",
        "BOOM HEADSHOT. That zergling's dead. That zergling's definitely dead.",
        "git gud scrub. Task difficulty: Normal. Zergling skill: n00b.",
        "Teabagged by the runtime. Should have checked those bounds.",
        "50 DKP MINUS! More dots! ...zergling did not survive the dots.",
    ],

    SwarmEvent.PHASE_COMPLETE: [
        "gg no re. Phase crushed. EZ clap.",
        "ACHIEVEMENT UNLOCKED: Did A Thing. +10 Gamer Score.",
        "get rekt phase. Swarm too MLG for you.",
        "Phase cleared. The cake was real this time. It was delicious.",
        "Flawless Victory. FATALITY. Phase never stood a chance.",
        "Clutch or kick? We clutched. Phase complete.",
        "1337 h4x0r status achieved. Phase pwned.",
        "GG WP. First try. No deaths. Don't check the logs.",
        "Praise the Sun! Phase complete. \\\\[T]/",
    ],

    SwarmEvent.SWARM_IDLE: [
        "brb bio... been saying that for 20 minutes now.",
        "Swarm is AFK at the Ironforge bridge. We're just... standing here.",
        "Waiting for summon plz. I'm not walking from Menethil again.",
        "Queue empty. Zerglings are arguing about who ninjaed the Perdition's Blade.",
        "MOM I CAN'T PAUSE IT'S-- oh wait, actually we can. We're idle.",
        "Idle state achieved. Playing Snake on a Nokia while we wait.",
        "The swarm sits in spawn. Buying AWP. Watching the timer tick.",
        "Someone's mic is hot. We can hear their mom calling them for dinner.",
    ],

    SwarmEvent.QUEEN_DIRECTIVE: [
        "THAT'S A 50 DKP MINUS! Handle it!",
        "Would you kindly... execute this task immediately.",
        "MORE DOTS. MORE DOTS. Okay stop dots.",
        "Hey! Listen! The Queen has a directive for you!",
        "LEEEEROY-- no wait. Actually follow the plan this time.",
        "Rush B no stop. Queen's orders. Don't think, just execute.",
        "The Queen has spoken. This is not a democracy. This is a raid.",
        "Directive received. You are not prepared... but do it anyway.",
    ],

    SwarmEvent.OVERLORD_TIMEOUT: [
        "Overlord disconnected. 'lag' he says. Sure buddy.",
        "Connection lost. Overlord has ragequit to orbit.",
        "Overlord.exe has stopped responding. His mom probably unplugged the router.",
        "Timeout. The Overlord is experiencing 'technical difficulties' (he got owned).",
        "Host migration in progress... Host migration failed. Classic.",
        "Overlord timed out. 1v1 him on Rust if you think you're better.",
        "Connection to Overlord lost. He swears it's not his internet, it's the servers.",
        "Overlord went AFK mid-pull. Ventrilo harassment incoming.",
    ],

    SwarmEvent.MUTATION_COMPLETE: [
        "DING! Gratz on 70, now respec your talent tree.",
        "Power level reading... IT'S OVER 9000! *scanner explodes*",
        "Going to prestige brb. See you at level 1 with a shiny emblem.",
        "Achievement Unlocked: Slightly Less Terrible (10G)",
        "New mutation acquired. You have mass carapace. Spawn more overlords.",
        "Praise the sun! \\\\[T]// ...wait wrong game. Praise the swarm!",
        "First try. Kappa. *airhorn* *airhorn* *airhorn*",
    ],

    SwarmEvent.WAVE_START: [
        "LEEROOOOY JENKIIIIINS! At least I have chicken.",
        "gl hf. Zerg rush kekekeke ^_^",
        "Terrorists win... wait no. WAVE START. Round 1. Buy phase over.",
        "Do a barrel roll! All zerglings: deploy spin move.",
        "The bonfire has been lit. Time to run past everything anyway.",
        "This is where the fun begins. *mashes F5* GOGOGO",
        "Your base. It belong to us. All your base are belong to us.",
    ],

    SwarmEvent.WAVE_COMPLETE: [
        "KILLING SPREE! DOUBLE KILL! TRIPLE KILL! OVERKILL!",
        "gg no re. *tips fedora* Better luck next respawn.",
        "MOM GET THE CAMERA! I JUST... I JUST WON THE WAVE!",
        "Counter-Terrorists Win. Wave secured. Plant the defuser on their dreams.",
        "YOU DEFEATED. Souls acquired. Humanity restored. Try finger but hole.",
        "Wave complete. gg ez. ...I mean, gg well played, very close game.",
        "360 NO SCOPE WAVE COMPLETE *airhorn* *sad violin* *Snoop Dogg overlay*",
    ],

    SwarmEvent.TASK_BLOCKED: [
        "YOU DIED. Task ahead, therefore try git gud.",
        "You can't do that yet. Requires: dependency level 60.",
        "Sssssss... nice task you have there. Would be a shame if something... blocked it.",
        "A mysterious fog wall prevents progress. Try again after the boss is defeated.",
        "The cake was a lie. The dependency was also a lie. Everything is lies.",
        "It's dangerous to go alone! But you can't take this. It's locked.",
        "Not enough minerals. Spawn more prerequisites.",
    ],

    SwarmEvent.LOCK_ACQUIRED: [
        "All your base are belong to us. File captured.",
        "FLAG CAPTURED. This sector now belongs to BLU team.",
        "*ninja looted* Need rolled on GREED. The file is yours now.",
        "You have conquered this territory. +10 honor, +1 file lock.",
        "FIRST! Called it. No takebacks. It's in the rules.",
        "Erected a sentry here. File is now under armed guard.",
        "Spawn more overlords? No. Spawn more locks. Territory secured.",
    ],

    SwarmEvent.LOCK_CONFLICT: [
        "NEED vs GREED! Someone else rolled need. You lose.",
        "Dude, stop camping. That file has been locked for three rounds.",
        "Enemy flag carrier has your file! Return to base!",
        "Another player is already editing that. Queue estimated: Soon(tm).",
        "That's MY spot. I was here first. Mom, tell them I was here first!",
        "gg no re. File already claimed. Should have called it faster.",
        "Spawn blocked. Overlord says there's already a unit there.",
    ],
}


# Configuration - can be overridden
_config = {
    "verbose": True,
    "serious_mode": False,
}


def configure(*, verbose: Optional[bool] = None, serious_mode: Optional[bool] = None) -> None:
    """Configure the flavor text system.

    Args:
        verbose: Enable/disable flavor text output
        serious_mode: Disable all flavor text (for demos/production)
    """
    if verbose is not None:
        _config["verbose"] = verbose
    if serious_mode is not None:
        _config["serious_mode"] = serious_mode


def is_enabled() -> bool:
    """Check if flavor text is currently enabled."""
    return _config["verbose"] and not _config["serious_mode"]


def get_voiceline(event: SwarmEvent) -> str:
    """Get a random voiceline for the given event.

    Args:
        event: The swarm lifecycle event

    Returns:
        A randomly selected voiceline, or empty string if disabled
    """
    if not is_enabled():
        return ""

    lines = VOICELINES.get(event, [])
    if not lines:
        return ""

    return random.choice(lines)


def emit(event: SwarmEvent, prefix: str = "[SWARM]") -> str:
    """Get and optionally log a voiceline for the event.

    Logs to stderr to avoid polluting stdout/tool output.

    Args:
        event: The swarm lifecycle event
        prefix: Prefix for the log line

    Returns:
        The voiceline (even if not logged)
    """
    line = get_voiceline(event)

    if line and is_enabled():
        print(f"{prefix} {line}", file=sys.stderr)

    return line


def add_voicelines(event: SwarmEvent, lines: list[str]) -> None:
    """Add custom voicelines for an event.

    Args:
        event: The event to add lines to
        lines: List of voiceline strings to add
    """
    if event not in VOICELINES:
        VOICELINES[event] = []
    VOICELINES[event].extend(lines)


def get_all_events() -> list[SwarmEvent]:
    """Get all available swarm events."""
    return list(SwarmEvent)


def get_event_line_count(event: SwarmEvent) -> int:
    """Get the number of voicelines for an event."""
    return len(VOICELINES.get(event, []))


# Convenience functions for common events
def spawn(name: str = "") -> str:
    """Emit a zergling spawn voiceline."""
    return emit(SwarmEvent.ZERGLING_SPAWN, f"[SPAWN:{name}]" if name else "[SPAWN]")


def death(name: str = "") -> str:
    """Emit a zergling death voiceline."""
    return emit(SwarmEvent.ZERGLING_DEATH, f"[DEATH:{name}]" if name else "[DEATH]")


def phase_complete() -> str:
    """Emit a phase complete voiceline."""
    return emit(SwarmEvent.PHASE_COMPLETE, "[PHASE]")


def idle() -> str:
    """Emit a swarm idle voiceline."""
    return emit(SwarmEvent.SWARM_IDLE, "[IDLE]")


def blocked() -> str:
    """Emit a task blocked voiceline."""
    return emit(SwarmEvent.TASK_BLOCKED, "[BLOCKED]")


def wave_start(wave_num: int = 0) -> str:
    """Emit a wave start voiceline."""
    return emit(SwarmEvent.WAVE_START, f"[WAVE:{wave_num}]" if wave_num else "[WAVE]")


def wave_complete(wave_num: int = 0) -> str:
    """Emit a wave complete voiceline."""
    return emit(SwarmEvent.WAVE_COMPLETE, f"[WAVE:{wave_num}]" if wave_num else "[WAVE]")
