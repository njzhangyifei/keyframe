import cv2

from cvutils import CVFrame


class CVVideoCapture:
    def __init__(self, file_handle, is_camera=False):
        self.is_camera = is_camera
        self.file_handle = file_handle
        self.frame_count = None
        self.capture = cv2.VideoCapture(self.file_handle)
        self.update_frame_count()

    @property
    def is_open(self):
        return self.capture.isOpened()

    def open(self, arg):
        return self.capture.open(arg)

    def release(self):
        self.capture.release()

    def read(self):
        if not self.capture.isOpened():
            return None
        frame_pos = self.get_position_frame()
        ret, frame = self.capture.read()
        if not ret:
            return None
        return CVFrame(frame, position_frame=frame_pos)

    def set(self, cv_prop, val):
        return self.capture.set(cv_prop, val)

    def get(self, cv_prop):
        return self.capture.get(cv_prop)

    def update_frame_count(self):
        current_pos = self.capture.get(cv2.CAP_PROP_POS_FRAMES)
        self.capture.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
        self.frame_count = self.capture.get(cv2.CAP_PROP_POS_FRAMES)
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, current_pos)

    def get_frame_count(self):
        if self.frame_count is None:
            self.update_frame_count()
        return self.frame_count

    def get_frame_rate(self):
        return self.get(cv2.CAP_PROP_FPS)

    def set_frame_rate(self, rate):
        return self.set(cv2.CAP_PROP_FPS, rate)

    def get_frame_height(self):
        return self.get(cv2.CAP_PROP_FRAME_HEIGHT)

    def set_frame_height(self, height):
        return self.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def get_frame_width(self):
        return self.get(cv2.CAP_PROP_FRAME_WIDTH)

    def set_frame_width(self, width):
        return self.set(cv2.CAP_PROP_FRAME_WIDTH, width)

    def get_position_millis(self):
        return self.get(cv2.CAP_PROP_POS_MSEC)

    def set_position_millis(self, millis):
        return self.set(cv2.CAP_PROP_POS_MSEC, millis)

    def get_position_frame(self):
        return self.get(cv2.CAP_PROP_POS_FRAMES)

    def set_position_frame(self, frame):
        return self.set(cv2.CAP_PROP_POS_FRAMES, frame)
