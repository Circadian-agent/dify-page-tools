from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from page_tools_client import validate_key


class CircadianPageToolsProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        # No free auth probe exists. Never charge a request just to save a key.
        try:
            validate_key(credentials.get("api_key"))
        except ValueError as error:
            raise ToolProviderCredentialValidationError(str(error)) from None
