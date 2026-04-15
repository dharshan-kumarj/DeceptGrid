"""
Layer 5: Cryptographic Code Signing for Meter Commands
Uses GPG (GNU Privacy Guard) with RSA 4096-bit keys
"""

import gnupg
import os
import logging
from typing import Tuple, Optional, Dict
from pathlib import Path
import json

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
        self.gpg = gnupg.GPG()

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
            "engineer_1": "DE4A19D0F73B66A3",  # Example fingerprint
            "admin": "D2A1E3F4B5C6D7E8",
            "ops_team": "A1B2C3D4E5F6G7H8"
        }

    def import_public_key(self, key_path: str, signer_name: str) -> bool:
        """
        Import a public key and register the signer.

        Args:
            key_path: Path to ASCII-armored public key file
            signer_name: Name/identifier for this signer

        Returns:
            True if successful
        """
        try:
            with open(key_path) as f:
                key_data = f.read()

            import_result = self.gpg.import_keys(key_data)

            if import_result.count > 0:
                # Get fingerprint from imported key
                fingerprint = import_result.fingerprints[0]
                self.authorized_signers[signer_name] = fingerprint

                # Save updated mapping
                config_file = self.keys_dir / "authorized_signers.json"
                with open(config_file, 'w') as f:
                    json.dump(self.authorized_signers, f, indent=2)

                logger.info(f"✓ Imported public key for {signer_name}: {fingerprint}")
                return True
            else:
                logger.error(f"✗ Failed to import key from {key_path}")
                return False

        except Exception as e:
            logger.error(f"✗ Error importing key: {e}")
            return False

    def verify_signature(self, signed_payload: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verify a GPG-signed payload.

        Args:
            signed_payload: ASCII-armored GPG message

        Returns:
            (is_valid, signer_identity, command_json)
        """
        try:
            # Verify signature
            verified = self.gpg.verify(signed_payload)

            if not verified.valid:
                logger.warning("INVALID_SIGNATURE: GPG signature verification failed")
                return False, None, None

            # Extract signer info
            signer_fingerprint = verified.fingerprint
            signer_name = verified.username

            # Check if signer is authorized
            is_authorized = signer_fingerprint in self.authorized_signers.values()

            if not is_authorized:
                logger.warning(
                    f"UNAUTHORIZED_SIGNER: {signer_name} (fingerprint: {signer_fingerprint})"
                )
                return False, None, None

            # Extract the signed data
            command_json = verified.data.decode('utf-8')

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
