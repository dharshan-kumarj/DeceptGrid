import React, { useState, useEffect } from 'react';
import { API, apiUpload } from '../../constants/api.ts';

/**
 * Steg.jsx - Engineer Steganography Panel
 * Person C - Steganography operations for engineers to hide/extract alert messages
 */

const Steg = () => {
  // State for encode section
  const [alertMessage, setAlertMessage] = useState('');
  const [encodeImageFile, setEncodeImageFile] = useState(null);
  const [encodedImageUrl, setEncodedImageUrl] = useState('');
  const [encodeLoading, setEncodeLoading] = useState(false);

  // State for decode section
  const [decodeImageFile, setDecodeImageFile] = useState(null);
  const [decodedMessage, setDecodedMessage] = useState('');
  const [decodeSuccess, setDecodeSuccess] = useState(false);
  const [decodeLoading, setDecodeLoading] = useState(false);

  // Error states
  const [encodeError, setEncodeError] = useState('');
  const [decodeError, setDecodeError] = useState('');

  // Load latest attack from logs on component mount
  useEffect(() => {
    loadLatestAttack();
  }, []);

  const loadLatestAttack = async () => {
    try {
      const response = await fetch(API.ATTACK_LOGS + '?limit=1');
      if (response.ok) {
        const data = await response.json();
        if (data.logs && data.logs.length > 0) {
          const latestAttack = data.logs[0];
          setAlertMessage(`SECURITY ALERT: ${latestAttack.type} detected from ${latestAttack.ip} targeting ${latestAttack.target}. Details: ${latestAttack.details}`);
        }
      }
    } catch (error) {
      // Fallback message if can't load from logs
      setAlertMessage('SECURITY ALERT: Suspicious activity detected on smart grid infrastructure. Immediate attention required.');
    }
  };

  const handleEncodeImageSelect = (e) => {
    const file = e.target.files[0];
    if (file && (file.type === 'image/jpeg' || file.type === 'image/png')) {
      setEncodeImageFile(file);
      setEncodeError('');
    } else {
      setEncodeError('Please select a valid JPG or PNG image file.');
      setEncodeImageFile(null);
    }
  };

  const handleDecodeImageSelect = (e) => {
    const file = e.target.files[0];
    if (file && (file.type === 'image/jpeg' || file.type === 'image/png')) {
      setDecodeImageFile(file);
      setDecodeError('');
    } else {
      setDecodeError('Please select a valid JPG or PNG image file.');
      setDecodeImageFile(null);
    }
  };

  const handleEncode = async () => {
    if (!encodeImageFile || !alertMessage.trim()) {
      setEncodeError('Please select an image and enter an alert message.');
      return;
    }

    setEncodeLoading(true);
    setEncodeError('');
    setEncodedImageUrl('');

    try {
      const formData = new FormData();
      formData.append('image', encodeImageFile);
      formData.append('alert_message', alertMessage.trim());

      const response = await apiUpload(API.STEG_ENCODE, formData);

      if (response.ok) {
        // Create download URL for the encoded image
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        setEncodedImageUrl(url);
      } else {
        const errorData = await response.json();
        setEncodeError(errorData.detail || 'Encoding failed. Please try with a different image.');
      }
    } catch (error) {
      setEncodeError('Network error. Please ensure the backend is running.');
    } finally {
      setEncodeLoading(false);
    }
  };

  const handleDecode = async () => {
    if (!decodeImageFile) {
      setDecodeError('Please select an image to decode.');
      return;
    }

    setDecodeLoading(true);
    setDecodeError('');
    setDecodedMessage('');
    setDecodeSuccess(false);

    try {
      const formData = new FormData();
      formData.append('image', decodeImageFile);

      const response = await apiUpload(API.STEG_DECODE, formData);
      const data = await response.json();

      if (response.ok && data.success) {
        setDecodedMessage(data.message);
        setDecodeSuccess(true);
      } else {
        if (response.status === 404) {
          setDecodeError('No hidden message found in this image.');
        } else {
          setDecodeError(data.detail || 'Decoding failed. Please try with a different image.');
        }
      }
    } catch (error) {
      setDecodeError('Network error. Please ensure the backend is running.');
    } finally {
      setDecodeLoading(false);
    }
  };

  const downloadEncodedImage = () => {
    if (encodedImageUrl) {
      const link = document.createElement('a');
      link.href = encodedImageUrl;
      link.download = 'encoded_security_alert.png';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className=\"bg-white rounded-xl shadow-lg p-6 max-w-4xl mx-auto\">
      <div className=\"border-b border-gray-200 pb-4 mb-6\">
        <h2 className=\"text-2xl font-bold text-gray-800 flex items-center\">
          <span className=\"bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium mr-3\">
            ENGINEER
          </span>
          Steganography Panel
        </h2>
        <p className=\"text-gray-600 mt-2\">Hide and extract security alerts in images for covert communication</p>
      </div>

      <div className=\"grid md:grid-cols-2 gap-8\">
        {/* ENCODE SECTION */}
        <div className=\"bg-green-50 rounded-lg p-6 border border-green-200\">
          <h3 className=\"text-xl font-semibold text-green-800 mb-4 flex items-center\">
            <svg className=\"w-5 h-5 mr-2\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\">
              <path strokeLinecap=\"round\" strokeLinejoin=\"round\" strokeWidth={2} d=\"M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z\" />
            </svg>
            ENCODE MESSAGE
          </h3>

          <div className=\"space-y-4\">
            <div>
              <label className=\"block text-sm font-medium text-green-700 mb-2\">
                Alert Message to Hide
              </label>
              <textarea
                value={alertMessage}
                onChange={(e) => setAlertMessage(e.target.value)}
                placeholder=\"Enter security alert message...\"
                className=\"w-full p-3 border border-green-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500 resize-none h-24\"
                maxLength={500}
              />
              <div className=\"text-xs text-green-600 mt-1\">
                {alertMessage.length}/500 characters
              </div>
            </div>

            <div>
              <label className=\"block text-sm font-medium text-green-700 mb-2\">
                Cover Image (JPG/PNG)
              </label>
              <input
                type=\"file\"
                accept=\"image/jpeg,image/png\"
                onChange={handleEncodeImageSelect}
                className=\"w-full p-2 border border-green-300 rounded-md focus:ring-2 focus:ring-green-500\"
              />
              {encodeImageFile && (
                <div className=\"text-sm text-green-600 mt-1\">
                  ✓ Selected: {encodeImageFile.name}
                </div>
              )}
            </div>

            {encodeError && (
              <div className=\"bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded text-sm\">
                {encodeError}
              </div>
            )}

            <button
              onClick={handleEncode}
              disabled={encodeLoading || !encodeImageFile || !alertMessage.trim()}
              className=\"w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded-md transition duration-200 flex items-center justify-center\"
            >
              {encodeLoading ? (
                <svg className=\"animate-spin -ml-1 mr-3 h-5 w-5 text-white\" xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 24 24\">
                  <circle className=\"opacity-25\" cx=\"12\" cy=\"12\" r=\"10\" stroke=\"currentColor\" strokeWidth=\"4\"></circle>
                  <path className=\"opacity-75\" fill=\"currentColor\" d=\"M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z\"></path>
                </svg>
              ) : (
                <svg className=\"w-5 h-5 mr-2\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\">
                  <path strokeLinecap=\"round\" strokeLinejoin=\"round\" strokeWidth={2} d=\"M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z\" />
                </svg>
              )}
              {encodeLoading ? 'Hiding Message...' : 'Hide Message in Image'}
            </button>

            {encodedImageUrl && (
              <div className=\"bg-green-100 border border-green-400 text-green-700 px-3 py-2 rounded\">
                <div className=\"flex items-center justify-between\">
                  <span className=\"text-sm font-medium\">✓ Message hidden successfully!</span>
                  <button
                    onClick={downloadEncodedImage}
                    className=\"bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm font-medium\"
                  >
                    Download
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* DECODE SECTION */}
        <div className=\"bg-blue-50 rounded-lg p-6 border border-blue-200\">
          <h3 className=\"text-xl font-semibold text-blue-800 mb-4 flex items-center\">
            <svg className=\"w-5 h-5 mr-2\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\">
              <path strokeLinecap=\"round\" strokeLinejoin=\"round\" strokeWidth={2} d=\"M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z\" />
            </svg>
            DECODE MESSAGE
          </h3>

          <div className=\"space-y-4\">
            <div>
              <label className=\"block text-sm font-medium text-blue-700 mb-2\">
                Encoded Image (JPG/PNG)
              </label>
              <input
                type=\"file\"
                accept=\"image/jpeg,image/png\"
                onChange={handleDecodeImageSelect}
                className=\"w-full p-2 border border-blue-300 rounded-md focus:ring-2 focus:ring-blue-500\"
              />
              {decodeImageFile && (
                <div className=\"text-sm text-blue-600 mt-1\">
                  ✓ Selected: {decodeImageFile.name}
                </div>
              )}
            </div>

            {decodeError && (
              <div className=\"bg-red-100 border border-red-400 text-red-700 px-3 py-2 rounded text-sm\">
                {decodeError}
              </div>
            )}

            <button
              onClick={handleDecode}
              disabled={decodeLoading || !decodeImageFile}
              className=\"w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded-md transition duration-200 flex items-center justify-center\"
            >
              {decodeLoading ? (
                <svg className=\"animate-spin -ml-1 mr-3 h-5 w-5 text-white\" xmlns=\"http://www.w3.org/2000/svg\" fill=\"none\" viewBox=\"0 0 24 24\">
                  <circle className=\"opacity-25\" cx=\"12\" cy=\"12\" r=\"10\" stroke=\"currentColor\" strokeWidth=\"4\"></circle>
                  <path className=\"opacity-75\" fill=\"currentColor\" d=\"M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z\"></path>
                </svg>
              ) : (
                <svg className=\"w-5 h-5 mr-2\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\">
                  <path strokeLinecap=\"round\" strokeLinejoin=\"round\" strokeWidth={2} d=\"M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z\" />
                </svg>
              )}
              {decodeLoading ? 'Extracting...' : 'Extract Hidden Message'}
            </button>

            {decodedMessage && (
              <div className={`border px-3 py-2 rounded text-sm ${
                decodeSuccess
                  ? 'bg-green-100 border-green-400 text-green-700'
                  : 'bg-gray-100 border-gray-400 text-gray-700'
              }`}>
                <div className=\"flex items-start\">
                  {decodeSuccess && (
                    <svg className=\"w-5 h-5 text-green-600 mr-2 mt-0.5 flex-shrink-0\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\">
                      <path strokeLinecap=\"round\" strokeLinejoin=\"round\" strokeWidth={2} d=\"M5 13l4 4L19 7\" />
                    </svg>
                  )}
                  <div>
                    <strong className=\"block mb-1\">Extracted Message:</strong>
                    <div className=\"whitespace-pre-wrap break-words\">{decodedMessage}</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className=\"mt-8 bg-gray-50 rounded-lg p-4 border border-gray-200\">
        <h4 className=\"text-sm font-semibold text-gray-700 mb-2\">Usage Instructions:</h4>
        <ul className=\"text-sm text-gray-600 space-y-1\">
          <li>• <strong>Encode:</strong> Hide security alert messages in innocent-looking images for covert communication</li>
          <li>• <strong>Decode:</strong> Extract hidden messages from suspected steganographic images</li>
          <li>• Supports JPG and PNG formats up to 10MB</li>
          <li>• Messages are embedded using LSB (Least Significant Bit) steganography</li>
        </ul>
      </div>
    </div>
  );
};

export default Steg;