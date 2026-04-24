# Base64 Auto Charset

A Sublime Text plugin for Base64 decoding with automatic charset detection
(UTF-8, GB18030/GBK/GB2312, Big5, EUC-JP, Shift_JIS, EUC-KR, etc.), and
Base64 encoding with GB18030 or UTF-8 charset.

## Features

### Base64 Decode (with automatic charset detection)
- Automatically detects the charset of the decoded bytes
- Supports UTF-8, UTF-8 with BOM, GB18030/GBK/GB2312, Big5, EUC-JP, Shift_JIS, EUC-KR, and more
- Uses the `chardet` library for enhanced detection when available (optional)
- Handles Base64 strings with or without padding
- Can replace selection in-place or open result in a new tab

### Base64 Encode
- **GB18030 Encode**: encode the selected text with GB18030 charset, then Base64
- **UTF-8 Encode**: encode the selected text with UTF-8 charset, then Base64

## Installation

### Via Package Control (recommended, once accepted)

1. Open the Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
2. Run `Package Control: Install Package`
3. Search for `Base64AutoCharset` and install

### Manual installation

1. In Sublime Text, go to `Preferences` -> `Browse Packages...`
2. Copy the `Base64AutoCharset` folder into the `Packages` directory
3. Restart Sublime Text

## Usage

All commands are available through the Command Palette. Select some text first
(or none, to operate on the entire file), then open the Command Palette with
`Cmd+Shift+P` / `Ctrl+Shift+P` and type `Base64`:

| Command | Description |
|---------|-------------|
| `Base64: Decode (Auto Charset)` | Decode Base64 in place, auto-detect charset |
| `Base64: Decode to New Tab (Auto Charset)` | Decode into a new tab, keep the original |
| `Base64: Encode (GB18030)` | Encode text as GB18030, then Base64 |
| `Base64: Encode (UTF-8)` | Encode text as UTF-8, then Base64 |

The same commands are also available from the main menu under
`Edit -> Base64 Auto Charset`.

### Optional key bindings

This plugin does not bind any keys by default, to avoid conflicts with other
packages. If you want key bindings, add them to your
`Preferences -> Key Bindings`, for example:

```json
[
    { "keys": ["ctrl+shift+d"], "command": "base64_decode_auto_charset" },
    { "keys": ["ctrl+shift+e"], "command": "base64_encode_gb18030" },
    { "keys": ["ctrl+shift+u"], "command": "base64_encode_utf8" },
    { "keys": ["ctrl+shift+alt+d"], "command": "base64_decode_to_new_tab" }
]
```

## Use cases

### Chinese enterprise email / MIME debugging

MIME headers in enterprise email (Subject, From, To, attachment filenames, ...)
are often Base64-encoded, and the underlying bytes may be GB18030/GBK rather
than UTF-8. Select the encoded string and run `Base64: Decode (Auto Charset)`
to get the original text with the correct charset detected automatically:

```
Subject: =?gb18030?B?xOO6w8rAvec=?=
# select "xOO6w8rAvec=" and run Base64: Decode (Auto Charset)
# -> 你好世界  (detected charset: GB18030)
```

### API response inspection

Base64-encoded payloads returned from APIs can be decoded in place to inspect
their original content, regardless of whether the server uses UTF-8 or a
legacy Chinese encoding.

## Charset detection strategy

Detection order:

1. **UTF-8 BOM** - check for the `\xef\xbb\xbf` prefix
2. **UTF-8** - try UTF-8, using `chardet` to disambiguate when non-ASCII bytes are present
3. **GB18030** - try GB18030 (a superset of GBK and GB2312)
4. **Other CJK encodings** - try Big5, EUC-JP, Shift_JIS, EUC-KR in order
5. **chardet detection** - statistical detection via the `chardet` library
6. **Latin-1 fallback** - never fails; used as a last resort

The `chardet` library is used only when it is already available (e.g. bundled
with Sublime Text 4 or installed manually); the plugin works without it, with
a slightly reduced accuracy for ambiguous cases.

## Privacy

This plugin runs entirely locally. No text is sent to any external service.

## Testing

A standalone test suite is provided for the core encode/decode logic:

```bash
python3 test_base64_auto_charset.py
```

48 test cases cover UTF-8 / GB18030 encode and decode, round-trip, Base64
validation, edge cases, real-world email scenarios, and GB18030-specific
characters.

## License

[MIT](LICENSE)
