import os
import gdal


def main():
    inraster = []
    outraster = []
    for root, dirs, files in os.walk('C:/Users/nflue/Documents/Masterarbeit/02_Data/01_prep_raster'):
        for file in files:
            if file.endswith('.tif'):
                if '20201105_Sarine_ppk_2_GCP_dsm.tif' in file:
                    print(os.path.join(root,file))
                    inraster.append(os.path.join(root, file))
                    outraster.append(os.path.join(cwd, 'data', 'results', 'dsms', 'AF2020_dsm.tif'))
                if '20202008_Sarine_RGB_ppk_GCP02_dsm.tif' in file:
                    print(os.path.join(root,file))
                    inraster.append(os.path.join(root, file))
                    outraster.append(os.path.join(cwd, 'data', 'results', 'dsms', 'BF2020_dsm.tif'))
                if '20211014_Sarine_proc_dsm_mask.tif' in file:
                    print(os.path.join(root,file))
                    inraster.append(os.path.join(root, file))
                    outraster.append(os.path.join(cwd, 'data', 'results', 'dsms', 'AF2021_dsm.tif'))


    for inr, outr in zip(inraster,outraster):
        ds = gdal.Open(inr)

        gdal.Warp(outr, ds,
                  yRes = 0.1,
                  xRes = 0.1,
                  resampleAlg = "bilinear",
                  )

if __name__ == "__main__":
    main()