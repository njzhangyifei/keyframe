import os

import numpy as np

from cvutils import CVVideoCapture
import json


class CVAcceptanceTest:
    def __init__(self, numpy_file_prefix):
        self.numpy_file_prefix = numpy_file_prefix
        pass

    def load_params_file(self, cv_video_cap: CVVideoCapture, postfix=None):
        file_path = cv_video_cap.file_handle + '.' + \
                    self.numpy_file_prefix + '_params.' + \
                    (postfix if postfix else str(int(cv_video_cap.frame_count))) + \
                    '.json'
        data = None
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                except ValueError:
                    data = None
        return data

    def save_params_file(self, params, cv_video_cap: CVVideoCapture,
                         postfix=None):
        file_path = cv_video_cap.file_handle + '.' + \
                    self.numpy_file_prefix + '_params.' + \
                    (postfix if postfix else str(int(cv_video_cap.frame_count))) + \
                    '.json'
        with open(file_path, 'w') as f:
            json.dump(params, f)

    def save_acceptance_file(self, acceptance, cv_video_cap: CVVideoCapture,
                             postfix=None):
        np.save(cv_video_cap.file_handle + '.' +
                self.numpy_file_prefix + '_acceptance.' +
                (postfix if postfix else str(acceptance.size)) + '.npy',
                acceptance)

    def load_acceptance_file(self, cv_video_cap: CVVideoCapture, count=0,
                             postfix=None):
        file_path = cv_video_cap.file_handle + '.' + \
                    self.numpy_file_prefix + '_acceptance.' + \
                    (postfix if postfix else str(int(cv_video_cap.frame_count)
                                                 if count == 0 else count)) + '.npy'
        if os.path.exists(file_path):
            return np.load(file_path)
        return None
