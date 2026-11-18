import astropy
from astropy.table import Table
import synphot

test_data = "/Users/mayabasu/PycharmProjects/uvex-insim/UVEX/data_files/CALDB/scopesim/UVIM_FUV_filter_response.dat"
table = Table()




def load_effect(path:str, expected_wave_header:str, expected_data_header:str):
    #missing error handling
    table = astropy.io.ascii.read(path)
    wave = table[expected_wave_header]
    data = table[expected_data_header]
    #synphot does not do much to check that the data loaded makes sense, we will at least check the lengths
    #maybe add more checks in the future?
    assert len(wave) == len(data), f"Could not load data from {path} due to data and wave columns having different lengths"

    #sift through the comments and look for 'wavelength-unit: blah'
    unit_comments = 0
    for comment in table.meta["comments"]:
        if "wavelength_unit" in comment:
            unit_comments += 1
            unit = comment.split(":")[1].strip()
            match unit:
                case "nm":
                    wave = wave
                case "um":
                    print(f" \t Loaded wavelength values in um, converted to nm")
                    wave = wave*1000
                case "angstrom":
                    print(f" \t Loaded wavelength values in angstrom, converted to nm")
                    wave = wave*0.1
                case _:
                    print(f" '{unit}' is not a supported unit, please use nm, um, or angstrom")
                    raise Exception("Failed to load file due to invalid units")



    assert unit_comments==1, f"Expected one comment of {path} to contain wavelength_unit, found {unit_comments}"



    effect = synphot.Empirical1D(points=wave,lookup_table=data)
    return effect

