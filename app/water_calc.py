from tkinter import ttk
import tkinter as tk
from RangeSlider import RangeSliderH
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from data_processing import data_processing


class water_calc(ttk.Frame):
    """
    widgets needed:
        - silicate region birs radiobuttons
        - water region birs scale
        - Store button
    """

    def __init__(self, parent, app, *args, **kwargs):

        super().__init__(parent, *args, **kwargs)
        self.app = app
        # Frame settings
        self.rowconfigure(0, weight=1)
        self.rowconfigure(7, weight=1)
        self.columnconfigure(0, weight=1)

        self.colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

        # Create plot canvas
        self.fig, (self.ax1, self.ax2) = plt.subplots(
            2, 1, figsize=(5, 7), constrained_layout=True, dpi=100
        )
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(
            row=0, column=0, rowspan=6, columnspan=5, sticky=("nesw")
        )

        self.ax1.set_title("Silicate region")
        self.ax1.set_xlabel(" ")
        self.ax1.set_ylabel("Intensity (arbitr. units)")
        self.ax1.set_yticks([])
        self.ax1.set_xlim(150, 1400)

        self.ax2.set_title("H$_2$O  region")
        self.ax2.set_yticks([])
        self.ax2.set_xlim(2700, 4000)
        self.ax2.set_xlabel("Raman shift cm$^{-1}$")

        self.fig.patch.set_facecolor(app.bgClr_plt)

        self.fig.canvas.draw()

        # Object to store lines to be dragged
        self._dragging_line = None
        # Store the id of the H2O bir being dragged, 0 for left, 1 for right
        self._dragging_line_id = None

        self.raw_spectra = []
        self.baselines = []
        self.corrected = []

    def initiate_plot(self, index):

        self.data = self.app.data.spectra[index]

        self.H2O_left, self.H2O_right = self.app.data.processing.loc[index, ["water_left", "water_right"]]
        H2O_bir = np.array([[1500, self.H2O_left], [self.H2O_right, 4000]])
        self.Si_birs_select = int(self.app.data.processing.loc[index, "Si_bir"])

        y_max_Si = np.max(self.data.signal.long_corrected[self.data.x < 1400]) * 1.2
        y_max_h2o = np.max(self.data.signal.long_corrected[self.data.x > 2500]) * 1.2

        self.ax1.set_ylim(0, y_max_Si * 1.05)
        self.ax2.set_ylim(0, y_max_h2o)

        for ax in (self.ax1, self.ax2):
            # Remove old plotted lines
            for i, line in enumerate(ax.get_lines()):
                line.remove()

        self.fig.canvas.draw_idle()

        # Plot spectra
        for ax in (self.ax1, self.ax2):
            # Long corrected
            self.raw_spectra.append(ax.plot(self.data.x, self.data.signal.long_corrected, color=self.colors[0], linewidth=1.2))
            # Baseline
            self.baselines.append(ax.plot(self.data.x, self.data.baseline, linestyle="dashed", color=self.colors[2], linewidth=1.2))
            # Baseline corrected
            self.corrected.append(ax.plot(self.data.x, self.data.signal.baseline_corrected, color=self.colors[1], linewidth=1.2))
            
        # Plot baseline interpolation regions
        # Silicate region
        Si_bir0_polygons = [self.ax1.axvspan(bir[0], bir[1], alpha=0.3, color="gray", edgecolor=None, visible=False) for bir in data_processing.Si_bir_0]
        Si_bir1_polygons = [self.ax1.axvspan(bir[0], bir[1], alpha=0.3, color="gray", edgecolor=None, visible=False) for bir in data_processing.Si_bir_1]
        self.Si_bir_polygons = [Si_bir0_polygons, Si_bir1_polygons]
        for polygon in self.Si_bir_polygons[self.Si_birs_select]:
            polygon.set_visible(True)
        # Water region
        self.H2O_bir_polygons = [self.ax2.axvspan(bir[0], bir[1], alpha=0.3, color="gray") for bir in H2O_bir]
        self.H2O_bir_lines = [self.ax2.axvline(x, color="k", linewidth=1, visible=False) for x in [self.H2O_left, self.H2O_right]]

        # Connect mouse events to callback functions
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)
        self.fig.canvas.mpl_connect('button_release_event', self._on_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self._on_motion)

        self.canvas.draw()

    def update_plot_sample(self, index):

        self.data = self.app.data.spectra[index]

        self.H2O_left, self.H2O_right = self.app.data.processing.loc[index, ["water_left", "water_right"]]
        self.Si_birs_select = int(self.app.data.processing.loc[index, "Si_bir"])

        y_max_Si = np.max(self.data.signal.long_corrected[self.data.x < 1400]) * 1.2
        y_max_h2o = np.max(self.data.signal.long_corrected[self.data.x > 2500]) * 1.2

        self.ax1.set_ylim(0, y_max_Si * 1.05)
        self.ax2.set_ylim(0, y_max_h2o)

        for i, _ in enumerate([self.ax1, self.ax2]):
            # Long corrected
            self.raw_spectra[i][0].set_data(self.data.x, self.data.signal.long_corrected)
            # Baseline
            self.baselines[i][0].set_data(self.data.x, self.data.baseline)
            # Baseline corrected
            self.corrected[i][0].set_data(self.data.x, self.data.signal.baseline_corrected)

        for line, x in zip(self.H2O_bir_lines, (self.H2O_left, self.H2O_right)):
            line.set_xdata([x, x])
        
        self.update_H2O_birs()
        self.update_Si_birs()


    def update_H2O_birs(self):

        polygon_left = np.array([[1500, 0.], [1500, 1.], [self.H2O_left, 1.], [self.H2O_left, 0.]])
        polygon_right = np.array([[self.H2O_right, 0.], [self.H2O_right, 1.], [4000, 1.], [4000, 0.]])
        H2O_polygons_new = [polygon_left, polygon_right]
        for polygon_old, polygon_new in zip(self.H2O_bir_polygons, H2O_polygons_new):
            polygon_old.set_xy(polygon_new)

        self.fig.canvas.draw_idle()


    def update_Si_birs(self):

        for polygon in self.Si_bir_polygons[self.Si_birs_select]:
            polygon.set_visible(True)
        for polygon in self.Si_bir_polygons[abs(self.Si_birs_select - 1)]:
            polygon.set_visible(False)
        self.fig.canvas.draw_idle()


    def recalculate_baseline(self):

        H2O_bir = np.array([[1500, round(self.H2O_left, -1)], [round(self.H2O_right, -1), 4000]])
        Si_bir = self.app.data.Si_birs[self.Si_birs_select]
        birs = np.concatenate((Si_bir, H2O_bir))
 
        self.data.baselineCorrect(baseline_regions=birs)
        self.baselines[1][0].set_data(self.data.x, self.data.baseline)

        self.fig.canvas.draw_idle()


    def _on_click(self, event):
        """ 
        callback method for mouse click event
        :type event: MouseEvent
        """
        # left click
        if event.button == 1 and event.inaxes in [self.ax2]:
            line = self._find_neighbor_line(event)
            if line:
                self._dragging_line = line
     

    def _on_release(self, event):
        """ callback method for mouse release event
        :type event: MouseEvent
        """
        if event.button == 1 and event.inaxes in [self.ax2] and self._dragging_line:
            new_x = event.xdata
            self.H2O_bir_lines[self._dragging_line_id] = self._dragging_line
            self._dragging_line = None
            self._dragging_line_id = None
            # self._dragging_line.remove()
            id = self._dragging_line_id
            if id == 0:
                self.H2O_left = round(new_x, -1)
            elif id == 1:
                self.H2O_right = round(new_x, -1)
            self.recalculate_baseline()
            self.update_H2O_birs()


    def _on_motion(self, event):
        """ callback method for mouse motion event
        :type event: MouseEvent
        """
        if self._dragging_line:
            new_x = event.xdata
            y = self._dragging_line.get_ydata()
            self._dragging_line.set_data([new_x, new_x], y)
            # self.fig.canvas.draw_idle()
            id = self._dragging_line_id
            if id == 0:
                if new_x > self.H2O_right:
                    new_x = self.H2O_right - 20
                self.H2O_left = new_x
            elif id == 1:
                if new_x < self.H2O_left:
                    new_x = self.H2O_left + 20
                self.H2O_right = new_x
            self.recalculate_baseline()
            self.update_H2O_birs()


    def _find_neighbor_line(self, event):
        """ 
        Find lines around mouse position
        :rtype: ((int, int)|None)
        :return: (x, y) if there are any point around mouse else None
        """
        distance_threshold = 10
        nearest_line = None
        for i, line in enumerate(self.H2O_bir_lines):
            x = line.get_xdata()[0]
            distance = abs(event.xdata - x)
            if distance < distance_threshold:
                nearest_line =  line
                self._dragging_line_id = i
        return nearest_line
            
