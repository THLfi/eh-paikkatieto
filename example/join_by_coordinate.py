"""Assign incident risk class by lat, lon position"""

import pandas as pd
import geopandas as gpd
import shapely.geometry as geom

INPUT_FILES = [
    "data/ptp2023/EH PTP data 2023 koko vuosi.xlsx"
]

SHAPEFILE = "data/eh_all_1km_2024-001.shp.zip"

LAT_COL = "leveysaste (tapahtuma)"
LON_COL = "pituusaste (tapahtuma)"
RISK_COL = "riskialueluokka (tapahtuma)"

print(f"Loading shapefile {SHAPEFILE}...")
risk_grid = gpd.read_file(SHAPEFILE)

for filename in INPUT_FILES:
    print(f"Loading {filename}...")
    if filename.endswith(".csv"):
        ptp_df = pd.read_csv(filename, delimiter=";", low_memory=False)
        lat = ptp_df[LAT_COL].str.replace(",", ".").astype(float)
        lon = ptp_df[LON_COL].str.replace(",", ".").astype(float)
        output_filename = filename.replace(".csv", "_risk.csv")
    elif filename.endswith(".xlsx"):
        ptp_df = pd.read_excel(filename)
        lat = ptp_df[LAT_COL]
        lon = ptp_df[LON_COL]
        output_filename = filename.replace(".xlsx", "_risk.xlsx")
    else:
        exit(1)
    if "RISK_COL" in ptp_df.columns:
        ptp_df = ptp_df.drop(columns=["RISK_COL"])

    geometry = [geom.Point(xy) for xy in zip(lon, lat)]
    ptp_gdf = gpd.GeoDataFrame(ptp_df, geometry=geometry, crs="EPSG:4326")
    # Convert to ETRS89 / TM35FIN(E,N)
    ptp_gdf = ptp_gdf.to_crs("EPSG:3067")

    result = gpd.sjoin(ptp_gdf, risk_grid, how="left", predicate="within")

    print(f"Risk class distribution ({filename}):")
    print(result.eh_risk.value_counts())

    print(f"Saving output as {output_filename}.")

    result = result.drop(
        columns=[
            "geometry",
            "index_right",
            "square_id",
            "euref_x",
            "euref_y",
            "shape_star",
            "shape_stle",
            "eh_risk_id",
            "population",
            "men",
            "women",
            "age_0_14",
            "age_15_64",
            "age_65_",
        ]
    ).rename(columns={"eh_risk": RISK_COL})

    if output_filename.endswith('.csv'):
        result.to_csv(output_filename, index=False, sep=";")
    elif output_filename.endswith('.xlsx'):
        result.to_excel(output_filename, index=False)
