# Importing necessary libraries
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.svm import SVR
from sklearn.metrics import r2_score
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
import joblib

# Loading data from an Excel file
df = pd.read_excel('query.xlsx')

# Data Preparation: Creating a feature matrix X and target vector y using past 5 temperature readings to predict the next one
X = []
y = []
for i in range(5, len(df)):
    X.append(df['Temperature'].iloc[i-5:i].values)  # Collecting a sliding window of the last 5 temperatures
    y.append(df['Temperature'].iloc[i])  # Collecting the current temperature to be predicted
X = np.array(X)  # Converting list to NumPy array for better handling in machine learning models
y = np.array(y)

# Splitting the dataset into training and testing sets with an 80:20 ratio
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Model Training: Using a Support Vector Machine with a linear kernel
svm_model = SVR(kernel='linear')
svm_model.fit(X_train, y_train)  # Training the model on the training data

# Model Evaluation: Making predictions on the test set
y_pred = svm_model.predict(X_test)

# Calculate and print performance metrics: Mean Absolute Error, Root Mean Squared Error, and R-squared
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r_squared = r2_score(y_test, y_pred)
print("Mean Absolute Error (MAE):", mae)
print("Root Mean Squared Error (RMSE):", rmse)
print("R-squared:", r_squared)

# Exporting the trained model and its columns for deployment or further use
svm_model_columns = list(X_train)  # Extracting the column names from the training set
print(svm_model_columns)
joblib.dump(svm_model_columns, 'svm_model_columns.pkl')  # Saving the column names to a file
joblib.dump(svm_model, 'svm_model.pkl')  # Saving the trained model to a file
print('Model dumped')
