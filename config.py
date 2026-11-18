import dataclasses
import warnings

import matplotlib.pyplot as plt
import astropy
import numpy as np
import yaml
import spectral_data

from typing import Tuple

from astropy.table import Table

@dataclasses.dataclass
class SpectralEffect():
    path:str
    data_header:str
    include:bool

    #todo: move to uvex module since this is UVEX specific
    @staticmethod
    def FUV_default() -> dict[str,dict[str,str|bool]]:

        dichroic = SpectralEffect(
            "/Users/mayabasu/PycharmProjects/uvex-insim/UVEX/data_files/CALDB/scopesim/UVIM_dichroic_response.dat",
            "reflection",
            True
        )
        contamination = SpectralEffect(
            "/Users/mayabasu/PycharmProjects/uvex-insim/UVEX/data_files/CALDB/scopesim/UVIM_FUV_contamination.dat",
            "transmission",
            True
        )
        fuv_filter = SpectralEffect(
            "/Users/mayabasu/PycharmProjects/uvex-insim/UVEX/data_files/CALDB/scopesim/UVIM_FUV_filter_response.dat",
            "transmission",
            True
        )
        return {"fuv_dichroic":dichroic.as_dict(),
                "contamination":contamination.as_dict(),
                "fuv_filter":fuv_filter.as_dict()}
    def as_dict(self) -> dict[str,str|bool]:
        return {"path":self.path,
         "include":self.include,
         "data_header":self.data_header
         }


@dataclasses.dataclass
class Config():
    spectral_effects:dict[str,dict[str,str|bool]]


    @staticmethod
    def FUV_default()-> Config:
        return Config(
            spectral_effects=SpectralEffect.FUV_default()
        )

    def write(self, file_name:str):
        with open(file_name, "w") as file:
            #add in error handling
            file.write(yaml.safe_dump({
                "spectral_effects":
                self.spectral_effects
            }))
    @staticmethod
    def load(file_name:str):
        with open(file_name, "r") as file:
            #add in error handling
            result = yaml.safe_load(file.read())
            print(result)
            wavelength_header = "wavelength"
            print(wavelength_header)

            #First, the FUV path
            fuv_path = result["FUVConfig"]
            print("Loading FUV Effects:")
            for index, (key, value) in enumerate(fuv_path.items()):
                match value[2]:
                    case True:
                        pass
                    case False:
                        print(f"Use of effect \033[1m {key} \033[0m is set to \033[1m False \033[0m, effect will not be loaded")
                        continue
                    case _:
                        warnings.warn("Effect is missing bool to indicate if it should be used, default is True")

                print(f"\033[1m {index}: {key} \033[0m from {value[0]} \n \t Loading headers '{wavelength_header}' and '{value[1]}'...")
                effect = spectral_data.load_effect(value[0], wavelength_header, value[1])
                print(f" \t {len(effect.points[0].data)} points total")
                wave = np.linspace(100,1000,10000)
                y = effect(wave)

                #plt.plot(wave,y)

                #plt.show()


config = Config.FUV_default()
config.write("test.yaml")
config.load("test.yaml")
#print(yaml.dump(config.spectral_effects["contamination"]))

#Config.load("test.yaml")

