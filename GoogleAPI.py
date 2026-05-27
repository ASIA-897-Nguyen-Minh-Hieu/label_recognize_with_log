#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import os
import re


# Imports the Google Cloud client library
from google.cloud import vision
from google.cloud import storage
from google.protobuf import json_format
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_fine_logo_result(picture_content):
    # WIP: if cannot recognize logo, crop pic into 4 and retry
    pass

def get_vision_result(picture_content):
    # Instantiates a client
    client = vision.ImageAnnotatorClient.from_service_account_json("Google-key.json")
    
    # Performs label detection on the image file
    response = client.annotate_image({
        'image': {'content': picture_content},
        'features': [
            {'type': vision.Feature.Type.TEXT_DETECTION},
            {'type': vision.Feature.Type.LOGO_DETECTION},
            {'type': vision.Feature.Type.LABEL_DETECTION}],
    })
    #logger.info(response)
    result = {
        "text": response.text_annotations[0].description,
        "labels": [],    # the possible kind of this product
        "logos": []
    }
    for label in response.label_annotations:
        result["labels"].append(label.description)
    for logo in response.logo_annotations:
        result["logos"].append(logo.description)
    return result



def get_vision_result_by_path(picture_path):
    # The name of the image file to annotate
    file_name = os.path.abspath(picture_path)

    # Loads the image into memory
    with io.open(file_name, 'rb') as image_file:
        content = image_file.read()

    return get_vision_result(content)

def get_vision_pdf_result(gcs_source_uri, gcs_destination_uri):
    mime_type = 'application/pdf'
    batch_size = 100
    # Instantiates a client
    client = vision.ImageAnnotatorClient.from_service_account_json("Google-key.json")
    feature = vision.types.Feature(
        type=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

    gcs_source = vision.types.GcsSource(uri=gcs_source_uri)
    input_config = vision.types.InputConfig(
        gcs_source=gcs_source, mime_type=mime_type)

    gcs_destination = vision.types.GcsDestination(uri=gcs_destination_uri)
    output_config = vision.types.OutputConfig(
        gcs_destination=gcs_destination, batch_size=batch_size)

    async_request = vision.types.AsyncAnnotateFileRequest(
        features=[feature], input_config=input_config,
        output_config=output_config)

    operation = client.async_batch_annotate_files(
        requests=[async_request])

    print('Waiting for the operation to finish.')
    operation.result(timeout=300)

    # Once the request has completed and the output has been
    # written to GCS, we can list all the output files.
    storage_client = storage.Client.from_service_account_json("Google-key.json")

    match = re.match(r'gs://([^/]+)/(.+)', gcs_destination_uri)
    bucket_name = match.group(1)
    prefix = match.group(2)

    bucket = storage_client.get_bucket(bucket_name)

    # List objects with the given prefix.
    blob_list = list(bucket.list_blobs(prefix=prefix))
    print('Output files:')
    for blob in blob_list:
        print(blob.name)

    # Process the first output file from GCS.
    # Since we specified batch_size=2, the first response contains
    # the first two pages of the input file.
    output = blob_list[0]

    json_string = output.download_as_string()
    response = json_format.Parse(
        json_string, vision.types.AnnotateFileResponse())

    # The actual response for the first page of the input file.
    first_page_response = response.responses[0]
    annotation = first_page_response.full_text_annotation

    # Here we print the full text from the first page.
    # The response contains more information:
    # annotation/pages/blocks/paragraphs/words/symbols
    # including confidence scores and bounding boxes
    print(u'Full text:\n{}'.format(
        annotation.text))



if __name__ == "__main__":
    # get_vision_result('Labels/4/4.jpg')gs://ou_label_recognize/20121217161019.pdf
    get_vision_pdf_result("gs://ou_label_recognize/20121217161019.pdf", "gs://ou_label_recognize/20121217161019.json")