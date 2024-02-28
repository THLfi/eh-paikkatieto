import os
import geopandas as gpd

# revision info - year and revision number
REV_YEAR = 2024
REV_NUM = 1

REVISION = f"{REV_YEAR}-{REV_NUM:03}"

# input files
SHP_GRID = "input/hila1km.zip"
SHP_VAESTO = "input/vaki2022_1km.zip"
SHP_TAAJAMA = "input/YKRTaajamat2022.zip"
SHP_KESKUSTA = "input/KeskustaAlueet2021.zip"

# output files
OUTPUTDIR = "output"
SHP_EH_FULLGRID = f"{OUTPUTDIR}/eh_all_1km_{REVISION}.shp.zip"
SHP_EH_POPULATED = f"{OUTPUTDIR}/eh_populated_1km_{REVISION}.shp.zip"

# risk classes
RISK_ID_YDINTAAJAMA = 1
RISK_ID_MUU_TAAJAMA = 2
RISK_ID_MAASEUTU = 3
RISK_ID_MUU_ALUE = 4
EH_RISK_NAMES = {
    1: "Ydintaajama",
    2: "Muu taajama",
    3: "Asuttu maaseutu",
    4: "Muu alue",
}

# `Keskustyyp` classes to map as 'Ydintaajama'
YDINTAAJAMA_KESKUSTYYP = ["Kaupunkiseudun iso alakeskus", "Kaupunkiseudun keskusta"]

# column names
EH_RISK_COLNAME = "eh_risk_id"
EH_RISK_STR_COLNAME = "eh_risk"


def classify_squares(grid, taajama, keskusta):
    grid["idx"] = grid.index

    # "Asuttu maaseutu"
    grid.loc[grid["vaesto"].notnull(), EH_RISK_COLNAME] = RISK_ID_MAASEUTU
    grid.loc[grid["vaesto"].notnull(), EH_RISK_STR_COLNAME] = EH_RISK_NAMES[
        RISK_ID_MAASEUTU
    ]

    # "Muu taajama"
    overlapping_taajama = taajama.sjoin(grid, how="inner", predicate="overlaps")["idx"]
    within_taajama = grid.sjoin(taajama, how="inner", predicate="within")["idx"]
    taajama_within = taajama.sjoin(grid, how="inner", predicate="within")["idx"]
    is_taajama = (
        grid.idx.isin(overlapping_taajama)
        | grid.idx.isin(within_taajama)
        | grid.idx.isin(taajama_within)
    )
    grid.loc[is_taajama, EH_RISK_COLNAME] = RISK_ID_MUU_TAAJAMA
    grid.loc[is_taajama, EH_RISK_STR_COLNAME] = EH_RISK_NAMES[RISK_ID_MUU_TAAJAMA]

    # "Ydintaajama"
    ydintaajama = keskusta[keskusta["Keskustyyp"].isin(YDINTAAJAMA_KESKUSTYYP)]
    overlapping_ydintaajama = ydintaajama.sjoin(
        grid, how="inner", predicate="overlaps"
    )["idx"]
    within_ydintaajama = grid.sjoin(ydintaajama, how="inner", predicate="within")["idx"]
    ydintaajama_within = ydintaajama.sjoin(grid, how="inner", predicate="within")["idx"]
    is_ydintaajama = (
        grid.idx.isin(overlapping_ydintaajama)
        | grid.idx.isin(within_ydintaajama)
        | grid.idx.isin(ydintaajama_within)
    )
    grid.loc[is_ydintaajama, EH_RISK_COLNAME] = RISK_ID_YDINTAAJAMA
    grid.loc[is_ydintaajama, EH_RISK_STR_COLNAME] = EH_RISK_NAMES[RISK_ID_YDINTAAJAMA]

    return grid.drop(columns="idx")


if __name__ == "__main__":
    if not os.path.exists(OUTPUTDIR):
        os.makedirs(OUTPUTDIR)

    # load input shapefiles
    gdf_grid = gpd.read_file(SHP_GRID)
    gdf_vaesto = gpd.read_file(SHP_VAESTO)
    gdf_taajama = gpd.read_file(SHP_TAAJAMA)
    gdf_keskusta = gpd.read_file(SHP_KESKUSTA)

    # rename grid square id column
    gdf_grid = gdf_grid.rename(columns={"nro": "square_id"})
    gdf_vaesto = gdf_vaesto.rename(columns={"id_nro": "square_id"})
    gdf_grid["square_id"] = gdf_grid["square_id"].astype("int64")
    gdf_vaesto["square_id"] = gdf_vaesto["square_id"].astype("int64")

    # initialize risk class
    gdf_grid[EH_RISK_COLNAME] = RISK_ID_MUU_ALUE
    gdf_grid[EH_RISK_STR_COLNAME] = EH_RISK_NAMES[RISK_ID_MUU_ALUE]

    # join population data to grid
    gdf_ensihoito = gpd.GeoDataFrame(
        gdf_grid.merge(
            gdf_vaesto[
                [
                    "square_id",
                    "vaesto",
                    "miehet",
                    "naiset",
                    "ika_0_14",
                    "ika_15_64",
                    "ika_65_",
                ]
            ],
            how="left",
            on="square_id",
            validate="one_to_one",
        )
    )

    # determine risk class for each square
    gdf_ensihoito = classify_squares(gdf_ensihoito, gdf_taajama, gdf_keskusta)

    # english column names
    gdf_ensihoito = gdf_ensihoito.rename(
        columns={
            "vaesto": "population",
            "miehet": "men",
            "naiset": "women",
            "ika_0_14": "age_0_14",
            "ika_15_64": "age_15_64",
            "ika_65_": "age_65_",
        }
    )

    # impute empty values
    gdf_ensihoito["population"] = gdf_ensihoito["population"].fillna(0)
    gdf_ensihoito["men"] = gdf_ensihoito["men"].fillna(0)
    gdf_ensihoito["women"] = gdf_ensihoito["women"].fillna(0)
    gdf_ensihoito["age_0_14"] = gdf_ensihoito["age_0_14"].fillna(0)
    gdf_ensihoito["age_15_64"] = gdf_ensihoito["age_15_64"].fillna(0)
    gdf_ensihoito["age_65_"] = gdf_ensihoito["age_65_"].fillna(0)

    # set column data types
    gdf_ensihoito[EH_RISK_COLNAME] = gdf_ensihoito[EH_RISK_COLNAME].astype("int64")
    gdf_ensihoito[EH_RISK_STR_COLNAME] = gdf_ensihoito[EH_RISK_STR_COLNAME].astype(
        "string"
    )
    gdf_ensihoito["population"] = gdf_ensihoito["population"].astype("int64")
    gdf_ensihoito["men"] = gdf_ensihoito["men"].astype("int64")
    gdf_ensihoito["women"] = gdf_ensihoito["women"].astype("int64")
    gdf_ensihoito["age_0_14"] = gdf_ensihoito["age_0_14"].astype("int64")
    gdf_ensihoito["age_15_64"] = gdf_ensihoito["age_15_64"].astype("int64")
    gdf_ensihoito["age_65_"] = gdf_ensihoito["age_65_"].astype("int64")

    # print summary and write to shapefile - full grid version
    print(f"{SHP_EH_FULLGRID}:")
    print(gdf_ensihoito[EH_RISK_STR_COLNAME].value_counts())
    print(gdf_ensihoito.info())

    gdf_ensihoito.to_file(SHP_EH_FULLGRID)

    # print summary and write to shapefile - inhabited only version
    print(f"{SHP_EH_POPULATED}:")
    gdf_eh_populated = gdf_ensihoito[gdf_ensihoito[EH_RISK_COLNAME] != RISK_ID_MUU_ALUE]
    print(gdf_eh_populated[EH_RISK_STR_COLNAME].value_counts())
    print(gdf_eh_populated.info())

    gdf_eh_populated.to_file(SHP_EH_POPULATED)
