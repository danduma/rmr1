from data_processing.import_spreadsheets import index_mouse_images, load_cohort_data, load_death_data, load_grip_strength_data
import json
import os
from db_functions import create_database

create_database()

# Load the grip strength data
# load_grip_strength_data( "/Users/masterman/Downloads/LEVF/Behavioral Testing/Grip strength")

# load_cohort_data("/Users/masterman/Downloads/LEVF/Mouse MasterIndex__ NOT CURRENT - Weights.csv")

# load_death_data("/Users/masterman/Downloads/LEVF/Mouse Death Sheet _ CL 2024-10-02 STILL UPDATING FROM JUNE.xlsx")

mouse_images = index_mouse_images('/Users/masterman/Downloads/LEVF/Whole body pictures')
with open('mouse_images.json', 'w') as f:
    json.dump(mouse_images, f)
