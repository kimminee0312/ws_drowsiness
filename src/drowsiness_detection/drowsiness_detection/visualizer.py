import cv2
import matplotlib.pyplot as plt

class Visualizer:
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.xdata, self.ydata = [], []
        self.line, = self.ax.plot([], [], 'r-', label='MAR (Yawning)')
        self.ax.set_xlabel("Frames")
        self.ax.set_ylabel("Value")
        self.ax.set_title("Real-time Drowsiness Detection")
        self.ax.legend()
        plt.ion()

    def update(self, frame, mar_avg, ear_avg, status):
        if mar_avg is not None:
            self.xdata.append(len(self.xdata) + 1)
            self.ydata.append(mar_avg)
            self.line.set_xdata(self.xdata)
            self.line.set_ydata(self.ydata)
            self.ax.relim()
            self.ax.autoscale_view()
            plt.draw()
            plt.pause(0.001)

        cv2.putText(frame, status, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.imshow("Drowsiness Detection", frame)

    def show(self):
        cv2.waitKey(1)

    def close(self):
        plt.ioff()
        plt.show()
        cv2.destroyAllWindows()
