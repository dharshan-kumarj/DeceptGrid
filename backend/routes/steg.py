"""
Steganography Routes for DeceptGrid API
Handles image encoding and decoding using LSB steganography.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import Response
from pathlib import Path
import tempfile
import os
from typing import Optional

from models.request_models import (
    StegDecodeResponse,
    StegErrorResponse,
    ErrorResponse,
    validate_image_file
)
from utils.steganography import LSBSteganography

router = APIRouter()


@router.post("/encode",
            response_class=Response,
            summary="Hide message in image",
            description="Encode a text message into an image using LSB steganography")
async def encode_message(
    image: UploadFile = File(..., description="Image file to encode message into"),
    alert_message: str = Form(..., description="Text message to hide in the image")
):
    """
    Hide a text message in an image using LSB steganography.

    Returns the encoded image as a downloadable PNG file.
    """
    temp_file = None

    try:
        # Validate image file
        is_valid, error_msg = validate_image_file(
            image.content_type or "unknown",
            image.size or 0
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Read image data
        image_data = await image.read()

        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image file"
            )

        # Validate message length
        if not alert_message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )

        # Check if message fits in image
        max_capacity = LSBSteganography.get_max_capacity(image_data)
        if len(alert_message) > max_capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message too long. Maximum capacity: {max_capacity} characters, "
                      f"message length: {len(alert_message)} characters"
            )

        # Encode message into image
        try:
            encoded_image_data = LSBSteganography.encode_message(image_data, alert_message)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Encoding failed: {str(e)}"
            )

        # Generate filename for encoded image
        original_name = Path(image.filename or "image").stem
        encoded_filename = f"{original_name}_encoded.png"

        # Return encoded image as file response
        return Response(
            content=encoded_image_data,
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename={encoded_filename}",
                "Content-Length": str(len(encoded_image_data))
            }
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during encoding: {str(e)}"
        )

    finally:
        # Clean up temporary file if created
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except Exception:
                pass


@router.post("/decode",
            response_model=StegDecodeResponse,
            responses={
                400: {"model": ErrorResponse, "description": "Invalid image file"},
                404: {"model": ErrorResponse, "description": "No hidden message found"},
                500: {"model": ErrorResponse, "description": "Decoding failed"}
            },
            summary="Extract message from image",
            description="Decode a hidden text message from an image using LSB steganography")
async def decode_message(
    image: UploadFile = File(..., description="Encoded image file to extract message from")
):
    """
    Extract a hidden text message from an image using LSB steganography.

    Returns the decoded message as JSON.
    """
    try:
        # Validate image file
        is_valid, error_msg = validate_image_file(
            image.content_type or "unknown",
            image.size or 0
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Read image data
        image_data = await image.read()

        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image file"
            )

        # Decode message from image
        try:
            decoded_message = LSBSteganography.decode_message(image_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Decoding failed: {str(e)}"
            )

        # Check if message was found
        if decoded_message is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No hidden message found in image"
            )

        return StegDecodeResponse(message=decoded_message)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during decoding: {str(e)}"
        )


@router.get("/capacity",
           summary="Check image capacity",
           description="Calculate maximum message capacity for an image")
async def check_capacity(
    image: UploadFile = File(..., description="Image file to check capacity for")
):
    """
    Calculate the maximum number of characters that can be hidden in an image.
    """
    try:
        # Validate image file
        is_valid, error_msg = validate_image_file(
            image.content_type or "unknown",
            image.size or 0
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Read image data
        image_data = await image.read()

        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image file"
            )

        # Calculate capacity
        max_capacity = LSBSteganography.get_max_capacity(image_data)

        return {
            "max_capacity_characters": max_capacity,
            "max_capacity_words": max_capacity // 5,  # Rough estimate
            "image_filename": image.filename
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking capacity: {str(e)}"
        )