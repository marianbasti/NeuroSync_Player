import time
import numpy as np
from typing import List
import logging

from livelink.connect.livelink_init import create_socket_connection, FaceBlendShape

from livelink.animations.blending_anims import blend_in, blend_out  

logging.basicConfig(level=logging.INFO)

def pre_encode_facial_data(facial_data: List[np.ndarray], py_face, fps: int = 60) -> List[bytes]:
    try:
        logging.info("Starting pre-encoding of facial data")
        encoded_data = []

        blend_in_frames = int(0.05 * fps)
        blend_out_frames = int(0.3 * fps)

        logging.info(f"Blending in for {blend_in_frames} frames")
        blend_in(facial_data, fps, py_face, encoded_data, blend_in_frames)

        for frame_index, frame_data in enumerate(facial_data[blend_in_frames:-blend_out_frames]):
            for i in range(min(len(frame_data), 51)):  
                py_face.set_blendshape(FaceBlendShape(i), frame_data[i])
            encoded_data.append(py_face.encode())
            logging.debug(f"Encoded frame {frame_index + blend_in_frames}")

        logging.info(f"Blending out for {blend_out_frames} frames")
        blend_out(facial_data, fps, py_face, encoded_data, blend_out_frames)

        logging.info("Finished pre-encoding of facial data")
        return encoded_data

    except Exception as e:
        logging.error(f"An error occurred during pre-encoding: {e}")
        return []

def send_pre_encoded_data_to_unreal(encoded_facial_data: List[bytes], start_event, fps: int, socket_connection=None):
    try:
        own_socket = False
        if socket_connection is None:
            socket_connection = create_socket_connection()
            own_socket = True

        logging.info("Waiting for start event")
        start_event.wait()  # Wait until the event signals to start

        frame_duration = 1 / fps  # Time per frame in seconds
        start_time = time.time()  # Get the initial start time

        logging.info("Starting to send pre-encoded data to Unreal")
        for frame_index, frame_data in enumerate(encoded_facial_data):
            current_time = time.time()
            elapsed_time = current_time - start_time

            expected_time = frame_index * frame_duration  # Time the current frame should be sent

            # If we are behind schedule, skip the frame
            if elapsed_time < expected_time:
                time.sleep(expected_time - elapsed_time)  # Sleep only for the remaining time for this frame
            elif elapsed_time > expected_time + frame_duration:
                # We've fallen behind by more than one frame, so continue to realign
                logging.warning(f"Skipping frame {frame_index} due to delay")
                continue

            socket_connection.sendall(frame_data)  # Send the frame
            logging.debug(f"Sent frame {frame_index}")

        logging.info("Finished sending pre-encoded data to Unreal")

    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        if own_socket:
            socket_connection.close()
            logging.info("Socket connection closed")
