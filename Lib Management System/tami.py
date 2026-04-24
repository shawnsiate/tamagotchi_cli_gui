#!/usr/bin/env python3
"""

How to run:
    python3 tamagotchi.py

Controls (type commands when prompted):
    feed      - Feed the pet (reduces hunger)
    play      - Play with the pet (increases happiness, costs energy)
    sleep     - Let the pet sleep (restore energy, advance time)
    med       - Give medicine (restore health, costs happiness)
    clean     - Clean pet (small boosts)
    status    - Show current stats
    help      - Show commands
    save      - Save pet to a file
    load      - Load pet from a file
    quit      - Exit the game

The game runs in ticks (default 6 seconds). Each tick the pet's hunger increases, energy drops, and other effects happen.
"""

import time
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime

TICK_DURATION = 6.0  # seconds per tick (you can change this when running)
MAX_STAT = 100
MIN_STAT = 0


def clamp(value, a=MIN_STAT, b=MAX_STAT):
    return max(a, min(b, int(value)))


@dataclass
class Tamagotchi:
    name: str = "Tama"
    hunger: int = 20        # 0 = full, 100 = starving
    happiness: int = 80    # 0 = depressed, 100 = ecstatic
    energy: int = 80       # 0 = exhausted, 100 = energetic
    health: int = 90       # 0 = dead/sick, 100 = perfect
    age_ticks: int = 0     # number of ticks elapsed
    clean: int = 80        # cleanliness 0-100
    alive: bool = True

    def tick(self):
        """Advance the state by one tick."""
        if not self.alive:
            return

        self.age_ticks += 1

        # Natural changes
        self.hunger = clamp(self.hunger + 6)  # gets hungrier
        self.energy = clamp(self.energy - 5)  # uses energy while awake
        self.clean = clamp(self.clean - 3)    # gets dirty

        # Happiness suffers when hungry or dirty or low energy
        if self.hunger > 60:
            self.happiness = clamp(self.happiness - 4)
        else:
            self.happiness = clamp(self.happiness - 1)

        if self.clean < 40:
            self.happiness = clamp(self.happiness - 2)

        if self.energy < 30:
            self.happiness = clamp(self.happiness - 2)

        # Health impacted by extreme conditions
        if self.hunger > 85:
            self.health = clamp(self.health - 6)
        elif self.hunger > 60:
            self.health = clamp(self.health - 2)
        else:
            # slight recovery when well-fed
            if self.health < 95:
                self.health = clamp(self.health + 1)

        if self.clean < 25:
            self.health = clamp(self.health - 3)

        if self.happiness < 20:
            self.health = clamp(self.health - 2)

        # passive small recovery for energy if not too hungry
        if self.hunger < 40 and self.energy < 80:
            self.energy = clamp(self.energy + 1)

        # Check life status
        if self.health <= 0:
            self.alive = False

    # Player actions
    def feed(self):
        if not self.alive:
            return "...it's gone. You can't feed a pet that isn't alive."
        change = 30
        self.hunger = clamp(self.hunger - change)
        self.clean = clamp(self.clean - 5)
        self.happiness = clamp(self.happiness + 3)
        return f"You fed {self.name}. Hunger -{change}, Happiness +3, Clean -5."

    def play(self):
        if not self.alive:
            return "...it's gone."
        if self.energy < 15:
            return f"{self.name} is too tired to play. Try letting it sleep."
        self.happiness = clamp(self.happiness + 18)
        self.energy = clamp(self.energy - 20)
        self.hunger = clamp(self.hunger + 8)
        return f"You played with {self.name}! Happiness +18, Energy -20, Hunger +8."

    def sleep(self):
        if not self.alive:
            return "...it's gone."
        # sleeping advances several ticks worth of rest
        restored = 45
        self.energy = clamp(self.energy + restored)
        self.hunger = clamp(self.hunger + 20)
        self.happiness = clamp(self.happiness + 4)
        return f"{self.name} slept. Energy +{restored}, Hunger +20, Happiness +4."

    def med(self):
        if not self.alive:
            return "...it's gone."
        cost = 10
        healed = 30
        if self.happiness < 8:
            # giving medicine when extremely unhappy has small effect
            healed = 10
        self.health = clamp(self.health + healed)
        self.happiness = clamp(self.happiness - cost)
        return f"You gave medicine. Health +{healed}, Happiness -{cost}."

    def clean_pet(self):
        if not self.alive:
            return "...it's gone."
        gain = 35
        self.clean = clamp(self.clean + gain)
        self.happiness = clamp(self.happiness + 5)
        self.energy = clamp(self.energy - 5)
        return f"You cleaned {self.name}. Clean +{gain}, Happiness +5, Energy -5."

    def status(self):
        state = "alive" if self.alive else "dead"
        return {
            "name": self.name,
            "state": state,
            "hunger": self.hunger,
            "happiness": self.happiness,
            "energy": self.energy,
            "health": self.health,
            "clean": self.clean,
            "age_ticks": self.age_ticks,
        }

    def to_json(self):
        return json.dumps(asdict(self), indent=2)

    @staticmethod
    def from_json(obj):
        if isinstance(obj, str):
            obj = json.loads(obj)
        pet = Tamagotchi(name=obj.get("name", "Tama"))
        pet.hunger = obj.get("hunger", 20)
        pet.happiness = obj.get("happiness", 80)
        pet.energy = obj.get("energy", 80)
        pet.health = obj.get("health", 90)
        pet.age_ticks = obj.get("age_ticks", 0)
        pet.clean = obj.get("clean", 80)
        pet.alive = obj.get("alive", True)
        return pet


# Utility functions

def print_status(pet: Tamagotchi):
    s = pet.status()
    print("\n------- PET STATUS -------")
    print(f"Name: {s['name']}    State: {s['state']}")
    print(f"Age (ticks): {s['age_ticks']}")
    print(f"Hunger:     {s['hunger']}/100 (0=full,100=starving)")
    print(f"Happiness:  {s['happiness']}/100")
    print(f"Energy:     {s['energy']}/100")
    print(f"Health:     {s['health']}/100")
    print(f"Cleanliness:{s['clean']}/100")
    print("---------------------------\n")


def save_pet(pet: Tamagotchi, filename=None):
    if filename is None:
        filename = f"{pet.name.lower()}_save.json"
    data = asdict(pet)
    data["saved_at"] = datetime.now().isoformat()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return filename


def load_pet(filename):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Tamagotchi.from_json(data)


def print_help():
    print("Commands:")
    print("  feed   - Feed the pet")
    print("  play   - Play with the pet")
    print("  sleep  - Let the pet sleep")
    print("  med    - Give medicine")
    print("  clean  - Clean the pet")
    print("  status - Show status")
    print("  save   - Save pet to file")
    print("  load   - Load pet from file")
    print("  help   - Show this help")
    print("  quit   - Exit")


# Main game loop

def main():
    print("Welcome to Tamagotchi (terminal edition)!")
    name = input("Name your pet (or press Enter for 'Tama'): ").strip() or "Tama"
    pet = Tamagotchi(name=name)

    print(f"Great! Meet {pet.name}. Type 'help' for commands. Game ticks every {TICK_DURATION} seconds.")
    print_status(pet)

    last_tick = time.time()

    try:
        while True:
            # If pet dead, only allow save/load/quit
            if not pet.alive:
                print(f"\nSadly, {pet.name} has passed away. You can save the final state, load another save, or quit.")

            # Wait for input with a small timeout so ticks can happen.
            print("Enter command (help for list): ", end="", flush=True)
            start = time.time()
            # We'll poll input in small sleep intervals to allow ticks
            command = None
            typed = ""
            while True:
                # Tick handling
                now = time.time()
                if now - last_tick >= TICK_DURATION:
                    pet.tick()
                    last_tick = now
                    # Inform brief automatic updates
                    if pet.alive:
                        print(f"\n[Tick] {pet.name} aged to {pet.age_ticks}. Hunger {pet.hunger}, Energy {pet.energy}.")
                    else:
                        print(f"\n[Tick] {pet.name} has died.")

                # Non-blocking input attempt
                if os.name == "nt":
                    # On Windows, use msvcrt
                    import msvcrt
                    if msvcrt.kbhit():
                        ch = msvcrt.getwch()
                        if ch == '\r' or ch == '\n':
                            command = typed.strip()
                            print("")
                            break
                        elif ch == '\x08':  # backspace
                            typed = typed[:-1]
                            # Erase char from console (best-effort)
                            print("\b \b", end="", flush=True)
                        else:
                            typed += ch
                            print(ch, end="", flush=True)
                else:
                    # POSIX: use select on stdin
                    import select
                    r, _, _ = select.select([sys.stdin], [], [], 0.5)
                    if r:
                        line = sys.stdin.readline()
                        if not line:
                            # EOF
                            command = "quit"
                        else:
                            command = line.strip()
                        break

                # small sleep to avoid busy loop
                time.sleep(0.05)

            if command is None:
                command = typed.strip()

            if not command:
                # empty command -> continue loop, ticks still happen
                continue

            cmd = command.lower()

            if cmd == "help":
                print_help()
            elif cmd == "status":
                print_status(pet)
            elif cmd == "feed":
                print(pet.feed())
            elif cmd == "play":
                print(pet.play())
            elif cmd == "sleep":
                print(pet.sleep())
            elif cmd in ("med", "medicine"):
                print(pet.med())
            elif cmd == "clean":
                print(pet.clean_pet())
            elif cmd == "save":
                filename = save_pet(pet)
                print(f"Saved to {filename}")
            elif cmd == "load":
                fn = input("Filename to load (e.g. tama_save.json): ").strip()
                if not os.path.exists(fn):
                    print("File not found.")
                else:
                    pet = load_pet(fn)
                    print(f"Loaded pet {pet.name}.")
                    print_status(pet)
            elif cmd == "quit":
                ask = input("Do you want to save before quitting? Shawn: ").strip().lower()
                if ask == "y":
                    fn = save_pet(pet)
                    print(f"Saved to {fn}")
                print("Bye! Thanks for playing.")
                break
            else:
                print("Unknown command. Type 'help' to see available commands.")

    except KeyboardInterrupt:
        print("\nInterrupted. Exiting game.")


if __name__ == "__main__":
    main()





