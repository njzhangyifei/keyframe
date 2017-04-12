from cvutils import CVFrame
from cvutils.cvframebuffer import CVFrameBuffer
import numpy as np

buffer = CVFrameBuffer(10)
buffer.append(CVFrame(np.zeros([10, 10])))
buffer.append(CVFrame(np.ones([10, 10])))

print(buffer[0].cv_mat)
