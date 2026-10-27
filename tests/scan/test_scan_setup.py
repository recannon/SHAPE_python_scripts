#Last modified by @recannon 08/04/2026
#Tests for functions within run_grid

# import pytest
# import shutil
# from pathlib import Path

# from pyshape.scan.run_grid import setup_grid_scan, create_polescan_lists

#===Tests===

# class TestPolescanSetup:
    
#     def test_no_duplicated_pole_values(self):
#         '''Tests that only one value is every generated at poles
#         (Saves computing power for identical solutions)'''
#         bet_arr,_ = create_polescan_lists(-90,90,45,0,360,180)
#         assert sum(bet_arr==-90) == 1
#         assert sum(bet_arr==90) == 1
        
#     def test_no_duplicated_lambda_values(self):
#         '''Tests that no duplicated lambda values are generated
#         lam=0 and lam=360 are the same.'''
#         bet_arr,lam_arr = create_polescan_lists(-90,90,45,0,360,180)
#         assert len(lam_arr[bet_arr==0]) == 2
        
# class TestValidation:
    
    # def test_
        # with pytest.raises(SystemExit):
    