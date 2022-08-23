# extractor-coco
The extractor runs on a folder of images that contains, in the same directory, a COCO JSON formatted annotation file. The extractor-coco displays the images overlaid with COCO JSON formated annotations. This function is suitable when examining the existing annotations, correcting annotation issues, for previewing the data stored on a server. The bounding box type of annotations are currently supported. 

COCO JSON format was selected because it is a common format for object detection tasks and also suitable for converting from and to other formats, e.g. https://roboflow.com/formats/coco-json 

### Modifying color and thickness of the bounding box
The color and thickness of the bounding box line can be modified by changing the parameter ... 
