class CVProgressTracker:
    def __init__(self, callback, callback_complete=None,
                 callback_per_num_update=5):
        self._callback_per_num_update = 0
        self.callback_per_num_update = callback_per_num_update
        self._counter = 0
        self._progress = 0.0
        self._running = False
        self._callback = None
        self._callback_complete = None
        self.callback_progress = callback

    @property
    def callback_per_num_update(self):
        return self._callback_per_num_update

    @callback_per_num_update.setter
    def callback_per_num_update(self, val):
        if round(val) > 0:
            self._callback_per_num_update = round(val)
        else:
            self._callback_per_num_update = 1

    @property
    def callback_progress(self):
        return self._callback

    @callback_progress.setter
    def callback_progress(self, val):
        if val and val.__call__:
            self._callback = val

    @property
    def callback_complete(self):
        return self._callback_complete

    @callback_complete.setter
    def callback_complete(self, val):
        if val and val.__call__:
            self._callback_complete = val

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, val):
        self._counter = 0
        if val and not self._running:
            self.progress = 0.0
        self._running = val
        if self.callback_progress:
            self.callback_progress(self)

    def complete(self):
        self.progress = 1.0
        self.running = False
        if self.callback_complete:
            self.callback_complete(self)

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, val):
        self._progress = val
        if self._counter == 0 and self.callback_progress:
            self.callback_progress(self)
        self._counter = (self._counter + 1) % self.callback_per_num_update


class CVProgressTrackerProxy:
    def __init__(self, progress_tracker: CVProgressTracker):
        self.progress_tracker = progress_tracker

    def start(self):
        self.progress_tracker.running = True

    def set_progress(self, progress):
        self.progress_tracker.progress = progress

    def get_progress(self):
        return self.progress_tracker.progress

    def complete(self):
        self.progress_tracker.complete()
