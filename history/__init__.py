import rainbowhat as rh

class CatHistory:
    def __init__(self, histpath):
        self.current_item = 0
        self.histpath = histpath
        with open('cathistory.log') as f:
            self.history = [line.rstrip('\n') for line in f]

    def add_history(self, event_time):
        self.history = self.history[0:20]
        self.history.insert(0, event_time)
        with open(self.histpath, "w") as histfile:
            for evt in self.history:
                histfile.write(f'{evt}\n')
        current_item = 0
        return event_time

    def get_latest(self):
        self.current_item = 0
        if len(self.history) > 0:
            return self.history[self.current_item]
        return ''

    def get_next(self):
        if len(self.history) < 1:
            return ''
        self.current_item = (self.current_item + 1) % len(self.history)
        return self.history[self.current_item]

    def get_prev(self):
        if len(self.history) < 1:
            return ''
        self.current_item = (0 if self.current_item == 0 else self.current_item - 1)
        return self.history[self.current_item]
