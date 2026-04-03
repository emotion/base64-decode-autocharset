"""
Base64 Auto Charset - Sublime Text Plugin

Features:
1. Base64 Decode with automatic charset detection (supports GB18030, UTF-8, etc.)
2. Base64 Encode with GB18030 charset
3. Base64 Encode with UTF-8 charset

Works with selected text or entire file content.
"""

import sublime
import sublime_plugin
import base64
import codecs


def detect_charset(raw_bytes):
    """
    Detect the charset of raw bytes using multiple strategies.
    Returns (decoded_string, charset_name).

    Strategy:
    1. Try UTF-8 first (most common)
    2. Try GB18030 (superset of GBK/GB2312)
    3. Use chardet library if available
    4. Fallback to latin-1 (never fails)
    """
    # Strategy 1: Try UTF-8 (with BOM check)
    if raw_bytes[:3] == b'\xef\xbb\xbf':
        try:
            decoded = raw_bytes[3:].decode('utf-8')
            return decoded, 'UTF-8 (BOM)'
        except UnicodeDecodeError:
            pass

    try:
        decoded = raw_bytes.decode('utf-8')
        # Verify it's not just ASCII being detected as UTF-8
        # by checking if there are actual multi-byte sequences
        if any(b > 127 for b in raw_bytes):
            # Additional validation: try GB18030 and see if it also works
            # If both work, use heuristics
            try:
                gb_decoded = raw_bytes.decode('gb18030')
                # Use chardet to disambiguate
                charset_result = _chardet_detect(raw_bytes)
                if charset_result and charset_result.lower() in ('gb2312', 'gbk', 'gb18030'):
                    return gb_decoded, 'GB18030'
            except (UnicodeDecodeError, LookupError):
                pass
        return decoded, 'UTF-8'
    except UnicodeDecodeError:
        pass

    # Strategy 2: Try GB18030 (superset of GBK and GB2312)
    try:
        decoded = raw_bytes.decode('gb18030')
        return decoded, 'GB18030'
    except (UnicodeDecodeError, LookupError):
        pass

    # Strategy 3: Try other common CJK encodings
    for encoding in ['big5', 'euc-jp', 'shift_jis', 'euc-kr']:
        try:
            decoded = raw_bytes.decode(encoding)
            return decoded, encoding.upper()
        except (UnicodeDecodeError, LookupError):
            pass

    # Strategy 4: Use chardet library
    charset_result = _chardet_detect(raw_bytes)
    if charset_result:
        try:
            decoded = raw_bytes.decode(charset_result)
            return decoded, charset_result.upper()
        except (UnicodeDecodeError, LookupError):
            pass

    # Strategy 5: Fallback to latin-1 (always succeeds)
    decoded = raw_bytes.decode('latin-1')
    return decoded, 'Latin-1 (fallback)'


def _chardet_detect(raw_bytes):
    """
    Try to detect charset using chardet library.
    Returns charset name string or None.
    """
    try:
        import chardet
        result = chardet.detect(raw_bytes)
        if result and result.get('confidence', 0) > 0.5:
            encoding = result['encoding']
            if encoding:
                # Normalize encoding names
                encoding_lower = encoding.lower()
                if encoding_lower in ('gb2312', 'gbk', 'gb18030'):
                    return 'gb18030'
                return encoding
    except ImportError:
        pass
    return None


def is_valid_base64(text):
    """Check if the given text is valid base64."""
    import re
    # Remove whitespace
    text = text.strip()
    if not text:
        return False
    # Base64 pattern: A-Z, a-z, 0-9, +, /, = (padding)
    clean = text.replace('\n', '').replace('\r', '').replace(' ', '')
    pattern = r'^[A-Za-z0-9+/]+=*$'
    if not re.match(pattern, clean):
        return False
    # Accept both padded (len % 4 == 0) and unpadded base64
    # Unpadded is valid if len % 4 != 1 (which would be impossible in base64)
    return len(clean) % 4 != 1


class Base64DecodeAutoCharsetCommand(sublime_plugin.TextCommand):
    """
    Decode base64 selected text with automatic charset detection.
    If no selection, decode the entire file content.
    """

    def run(self, edit):
        view = self.view
        selections = view.sel()

        if len(selections) == 1 and selections[0].empty():
            # No selection - use entire file content
            region = sublime.Region(0, view.size())
            self._decode_region(edit, region)
        else:
            # Process each selection (in reverse to preserve positions)
            for region in reversed(list(selections)):
                if not region.empty():
                    self._decode_region(edit, region)

    def _decode_region(self, edit, region):
        view = self.view
        text = view.substr(region).strip()

        if not text:
            sublime.status_message("Base64 Decode: No text to decode")
            return

        if not is_valid_base64(text):
            sublime.status_message("Base64 Decode: Invalid base64 string")
            return

        try:
            # Remove whitespace before decoding
            clean_text = text.replace('\n', '').replace('\r', '').replace(' ', '')
            # Add padding if necessary
            padding_needed = len(clean_text) % 4
            if padding_needed:
                clean_text += '=' * (4 - padding_needed)
            raw_bytes = base64.b64decode(clean_text)
        except Exception as e:
            sublime.status_message("Base64 Decode Error: {}".format(str(e)))
            return

        # Detect charset and decode
        decoded_str, charset = detect_charset(raw_bytes)

        # Replace selection with decoded text
        view.replace(edit, region, decoded_str)

        # Show charset info in status bar
        sublime.status_message(
            "Base64 Decoded | Charset: {} | {} bytes -> {} chars".format(
                charset, len(raw_bytes), len(decoded_str)
            )
        )


class Base64EncodeGb18030Command(sublime_plugin.TextCommand):
    """
    Encode selected text to base64 using GB18030 charset.
    If no selection, encode the entire file content.
    """

    def run(self, edit):
        view = self.view
        selections = view.sel()

        if len(selections) == 1 and selections[0].empty():
            region = sublime.Region(0, view.size())
            self._encode_region(edit, region, 'gb18030')
        else:
            for region in reversed(list(selections)):
                if not region.empty():
                    self._encode_region(edit, region, 'gb18030')

    def _encode_region(self, edit, region, encoding):
        view = self.view
        text = view.substr(region)

        if not text:
            sublime.status_message("Base64 Encode: No text to encode")
            return

        try:
            raw_bytes = text.encode(encoding)
            encoded = base64.b64encode(raw_bytes).decode('ascii')
        except UnicodeEncodeError as e:
            sublime.status_message(
                "Base64 Encode Error: Cannot encode with {} - {}".format(
                    encoding.upper(), str(e)
                )
            )
            return

        view.replace(edit, region, encoded)
        sublime.status_message(
            "Base64 Encoded | Charset: {} | {} chars -> {} bytes".format(
                encoding.upper(), len(text), len(encoded)
            )
        )


class Base64EncodeUtf8Command(sublime_plugin.TextCommand):
    """
    Encode selected text to base64 using UTF-8 charset.
    If no selection, encode the entire file content.
    """

    def run(self, edit):
        view = self.view
        selections = view.sel()

        if len(selections) == 1 and selections[0].empty():
            region = sublime.Region(0, view.size())
            self._encode_region(edit, region, 'utf-8')
        else:
            for region in reversed(list(selections)):
                if not region.empty():
                    self._encode_region(edit, region, 'utf-8')

    def _encode_region(self, edit, region, encoding):
        view = self.view
        text = view.substr(region)

        if not text:
            sublime.status_message("Base64 Encode: No text to encode")
            return

        try:
            raw_bytes = text.encode(encoding)
            encoded = base64.b64encode(raw_bytes).decode('ascii')
        except UnicodeEncodeError as e:
            sublime.status_message(
                "Base64 Encode Error: Cannot encode with {} - {}".format(
                    encoding.upper(), str(e)
                )
            )
            return

        view.replace(edit, region, encoded)
        sublime.status_message(
            "Base64 Encoded | Charset: {} | {} chars -> {} bytes".format(
                encoding.upper(), len(text), len(encoded)
            )
        )


class Base64DecodeToNewTabCommand(sublime_plugin.TextCommand):
    """
    Decode base64 selected text and open result in a new tab.
    Useful for viewing decoded content without modifying the original.
    """

    def run(self, edit):
        view = self.view
        selections = view.sel()

        text = ""
        if len(selections) == 1 and selections[0].empty():
            text = view.substr(sublime.Region(0, view.size())).strip()
        else:
            parts = []
            for region in selections:
                if not region.empty():
                    parts.append(view.substr(region).strip())
            text = '\n'.join(parts)

        if not text:
            sublime.status_message("Base64 Decode: No text to decode")
            return

        if not is_valid_base64(text):
            sublime.status_message("Base64 Decode: Invalid base64 string")
            return

        try:
            clean_text = text.replace('\n', '').replace('\r', '').replace(' ', '')
            # Add padding if necessary
            padding_needed = len(clean_text) % 4
            if padding_needed:
                clean_text += '=' * (4 - padding_needed)
            raw_bytes = base64.b64decode(clean_text)
        except Exception as e:
            sublime.status_message("Base64 Decode Error: {}".format(str(e)))
            return

        decoded_str, charset = detect_charset(raw_bytes)

        # Open in new tab
        new_view = view.window().new_file()
        new_view.set_name("Base64 Decoded ({})".format(charset))
        new_view.set_scratch(True)
        new_view.run_command('insert', {'characters': decoded_str})

        sublime.status_message(
            "Base64 Decoded in new tab | Charset: {} | {} bytes".format(
                charset, len(raw_bytes)
            )
        )
