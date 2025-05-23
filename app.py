
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, ClientSettings
import av
import cv2
import boto3
import uuid
import json
import tempfile
import traceback

# AWS setup
AWS_ID = st.secrets["aws"]["aws_access_key_id"]
AWS_SECRET = st.secrets["aws"]["aws_secret_access_key"]
REGION = st.secrets["aws"]["region_name"]
BUCKET = st.secrets["aws"]["s3_bucket"]
LAMBDA_NAME = st.secrets["aws"]["lambda_name"]

session = boto3.Session(
    aws_access_key_id=AWS_ID,
    aws_secret_access_key=AWS_SECRET,
    region_name=REGION
)
s3 = session.client("s3")
lambda_client = session.client("lambda")

st.set_page_config(page_title="Auto Emotion Detection", layout="centered")
st.title("Live Emotion Detector")

user_id = st.text_input("Enter your user ID (required)", value="anonymous")

FRAME_CAPTURED = st.empty()
RESULT = st.empty()

class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame_count = 0

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1

        if self.frame_count % 100 == 0 and user_id:
            FRAME_CAPTURED.info("Image captured")
            filename = f"{uuid.uuid4()}.jpg"
            _, buffer = cv2.imencode('.jpg', img)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmpfile:
                tmpfile.write(buffer.tobytes())
                tmpfile.flush()
                with open(tmpfile.name, "rb") as f:
                    s3.upload_fileobj(f, BUCKET, filename)

            payload = {"bucket": BUCKET, "image": filename, "user_id": user_id}

            try:
                response = lambda_client.invoke(
                    FunctionName=LAMBDA_NAME,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload),
                )

                result = json.load(response["Payload"])

                if response["StatusCode"] == 200:
                    data = json.loads(result.get("body", "{}"))
                    if data:
                        top = data[0]
                        emotion = top['TopEmotion']
                        conf = top['Confidence']
                        RESULT.success(f"{emotion} ({conf}%)")
                    else:
                        RESULT.warning("No face detected.")
                else:
                    RESULT.error(f"Lambda Error: {result.get('errorMessage', 'Unknown')}")
            except Exception as e:
                st.error("Exception while invoking Lambda:")
                st.code(traceback.format_exc())

        return av.VideoFrame.from_ndarray(img, format="bgr24")

webrtc_streamer(
    key="emotion",
    video_processor_factory=VideoProcessor,
    client_settings=ClientSettings(
        media_stream_constraints={"video": True, "audio": False},
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    )
)
