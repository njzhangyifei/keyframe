import json
import os
import pickle

import cv2
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QProgressDialog, QFileDialog, QMessageBox

from cvutils import CVVideoCapture, CVSharpness, CVCorrelation, \
    CVOpticalFlow
from cvutils.cvarrayfilteredvideocapture import CVArrayFilteredVideoCapture
from cvutils.cvprogresstracker import CVProgressTracker
from sfmkeyframe.view.VideoPlaybackControlWidget import \
    VideoPlaybackControlWidget
from sfmkeyframe.view.VideoPlaybackWidget import VideoPlaybackWidget
from sfmkeyframe.view.ui.FilterWidget import Ui_FilterWidget
from utils.progressworker import ProgressWorker


# noinspection PyTypeChecker
class FilterWidget(QGroupBox):
    closed = pyqtSignal([str])

    def __init__(self, cv_video_cap):
        super(FilterWidget, self).__init__()
        self.cv_video_cap = cv_video_cap  # type: CVVideoCapture
        self.ui = Ui_FilterWidget()
        self.ui.setupUi(self)
        self.ui.spinBoxFilterSharpness_windowSize.setValue(self.cv_video_cap.get_frame_rate())
        self.opticalflow_feature_params = dict(maxCorners=500, qualityLevel=0.3,
                                               minDistance=7, blockSize=7)
        self.opticalflow_lk_params = dict(winSize=(15, 15), maxLevel=2,
                                          criteria=(
                                              cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                                              10, 0.03)
                                          )
        self.frame_acceptance_np = None
        self.sharpness_filter = None
        self.correlation_filter = None
        self.opticalflow_filter = None
        self.sharpness_filter_status = ""
        self.correlation_filter_status = ""
        self.opticalflow_filter_status = ""
        self.filter_worker = None
        self.filter_worker_thread = None
        self.filter_worker_progressdialog = None  # type: QProgressDialog

        self.ui.pushButtonFilterGlobal_run.clicked.connect(self.pushButtonFilterGlobal_run_clicked)
        self.ui.pushButtonFilterParams_save.clicked.connect(self.pushButtonFilterParams_save_clicked)
        self.ui.pushButtonFilterParams_load.clicked.connect(self.pushButtonFilterParams_load_clicked)
        self.ui.pushButtonFilterGlobal_preview.clicked.connect(self.pushButtonFilterGlobal_preview_clicked)

        self.playback_widget = None
        self.playback_control_widget = None
        self.filtered_video_capture = None

        self.update_filter_status()

    def closeEvent(self, e):
        self.closed.emit(self.cv_video_cap.file_handle)
        super(FilterWidget, self).closeEvent(e)

    @property
    def params_batch_count(self):
        val = min(self.ui.spinBoxFilterGlobal_batchSize.value(), self.cv_video_cap.get_frame_count())
        val = int(val)
        self.ui.spinBoxFilterGlobal_batchSize.setValue(val)
        return val

    def load_params_batch_count(self, val):
        val = min(val, self.cv_video_cap.get_frame_count())
        val = int(val)
        self.ui.spinBoxFilterGlobal_batchSize.setValue(val)

    @property
    def params_sharpness(self):
        params = {
            'enabled': self.ui.groupBoxFilterSharpness.isChecked(),
            'z_score': self.ui.doubleSpinBoxFilterSharpness_zscore.value(),
            'window_size': self.ui.spinBoxFilterSharpness_windowSize.value(),
        }
        return params

    def load_params_sharpness(self, params):
        self.ui.groupBoxFilterSharpness.setChecked(params['enabled'])
        self.ui.doubleSpinBoxFilterSharpness_zscore.setValue(params['z_score'])
        self.ui.spinBoxFilterSharpness_windowSize.setValue(params['window_size'])

    @property
    def params_correlation(self):
        params = {
            'enabled': self.ui.groupBoxFilterCorrelation.isChecked(),
            'threshold': self.ui.doubleSpinBoxFilterCorrelation_threshold.value()
        }
        return params

    def load_params_correlation(self, params):
        self.ui.groupBoxFilterCorrelation.setChecked(params['enabled'])
        self.ui.doubleSpinBoxFilterCorrelation_threshold.setValue(params['threshold'])

    @property
    def params_opticalflow(self):
        params = {
            'enabled': self.ui.groupBoxFilterOpticalFlow.isChecked(),
            'threshold': self.ui.doubleSpinBoxFilterOpticalFlow_threshold.value(),
            'opticalflow_params': {
                'feature_params': self.opticalflow_feature_params,
                'lk_params': self.opticalflow_lk_params
            }
        }
        return params

    def load_params_opticalflow(self, params):
        self.ui.groupBoxFilterOpticalFlow.setChecked(params['enabled'])
        self.ui.doubleSpinBoxFilterOpticalFlow_threshold.setValue(params['threshold'])
        self.opticalflow_feature_params = params['opticalflow_params']['feature_params']
        self.opticalflow_lk_params = params['opticalflow_params']['lk_params']

    def save_params(self, filepath):
        with open(filepath, 'wb') as f:
            pickle.dump({
                'batch_count': self.params_batch_count,
                'sharpness': self.params_sharpness,
                'correlation': self.params_correlation,
                'opticalflow': self.params_opticalflow
            }, f)
        pass

    def load_params(self, filepath):
        with open(filepath, 'rb') as f:
            p = pickle.load(f)
            if p is not None:
                self.load_params_batch_count(p['batch_count'])
                self.load_params_sharpness(p['sharpness'])
                self.load_params_correlation(p['correlation'])
                self.load_params_opticalflow(p['opticalflow'])

    def prepare_filters(self):
        self.sharpness_filter_status = ""
        self.correlation_filter_status = ""
        self.opticalflow_filter_status = ""
        if self.params_sharpness['enabled']:
            sharpness = CVSharpness()
            self.sharpness_filter = {
                'filter': sharpness,
                'params': self.params_sharpness,
                'params_loaded': sharpness.load_params_file(self.cv_video_cap),
                'calculation': sharpness.load_calculation_file(self.cv_video_cap),
                'acceptance': None,
                'acceptance_loaded': sharpness.load_acceptance_file(self.cv_video_cap),
            }
        else:
            self.sharpness_filter = None
        if self.params_correlation['enabled']:
            correlation = CVCorrelation()
            self.correlation_filter = {
                'filter': correlation,
                'params': self.params_correlation,
                'params_loaded': correlation.load_params_file(self.cv_video_cap),
                'acceptance': None,
                'acceptance_loaded': correlation.load_acceptance_file(self.cv_video_cap),
            }
        else:
            self.correlation_filter = None
        if self.params_opticalflow['enabled']:
            optical_flow_params = self.params_opticalflow['opticalflow_params']
            opticalflow = CVOpticalFlow(optical_flow_params['feature_params'],
                                        optical_flow_params['lk_params'])
            self.opticalflow_filter = {
                'filter': opticalflow,
                'params': self.params_opticalflow,
                'params_loaded': opticalflow.load_params_file(self.cv_video_cap),
                'acceptance': None,
                'acceptance_loaded': opticalflow.load_acceptance_file(self.cv_video_cap),
            }
        else:
            self.opticalflow_filter = None

    def create_progressbar_dialog(self, title):
        self.filter_worker_progressdialog = QProgressDialog(
            title, None, 0, 1000, self
        )
        self.filter_worker_progressdialog.setWindowTitle('Filter Progress')
        self.filter_worker_progressdialog.setMinimumWidth(500)
        self.filter_worker_progressdialog.setWindowModality(QtCore.Qt.WindowModal)
        self.filter_worker_progressdialog.setAutoClose(False)
        self.filter_worker_progressdialog.setAutoReset(False)
        self.filter_worker_progressdialog.setValue(1000)
        self.filter_worker_progressdialog.show()

    def update_progressbar_dialog_title(self, title):
        self.filter_worker_progressdialog.setLabelText(title)
        self.update_filter_status()

    def update_progressbar_dialog_value(self, value):
        self.filter_worker_progressdialog.setValue(min(round(value * 1000), 1000))

    def destroy_progressbar_dialog(self):
        self.filter_worker_progressdialog.close()
        self.filter_worker_progressdialog.destroy()

    def update_filter_status(self):
        self.ui.labelFilterSharpness_status.setText("N/A" if self.sharpness_filter_status == "" else self.sharpness_filter_status)
        self.ui.labelFilterCorrelation_status.setText("N/A" if self.correlation_filter_status == "" else self.correlation_filter_status)
        self.ui.labelFilterOpticalFlow_status.setText("N/A" if self.opticalflow_filter_status == "" else self.opticalflow_filter_status)

    def pushButtonFilterParams_load_clicked(self):
        filename = QFileDialog.getOpenFileName(self, 'Open saved filter params',
                                               os.path.dirname(os.path.abspath(self.cv_video_cap.file_handle)),
                                               filter='*.pickled_params')[0]
        if os.path.exists(filename):
            self.load_params(filename)

    def pushButtonFilterParams_save_clicked(self):
        filename = QFileDialog.getSaveFileName(self, 'Save filter params',
                                               os.path.dirname(os.path.abspath(self.cv_video_cap.file_handle)),
                                               filter='*.pickled_params')[0]
        if not filename.endswith(".pickled_params"):
            filename += ".pickled_params"
        self.save_params(filename)

    def pushButtonFilterGlobal_preview_clicked(self):
        if self.playback_widget:
            self.playback_widget.close()
            self.playback_widget = None
        if self.playback_control_widget:
            self.playback_control_widget.close()
            self.playback_control_widget = None

        if self.frame_acceptance_np is None:
            msgbox = QMessageBox(self)
            msgbox.setWindowTitle('Error')
            msgbox.setIcon(QMessageBox.Warning)
            msgbox.setText('Nothing to preview.\nPlease run filters first!')
            msgbox.show()
            return

        self.filtered_video_capture = CVArrayFilteredVideoCapture(self.cv_video_cap, 1, self.frame_acceptance_np)
        self.playback_widget = VideoPlaybackWidget()
        self.playback_control_widget = VideoPlaybackControlWidget(self.filtered_video_capture)
        self.playback_widget.show()
        self.playback_control_widget.incomingFrame.connect(self.playback_widget.on_incomingFrame)
        self.playback_control_widget.show()
        self.closed.connect(self.playback_widget.close)
        self.closed.connect(self.playback_control_widget.close)

    def pushButtonFilterGlobal_run_clicked(self):
        self.create_progressbar_dialog('Loading...')

        self.prepare_filters()

        def worker_function(progress_changed, state_changed):
            sharpness_filter_updated = False
            self.frame_acceptance_np = np.ones([int(self.cv_video_cap.get_frame_count())],
                                               dtype=np.bool_)

            if self.sharpness_filter:
                progress_changed.emit(0)
                state_changed.emit('Running sharpness filter...')

                def callback(obj):
                    progress_changed.emit(obj.progress)

                sharpness_filter = self.sharpness_filter['filter']  # type: CVSharpness
                sharpness_value = self.sharpness_filter['calculation']
                if sharpness_value is None:
                    # calculate and save
                    progress_changed.emit(0)
                    state_changed.emit('Analyzing video for image sharpness...')
                    print('sharpness recalculating')
                    sharpness_value = sharpness_filter.calculate_sharpness_video_capture(
                        cv_video_capture=self.cv_video_cap,
                        progress_tracker=CVProgressTracker(callback),
                        batch_size=self.params_batch_count
                    )
                    sharpness_filter.save_calculation_file(sharpness_value, self.cv_video_cap)
                progress_changed.emit(1)
                state_changed.emit('Running sharpness acceptance test...')
                if (self.sharpness_filter['params'] != self.sharpness_filter['params_loaded']) or \
                        (self.sharpness_filter['acceptance_loaded'] is None):
                    # different params
                    sharpness_acceptance = \
                        sharpness_filter.test_sharpness_acceptance(
                            sharpness_calculated=sharpness_value,
                            frame_window_size=self.sharpness_filter['params']['window_size'],
                            z_score=self.params_sharpness['z_score']
                        )
                    self.sharpness_filter['acceptance'] = sharpness_acceptance
                    self.sharpness_filter['acceptance_loaded'] = sharpness_acceptance
                    sharpness_filter.save_params_file(self.sharpness_filter['params'], self.cv_video_cap)
                    sharpness_filter.save_acceptance_file(sharpness_acceptance,
                                                          self.cv_video_cap)
                    sharpness_filter_updated = True

                original_count = np.sum(self.frame_acceptance_np)
                current_count = np.sum(self.sharpness_filter['acceptance_loaded'])
                self.sharpness_filter_status = ("[%d] => [%d] frames (%.2f%% dropped)" %
                                                (original_count, current_count,
                                                 (original_count-current_count)/original_count*100))
                progress_changed.emit(1)
                state_changed.emit('Sharpness filter done...')
                self.frame_acceptance_np = self.sharpness_filter['acceptance_loaded']
            else:
                sharpness_filter_updated = True

            correlation_filter_updated = False
            if sharpness_filter_updated:
                # requires recalculation
                correlation_filter_updated = True

            if self.correlation_filter:
                progress_changed.emit(0)
                state_changed.emit('Running correlation filter...')

                def callback(obj):
                    progress_changed.emit(obj.progress)

                # correlation filter enabled
                correlation_filter = self.correlation_filter['filter']  # type: CVCorrelation

                if correlation_filter_updated:
                    self.correlation_filter['acceptance_loaded'] = None
                if (self.correlation_filter['params'] != self.correlation_filter['params_loaded']) or \
                        (self.correlation_filter['acceptance_loaded'] is None):

                    progress_changed.emit(0)
                    state_changed.emit('Removing still frames using cross correlation...')
                    print('correlation recalculating')
                    # different params
                    correlation_acceptance = \
                        correlation_filter.test_correlation_video_capture(
                            cv_video_capture=self.cv_video_cap,
                            correlation_limit=self.correlation_filter['params']['threshold'],
                            frame_acceptance_np=self.frame_acceptance_np,
                            progress_tracker=CVProgressTracker(callback),
                            batch_size=self.params_batch_count,
                        )
                    self.correlation_filter['acceptance'] = correlation_acceptance
                    self.correlation_filter['acceptance_loaded'] = correlation_acceptance
                    correlation_filter.save_params_file(self.correlation_filter['params'], self.cv_video_cap)
                    correlation_filter.save_acceptance_file(correlation_acceptance, self.cv_video_cap)
                    correlation_filter_updated = True

                original_count = np.sum(self.frame_acceptance_np)
                current_count = np.sum(self.correlation_filter['acceptance_loaded'])
                self.correlation_filter_status = ("[%d] => [%d] frames (%.2f%% dropped)" %
                                                  (original_count, current_count,
                                                   (original_count-current_count)/original_count*100))
                progress_changed.emit(1)
                state_changed.emit('Correlation filter done...')
                self.frame_acceptance_np = self.correlation_filter['acceptance_loaded']
            else:
                correlation_filter_updated = True

            opticalflow_filter_updated = False
            if correlation_filter_updated:
                # requires recalculation
                opticalflow_filter_updated = True

            if self.opticalflow_filter:
                # optical_flow enabled
                progress_changed.emit(1)
                state_changed.emit('Running optical flow filter...')

                def callback(obj):
                    progress_changed.emit(obj.progress)

                opticalflow_filter = self.opticalflow_filter['filter'] # type: CVOpticalFlow
                if opticalflow_filter_updated:
                    self.opticalflow_filter['acceptance_loaded'] = None
                if (json.dumps(self.opticalflow_filter['params'], sort_keys=True) !=
                        json.dumps(self.opticalflow_filter['params_loaded'], sort_keys=True)) or \
                        (self.opticalflow_filter['acceptance_loaded'] is None):
                    # different params
                    progress_changed.emit(0)
                    state_changed.emit('Calculating distance between frames using optical flow...')
                    print('opticalflow recalculating')
                    opticalflow_acceptance = \
                        opticalflow_filter.test_optical_flow_video_capture(
                            cv_video_capture=self.cv_video_cap,
                            distance_limit=self.opticalflow_filter['params']['threshold'],
                            frame_acceptance_np=self.frame_acceptance_np,
                            progress_tracker=CVProgressTracker(callback),
                            batch_size=self.params_batch_count,
                        )
                    self.opticalflow_filter['acceptance'] = opticalflow_acceptance
                    self.opticalflow_filter['acceptance_loaded'] = opticalflow_acceptance
                    opticalflow_filter.save_params_file(self.opticalflow_filter['params'], self.cv_video_cap)
                    opticalflow_filter.save_acceptance_file(opticalflow_acceptance, self.cv_video_cap)

                original_count = np.sum(self.frame_acceptance_np)
                current_count = np.sum(self.opticalflow_filter['acceptance_loaded'])
                self.opticalflow_filter_status = ("[%d] => [%d] frames (%.2f%% dropped)" %
                                                  (original_count, current_count,
                                                   (original_count-current_count)/original_count*100))
                progress_changed.emit(1)
                state_changed.emit('Optical flow filter done...')
                self.frame_acceptance_np = self.opticalflow_filter['acceptance_loaded']
            else:
                opticalflow_filter_updated = True

            progress_changed.emit(1)
            state_changed.emit('All filters done!')
            print('all filters done')

        self.filter_worker_thread = QThread(self)
        self.filter_worker_thread.start()
        self.filter_worker = ProgressWorker(worker_function)
        self.filter_worker.moveToThread(self.filter_worker_thread)
        self.filter_worker.progress_changed.connect(self.update_progressbar_dialog_value)
        self.filter_worker.state_changed.connect(self.update_progressbar_dialog_title)
        self.filter_worker.finished.connect(self.destroy_progressbar_dialog)
        self.filter_worker.finished.connect(self.update_filter_status)
        self.filter_worker.start.emit()
