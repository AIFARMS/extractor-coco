# extractor-coco
The extractor runs on a folder of images that also contains, in the same directory, a COCO JSON formatted annotation file. The extractor-coco displays the images overlaid with COCO JSON formated annotations. This function is suitable when examining the existing annotations, correcting annotation issues, for previewing and displaying the data that is stored on a server. Currently, the bounding box annotations are supported. COCO JSON was chosen because it is a common format for object detection tasks and also suitable for converting from and to other formats, e.g. https://roboflow.com/formats/coco-json 
### Modifying the color of annotations
The color of the annotations and the thickness of the line can be modified by changing the parameter ... 
