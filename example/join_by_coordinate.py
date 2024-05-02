"""Assign incident risk class by lat, lon position"""

import pandas as pd
import geopandas as gpd
import shapely.geometry as geom

INPUT_FILES = [
    'data/ptp2023/EH Q123 Emergency Chain All Dispatches Q1-2023.csv',
    'data/ptp2023/EH Emergency Chain All Dispatches 2023-Q2.csv',
    'data/ptp2023/EH Emergency Chain All Dispatches_Migrated Data_2023-Q3-2023-11-03.csv',
    'data/ptp2023/Q4_23_EH Emergency Chain All Dispatches_Migrated_Data_filtered-utf8.csv'
]

SHAPEFILE = 'data/eh_all_1km_2024-001.shp.zip'

LAT_COL = 'leveysaste (tapahtuma)'
LON_COL = 'pituusaste (tapahtuma)'
RISK_COL = 'riskialueluokka (tapahtuma)'

risk_grid = gpd.read_file(SHAPEFILE)

for filename in INPUT_FILES:
    ptp_df = pd.read_csv(filename, delimiter=';', low_memory=False)
    if 'RISK_COL' in ptp_df.columns:
        ptp_df = ptp_df.drop(columns=['RISK_COL'])

    lat = ptp_df[LAT_COL].str.replace(',', '.').astype(float)
    lon = ptp_df[LON_COL].str.replace(',', '.').astype(float)

    geometry = [geom.Point(xy) for xy in zip(lon, lat)]
    ptp_gdf = gpd.GeoDataFrame(ptp_df, geometry=geometry, crs='EPSG:4326')
    # Convert to ETRS89 / TM35FIN(E,N)
    ptp_gdf = ptp_gdf.to_crs('EPSG:3067')

    result = gpd.sjoin(ptp_gdf, risk_grid, how="left", predicate="within")

    print(f"Risk class distribution ({filename}):")
    print(result.eh_risk.value_counts())

    output_filename = filename.replace('.csv', '_risk.csv')
    print(f"Saving output as {output_filename}.")

    result.drop(columns=['geometry', 'index_right', 'square_id',
                         'euref_x', 'euref_y', 'shape_star',
                         'shape_stle', 'eh_risk_id', 'population',
                         'men', 'women', 'age_0_14', 'age_15_64', 'age_65_']) \
    .rename(columns={'eh_risk': RISK_COL}) \
    .to_csv(output_filename, index=False, sep=';')
