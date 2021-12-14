from flask import Flask
from flask_restx import Api, Resource
from werkzeug.datastructures import FileStorage
from PIL import Image
from io import BytesIO
import base64
from flask_cors import CORS, cross_origin


from model import yolov5
app = Flask(__name__)
api = Api(app)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

upload_parser = api.parser()
upload_parser.add_argument('file', 
                           location='files',
                           type=FileStorage)


@api.route('/upload/')
@api.expect(upload_parser)
class UploadDemo(Resource):
    def post(self):
        args = upload_parser.parse_args()
        file = args.get('file')
        bytes = file.read()
        classes, converted_img = yolov5.yolov5(Image.open(BytesIO(bytes)).convert("RGB"))
        bytes_io = BytesIO()
        converted_img.save(bytes_io, format="PNG")
        result = {
            'prediction': classes,
            'image':  base64.b64encode(bytes_io.getvalue()).decode("utf-8")
         }
        return result


webcam_parser = api.parser()
webcam_parser.add_argument('webcam', 
                           type=str)
@api.route('/webcam/')
@api.expect(webcam_parser)
class UploadDemo(Resource):
    @api.expect(webcam_parser)
    @api.doc(responses={"response": 'json'})
    def post(self):
        args = webcam_parser.parse_args()
        b = args["webcam"]
        # b=b.replace('/', '%2F')
        print(b)
        dec = base64.b64decode(b + "===")
        classes, converted_img = yolov5.yolov5(Image.open(BytesIO(dec)).convert("RGB"))
        bytes_io = BytesIO()
        converted_img.save(bytes_io, format="PNG")
        result = {
            'prediction': classes,
            'image': base64.b64encode(bytes_io.getvalue()).decode("utf-8")
        }
        print(result)
     

        def image_to_byte_array(image):
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format="PNG")
                img_byte_arr = img_byte_arr.getvalue()
                ret = base64.b64encode(img_byte_arr).decode("utf-8")
                return ret
        # return result
        return image_to_byte_array(converted_img)
       
if __name__ == '__main__':
    app.run()    