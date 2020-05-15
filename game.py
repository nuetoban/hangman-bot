import re


class Game:
    def __init__(self, word: str, player_id: int):
        self.player_id = player_id
        self.word = word
        self.mask = [False] * len(word)
        self.stage = 0  # If we reach 11 stage then the game is over
        self.guessed_letters = []

        # х у й  -  self.word
        # 0 0 1  -  self.mask
        # _ _ й  -  apply_mask()

    def apply_mask(self):
        out = []

        [out.append(c) if m else out.append('_') for c, m in zip(self.word, self.mask)]

        return ' '.join(out)

    def try_letter(self, letter: str) -> bool:
        positions = [m.start() for m in re.finditer(letter, self.word)]
        for p in positions:
            self.mask[p] = True

        self.guessed_letters.append(ord(letter))

        return len(positions) > 0

    def no_letters_left(self) -> bool:
        return all(self.mask)

    def next_stage(self) -> int:
        self.stage += 1
        return self.stage

    def last_stage_reached(self) -> bool:
        return self.stage >= 11
