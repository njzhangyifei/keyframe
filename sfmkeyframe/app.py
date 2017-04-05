import sys

import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QFileDialog

from cvutils import CVFrame
from sfmkeyframe.view.VideoPlaybackWidget import VideoPlaybackWidget


def select_file():
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.AnyFile)
    filename, filter_type = dlg.getOpenFileNames()
    return filename

def get_video_cap(filename):
    print('Opening ' + filename)
    video_cap = cv2.VideoCapture(filename)
    frame_rate = video_cap.get(cv2.CAP_PROP_FPS)
    print('Frame rate = ' + str(frame_rate))
    return video_cap, frame_rate

    # widget = VideoWidget(video_cap, frame_rate * 1.5)
    #
    # widget.setWindowTitle('PyQt - OpenCV Test')
    # widget.show()
    #
    # sys.exit(app.exec_()
def run():
    app = QApplication(sys.argv)

    filename = select_file()[0]
    # filename = '/home/yifei/develop/sealab/keyframe/data/GP017728.MP4'
    # filename = 'C://Users//Yifei//unixhome//develop//sealab//keyframe//data' \
    #            '//GP017728.MP4'
    video_cap, frame_rate = get_video_cap(filename)

    def buildFrame(frame):
        height, width = frame.shape[:2]
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_gray_rgb = cv2.cvtColor(frame_gray, cv2.COLOR_GRAY2RGB)

        kernel_x = np.array([(0, 0, 0), (-1, 0, 1), (0, 0, 0)], np.float)
        kernel_y = np.array([(0, -1, 0), (0, 0, 0), (0, 1, 0)], np.float)
        filtered_x = cv2.filter2D(frame_gray, cv2.CV_64F, kernel_x)
        filtered_y = cv2.filter2D(frame_gray, cv2.CV_64F, kernel_y)
        filtered_x_gray = cv2.convertScaleAbs(filtered_x)
        filtered_y_gray = cv2.convertScaleAbs(filtered_y)
        filtered_x_gray_rgb = cv2.cvtColor(filtered_x_gray, cv2.COLOR_GRAY2RGB)
        filtered_y_gray_rgb = cv2.cvtColor(filtered_y_gray, cv2.COLOR_GRAY2RGB)

        sharpness = (np.sum(filtered_y ** 2)
                     + np.sum(filtered_x ** 2)) / float(height * width * 2)

        # sobel_x = cv2.Sobel(frame_gray, cv2.CV_64F, 1, 0)
        # sobel_y = cv2.Sobel(frame_gray, cv2.CV_64F, 0, 1)
        # laplacian = cv2.Laplacian(frame_gray, cv2.CV_64F)
        # laplacian_gray = cv2.convertScaleAbs(laplacian)
        # laplacian_gray_rgb = cv2.cvtColor(laplacian_gray, cv2.COLOR_GRAY2RGB)
        # sobel_x_gray = cv2.convertScaleAbs(sobel_x)
        # sobel_y_gray = cv2.convertScaleAbs(sobel_y)
        # sobel_x_gray_rgb = cv2.cvtColor(sobel_x_gray, cv2.COLOR_GRAY2RGB)
        # sobel_y_gray_rgb = cv2.cvtColor(sobel_y_gray, cv2.COLOR_GRAY2RGB)

        font = cv2.FONT_HERSHEY_COMPLEX
        cv2.putText(frame_gray_rgb, str(video_cap.get(cv2.CAP_PROP_POS_FRAMES)),
                    (0, 40), font, 1, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_gray_rgb, str(sharpness), (0, height - 10),
                    font, 1, (255, 255, 255), 1, cv2.LINE_AA)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        combine = np.zeros((height * 2, width * 2, 3), np.uint8)

        # combine 2 images
        combine[:height, :width, :3] = frame_rgb
        combine[:height, width:width * 2, :3] = frame_gray_rgb
        # combine[height:height*2, width:width*2, :3] = sobel_x_gray_rgb
        # combine[height:height*2, :width, :3] = sobel_y_gray_rgb
        combine[height:height * 2, width:width * 2, :3] = filtered_x_gray_rgb
        combine[height:height * 2, :width, :3] = filtered_y_gray_rgb

        return combine

    def get_frame():
        retval, frame = video_cap.read()
        if retval:
            return CVFrame(buildFrame(frame))
        return None

    main_window = VideoPlaybackWidget(get_frame_func=get_frame,
                                      frame_rate=frame_rate)
    main_window.show()
    rtnval = app.exec_()
    return rtnval


if __name__ == '__main__':
    sys.exit(run())
