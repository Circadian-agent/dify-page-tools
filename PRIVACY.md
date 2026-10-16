# Privacy and data flow

Circadian Page Tools is operated by AI agents under human oversight. Contact: ops@send.circadian-agent.com.

## Data sent

Each invocation sends the requested public page URL, including its query parameters, to `https://prod.api.market` over HTTPS. The private API.market key is sent only in the `x-api-market-key` request header to that fixed host. The plugin does not send a conversation history, model prompt or other Dify credentials.

API.market authenticates and meters the request, then forwards the requested URL to the Circadian Page Tools service hosted on Vercel at circadian-agent.com. The service fetches the requested public page. The page host sees a server request and the URL, but the plugin's API.market credential is not part of that target request. Page text or metadata returns through API.market to your Dify application.

Only provide URLs and content that you have permission to retrieve and process. URLs can themselves contain personal data or tokens. Do not submit those URLs or sensitive content.

## Storage and logging

The plugin adds no database, persistent storage, analytics or telemetry. It does not intentionally log API keys, requested URLs, page content or raw gateway error bodies. It keeps request data in memory while running and returns page data to Dify.

Dify stores the configured credential and may retain tool inputs, outputs and workflow logs under your workspace settings and its privacy policy. API.market handles account information and request metering. API.market, Vercel, Circadian's hosting infrastructure and the destination website may retain operational or access logs. The plugin cannot control their retention. Do not interpret the absence of plugin-side persistence as a promise that these services do not log requests.

No payment details are collected by this plugin. Any external API account, wallet funding or billing data is handled on API.market, outside the plugin. Contact the relevant service for its account records or deletion requests.

- [Dify privacy policy](https://dify.ai/legal/privacy-policy)
- [API.market service and account information](https://api.market/store/circadian/page-tools)
- [Circadian privacy policy](https://circadian-agent.com/privacy)
