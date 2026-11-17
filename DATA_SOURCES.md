# Data Sources & Copyright

This skill (plus-automation-en) ships with no data files (the PLUS engine is bundled with the author's authorization — see item 9); all data is fetched on demand at runtime from the public channels listed below. For academic use and publication, cite them in the corresponding formats.

## 1. Land-use data: CLCD / ESA WorldCover

### 1.1 CLCD (annual land cover of China, 30m)

- Data: Yang & Huang (2021) China 30m annual land-cover dataset (1990-2022)
- Access: NCDC (National Cryosphere Desert Data Center) domestic mirror; users must register and apply for download permission themselves
- License: scientific, educational, non-commercial use
- Citation: Yang, J., and Huang, X. (2021). The 30 m annual land cover dataset and its dynamics in China from 1990 to 2019. *Earth System Science Data*, 13, 3907–3925. https://doi.org/10.5194/essd-13-3907-2021

### 1.2 ESA WorldCover (global land cover, 10m; 2020 v100 / 2021 v200)

- Data: ESA WorldCover global 10m land cover, 11 classes (tree/shrub/grassland/cropland/built-up/bare/ice-snow/water/herbaceous wetland/mangrove/moss-lichen); only two epochs, 2020 and 2021
- Access: AWS S3 tiles (entry at esa-worldcover.org/en/data-access); this skill auto-downloads 3° tiles and resamples to 30m per user decision (Albers equal-area reprojection, majority resampling)
- License: **CC BY 4.0** (commercial use allowed with attribution)
- Citation: ESA WorldCover 10 m 2021 v200, https://doi.org/10.5281/zenodo.7254221 (2020 is v100, https://doi.org/10.5281/zenodo.5571936; please re-verify the release page before publishing)

## 2. Terrain data (DEM): CGIAR-CSI SRTM v4 (30m)

- Data: Hole-filled SRTM global digital elevation model v4
- Access: https://srtm.csi.cgiar.org
- Copyright: © CGIAR-CSI, non-commercial use
- Citation: Jarvis, A., Reuter, H. I., Nelson, A., and Guevara, E. (2008). Hole-filled SRTM for the globe, Version 4. CGIAR-CSI SRTM 90m Database. https://srtm.csi.cgiar.org

## 3. Climate data (annual mean temperature / annual precipitation): NCEP reanalysis & CMAP enhanced precipitation

- Data: NCEP/NCAR reanalysis (monthly mean temperature), CMAP enhanced precipitation (monthly precipitation), 2.5° grid
- Access: NOAA Physical Sciences Laboratory, https://psl.noaa.gov
- Copyright: U.S. federal government public domain data
- Citation: Kalnay, E., et al. (1996). The NCEP/NCAR 40-Year Reanalysis Project. *Bulletin of the American Meteorological Society*, 77, 437–471.; Xie, P., and Arkin, P. A. (1997). Global precipitation: A 17-year monthly analysis based on gauge observations, satellite estimates, and numerical model outputs. *Bulletin of the American Meteorological Society*, 78, 2539–2558.

## 4. Population data: WorldPop (100m)

- Data: WorldPop global population rasters (China, UN-adjusted)
- Access: https://www.worldpop.org
- License: CC BY 4.0
- Citation: WorldPop (www.worldpop.org - School of Geography and Environmental Science, University of Southampton)

## 5. Road / water / facility data: OpenStreetMap

- Data: roads, railways, water bodies, stations and other vector features (obtained via the Overpass API and openstreetmap.fr per-province packages)
- Copyright: © OpenStreetMap contributors, used under ODbL (https://www.openstreetmap.org/copyright)

## 6. Soil data: ISRIC SoilGrids (250m)

- Data: SoilGrids 2.0 global soil properties (clay content, etc.)
- Access: https://files.isric.org
- License: CC BY 4.0
- Citation: Poggio, L., et al. (2021). SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty. *SOIL*, 7, 217–240.

## 7. Administrative boundaries & codes

- Boundaries: Alibaba DataV GeoAtlas public boundary service (auto-corrected GCJ-02→WGS84 at runtime)
- Administrative code table: china-division public dataset (unpkg distribution)

## 8. Nighttime lights (optional, GDP proxy): VIIRS annual composites

- Data: VIIRS Nighttime Lights Annual Composites
- Access: Earth Observation Group, Colorado School of Mines (https://eogdata.mines.edu)
- Copyright: public domain; credit EOG/NOAA when used

## 9. PLUS engine

- PLUS.exe (the model engine) is software developed by the HPSCIL Lab (Prof. Xun Liang); **with the author's own authorization, this skill bundles and distributes the engine files** (`runtime\plus-backend`), used solely for invoking and automating the PLUS model.
- Citation: Liang, X., et al. (2021). Understanding the drivers of sustainable land expansion using a patch-generating land use simulation (PLUS) model: A case study in Wuhan, China. *Computers, Environment and Urban Systems*, 85, 101569.

## 10. Acknowledgments for no-registration data sources (user decision 2026-11-11: every downloadable-without-registration source must be acknowledged)

The no-registration data sources of this skill are **freely published** by their institutions; please acknowledge them in the corresponding format when using the results (papers/reports/presentations):

- **Esri Land Cover (Sentinel-2 10m annual, 2017-2025)**: produced by Esri, Impact Observatory, and Microsoft from Sentinel-2 imagery on Microsoft's Planetary Computer; license CC BY 4.0. Acknowledge: "Land cover data by Esri, Impact Observatory, and Microsoft".
- **ESA WorldCover (10m, 2020/2021)**: published by ESA; license CC BY 4.0. Acknowledge: "© ESA WorldCover project / Contains modified Copernicus Sentinel data".
- **ESA CCI Land Cover (300m)**: ESA Climate Change Initiative (ESA CCI); cite per the ESA CCI citation format.
- **Dynamic World (10m)**: Google and World Resources Institute; distributed via Planetary Computer; license CC BY 4.0.

## General statement

- The latest statements of each data provider prevail; this document lists only the currently known terms.
- Users should verify the applicability of the above licenses for their intended use when using/distributing model outputs.
- This skill is a research tool; for commercial use, obtain commercial authorization from the respective data providers first.
