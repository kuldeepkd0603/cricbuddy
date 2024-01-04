import joblib
import os

# Define the filename
#filename = 'C:\IPLFreak-master\iplfreak\first-innings-score-lr-model.joblib'

# Load the data from the file
loaded_data = joblib.load('C:\IPLFreak-master\iplfreak\first-innings-score-lr-model.joblib')

print(loaded_data)
