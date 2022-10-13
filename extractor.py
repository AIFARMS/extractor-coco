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

    @staticmethod
    def image_resize(image, width = None, height = None, inter = cv2.INTER_AREA):
        # initialize the dimensions of the image to be resized and
        # grab the image size
        dim = None
        (h, w) = image.shape[:2]

        # if both the width and height are None, then return the
        # original image
        if width is None and height is None:
            return image

        # check to see if the width is None
        if width is None:
            # calculate the ratio of the height and construct the
            # dimensions
            r = height / float(h)
            if r >= 1:
                return image
            dim = (int(w * r), height)

        # otherwise, the height is None
        else:
            # calculate the ratio of the width and construct the
            # dimensions
            r = width / float(w)
            if r >= 1:
                return image
            dim = (width, int(h * r))

        # resize the image
        resized = cv2.resize(image, dim, interpolation = inter)

        # return the resized image
        return resized

    # Overridden method that performs the processing on the message
    # Prepares the environment for Open Drone Map by linking to image files and
    # checking settings for overrides. Also uploads the results of the run
    def process_message(self, connector, host, secret_key, resource, parameters):
        if not parameters.get("parameters", ""):
            user_params = {}
        else:
            user_params = json.loads(parameters["parameters"])
        color = user_params.get("color", "#8b008b")
        try:
            if color.startswith("#"):\
                rgb = webcolors.hex_to_rgb(color)
            else:
                rgb = webcolors.name_to_rgb(color)
        except ValueError:
            rgb = webcolors.hex_to_rgb("#8b008b")
        width = int(user_params.get("width", "5"))

        annotation_files = []
        for localfile in resource['local_paths']:
            if localfile.lower().endswith('.coco.json'):
                annotation_files.append(localfile)
        self.logger.debug(f"Annotation file {','.join(annotation_files)}")
        if not annotation_files:
            connector.status_update(StatusMessage.processing, resource, "Could not find coco.json file.")
            return

        # load the annotations
        for annotation_file in annotation_files:
            with open(annotation_file, "r") as jsonFile:
                data = json.load(jsonFile)

            # add metadata to dataset
            content = data.get('info', []).copy()
            content['filename'] = annotation_file
            content['licenses'] = [x['name'] for x in data.get('licenses', []) if 'name' in x]
            content['annotations'] = len(data["annotations"])
            content['images'] = len(data["images"])
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

                    # write preview
                    handle, outfile = tempfile.mkstemp(suffix=".jpg")
                    try:
                        os.close(handle)

                        cv2.imwrite(outfile, self.image_resize(img, width=800))
                        previewid = pyclowder.files.upload_preview(connector, host, secret_key, clowder_image['id'], outfile)

                        url = '%sapi/previews/%s/title?key=%s' % (host, previewid, secret_key)
                        headers = {'Content-Type': 'application/json'}
                        connector.post(url, headers=headers, data=json.dumps({"title": "coco"}),
                                       verify=connector.ssl_verify if connector else True)

                        cv2.imwrite(outfile, self.image_resize(img, width=225))
                        pyclowder.files.upload_thumbnail(connector, host, secret_key, clowder_image['id'], outfile)
                    finally:
                        os.unlink(outfile)


if __name__ == "__main__":
    extractor = CocoAnnotation()
    extractor.start()
