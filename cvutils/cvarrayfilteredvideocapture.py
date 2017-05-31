import numpy as np
from cvutils import CVVideoCapture


class CVArrayFilteredVideoCapture(CVVideoCapture):
    def __init__(self, cv_video_cap: CVVideoCapture, frame_rate, filter_array):
        super(CVArrayFilteredVideoCapture, self). \
            __init__(cv_video_cap.file_handle, cv_video_cap.is_camera)
        self.key_frames_pos = 0
        self.frame_rate = frame_rate
        self.cv_video_cap = cv_video_cap
        self.filter_array = filter_array
        self.key_frames = np.where(self.filter_array)[0]
        self.frame_count = len(self.key_frames)

    def read(self):
        if not self.cv_video_cap.is_open:
            return None
        self.cv_video_cap.set_position_frame(self.key_frames[self.key_frames_pos])
        self.key_frames_pos += 1
        self.key_frames_pos = min(self.key_frames_pos, self.frame_count-1)
        return self.cv_video_cap.read()

    def get_position_frame(self):
        return self.key_frames_pos

    def set_position_frame(self, frame):
        self.key_frames_pos = min(frame, self.frame_count-1)
        self.cv_video_cap.set_position_frame(self.key_frames[self.key_frames_pos])

    def get_position_millis(self):
        return 0

    def set_position_millis(self, millis):
        return

    def set_frame_rate(self, rate):
        self.frame_rate = rate

    def get_frame_rate(self):
        return self.frame_rate

