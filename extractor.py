#!/usr/bin/env python

import logging
from re import U
import tempfile
import os
import json

from pyclowder.extractors import Extractor
from pyclowder.utils import CheckMessage
from pyclowder.utils import StatusMessage
import pyclowder.files
import pyclowder.datasets

import cv2
import webcolors

# This class prepares and runs the coco extractor code in the Clowder environment
class CocoAnnotation(Extractor):

    def __init__(self):
        Extractor.__init__(self)

        # parse command line and load default logging configuration
        self.setup()

        # setup logging for the exctractor
        self.logger = logging.getLogger('__main__')
        self.logger.setLevel(logging.DEBUG)
        logging.getLogger('pyclowder').setLevel(logging.INFO)
        logging.getLogger('pika').setLevel(logging.INFO)

    # Overidden method that checks if we want to process a message, or not
    def check_message(self, connector, host, secret_key, resource, parameters):
        if resource['triggering_file'] is None or resource['triggering_file'].lower().endswith('.coco.json'):
            return CheckMessage.download
        return CheckMessage.ignore

    # Overridden method that performs the processing on the message
    # Prepares the environment for Open Drone Map by linking to image files and
    # checking settings for overrides. Also uploads the results of the run
    def process_message(self, connector, host, secret_key, resource, parameters):
        if not parameters.get("parameters", ""):
            user_params = {}
        else:
            user_params = json.loads(parameters["parameters"])
        rgb = webcolors.name_to_rgb(user_params.get("color", "purple"))
        width = int(user_params.get("width", "5"))

        annotation_file = None
        for localfile in resource['local_paths']:
            if localfile.lower().endswith('.coco.json'):
                annotation_file = localfile
        self.logger.debug(f"Annotation file {annotation_file}")
        if not annotation_file:
            connector.status_update(StatusMessage.processing, resource, "Could not find coco.json file.")
            return

        # load the annotations
        with open(annotation_file, "r") as jsonFile:
            data = json.load(jsonFile)

        # add metadata to dataset
        content = data.get('info', []).copy()
        content['licenses'] = [x['name'] for x in data.get('licenses', []) if 'name' in x]
        metadata = self.get_metadata(content, resource['type'], resource['id'], host)
        pyclowder.datasets.upload_metadata(connector, host, secret_key, resource['id'], metadata)

        # loop through all images
        for image in data["images"]:
            # find all annotations
            annotations = [a for a in data["annotations"] if a['image_id'] == image['id']]

            # find image in clowder
            clowder_image = next((x for x in resource['files'] if x['filename'] == image['file_name']), None)
            local_image = next((x for x in resource['local_paths'] if x.endswith(image['file_name'])), None)
            if annotations and clowder_image and local_image:
                img = cv2.imread(local_image)

                for a in annotations:
                    x = int(a['bbox'][0])
                    y = int(a['bbox'][1])
                    w = int(a['bbox'][2])
                    h = int(a['bbox'][3])
                    #add a rectangle to the image based on the bounding box coordinates
                    img = cv2.rectangle(img,(x,y),(x+w,y+h), rgb, width)
                    #write the images with annotations overlaid to the created folder

                handle, outfile = tempfile.mkstemp(suffix=".jpg")
                try:
                    os.close(handle)
                    cv2.imwrite(outfile, img)
                    pyclowder.files.upload_preview(connector, host, secret_key, clowder_image['id'], outfile)
                finally:
                    os.unlink(outfile)


if __name__ == "__main__":
    extractor = CocoAnnotation()
    extractor.start()
