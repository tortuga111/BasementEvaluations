import geopandas as gpd


def load_data_with_crs_2056(path_to_data: str) -> gpd.geodataframe:
    loaded_data = gpd.read_file(path_to_data)
    if loaded_data.crs is None:
        loaded_data.crs = 2056
    assert loaded_data.crs == 2056
    return loaded_data
