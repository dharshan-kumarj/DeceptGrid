#!/usr/bin/env python3
"""
Test script for LSB Steganography functionality
Tests encoding and decoding without requiring FastAPI dependencies
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.steganography import LSBSteganography
from PIL import Image
import io

def create_test_image(width=100, height=100):
    """Create a simple test image for testing."""
    # Create a simple red image for testing
    image = Image.new('RGB', (width, height), (255, 0, 0))

    # Convert to bytes
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer.getvalue()

def test_steganography():
    """Test encode/decode functionality."""
    print("🧪 Testing LSB Steganography...")

    # Test message
    test_message = "DeceptGrid Attack Alert: False data injection detected!"

    try:
        # Create test image
        print("📸 Creating test image...")
        image_data = create_test_image(200, 200)

        # Test encoding
        print(f"🔒 Encoding message: '{test_message}'")
        encoded_data = LSBSteganography.encode_message(image_data, test_message)
        print(f"✓ Encoded successfully ({len(encoded_data)} bytes)")

        # Test decoding
        print("🔓 Decoding message...")
        decoded_message = LSBSteganography.decode_message(encoded_data)

        if decoded_message == test_message:
            print(f"✅ SUCCESS: Decoded correctly: '{decoded_message}'")
            return True
        else:
            print(f"❌ FAIL: Expected '{test_message}', got '{decoded_message}'")
            return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_capacity():
    """Test capacity calculation."""
    print("\n📏 Testing capacity calculation...")

    try:
        image_data = create_test_image(100, 100)
        capacity = LSBSteganography.get_max_capacity(image_data)
        expected = (100 * 100 * 3 - 16) // 8  # width * height * 3 channels - delimiter, / 8 bits per char

        print(f"Image capacity: {capacity} characters")
        print(f"Expected: {expected} characters")

        if capacity == expected:
            print("✅ Capacity calculation correct")
            return True
        else:
            print(f"❌ Capacity mismatch: expected {expected}, got {capacity}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_oversized_message():
    """Test handling of oversized messages."""
    print("\n⚠️ Testing oversized message handling...")

    try:
        # Create small image
        image_data = create_test_image(10, 10)

        # Create message that's too large
        large_message = "x" * 1000  # Way too large for 10x10 image

        try:
            LSBSteganography.encode_message(image_data, large_message)
            print("❌ FAIL: Should have raised error for oversized message")
            return False
        except ValueError as e:
            print(f"✅ SUCCESS: Correctly caught oversized message: {str(e)}")
            return True

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 DeceptGrid Steganography Test Suite")
    print("=" * 50)

    tests_passed = 0
    total_tests = 3

    if test_steganography():
        tests_passed += 1

    if test_capacity():
        tests_passed += 1

    if test_oversized_message():
        tests_passed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} passed")

    if tests_passed == total_tests:
        print("🎉 All tests passed! Steganography implementation is working correctly.")
        sys.exit(0)
    else:
        print("💥 Some tests failed. Check the implementation.")
        sys.exit(1)