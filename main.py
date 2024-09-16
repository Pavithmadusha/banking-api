from typing import Union

from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import face_recognition
from PIL import Image
import cv2
import io
import numpy as np
import mysql.connector
from mysql.connector import Error
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure MySQL connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='banking_db',
            user='root',
            password=''
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/register_face/")
async def register_face(userId: str = Form(...), file: UploadFile = File(...)):
    try:
        # Read the image file
        image_data = await file.read()
        print('done')
        # Convert image data to a PIL Image
        image = Image.open(io.BytesIO(image_data))
        image_array = np.array(image)
        
        rgb_small_frame = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        if not face_encodings:
            raise HTTPException(status_code=400, detail="No face found in the image")
        
        # Serialize encoding to binary format
        face_encoding_binary = face_encodings[0].tobytes()

        # Store in MySQL
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO faces (userId, encoding) VALUES (%s, %s)", (userId, face_encoding_binary))
        connection.commit()
        cursor.close()
        connection.close()
        return {"message": "Face registered successfully"}
    
    except Exception as e:
        # Log the exception for debugging
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@app.post("/authenticate/")
async def authenticate(file: UploadFile = File(...)):
    try:
        # Load the image file
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        image_array = np.array(image)
        
        rgb_small_frame = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        unknown_face_encoding = face_recognition.face_encodings(rgb_small_frame, face_locations)

        if len(unknown_face_encoding) == 0:
            raise HTTPException(status_code=400, detail="No face found in the image")
        
        # Retrieve all stored encodings from MySQL
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT userId, encoding FROM faces")
        stored_faces = cursor.fetchall()
        cursor.close()
        connection.close()

        known_faces = []
        known_face_userIds = []

        for userId, encoding in stored_faces:
            # Deserialize encoding
            encoding_np = np.frombuffer(encoding, dtype=np.float64)
            known_faces.append(encoding_np)
            known_face_userIds.append(userId)

        # Compare with known faces
        matches = face_recognition.compare_faces(known_faces, unknown_face_encoding[0])

        if True in matches:
            matched_userId = known_face_userIds[matches.index(True)]
            return {"authenticated_as": matched_userId}
        else:
            return {"authenticated_as": "Unknown"}

    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))