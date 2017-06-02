# Keyframe
A simple tool for selecting keyframes from SfM (structure from motion) videos,
using naive sharpness, correlation and optical flow criteria.

<p align="center">
  <img src="https://cloud.githubusercontent.com/assets/2238599/26716249/9290b81c-472d-11e7-8bf3-fc025020844e.png">
<p align="center">

## Dependencies
- `python3`
- `numpy`
- `cv2` (opencv3 python binding)
- `pyqt5`

Assuming you have set up your path correctly, I will use `pip3` and `python3` to 
refer to those executables in your `python3` installation.

### Linux (Ubuntu)
- `sudo apt-get install python3-pyqt5`
- `pip3 install numpy`
- Compile OpenCV 3 with python3 binding (3.2.0 was used during development). 
You can follow the [steps](https://stackoverflow.com/questions/40051573/opencv-3-1-0-with-python-3-5).


### Windows
- Run `pip3 install pyqt5`
- Install `numpy`, `opencv_python‑3.2.0` prebuilt wheels from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/)
by first downloading the `.whl` files and then `pip3 install <filename>.whl`

## Usage

<p align="center">
  <img src="https://cloud.githubusercontent.com/assets/2238599/26714939/8d373ba2-4728-11e7-83a2-7fcdd6790dd9.png">
</p>

1. Run  `./run.py` or just double-click on `run.py` if you are using windows.
2. Load the video file
3. Enable or disable filters
    - Filters will be run **from top to bottom** (first sharpness, then correlation, finally optical flow)
    - The **output** of a previous filter will be the **input** of the next filter
    - The order of filters **CANNOT** be changed (for now)
    - You can have all or no filters enabled
4. Click `Run`
5. Tune parameters, `Preview` or `Export`
6. You can save the tuned filter parameters into a file for later reuse.

## Filter Details

### Sharpness
- `Z-score`, we will reject frames whose **single-tailed** z-score of sharpness
value (within the distribution of `Window Size` frames) is greater than this value.
Note that, this score is actually *median absolute deviation*, used here to
compensate for outliers. 
Here is an [NIST](http://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm) page for reference.
- `Window Size`, how many frames do we consider to be in the same sharpness distribution.
In other words, the window size of moving median for the sharpness distribution.

### Correlation
- `Threshold`, between 0 and 1, we will remove the first of two consecutive frames 
if the correlation of them is higher than threshold (since they appear to be still frames).

### Optical Flow
- `Threshold`, **minimum number of pixels for the apparent camera motion**. 
We will try to reject if the camera motion is too small. 
Sometimes, this goal cannot be achieved (motion between frames too large or lost tracking) 
and we will accept the frame with value closest to the threshold.

### Filter Result Statistics
- Statistics for filter result will show after a filter finishes.
- They will be in the form of `[Input # of frames] => [Output # of frames]`

<p align="center">
  <img src="https://cloud.githubusercontent.com/assets/2238599/26716002/9a1ed114-472c-11e7-84d9-f2809c48be07.png">
</p>

## tl;dr
- (Key Frame Selection for Structure and Motion)[https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&ved=0ahUKEwi5l6iC1p7UAhUixFQKHaDjAPAQFggtMAA&url=http%3A%2F%2Fcv.snu.ac.kr%2Fhyunxx%2FSeminar%2F2004%2F2004-12-00%2FKeyFrameSelection.ppt&usg=AFQjCNFwFRiHpKfraWnwP0xQPUJrZb3W5A&sig2=o3dzc8nM6hoN-qNDdLtx9A&cad=rja]

## License
```
Released under The MIT License
Copyright 2017 Yifei Zhang
```
