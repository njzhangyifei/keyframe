from multiprocessing.managers import BaseManager

from cvutils.cvprogresstracker import CVProgressTracker


class MathsClass(object):
    def add(self, x, y):
        return x + y
    def mul(self, x, y):
        return x * y

class MyManager(BaseManager):
    pass

MyManager.register('test', CVProgressTracker)


if __name__ == '__main__':
    manager = MyManager()
    manager.start()
    def callback(arg):
        print(arg)
    maths = manager.test(callback)
    maths.complete()

