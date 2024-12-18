# This code is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
# For more details, visit: https://creativecommons.org/licenses/by-nc/4.0/

import os
import pygame
import logging
from threading import Thread

from livelink.connect.livelink_init import create_socket_connection, initialize_py_face
from livelink.animations.default_animation import default_animation_loop, stop_default_animation

from utils.neurosync_api_connect import send_audio_to_neurosync, read_audio_file_as_bytes
from utils.api_utils import save_generated_data_from_wav, initialize_directories
from utils.generated_utils import run_audio_animation

def process_wav_file(wav_file, py_face, socket_connection, default_animation_thread):
    """
    Processes the wav file by sending it to the API and running the animation.
    """
    logging.info(f"Processing file: {wav_file}")

    # Check if the file exists
    if not os.path.exists(wav_file):
        logging.error(f"File {wav_file} does not exist.")
        return

    # Read the wav file as bytes
    audio_bytes = read_audio_file_as_bytes(wav_file)
    
    if audio_bytes is None:
        logging.error(f"Failed to read {wav_file}")
        return

    logging.info(f"Successfully read {wav_file}")

    # Send the audio bytes to the API and get the blendshapes
    blendshapes = send_audio_to_neurosync(audio_bytes)
    
    if blendshapes is None:
        logging.error("Failed to get blendshapes from the API.")
        return

    logging.info("Successfully received blendshapes from the API")

    # Run the animation using the blendshapes data
    run_audio_animation(wav_file, blendshapes, py_face, socket_connection, default_animation_thread)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Initializing directories and resources")

    # Initialize directories and other resources
    initialize_directories()

    # Initialize py_face and the socket connection
    py_face = initialize_py_face()
    socket_connection = create_socket_connection()

    # Start the default animation thread
    default_animation_thread = Thread(target=default_animation_loop, args=(py_face,))
    default_animation_thread.start()
    logging.info("Default animation thread started")

    try:
        while True:
            wav_file = input("Enter the path to the .wav file (or 'q' to quit): ").strip()
            if wav_file.lower() == 'q':
                break

            # Process the wav file (send to API, run animation)
            process_wav_file(wav_file, py_face, socket_connection, default_animation_thread)

    finally:
        logging.info("Stopping default animation and cleaning up")
        # Stop the default animation when quitting
        stop_default_animation.set()
        if default_animation_thread:
            default_animation_thread.join()
        pygame.quit()
        socket_connection.close()
        logging.info("Cleanup complete")
