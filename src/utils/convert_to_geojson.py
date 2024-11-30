import geopandas as gpd

# wrs_path = "Water Resource Areas [Atkins 2012]/waterresourceareas.shp"
# wrdf = gpd.read_file(wrs_path)
# stream_lake_names = "Stream_ Lake GeoNames/geonames_h.shp"
# slnf = gpd.read_file(stream_lake_names)
# rainguages = "Rain Gauges/raingauges.shp"
# rgf = gpd.read_file(rainguages)

# wrs = "./wrs.geojson"
# sln = "./sln.geojson"
# rg = "./rg.geojson"

# wrdf.to_file(wrs, driver="GeoJSON")
# print(f"Shapefile converted to GeoJSON and saved at {wrs}")

# slnf.to_file(sln, driver="GeoJSON")
# print(f"Shapefile converted to GeoJSON and saved at {sln}")

# rgf.to_file(rg, driver="GeoJSON")
# print(f"Shapefile converted to GeoJSON and saved at {rg}")

mlwplaces_point = "mlwplaces_point.shp"
mlwplaces_pointr = "mlwplaces_point.geojson"
mlwplaces_pointf = gpd.read_file(mlwplaces_point)
mlwplaces_pointf.to_file(mlwplaces_pointr, driver="GeoJSON")
