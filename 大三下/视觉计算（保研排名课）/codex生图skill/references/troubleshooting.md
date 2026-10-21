# Troubleshooting

## Failure split

### Sandbox/network path issue

Symptoms:

- PowerShell `Invoke-RestMethod` fails before a useful JSON body appears
- `curl.exe` reports `schannel` credential or certificate errors
- Python HTTPS call times out on read

Action:

1. Keep the same prompt and parameters.
2. Rerun the script with escalated host-network access.
3. Only blame the gateway after the host-network retry also fails.

### Gateway/business error

Symptoms:

- HTTP `400` with JSON error body
- HTTP `401` / `403`
- Response has no `image_generation_call`

Action:

1. Print the error body.
2. Fix the request, not the transport.

Common example:

- `Invalid size ... below the current minimum pixel budget`
  Action: request a larger size such as `1024x1024` or `1024x1536`.

## Prompting reminders

- For livestream screenshots, specify `vertical`, `mobile screenshot`, `UI overlays`, `chat bubbles`, `gift area`, and `viewer count`.
- For poster-style images, specify `poster`, `hero image`, or `promotional image`.
- If the user wants a screenshot feel, explicitly avoid `poster layout`.

