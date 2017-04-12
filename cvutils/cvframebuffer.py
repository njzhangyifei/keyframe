from collections import deque


class CVFrameBuffer(deque):
    def __init__(self, maxlen):
        super(CVFrameBuffer, self).__init__([], maxlen=maxlen)

    def get_last(self, index=0):
        latest = len(self) - 1
        if latest - index < 0:
            return None
        return self[latest-index]

