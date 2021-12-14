import io
import json
import base64
import uuid
import logging
import sys
import uvicorn
from typing import List
from PIL import Image
from io import BytesIO
from starlette.responses import Response
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

from model import yolov5 



# FastAPI
app = FastAPI(
    title="Serving YOLO",
    description="""Visit port 8088/docs for the FastAPI documentation.""",
    version="0.0.1",
)


class ConnectionManager:
    """Web socket connection manager."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


conn_mgr = ConnectionManager()


def base64_encode_img(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    buffered.seek(0)
    img_byte = buffered.getvalue()
    encoded_img = "data:image/png;base64," + base64.b64encode(img_byte).decode()
    return encoded_img


@app.get("/")
def home():
    return {"message": "YOLO - You Only Look Once"}


@app.post("/yolo")
def process_yolov5(file: UploadFile = File(...)):
    file_bytes = file.file.read()
    # print(file_bytes)
    image = Image.open(io.BytesIO(file_bytes))
    name = f"{str(uuid.uuid4())}.png"

    image.save(name)
    image.filename = name
    classes, converted_img = yolov5.yolov5(image)

    bytes_io = io.BytesIO()
    converted_img.save(name)
    converted_img.save(bytes_io, format="PNG")
    return Response(bytes_io.getvalue(), media_type="image/png")


@app.websocket("/yolo_ws/{client_id}")
async def process_yolov5_ws(websocket: WebSocket, client_id: int):
    await conn_mgr.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Convert to PIL image
            image = data[data.find(",") + 1 :]
            dec = base64.b64decode(image + "===")
            image = Image.open(BytesIO(dec)).convert("RGB")

            # Process the image
            name = f"/data/{str(uuid.uuid4())}.png"
            image.filename = name
            classes, converted_img = yolov5.yolov5(image)

            result = {
                "prediction": json.dumps(classes),
                "output": base64_encode_img(converted_img),
            }
            # logging.info("-----", json.dumps(result))

            # Send back the result
            await conn_mgr.send_message(json.dumps(result), websocket)

            # await conn_mgr.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        conn_mgr.disconnect(websocket)
        await conn_mgr.broadcast(f"Client #{client_id} left the chat")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8088, reload=True)