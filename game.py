import json
import re
from random import choice


class Game:
    def __init__(self, word: str, player_id: int):
        self.player_id = player_id
        self.word = word
        self.mask = [False] * len(word)
        self.stage = 0  # If we reach 11 stage then the game is over
        self.guessed_letters = []
        self.errors = []

        # Open 1 letter
        self.try_letter(choice(self.word))

        # х у й  -  self.word
        # 0 0 1  -  self.mask
        # _ _ й  -  apply_mask()

    def apply_mask(self):
        out = []

        [out.append(c) if m else out.append("_") for c, m in zip(self.word, self.mask)]

        return " ".join(out)

    def try_letter(self, letter: str) -> bool:
        positions = [m.start() for m in re.finditer(letter, self.word)]
        for p in positions:
            self.mask[p] = True

        self.guessed_letters.append(ord(letter))

        if len(positions) == 0:
            self.errors.append(letter)

        return len(positions) > 0

    def errors_str(self) -> str:
        return ", ".join(self.errors)

    def no_letters_left(self) -> bool:
        return all(self.mask)

    def next_stage(self) -> int:
        self.stage += 1
        return self.stage

    def last_stage_reached(self) -> bool:
        return self.stage >= 11

    def to_json(self) -> str:
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, document: str):
        d = json.loads(document)

        new_game = cls(d["word"], d["player_id"])
        new_game.mask = d["mask"]
        new_game.stage = d["stage"]
        new_game.guessed_letters = d["guessed_letters"]
        new_game.errors = d["errors"]

        return new_game
