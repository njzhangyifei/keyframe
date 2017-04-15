import logging
import numpy as np
import cv2
import sys
from PyQt5.QtWidgets import QFileDialog, QApplication


def select_file():
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.AnyFile)
    filename, filter_type = dlg.getOpenFileNames()
    return filename


def main(filename):
    # filename = 'C:/Users/Yifei/unixhome/develop/sealab/keyframe/data/GP017728.MP4'
    cap = cv2.VideoCapture(filename)
    # params for ShiTomasi corner detection
    feature_params = dict(maxCorners=300,
                          qualityLevel=0.3,
                          minDistance=7,
                          blockSize=7)
    # Parameters for lucas kanade optical flow
    lk_params = dict(winSize=(15, 15),
                     maxLevel=2,
                     criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

    # Create some random colors
    color = np.random.randint(0, 255, (1000, 3))
    # Take first frame and find corners in it
    ret, old_frame = cap.read()
    old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)
    # Create a mask image for drawing purposes
    mask = np.zeros_like(old_frame)
    while (1):
        ret, frame = cap.read()

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # calculate optical flow
        p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None,
                                               **lk_params)
        # Select good points
        good_new = p1[st == 1]
        good_old = p0[st == 1]
        displacement = (good_new - good_old) ** 2
        distance = np.sum(displacement, axis=1)
        mean_distance = distance.mean()

        # draw the tracks
        for i, (new, old) in enumerate(zip(good_new, good_old)):
            a, b = new.ravel()
            c, d = old.ravel()
            mask = cv2.line(mask, (a, b), (c, d), color[i].tolist(), 2)
            frame = cv2.circle(frame, (a, b), 5, color[i].tolist(), -1)
        img = cv2.add(frame, mask)

        font = cv2.FONT_HERSHEY_COMPLEX

        r = 0.8
        dim = (int(img.shape[1] * r), int(img.shape[0] * r))
        # perform the actual resizing of the image and show it
        resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
        cv2.putText(resized, str(mean_distance),
                    (0, 40), font, 1, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.imshow('frame', resized)
        k = cv2.waitKey(30) & 0xff
        if k == 27:
            break

        if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) % 100 == 0:
            p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)
            mask = np.zeros_like(old_frame)
        else:
            p0 = good_new.reshape(-1, 1, 2)

        # Now update the previous frame and previous points
        old_gray = frame_gray.copy()

    cv2.destroyAllWindows()
    cap.release()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    logging.info('test')
    app = QApplication(sys.argv)
    filename = select_file()[0]
    main(filename)
    sys.exit(app.exec_())
