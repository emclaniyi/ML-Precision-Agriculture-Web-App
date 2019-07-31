# importing required libraries.
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, LinearSVC
from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix
import pickle

data = pd.read_csv('final_data.csv')

#mapping crop type
data['crop_type'].unique()
mapping = {'carrot': 1, 'coconut': 2, 'cotton': 3, 'groundnut': 4, 'melon': 5, 'millet': 6, 'potatoes': 7, 'rice': 8,
           'vegetable': 9, 'wheat': 10}
data['crop_type'] = data['crop_type'].map(mapping)

#mapping soil type
data['Soil_type'].unique()
mapping = {'clay': 1, 'Sandy': 2, 'loamy': 3}
data['Soil_type'] = data['Soil_type'].map(mapping)

X = data.drop('crop_type', axis=1).values
y = data.crop_type.values

# splitting data as X_train and X_test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2,random_state = 0)

# Feature Scaling
sc = StandardScaler()
X_train = sc.fit_transform(X_train)
X_test = sc.transform(X_test)

#Support Vector Machines


model = SVC(C=2.0, cache_size=200, class_weight=None, coef0=0.5, decision_function_shape='ovr', degree=3, gamma='auto_deprecated', kernel='rbf', max_iter=-1, probability=False, random_state= 50, shrinking=True, tol=0.11, verbose=False)
#model = SVC(kernel='linear', decision_function_shape='ovo', C = 0.02, gamma='scale', cache_size=200, coef0=0.0)
model.fit(X_train,y_train)

"""with open('crop_recommender.pkl', 'wb') as f:
    pickle.dump(model, f)

pickle_in = open('crop_recommender.pkl', 'rb')
clf = pickle.load(pickle_in)"""

prediction_svm=model.predict(X_test)
#print(accuracy_score(y_true, y_pred))
print(accuracy_score(y_test, prediction_svm))
cm = confusion_matrix(y_test, prediction_svm)
print(cm)