from cvutils import CVVideoCapture


class CVFuncFilteredVideoCapture(CVVideoCapture):
    def __init__(self, cv_video_capture: CVVideoCapture, filter_func):
        super(CVFuncFilteredVideoCapture, self).\
            __init__(cv_video_capture.file_handle, cv_video_capture.is_camera)
        # assert not self.filter_func.__call__ is None
        if not filter_func.__call__:
            raise ValueError()
        self.filter_func = filter_func

    def read(self):
        while True:
            cv_frame = super(CVFuncFilteredVideoCapture, self).read()
            if cv_frame is None:
                return cv_frame
            if self.filter_func(cv_frame):
                return cv_frame

