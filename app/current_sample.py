from sympy import interpolate


class current_sample:
    def __init__(self, dataset, index):
        self.dataset = dataset
        self.index = index
        self.spectra = dataset.spectra[index]
        self.name = dataset.names[index]
        # Interpolation settings
        self.read_interpolation()
        # Baseline interpolation region settings
        self.read_water()
        # self.Si_birs_select = dataset.processing.loc[index, "Si_bir"]
        # self.H2O_left = dataset.processing.loc[index, "water_left"]
        # self.H2O_right = dataset.processing.loc[index, "water_right"]

        
        # self.interpolate = dataset.processing.loc[index, "interpolate"]
        # self.interpolate_left = dataset.processing.loc[index, "interpolate_left"]
        # self.interpolate_right = dataset.processing.loc[index, "interpolate_right"]
        # self.interpolation_smoothing = dataset.processing.loc[
        #     index, "interpolation_smoothing"
        # ]
        # Calculated areas
        self.recalculate_areas()

    def read_interpolation(self):
        # Interpolation settings
        self.interpolate = self.dataset.processing.loc[self.index, "interpolate"]
        self.interpolate_left = self.dataset.processing.loc[
            self.index, "interpolate_left"
        ]
        self.interpolate_right = self.dataset.processing.loc[
            self.index, "interpolate_right"
        ]
        self.interpolation_smoothing = self.dataset.processing.loc[
            self.index, "interpolation_smoothing"
        ]

    def read_water(self):
        self.Si_birs_select = self.dataset.processing.loc[self.index, "Si_bir"]
        self.H2O_left = self.dataset.processing.loc[self.index, "water_left"]
        self.H2O_right = self.dataset.processing.loc[self.index, "water_right"]

    def recalculate_interpolation(self):
        """
        
        """

        self.spectra.interpolate(
            interpolate=[self.interpolate_left, self.interpolate_right],
            smooth_factor=self.interpolation_smoothing,
            use=False,
        )

    def recalculate_baseline(self):
        """

        """
        smooth_factor = self.dataset.smooth_factor

        Si_bir = self.dataset.Si_birs[self.Si_birs_select]

        self.spectra.baselineCorrect(
            Si_birs=Si_bir,
            H2O_boundaries=[round(self.H2O_left, -1), round(self.H2O_right, -1)],
            smooth_factor=smooth_factor,
        )

    def recalculate_areas(self):
        """

        """
        self.spectra.calculate_SiH2Oareas()
        self.Si_area, self.H2O_area = self.spectra.SiH2Oareas

    def save_interpolation_settings(self):
        """
        
        """
        self.dataset.processing.loc[self.index, "interpolate"] = self.interpolate
        self.dataset.processing.loc[
            self.index, "interpolate_left"
        ] = self.interpolate_left
        self.dataset.processing.loc[
            self.index, "interpolate_right"
        ] = self.interpolate_right
        self.dataset.processing.loc[
            self.index, "interpolation_smoothing"
        ] = self.interpolation_smoothing

    def save_water_settings(self):
        """
        
        """
        self.dataset.processing.loc[self.index, "Si_bir"] = self.Si_birs_select
        self.dataset.processing.loc[self.index, ["water_left", "water_right"]] = round(
            self.H2O_left, -1
        ), round(self.H2O_right, -1)

        self.dataset.results.loc[self.index, ["SiArea", "H2Oarea"]] = (
            self.Si_area,
            self.H2O_area,
        )
        self.dataset.results.loc[self.index, "rWS"] = self.H2O_area / self.Si_area
