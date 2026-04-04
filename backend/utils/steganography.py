"""
LSB Steganography Implementation for DeceptGrid
Hides and extracts text messages from images using Least Significant Bit technique.
"""

from PIL import Image
import io
from typing import Optional


class LSBSteganography:
    """LSB Steganography class for hiding and extracting text from images."""

    # Message delimiter to mark end of hidden message
    DELIMITER = "1111111111111110"

    @staticmethod
    def text_to_binary(text: str) -> str:
        """Convert text to binary string."""
        return ''.join(format(ord(char), '08b') for char in text)

    @staticmethod
    def binary_to_text(binary: str) -> str:
        """Convert binary string to text."""
        text = ''
        for i in range(0, len(binary), 8):
            byte = binary[i:i+8]
            if len(byte) == 8:
                text += chr(int(byte, 2))
        return text

    @staticmethod
    def modify_pixel(pixel_value: int, bit: str) -> int:
        """Modify the least significant bit of a pixel value."""
        # Clear the LSB and set it to the new bit
        return (pixel_value & 0xFE) | int(bit)

    @staticmethod
    def encode_message(image_bytes: bytes, message: str) -> bytes:
        """
        Hide a text message in an image using LSB steganography.

        Args:
            image_bytes: Input image as bytes
            message: Text message to hide

        Returns:
            Encoded image as bytes

        Raises:
            ValueError: If message is too long for the image
        """
        # Load image from bytes
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if not already (handles different formats)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Convert message to binary and add delimiter
        binary_message = LSBSteganography.text_to_binary(message) + LSBSteganography.DELIMITER

        # Calculate maximum capacity (3 color channels per pixel)
        max_capacity = image.width * image.height * 3

        if len(binary_message) > max_capacity:
            raise ValueError(
                f"Message too long. Maximum capacity: {max_capacity // 8} characters, "
                f"message length: {len(message)} characters"
            )

        # Convert image to list for easier manipulation
        pixels = list(image.getdata())

        # Hide message bits in pixel LSBs
        bit_index = 0
        modified_pixels = []

        for pixel in pixels:
            if bit_index < len(binary_message):
                # Modify each RGB channel
                r, g, b = pixel

                # Modify red channel
                if bit_index < len(binary_message):
                    r = LSBSteganography.modify_pixel(r, binary_message[bit_index])
                    bit_index += 1

                # Modify green channel
                if bit_index < len(binary_message):
                    g = LSBSteganography.modify_pixel(g, binary_message[bit_index])
                    bit_index += 1

                # Modify blue channel
                if bit_index < len(binary_message):
                    b = LSBSteganography.modify_pixel(b, binary_message[bit_index])
                    bit_index += 1

                modified_pixels.append((r, g, b))
            else:
                # No more message bits, keep original pixel
                modified_pixels.append(pixel)

        # Create new image with modified pixels
        encoded_image = Image.new('RGB', image.size)
        encoded_image.putdata(modified_pixels)

        # Convert back to bytes (PNG format for lossless compression)
        output_buffer = io.BytesIO()
        encoded_image.save(output_buffer, format='PNG')
        output_buffer.seek(0)

        return output_buffer.getvalue()

    @staticmethod
    def decode_message(image_bytes: bytes) -> Optional[str]:
        """
        Extract hidden message from an image using LSB steganography.

        Args:
            image_bytes: Encoded image as bytes

        Returns:
            Decoded message text, or None if no message found
        """
        try:
            # Load image from bytes
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if not already
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Extract LSBs from all pixels
            pixels = list(image.getdata())
            all_bits = []
            for pixel in pixels:
                for channel_value in pixel:
                    all_bits.append(str(channel_value & 1))

            # Join all bits into one string for search
            full_bit_str = "".join(all_bits)
            
            # Find the first occurrence of the delimiter
            delim_index = full_bit_str.find(LSBSteganography.DELIMITER)
            
            if delim_index != -1:
                # Extract message bits before the delimiter
                message_bits = full_bit_str[:delim_index]
                return LSBSteganography.binary_to_text(message_bits)

            # If we reach here, no delimiter was found
            return None

        except Exception:
            # If any error occurs during decoding, return None
            return None

    @staticmethod
    def get_max_capacity(image_bytes: bytes) -> int:
        """
        Calculate maximum text capacity for an image.

        Args:
            image_bytes: Input image as bytes

        Returns:
            Maximum number of characters that can be hidden
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # 3 bits per pixel (RGB), 8 bits per character, minus delimiter length
            max_bits = (image.width * image.height * 3) - len(LSBSteganography.DELIMITER)
            return max_bits // 8
        except Exception:
            return 0