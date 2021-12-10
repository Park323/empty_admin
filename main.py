import argparse
import yaml
import requests
import json
import cv2
from coordinates_generator import CoordinatesGenerator
from colors import *

#python main.py --image images/parking_lot_1.png --data data/coordinates_1.yml
#python main.py --url URL주소

def main():
    args = parse_args()
    on_server = args.url!=None
    if on_server : #Get image from server
        URL = args.url
        image, annos = get_data(URL)
    else: #Testing
        image_file = args.image_file
        data_file = args.data_file
        
        image = cv2.imread(image_file).copy()
        with open(data_file, "r") as f:
            yml = yaml.load(f, Loader=yaml.FullLoader)
        annos = [obj['coordinates'] for obj in yml]

    if image is not None:
        with open(data_file, "w+") as f:
            generator = CoordinatesGenerator(image, f, annos, COLOR_RED)
            data = generator.generate(on_server)
            
    if on_server:
        post_data(data, URL)


def parse_args():
    parser = argparse.ArgumentParser(description='Generates Coordinates File')

    parser.add_argument("--image",
                        dest="image_file",
                        required=False,
                        help="Image file to generate coordinates on")

    parser.add_argument("--data",
                        dest="data_file",
                        required=False,
                        help="Data file to be used with OpenCV")
    
    parser.add_argument("--url",
                        dest="url",
                        required=False,
                        help="Server URL")
    
    return parser.parse_args()

def get_data(URL):
    import requests
     
    response = requests.get(URL) 
    if response.status_code == 200:
        data = response.json # 아래 데이터를 dictionary 형태로 받을 수 있습니다.

    pred_boxes = data["pred_boxes"]
    image = decode_base64(data["image"])
    
    return image, pred_boxes

def post_data(data, URL):
    URL = URL + '/set'
    headers = {'Content-type': 'application/json'}
    response = requests.post(URL, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
	    print("send complete") 

def decode_base64(data):
    import base64
    import numpy as np
    import cv2
    # base64string -> base64Image
    imageStr = base64.b64decode(data)
    nparr = np.fromstring(imageStr, np.uint8)
    base64Image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return base64Image

if __name__ == '__main__':
    main()
