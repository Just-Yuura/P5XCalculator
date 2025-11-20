import numpy as np

class RandomPool:
    def __init__(self, buffer_size = 100_000, seed = None):
        self.rng = np.random.default_rng(seed)
        self.buffer_size = buffer_size
        self.buffer = self.rng.random(buffer_size)
        self.index = 0


    def get(self, n = 1):
        if self.index + n > self.buffer_size:
            self.buffer = self.rng.random(self.buffer_size)
            self.index = 0

        result = self.buffer[self.index:self.index + n]
        self.index += n

        return result


    def get_single(self):
        if self.index >= self.buffer_size:
            self.buffer = self.rng.random(self.buffer_size)
            self.index = 0

        result = self.buffer[self.index]
        self.index += 1

        return result