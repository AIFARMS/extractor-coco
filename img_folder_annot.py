import cv2
import time 
import json
import os
import shutil
import sys, getopt
import numpy as np
import argparse

def get_args_parser(add_help=True):
   import argparse
   
   parser = argparse.ArgumentParser(description='Process command line arguments.')
   #parser.add_argument("-p", '--path', dest="imagedirpath", required =True, help='add path to image directory')
   #the path to the json file containing coco formatted annotations should be added as an argument when running the program
   parser.add_argument("-i", "--input", dest="annofile", required=True,  help="annotation file")
   #name of the folder that will contain annotated images 
   return parser

#open up the json file containing coco formatted annotations and extracts annotations and image list sections
def process_annofile(annofile):
   with open(args.annofile, "r") as jsonFile:
        data = json.load(jsonFile)
   annotations = data["annotations"]
   img_list = data["images"]
   return annotations, img_list

#creates an image dictionary based on the image list extracted in the earlier step and associates image id with the image file name
def create_img_dic(img_list):
   img_dic = {}
   for img in img_list:
       img_dic[img['id']] = img['file_name']
   return img_dic

#creates a dictionary that associates image id with the bounding box coordinates from the annotation section
def create_img_map(img_dic, annotations):
   images_map = {}
   for img in img_dic.keys():
       bbox = []
       for ann in annotations:
           if img == ann['image_id']:
               bbox.append(ann['bbox'])
       imgid = img
       images_map[imgid] = {}
       images_map[imgid]['box'] = bbox
              
   print("len images map: ", len(images_map))
   
   return images_map

def main(args): 
  
  anno_folder = "annotated_images"

  #creates a folder to store annotated images
  if os.path.exists(anno_folder):
    shutil.rmtree(anno_folder)
  os.mkdir(anno_folder)
  
  #extracts annotations and image list from the json coco file 
  annotations, img_list = process_annofile(args.annofile)
 
  img_dic = create_img_dic(img_list)
  
  img_map = create_img_map(img_dic, annotations)
  
  #for each image and bounding box in the created image map
  for img, annos in img_map.items():
        file =str(img_dic[img])
        print("annotating:", file)
        #reads the image
        img = cv2.imread(file)
        #for each bounding box annotation
        for i in annos['box']:
            x = int(i[0])
            y = int(i[1])
            w = int(i[2])
            h = int(i[3])
            #add a rectangle to the image based on the bounding box coordinates
            img = cv2.rectangle(img,(x,y),(x+w,y+h), (139,0,139), 9)
            #write the images with annotations overlaid to the created folder
            cv2.imwrite(anno_folder + "/%s_annot.jpg" % file, img)
            #window_name = 'image'
            #cv2.imshow(window_name, img)
            #cv2.waitKey(0) 
            #cv2.destroyAllWindows() 

if __name__ == "__main__":
     args = get_args_parser().parse_args()
     main(args)