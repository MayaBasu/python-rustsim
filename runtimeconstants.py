import dataclasses

@dataclasses.dataclass
class Parameters:
    precision = 0.00001

    #These three parameters determine the default spectral grid
    #which runs from min_wave_nm to max_wave_nm with wave_num points
    #units are nm
    min_wave_nm = 100
    max_wave_nm = 1000
    wave_num = 1000
