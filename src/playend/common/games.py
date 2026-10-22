"""Stable game families: the many titles read on screen ("EA Sports FC 26", "Tekken") grouped by game."""

GAME_KEYS = [
    ("ufc", "EA Sports UFC 5"),
    ("fighterz", "Dragon Ball FighterZ"),
    ("dragon ball", "Dragon Ball Sparking! ZERO"),
    ("demon slayer", "Demon Slayer"),
    ("naruto", "Naruto Storm Connections"),
    ("mortal kombat", "Mortal Kombat 1"),
    ("tekken", "Tekken 8"),
    ("brawlhalla", "Brawlhalla"),
    ("warzone", "Call of Duty: Warzone"),
    ("call of duty", "Call of Duty: Warzone"),
    ("fortnite", "Fortnite"),
    ("genshin", "Genshin Impact"),
    ("red dead", "Red Dead Redemption 2"),
    ("beach buggy", "Beach Buggy Racing 2"),
    ("j-stars", "J-Stars Victory VS+"),
    ("god of war", "God of War"),
    ("assassin", "Assassin's Creed Origins"),
    ("fc", "EA Sports FC"),
]
NO_GAME = "Aucun jeu (PS5, menus, noir)"


def game_family(title: str | None) -> str:
    text = (title or "").lower()
    for key, name in GAME_KEYS:
        if key in text:
            return name
    return NO_GAME if not text else title
