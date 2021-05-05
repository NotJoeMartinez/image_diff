import os, sys, random, pathlib, re
import PIL
import numpy as np
import datetime as dt
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import subprocess
import pandas as pd 
import datetime as dt
from PIL import Image, ImageOps

subprocess.run("find . -name '.DS_Store' -type f -delete", shell=True)
test_data_path = "datasets/testing/"
class_names = ['Broken Wire', 'Glue', 'Good', 'No Wires', 'One Third Wire', 'Two Third Wires', 'Unknown Debris']

def main(make_notes=True, class_names=class_names, test_data_path=test_data_path):

  most_recent_model = find_most_recent('models') # finds most recent model
  model = keras.models.load_model(f"models/{most_recent_model}") # loads most recent model
  
  model.summary()

  # for confusion matrix
  tested_images = test_all_imgs(model, class_names, test_data_path) 
  df = pd.DataFrame(tested_images, columns = ['predicted','actual','confidence','path'])
  plot_confusion_matrix(df,fig_name=f"notes/imgs/{most_recent_model}", show=True)  

  if make_notes == True:
    make_md_notes(most_recent_model, model, df)



""""Makes a markdown summary in notes/{model_name.md}"""
def make_md_notes(model_name, model, df):
  import markdown
  from contextlib import redirect_stdout

  with open(f"notes/{model_name}.md", 'w') as f:
    f.write(f"## {model_name} \n")

    f.write(f"### Model Summary \n")
    f.write("```")
    with redirect_stdout(f):
        model.summary()
    f.write("``` \n") 

    f.write(f"### Confusion Matrix \n")
    f.write(f"![Confusion Matrix](imgs/{model_name}.png) \n")

    f.write(f"### Dataframe predictions \n")
    f.write("```")
    with redirect_stdout(f):
      print(df)
    f.write("```")



""" Finds and returns the most recent model in the models directory """ 
def find_most_recent(directory):
  now = dt.datetime.now()
  dir_list = os.listdir(directory)
  datetimes = []
  for x in dir_list:
    dir_dt = dt.datetime.strptime(x, '%m_%d_%I:%M:%S%p')
    datetimes.append(dir_dt)

  most_recent = max(dt for dt in datetimes if dt < now)
  mr = most_recent.strftime("%m_%d_%-I:%M:%S%p")
  print(mr)
  return mr



""" Plots a confusion matrix and saves it to notes/imgs/{model_name.png}"""
def plot_confusion_matrix(df, fig_name="", show=False):
  import seaborn as sn
  fig, ax = plt.subplots(figsize=(20, 10))
  confusion_matrix = pd.crosstab(df['predicted'], df['actual'], rownames=['Predicted'], colnames=['Actual'])

  sn.heatmap(confusion_matrix, annot=True, ax=ax)
  plt.savefig(fig_name)

  if show == True:
    plt.show()


""" Plots prediction in a bar chart format with the red bar being the best guess"""
def plot_value_array(predictions_array, class_names):
  plt.grid(False)
  plt.xticks(range(7))
  plt.yticks([])
  thisplot = plt.bar(range(7), predictions_array, color="#777777")
  plt.ylim([0, 1])
  predicted_label = np.argmax(predictions_array)
  thisplot[predicted_label].set_color('red')



""" Plots the image in which the model is making predictions on and the percentage certanty """
def plot_image(predictions_array, class_names, img_array):
  plt.grid(False)
  plt.xticks([])
  plt.yticks([])
  plt.imshow(img_array, cmap=plt.cm.binary)
  predicted_label = np.argmax(predictions_array)
  plt.xlabel("{} {:2.0f}%".format(class_names[predicted_label],
                                100*np.max(predictions_array)))



  """
  Itterates through all test images, prints predictions, confidence levels 
  and wheather it actually  predicted it correctly it should return a pandas dataframe
  """
def test_all_imgs(model, class_names, test_data_path):

  rubric = {
  'broken_wire': 'Broken Wire', 
  'glue': 'Glue', 
  'good': 'Good', 
  'no_wires': 'No Wires', 
  'one_thirds_wires': 'One Third Wire', 
  'two_thirds_wire': 'Two Third Wires', 
  'unknown_debris': 'Unknown Debris'}
  
  pandas_data = []
  # makes list of test data paths
  data_paths = []
  for root, dirs, files in os.walk(test_data_path):
    for name in files:
      data_paths.append(os.path.join(root, name))

  # Makes preditctions of every image in the data paths list
  
  for count, img_path in enumerate(data_paths):
    temp_data = []
    size = (456, 456)
    data = np.ndarray(shape=(1, 456, 456, 3), dtype=np.float32)
    image = Image.open(img_path)
    image = ImageOps.fit(image, size, Image.ANTIALIAS)
    image_array = np.asarray(image)
    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
    data[0] = normalized_image_array
    prediction = model.predict(data)
    label_prediction = np.argmax(prediction[0])
    
    # find test image path parent
    test_file_name = re.findall("\/.*\/(.*\.jpg)", img_path)
    # print("test file name: ", test_file_name)
    parent_dir = re.findall("\/.*\/(.*)\/.*\/*.jpg", img_path)
    # print("Parent Dir: ",parent_dir)

    # find the parent directory applying it to the rubric then get the index of the class name
    prediction_truth_index = class_names.index(rubric[parent_dir[0]])
    prediction_truth = class_names[prediction_truth_index]
    temp_data.append(class_names[label_prediction]) 
    temp_data.append(prediction_truth) 
    # temp_data.append(100 * np.max(prediction[0])) 
    temp_data.append(np.max(prediction[0])) 
    temp_data.append(f"{parent_dir[0]}/{test_file_name[0]}")

    pandas_data.append(temp_data)
  
  return pandas_data 



""" Builds the plot with images of random images and one image of a broken wire """
def random_test_plot(model, class_names, test_data_path):
    data_paths = []
    for root, dirs, files in os.walk(test_data_path):
        for name in files:
            data_paths.append(os.path.join(root, name))

    random_test_images = random.choices(data_paths, k=6)
    num_rows = 3
    num_cols = 3
    num_images = num_rows*num_cols
    size = (456, 456)
    plt.figure(figsize=(2*2*num_cols, 2*num_rows))
    for i, img_path in enumerate(random_test_images):
        data = np.ndarray(shape=(1, 456, 456, 3), dtype=np.float32)
        image = Image.open(img_path)
        image = ImageOps.fit(image, size, Image.ANTIALIAS)
        image_array = np.asarray(image)
        normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
        data[0] = normalized_image_array
        prediction = model.predict(data)

        plt.subplot(num_rows, 2*num_cols, 2*i+1)
        plot_image(prediction[0], class_names, image_array)
        plt.subplot(num_rows, 2*num_cols, 2*i+2)
        plot_value_array(prediction[0], class_names)
        _ = plt.xticks(range(7), class_names, rotation=90)

    plt.tight_layout()
    plt.show()



if __name__ == '__main__':
    main()
    sys.exit(0)