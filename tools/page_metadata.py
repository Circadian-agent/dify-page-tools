from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from page_tools_client import fetch_page


class PageMetadataTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        result = fetch_page("meta", self.runtime.credentials.get("api_key"), tool_parameters.get("url"))
        yield self.create_json_message(result)
