"""Authentication module for OCI client with session token support."""

import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

import oci
from oci.auth.signers import SecurityTokenSigner
from oci.signer import Signer
from rich.console import Console

from .models import AuthType, OCIConfig

logger = logging.getLogger(__name__)
console = Console()


class OCIAuthenticationError(Exception):
    """Raised when OCI authentication fails due to expired or invalid token.

    This exception provides structured information for agentic LLM clients
    to recover from authentication failures by running the appropriate
    OCI CLI command.
    """

    def __init__(self, message: str, profile_name: str = "DEFAULT"):
        """
        Initialize authentication error with recovery information.

        Args:
            message: Error message describing the authentication failure
            profile_name: OCI profile name to use for re-authentication
        """
        self.profile_name = profile_name
        self.recovery_command = f"oci session authenticate --profile-name {profile_name}"
        super().__init__(message)


class OCIAuthenticator:
    """Handle OCI authentication with session token and API key support."""

    def __init__(self, config: OCIConfig):
        """Initialize authenticator with configuration."""
        self.config = config
        self.oci_config: Optional[dict[str, Any]] = None
        self.signer: Optional[Any] = None

    def authenticate(self) -> tuple[dict[str, Any], Any]:
        """
        Authenticate with OCI and return config and signer.

        Returns:
            Tuple of (config_dict, signer_object)

        Raises:
            RuntimeError: If authentication fails
        """
        try:
            self.oci_config = self._load_config()
            auth_type = self._determine_auth_type()
            self.signer = self._create_signer(auth_type)

            if self._validate_auth():
                console.print(
                    f"[green]Successfully authenticated using {auth_type.value} "
                    f"for profile '{self.config.profile_name}'[/green]"
                )
                return self.oci_config, self.signer
            else:
                raise RuntimeError("Authentication validation failed")

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise RuntimeError(f"Failed to authenticate with OCI: {e}")

    def _load_config(self) -> dict[str, Any]:
        """Load OCI configuration from file."""
        if self.config.config_file:
            config_file = Path(self.config.config_file)
        else:
            config_file = Path.home() / ".oci" / "config"

        if not config_file.exists():
            raise FileNotFoundError(f"OCI config file not found: {config_file}")

        oci_config = oci.config.from_file(
            file_location=str(config_file), profile_name=self.config.profile_name
        )

        if self.config.region:
            oci_config["region"] = self.config.region

        # Update config model with loaded values
        self.config.tenancy = oci_config.get("tenancy")
        self.config.user = oci_config.get("user")
        self.config.fingerprint = oci_config.get("fingerprint")
        self.config.key_file = oci_config.get("key_file")
        self.config.security_token_file = oci_config.get("security_token_file")
        self.config.pass_phrase = oci_config.get("pass_phrase")

        return dict(oci_config)

    def _determine_auth_type(self) -> AuthType:
        """Determine the authentication type from config."""
        if self.config.security_token_file:
            token_file = Path(self.config.security_token_file)
            if not token_file.exists():
                raise FileNotFoundError(
                    f"Security token file not found: {token_file}\n"
                    f"Please run: oci session authenticate --profile-name {self.config.profile_name}"
                )

            # Check token file age (tokens expire after 1 hour)
            token_age_hours = (time.time() - token_file.stat().st_mtime) / 3600
            if token_age_hours > 1:
                console.print(
                    f"[yellow]Security token may be expired "
                    f"(created {token_age_hours:.1f} hours ago)[/yellow]"
                )

            return AuthType.SESSION_TOKEN

        elif self.config.key_file and self.config.fingerprint:
            key_file = Path(self.config.key_file)
            if not key_file.exists():
                raise FileNotFoundError(f"Private key file not found: {key_file}")
            return AuthType.API_KEY

        else:
            raise ValueError(
                f"Unable to determine auth type for profile '{self.config.profile_name}'. "
                f"Config must have either security_token_file or (key_file + fingerprint)."
            )

    def _create_signer(self, auth_type: AuthType) -> Any:
        """Create appropriate signer based on auth type."""
        if auth_type == AuthType.SESSION_TOKEN:
            return self._create_session_token_signer()
        elif auth_type == AuthType.API_KEY:
            return self._create_api_key_signer()
        else:
            raise ValueError(f"Unsupported auth type: {auth_type}")

    def _create_session_token_signer(self) -> SecurityTokenSigner:
        """Create a session token signer."""
        token_file = self.config.security_token_file
        if not token_file:
            raise ValueError("Security token file path is not set")

        with open(token_file, "r") as f:
            token = f.read().strip()

        private_key = oci.signer.load_private_key_from_file(
            self.config.key_file, pass_phrase=self.config.pass_phrase
        )

        return SecurityTokenSigner(token, private_key)

    def _create_api_key_signer(self) -> Signer:
        """Create an API key signer."""
        return oci.signer.Signer(
            tenancy=self.config.tenancy,
            user=self.config.user,
            fingerprint=self.config.fingerprint,
            private_key_file_location=self.config.key_file,
            pass_phrase=self.config.pass_phrase,
        )

    def _validate_auth(self) -> bool:
        """Validate authentication by making a test API call."""
        try:
            identity_client = oci.identity.IdentityClient(self.oci_config, signer=self.signer)
            regions = identity_client.list_regions()
            logger.info(f"Authentication validated. Found {len(regions.data)} regions.")
            return True
        except oci.exceptions.ServiceError as e:
            if e.status == 401:
                logger.error("Authentication failed: Invalid credentials or expired token")
            else:
                logger.error(f"Service error during validation: {e}")
            return False
        except Exception as e:
            logger.error(f"Validation failed with unexpected error: {e}")
            return False

    def refresh_token(self) -> bool:
        """Refresh session token if using session token auth."""
        try:
            console.print("[yellow]Refreshing session token...[/yellow]")

            result = subprocess.run(
                ["oci", "session", "refresh", "--profile", self.config.profile_name],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                self.authenticate()
                console.print("[green]Token refreshed successfully[/green]")
                return True
            else:
                console.print(f"[red]Token refresh failed: {result.stderr}[/red]")
                return False

        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            return False


def create_session_token(
    profile_name: str,
    region_name: str,
    tenancy_name: str = "bmc_operator_access",
    config_file_path: Optional[str] = None,
    timeout_minutes: int = 5,
) -> bool:
    """
    Create OCI session token via OCI CLI.

    This function calls the OCI CLI to create session tokens:
    oci session authenticate --profile-name $profile_name --region $region_name --tenancy-name $tenancy_name

    Args:
        profile_name: Name of the OCI profile to create/update
        region_name: OCI region name (e.g., 'us-phoenix-1')
        tenancy_name: Tenancy name for authentication
        config_file_path: Optional custom path to OCI config file
        timeout_minutes: Timeout for the authentication process

    Returns:
        bool: True if session token was created successfully
    """
    try:
        result = subprocess.run(["oci", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            console.print("[red]OCI CLI not found. Please install it: pip install oci-cli[/red]")
            return False

        console.print(f"[blue]Creating session token for profile '{profile_name}'...[/blue]")

        cmd = [
            "oci",
            "session",
            "authenticate",
            "--profile-name",
            profile_name,
            "--region",
            region_name,
            "--tenancy-name",
            tenancy_name,
        ]

        if config_file_path:
            cmd.extend(["--config-file", config_file_path])

        console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
        console.print("[yellow]This will open a web browser for authentication...[/yellow]")

        result = subprocess.run(cmd, timeout=timeout_minutes * 60, text=True)

        if result.returncode == 0:
            console.print(f"[green]Session token created successfully for '{profile_name}'![/green]")

            try:
                config_path = (
                    Path(config_file_path) if config_file_path else Path.home() / ".oci" / "config"
                )
                if config_path.exists():
                    test_config = oci.config.from_file(
                        file_location=str(config_path), profile_name=profile_name
                    )
                    if test_config.get("security_token_file"):
                        console.print(
                            f"[dim]Session token file: {test_config['security_token_file']}[/dim]"
                        )
            except Exception as e:
                logger.warning(f"Could not verify session token creation: {e}")

            return True
        else:
            console.print(f"[red]Failed to create session token. Exit code: {result.returncode}[/red]")
            return False

    except subprocess.TimeoutExpired:
        console.print(f"[red]Session authentication timed out after {timeout_minutes} minutes[/red]")
        return False
    except FileNotFoundError:
        console.print("[red]OCI CLI not found. Please install: pip install oci-cli[/red]")
        return False
    except Exception as e:
        logger.error(f"Failed to create session token: {e}")
        console.print(f"[red]Error creating session token: {e}[/red]")
        return False


def validate_session_token(
    region: str,
    profile_name: str = "DEFAULT",
    config_file: Optional[str] = None,
) -> dict[str, Any]:
    """
    Validate if the session token for a region is valid.

    Args:
        region: OCI region name
        profile_name: OCI config profile name
        config_file: Optional path to config file

    Returns:
        Dictionary with validation result and details
    """
    try:
        config = OCIConfig(region=region, profile_name=profile_name, config_file=config_file)
        authenticator = OCIAuthenticator(config)

        oci_config, signer = authenticator.authenticate()

        # Check token age if using session token
        if config.security_token_file:
            token_file = Path(config.security_token_file)
            token_age_minutes = (time.time() - token_file.stat().st_mtime) / 60
            remaining_minutes = max(0, 60 - token_age_minutes)

            return {
                "valid": True,
                "auth_type": "session_token",
                "region": region,
                "profile": profile_name,
                "token_age_minutes": round(token_age_minutes, 1),
                "remaining_minutes": round(remaining_minutes, 1),
                "message": f"Session token is valid. Approximately {round(remaining_minutes)} minutes remaining.",
            }
        else:
            return {
                "valid": True,
                "auth_type": "api_key",
                "region": region,
                "profile": profile_name,
                "message": "API key authentication is valid.",
            }

    except Exception as e:
        return {
            "valid": False,
            "region": region,
            "profile": profile_name,
            "error": str(e),
            "message": f"Authentication failed: {e}",
        }
