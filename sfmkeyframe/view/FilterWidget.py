import cv2
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QGroupBox

from cvutils import CVFrame, CVVideoCapture, CVSharpness, CVCorrelation, \
    CVOpticalFlow
from .ui.FilterWidget import Ui_FilterWidget


class FilterWidget(QGroupBox):
    def __init__(self, cv_video_cap):
        super(FilterWidget, self).__init__()
        self.cv_video_cap = cv_video_cap  # type: CVVideoCapture
        self.ui = Ui_FilterWidget()
        self.ui.setupUi(self)
        self.ui.spinBoxFilterSharpness_windowSize.setValue(
            self.cv_video_cap.get_frame_rate())
        self.ui.pushButtonFilterGlobal_run.clicked.connect(
            self.pushButtonFilterGlobal_run_clicked)
        self.sharpness_filter = None
        self.correlation_filter = None
        self.opticalflow_filter = None

    def closeEvent(self, e):
        super(FilterWidget, self).closeEvent(e)

    @property
    def params_sharpness(self):
        params = {
            'enabled': self.ui.groupBoxFilterSharpness.isChecked(),
            'z_score': self.ui.doubleSpinBoxFilterSharpness_zscore.value(),
            'window_size': self.ui.spinBoxFilterSharpness_windowSize.value(),
        }
        return params

    @property
    def params_correlation(self):
        params = {
            'enabled': self.ui.groupBoxFilterCorrelation.isChecked(),
            'threshold': self.ui.doubleSpinBoxFilterCorrelation_threshold.value()
        }
        return params

    @property
    def params_opticalflow(self):
        feature_params = dict(maxCorners=500, qualityLevel=0.3,
                              minDistance=7, blockSize=7)
        lk_params = dict(winSize=(15, 15), maxLevel=2,
                         criteria=(
                             cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                             10, 0.03))
        params = {
            'enabled': self.ui.groupBoxFilterOpticalFlow.isChecked(),
            'threshold': self.ui.doubleSpinBoxFilterOpticalFlow_threshold.value(),
            'opticalflow_params': {
                'feature_params': feature_params,
                'lk_params': lk_params
            }
        }
        return params

    def prepare_filters(self):
        if self.params_sharpness['enabled']:
            sharpness = CVSharpness()
            self.sharpness_filter = {
                'filter': sharpness,
                'calculation': sharpness.load_calculation_file(self.cv_video_cap),
                'acceptance': None,
                'loadded_acceptance': sharpness.load_acceptance_file(self.cv_video_cap)
            }
        else:
            self.sharpness_filter = None
        if self.params_correlation['enabled']:
            correlation = CVCorrelation()
            self.correlation_filter = {
                'filter': correlation,
                'acceptance': correlation.load_acceptance_file(self.cv_video_cap),
            }
        else:
            self.correlation_filter = None
        if self.params_opticalflow['enabled']:
            optical_flow_params = self.params_opticalflow['opticalflow_params']
            opticalflow = CVOpticalFlow(optical_flow_params['feature_params'],
                                        optical_flow_params['lk_params'])
            self.opticalflow_filter = {
                'filter': opticalflow,
                'acceptance': opticalflow.load_acceptance_file(self.cv_video_cap),
            }
        else:
            self.opticalflow_filter = None

    def pushButtonFilterGlobal_run_clicked(self):
        self.prepare_filters()

        # print(str(self.params_sharpness) if self.params_sharpness['enabled']
        #       else 'sharpness filter is disabled')
        # print(str(self.params_correlation) if self.params_correlation['enabled']
        #       else 'correlation filter is disabled')
        # print(str(self.params_opticalflow) if self.params_opticalflow['enabled']
        #       else 'opticalflow filter is disabled')
        #
