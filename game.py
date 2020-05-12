import re


class Game:
    def __init__(self, word: str):
        self.word = word
        self.mask = [False] * len(word)

        # х у й  -  self.word
        # 0 0 1  -  self.mask
        # _ _ й  -  apply_mask()

    def apply_mask(self):
        out = []

        [out.append(c) if m else out.append('_') for c, m in zip(self.word, self.mask)]

        return ' '.join(out)

    def try_letter(self, letter: str):
        positions = [m.start() for m in re.finditer(letter, self.word)]
        for p in positions:
            self.mask[p] = True
