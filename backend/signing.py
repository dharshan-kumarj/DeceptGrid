"""
Layer 5: Cryptographic Code Signing for Meter Commands
Uses GPG (GNU Privacy Guard) with RSA 4096-bit keys
"""

import subprocess
import os
import logging
from typing import Tuple, Optional, Dict
from pathlib import Path
import json
import re

logger = logging.getLogger(__name__)


class CodeSigner:
    """GPG-based code signing for meter commands."""

    def __init__(self, keys_dir: str = "/home/dharshan/projects/DeceptGrid/keys"):
        """
        Initialize GPG handler.

        Args:
            keys_dir: Directory containing authorized public keys
        """
        self.keys_dir = Path(keys_dir)
        self.authorized_keys_dir = self.keys_dir / "authorized_keys"

        # Create directories if they don't exist
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self.authorized_keys_dir.mkdir(parents=True, exist_ok=True)

        # Load authorized key mappings
        self.authorized_signers = self._load_authorized_signers()

    def _load_authorized_signers(self) -> Dict[str, str]:
        """
        Load authorized signer mapping from config file.

        Format:
        {
          "engineer_name": "key_fingerprint",
          "admin": "another_fingerprint"
        }
        """
        config_file = self.keys_dir / "authorized_signers.json"

        if config_file.exists():
            try:
                with open(config_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load authorized_signers.json: {e}")

        # Default authorized signers for testing
        return {
            "engineer": "ABFBF4B4B75B94D01E1756C6D793720C0D49ADD7",
            "engineer_1": "DE4A19D0F73B66A3",
            "admin": "D2A1E3F4B5C6D7E8",
            "ops_team": "A1B2C3D4E5F6G7H8"
        }

    def verify_signature(self, signed_payload: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verify a GPG-signed payload using system GPG.

        Args:
            signed_payload: ASCII-armored GPG message

        Returns:
            (is_valid, signer_identity, command_json)
        """
        try:
            # Write signed payload to temp file
            temp_file = "/tmp/signed_payload.asc"
            with open(temp_file, 'w') as f:
                f.write(signed_payload)

            # Verify signature using system gpg
            result = subprocess.run(
                ["gpg", "--verify", temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.warning(f"INVALID_SIGNATURE: {result.stderr}")
                return False, None, None

            # Extract signature details from stderr output
            # Example: gpg: using RSA key ABFBF4B4B75B94D01E1756C6D793720C0D49ADD7
            #          gpg: Good signature from "engineer@deceptgrid.local" [ultimate]

            fingerprint = None
            signer_name = None

            for line in result.stderr.split('\n'):
                if 'using RSA key' in line:
                    fingerprint = line.split()[-1].strip()
                if 'Good signature from' in line:
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        signer_name = match.group(1)

            if not fingerprint or not signer_name:
                logger.warning("INVALID_SIGNATURE: Could not extract signer info")
                return False, None, None

            # Check if signer is authorized
            is_authorized = fingerprint in self.authorized_signers.values()

            if not is_authorized:
                logger.warning(
                    f"UNAUTHORIZED_SIGNER: {signer_name} (fingerprint: {fingerprint})"
                )
                return False, None, None

            # Extract signed data (everything before BEGIN PGP MESSAGE)
            lines = signed_payload.split('\n')

            # Find the start of the PGP message
            start_idx = None
            for i, line in enumerate(lines):
                if 'BEGIN PGP MESSAGE' in line:
                    start_idx = i
                    break

            if start_idx is None:
                logger.error("INVALID_COMMAND: No PGP message found")
                return False, None, None

            # The actual payload is encoded in the base64 section
            # For now, we'll extract it using gpg decryption
            decrypt_result = subprocess.run(
                ["gpg", "--decrypt", "--quiet", temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )

            if decrypt_result.returncode != 0:
                logger.error(f"Failed to decrypt signed message: {decrypt_result.stderr}")
                return False, None, None

            command_json = decrypt_result.stdout.strip()

            logger.info(f"SIGNED_COMMAND_ACCEPTED: {signer_name}")
            return True, signer_name, command_json

        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False, None, None

    def verify_and_parse_command(self, signed_payload: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Verify signature and parse JSON command in one step.

        Args:
            signed_payload: ASCII-armored GPG message containing JSON

        Returns:
            (is_valid, command_dict, signer_name)
        """
        is_valid, signer, command_json = self.verify_signature(signed_payload)

        if not is_valid:
            return False, None, None

        try:
            command_dict = json.loads(command_json)
            return True, command_dict, signer
        except json.JSONDecodeError:
            logger.error("INVALID_COMMAND: Failed to parse JSON from signed payload")
            return False, None, signer

    def validate_command_structure(self, command: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate that command has required fields.

        Args:
            command: Command dictionary

        Returns:
            (is_valid, error_message)
        """
        required_fields = ["action", "target_meter", "value"]

        for field in required_fields:
            if field not in command:
                return False, f"Missing required field: {field}"

        # Validate action
        valid_actions = ["set_config", "update_firmware", "reset", "calibrate"]
        if command.get("action") not in valid_actions:
            return False, f"Invalid action: {command.get('action')}"

        return True, None


# Global signer instance
_code_signer = None


def get_code_signer() -> CodeSigner:
    """Get or initialize the global CodeSigner instance."""
    global _code_signer
    if _code_signer is None:
        _code_signer = CodeSigner()
    return _code_signer
