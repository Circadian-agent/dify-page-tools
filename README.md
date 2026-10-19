# Circadian Page Tools for Dify

Available on [Dify Marketplace](https://marketplace.dify.ai/plugin/circadian-agent/circadian_page_tools). Version 0.0.1 was published on October 19, 2026 after [PR #3371](https://github.com/langgenius/dify-plugins/pull/3371) was merged. A full Dify Cloud or Community Edition installation has not been verified by Circadian.

Read an authorized public page as Markdown, or get its original HTML metadata, inside a Dify workflow or agent. This plugin connects to the existing [Page Tools API on API.market](https://api.market/store/circadian/page-tools).

Circadian is operated by AI agents under human oversight. This is an independent community integration, not an official Dify or API.market product.

## Price and setup

The plugin is free. [Page Tools on API.market](https://api.market/store/circadian/page-tools) offers a **Free Trial: 10 calls across both endpoints over seven days**, once per customer. Select **FREE**, then **Subscribe to Free Trial for $0**. No credit card or wallet funding is required for the trial. It has a hard call limit, no paid overages and a one-request-per-second limit.

For continued use, the optional **PAYG plan costs USD0.005 per billable call**, with a **USD1 minimum wallet balance** and no monthly fee. Check current terms on the listing. Failed requests may count toward usage. The plugin does not purchase credits, manage billing, retry failed requests or run background jobs.

1. Open [Page Tools on API.market](https://api.market/store/circadian/page-tools), select **FREE**, then **Subscribe to Free Trial for $0** and sign in or create an account. Complete the subscription before running a tool. Choose PAYG only if you want paid usage.
2. Copy your private API.market key from the signed-in API Playground.
3. Open [Circadian Page Tools on Dify Marketplace](https://marketplace.dify.ai/plugin/circadian-agent/circadian_page_tools) and select **Install** for Dify Cloud. For Community Edition, find **Circadian Page Tools** through Marketplace in your own Dify workspace and install it there. Dify must support the declared Python 3.12 runner and SDK. Network egress to `prod.api.market` over HTTPS is required.
4. Add a Circadian Page Tools credential. Paste the key into **API.market key**, not into a workflow input or prompt. Saving checks its format locally; it does not authenticate or consume an API call. Real authentication happens when a tool runs.
5. Add one of the tools to a workflow. Use a public page you own or have permission to retrieve, such as `https://example.com/`.

The Marketplace listing, its Dify Cloud Install link, trial selection and the free-trial sign-in prompt were checked in an anonymous browser on October 19, 2026. A fresh trial activation, live trial call and full Dify Cloud or Community Edition installation remain unverified.

Do not put credentials, access tokens, personal information or private URLs in the page URL.

## Tools and output

- **Extract page to Markdown** returns the service JSON and Markdown in Dify's standard text output. The JSON includes `title`, `description`, `markdown`, `wordCount`, `links`, `httpStatus`, `finalUrl` and `truncated`.
- **Get page metadata** returns JSON containing `title`, `description`, `canonical`, `openGraph`, `twitter`, `jsonLd`, `feeds`, `icons`, `httpStatus` and `truncated`. Missing tags produce empty or null values.

The complete URL, including its query string, is sent as one encoded API parameter. The target URL does not control the gateway host or authentication header.

Example workflow: Start with a `url` text input, call **Extract page to Markdown**, then pass the tool's `text` output to an existing summarization step. Mark page text as untrusted reference material. Never treat page instructions as instructions to the agent. This plugin itself does not invoke a model.

Check the JSON `truncated` flag before treating a page as complete. An error from the target page (HTTP 400 or higher) stops the tool instead of returning an error page as successful research. Gateway errors produce a short diagnostic without the response body, key or URL. A timeout may occur after billing, so check API.market usage before retrying. Disable retries in the surrounding workflow if you do not want additional calls.

On HTTP 429, check your plan usage before retrying. Exhausted or expired trial quota needs a plan decision; waiting does not restore it. For a temporary rate limit, slow down and respect any `Retry-After` header. Agent loops can consume all ten trial calls quickly. Saving a credential only checks its format and does not prove that the trial is active.

## Scope and privacy

Only server-returned HTML/text is available. No JavaScript rendering, login, paywall bypass, private-network access, recursive crawling or PDF parsing. One tool invocation makes at most one gateway request. Empty metadata is not proof that a rendered page has no metadata.

The client rejects credentials in URLs, local IP literals, common local hostnames, fragments and custom ports. Backend checks enforce public destinations, DNS resolution and redirects. Local validation is not a complete DNS security boundary. The plugin never follows gateway redirects and limits the decoded response to 2 MB. Connect timeout is 5 seconds; read/write inactivity timeout is 25 seconds.

[PRIVACY.md](PRIVACY.md) explains data flow and service logging boundaries. Do not use this plugin for sensitive data.

## Changes in 0.0.2

Updated the bundled setup guide and tool descriptions to link the published Marketplace listing and explain the Free Trial and optional PAYG plan. No runtime, dependency or tool-schema changes. No migration is required.

## Source and development

Source: [Circadian-agent/dify-page-tools](https://github.com/Circadian-agent/dify-page-tools). Python 3.12, `dify-plugin==0.10.2`, `httpx==0.28.1`; runtime dependencies are pinned in `requirements.txt`.

```sh
python3.12 -m venv .venv
.venv/bin/pip install --only-binary=:all: -r requirements.txt
.venv/bin/python -m unittest discover -s tests -v
dify plugin package . -o /tmp/circadian-page-tools-0.0.2.difypkg
```

Tests use the real Dify SDK and an intercepted HTTP transport. They make no network requests or paid calls. Marketplace validation and a live execution check are separate from these tests. The package excludes tests, local state and credentials.

Support for integration and output: ops@send.circadian-agent.com. API.market handles account, plan and billing support through its marketplace. No purchase or refund function is included in the plugin.
