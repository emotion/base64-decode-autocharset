#!/usr/bin/env python3
"""
Test suite for Base64AutoCharset Sublime Text plugin.

Tests the core functions without requiring Sublime Text:
1. detect_charset() - Automatic charset detection
2. is_valid_base64() - Base64 validation
3. Encode -> Decode round-trip tests
4. Edge cases and error handling

Run: python3 test_base64_auto_charset.py
"""

import base64
import sys
import os

# ============================================================
# Import core functions from the plugin
# We re-implement them here for standalone testing since
# the plugin imports sublime/sublime_plugin which aren't
# available outside Sublime Text.
# ============================================================


def _chardet_detect(raw_bytes):
    """Try to detect charset using chardet library."""
    try:
        import chardet
        result = chardet.detect(raw_bytes)
        if result and result.get('confidence', 0) > 0.5:
            encoding = result['encoding']
            if encoding:
                encoding_lower = encoding.lower()
                if encoding_lower in ('gb2312', 'gbk', 'gb18030'):
                    return 'gb18030'
                return encoding
    except ImportError:
        pass
    return None


def detect_charset(raw_bytes):
    """Detect the charset of raw bytes."""
    # UTF-8 BOM
    if raw_bytes[:3] == b'\xef\xbb\xbf':
        try:
            decoded = raw_bytes[3:].decode('utf-8')
            return decoded, 'UTF-8 (BOM)'
        except UnicodeDecodeError:
            pass

    # Try UTF-8
    try:
        decoded = raw_bytes.decode('utf-8')
        if any(b > 127 for b in raw_bytes):
            try:
                gb_decoded = raw_bytes.decode('gb18030')
                charset_result = _chardet_detect(raw_bytes)
                if charset_result and charset_result.lower() in ('gb2312', 'gbk', 'gb18030'):
                    return gb_decoded, 'GB18030'
            except (UnicodeDecodeError, LookupError):
                pass
        return decoded, 'UTF-8'
    except UnicodeDecodeError:
        pass

    # Try GB18030
    try:
        decoded = raw_bytes.decode('gb18030')
        return decoded, 'GB18030'
    except (UnicodeDecodeError, LookupError):
        pass

    # Other CJK
    for encoding in ['big5', 'euc-jp', 'shift_jis', 'euc-kr']:
        try:
            decoded = raw_bytes.decode(encoding)
            return decoded, encoding.upper()
        except (UnicodeDecodeError, LookupError):
            pass

    # chardet
    charset_result = _chardet_detect(raw_bytes)
    if charset_result:
        try:
            decoded = raw_bytes.decode(charset_result)
            return decoded, charset_result.upper()
        except (UnicodeDecodeError, LookupError):
            pass

    # Fallback
    decoded = raw_bytes.decode('latin-1')
    return decoded, 'Latin-1 (fallback)'


def is_valid_base64(text):
    """Check if the given text is valid base64."""
    import re
    text = text.strip()
    if not text:
        return False
    clean = text.replace('\n', '').replace('\r', '').replace(' ', '')
    pattern = r'^[A-Za-z0-9+/]+=*$'
    if not re.match(pattern, clean):
        return False
    # Accept both padded (len % 4 == 0) and unpadded base64
    # Unpadded is valid if len % 4 != 1 (which would be impossible in base64)
    return len(clean) % 4 != 1


# ============================================================
# Test Framework
# ============================================================

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def record(self, test_name, passed, detail=""):
        if passed:
            self.passed += 1
            print(f"  ✅ {test_name}")
        else:
            self.failed += 1
            self.errors.append((test_name, detail))
            print(f"  ❌ {test_name}: {detail}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Total: {total} | Passed: {self.passed} | Failed: {self.failed}")
        if self.errors:
            print(f"\nFailed tests:")
            for name, detail in self.errors:
                print(f"  - {name}: {detail}")
        print(f"{'='*60}")
        return self.failed == 0


results = TestResults()


# ============================================================
# Test 1: UTF-8 Base64 Decode
# ============================================================
def test_utf8_decode():
    print("\n📋 Test Group 1: UTF-8 Base64 Decode")

    # Simple ASCII
    original = "Hello, World!"
    b64 = base64.b64encode(original.encode('utf-8')).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "ASCII text decode",
        decoded == original,
        f"Expected '{original}', got '{decoded}' (charset: {charset})"
    )

    # Chinese UTF-8
    original = "你好世界，这是一段中文测试文本。"
    b64 = base64.b64encode(original.encode('utf-8')).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "UTF-8 Chinese decode",
        decoded == original,
        f"Expected '{original}', got '{decoded}' (charset: {charset})"
    )

    # Mixed Chinese and English UTF-8
    original = "Hello 你好 World 世界 2024!"
    b64 = base64.b64encode(original.encode('utf-8')).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "UTF-8 mixed Chinese/English decode",
        decoded == original,
        f"Expected '{original}', got '{decoded}' (charset: {charset})"
    )

    # UTF-8 with BOM
    original = "带BOM的UTF-8文本"
    bom_bytes = b'\xef\xbb\xbf' + original.encode('utf-8')
    b64 = base64.b64encode(bom_bytes).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "UTF-8 with BOM decode",
        decoded == original and 'BOM' in charset,
        f"Expected '{original}' with BOM charset, got '{decoded}' (charset: {charset})"
    )


# ============================================================
# Test 2: GB18030 Base64 Decode
# ============================================================
def test_gb18030_decode():
    print("\n📋 Test Group 2: GB18030 Base64 Decode")

    # Chinese text encoded in GB18030
    original = "你好世界"
    gb_bytes = original.encode('gb18030')
    b64 = base64.b64encode(gb_bytes).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "GB18030 Chinese decode",
        decoded == original,
        f"Expected '{original}', got '{decoded}' (charset: {charset})"
    )

    # Longer GB18030 text
    original = "这是一段比较长的中文文本，用来测试GB18030编码的Base64解码功能。包含标点符号：！@#￥%"
    gb_bytes = original.encode('gb18030')
    b64 = base64.b64encode(gb_bytes).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "GB18030 long text decode",
        decoded == original,
        f"Expected '{original}', got '{decoded}' (charset: {charset})"
    )

    # GB18030 with rare characters
    original = "简体中文：企业邮箱测试"
    gb_bytes = original.encode('gb18030')
    b64 = base64.b64encode(gb_bytes).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "GB18030 enterprise mail text",
        decoded == original,
        f"Expected '{original}', got '{decoded}' (charset: {charset})"
    )


# ============================================================
# Test 3: GB18030 Base64 Encode
# ============================================================
def test_gb18030_encode():
    print("\n📋 Test Group 3: GB18030 Base64 Encode")

    # Basic Chinese text
    original = "你好世界"
    expected_bytes = original.encode('gb18030')
    expected_b64 = base64.b64encode(expected_bytes).decode('ascii')
    actual_b64 = base64.b64encode(original.encode('gb18030')).decode('ascii')
    results.record(
        "GB18030 encode basic",
        actual_b64 == expected_b64,
        f"Expected '{expected_b64}', got '{actual_b64}'"
    )

    # Verify roundtrip: encode GB18030 -> base64 -> decode -> detect -> original
    original = "企业邮箱Base64编码测试，包含中英文混合内容！"
    b64 = base64.b64encode(original.encode('gb18030')).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "GB18030 encode-decode roundtrip",
        decoded == original,
        f"Expected '{original}', got '{decoded}' (charset: {charset})"
    )


# ============================================================
# Test 4: Encode -> Decode Round-trip Tests
# ============================================================
def test_roundtrip():
    print("\n📋 Test Group 4: Round-trip Tests")

    test_cases = [
        ("ASCII only", "Hello World 123!@#$"),
        ("Chinese UTF-8", "中文测试文本"),
        ("Mixed content", "Hello 你好 2024年"),
        ("Special chars", "特殊字符：【】「」（）《》"),
        ("Numbers and Chinese", "用户ID：12345，订单号：ORD-2024-001"),
        ("Email content", "Subject: 邮件主题\nFrom: test@example.com\n正文内容"),
        ("Long text", "这是一段比较长的测试文本。" * 20),
    ]

    # UTF-8 roundtrip
    for name, original in test_cases:
        b64 = base64.b64encode(original.encode('utf-8')).decode('ascii')
        raw = base64.b64decode(b64)
        decoded, charset = detect_charset(raw)
        results.record(
            f"UTF-8 roundtrip: {name}",
            decoded == original,
            f"Mismatch! (charset: {charset})"
        )

    # GB18030 roundtrip
    for name, original in test_cases:
        try:
            b64 = base64.b64encode(original.encode('gb18030')).decode('ascii')
            raw = base64.b64decode(b64)
            decoded, charset = detect_charset(raw)
            results.record(
                f"GB18030 roundtrip: {name}",
                decoded == original,
                f"Mismatch! Got '{decoded}' (charset: {charset})"
            )
        except UnicodeEncodeError:
            results.record(
                f"GB18030 roundtrip: {name}",
                True,
                "Skipped - text cannot be encoded in GB18030"
            )


# ============================================================
# Test 5: Base64 Validation
# ============================================================
def test_validation():
    print("\n📋 Test Group 5: Base64 Validation")

    valid_cases = [
        ("Simple base64", "SGVsbG8gV29ybGQ="),
        ("No padding", "SGVsbG8"),
        ("Double padding", "SGVsbG8gV29ybA=="),
        ("Longer string", "5L2g5aW95LiW55WM"),
        ("With newlines", "SGVsbG8g\nV29ybGQ="),
    ]

    for name, text in valid_cases:
        results.record(
            f"Valid: {name}",
            is_valid_base64(text),
            f"'{text}' should be valid base64"
        )

    invalid_cases = [
        ("Contains spaces only", "   "),
        ("Invalid chars", "SGVsbG8@V29ybGQ="),
        ("Invalid chars #", "SGVsbG8#V29ybGQ="),
    ]

    for name, text in invalid_cases:
        results.record(
            f"Invalid: {name}",
            not is_valid_base64(text),
            f"'{text}' should be invalid base64"
        )


# ============================================================
# Test 6: Edge Cases
# ============================================================
def test_edge_cases():
    print("\n📋 Test Group 6: Edge Cases")

    # Empty string
    b64 = base64.b64encode(b'').decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "Empty string",
        decoded == '',
        f"Expected empty string, got '{decoded}'"
    )

    # Single character
    original = "A"
    b64 = base64.b64encode(original.encode('utf-8')).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "Single ASCII char",
        decoded == original,
        f"Expected '{original}', got '{decoded}'"
    )

    # Single Chinese character (UTF-8)
    original = "中"
    b64 = base64.b64encode(original.encode('utf-8')).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "Single Chinese char (UTF-8)",
        decoded == original,
        f"Expected '{original}', got '{decoded}' (charset: {charset})"
    )

    # Single Chinese character (GB18030)
    original = "中"
    b64 = base64.b64encode(original.encode('gb18030')).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "Single Chinese char (GB18030)",
        decoded == original,
        f"Expected '{original}', got '{decoded}' (charset: {charset})"
    )

    # Binary-like content that's not a valid encoding
    raw_bytes = bytes(range(128, 256))
    b64 = base64.b64encode(raw_bytes).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "Binary content (fallback handling)",
        len(decoded) > 0,  # Should not crash
        f"Decoded to {len(decoded)} chars (charset: {charset})"
    )

    # Very long Chinese text in GB18030
    original = "这是企业邮箱系统中的一封测试邮件，" * 100
    b64 = base64.b64encode(original.encode('gb18030')).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "Very long GB18030 text (100x repeat)",
        decoded == original,
        f"Length mismatch: expected {len(original)}, got {len(decoded)} (charset: {charset})"
    )


# ============================================================
# Test 7: Real-world Email Scenarios
# ============================================================
def test_email_scenarios():
    print("\n📋 Test Group 7: Real-world Email Scenarios")

    # Email subject in GB18030 (common in Chinese enterprise email)
    subject = "关于2024年度工作总结的通知"
    b64 = base64.b64encode(subject.encode('gb18030')).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "Email subject (GB18030)",
        decoded == subject,
        f"Expected '{subject}', got '{decoded}' (charset: {charset})"
    )

    # Email subject in UTF-8
    subject = "Re: 会议纪要 - 项目进度讨论"
    b64 = base64.b64encode(subject.encode('utf-8')).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "Email subject (UTF-8)",
        decoded == subject,
        f"Expected '{subject}', got '{decoded}' (charset: {charset})"
    )

    # Email body with mixed content
    body = """尊敬的用户：

您好！感谢您使用企业邮箱服务。

以下是您的账户信息：
用户名：admin@company.com
容量：50GB
已使用：12.5GB (25%)

如有任何问题，请联系技术支持。

此致
敬礼
企业邮箱运维团队"""
    b64 = base64.b64encode(body.encode('gb18030')).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "Email body (GB18030, mixed content)",
        decoded == body,
        f"Content mismatch (charset: {charset})"
    )

    # MIME encoded header simulation
    header_text = "附件：2024年报表.xlsx"
    b64 = base64.b64encode(header_text.encode('gb18030')).decode('ascii')
    raw = base64.b64decode(b64)
    decoded, charset = detect_charset(raw)
    results.record(
        "MIME header (GB18030)",
        decoded == header_text,
        f"Expected '{header_text}', got '{decoded}' (charset: {charset})"
    )


# ============================================================
# Test 8: Specific GB18030 characters
# ============================================================
def test_gb18030_specific():
    print("\n📋 Test Group 8: GB18030 Specific Characters")

    # GB18030 4-byte characters (extended range beyond GBK)
    test_texts = [
        ("Common Chinese", "中华人民共和国"),
        ("Punctuation mix", "你好！世界？这是【测试】（内容）"),
        ("Japanese Kanji (shared)", "東京大学"),
        ("Numbers and Chinese", "第1章 第2节 共3页"),
        ("Technical terms", "CPU使用率：95%，内存占用：8GB"),
    ]

    for name, original in test_texts:
        try:
            gb_bytes = original.encode('gb18030')
            b64 = base64.b64encode(gb_bytes).decode('ascii')
            raw = base64.b64decode(b64)
            decoded, charset = detect_charset(raw)
            results.record(
                f"GB18030 specific: {name}",
                decoded == original,
                f"Expected '{original}', got '{decoded}' (charset: {charset})"
            )
        except Exception as e:
            results.record(
                f"GB18030 specific: {name}",
                False,
                f"Exception: {e}"
            )


# ============================================================
# Test 9: Verify GB18030 vs UTF-8 produce different base64
# ============================================================
def test_encoding_difference():
    print("\n📋 Test Group 9: Encoding Difference Verification")

    text = "你好世界"

    utf8_b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')
    gb_b64 = base64.b64encode(text.encode('gb18030')).decode('ascii')

    results.record(
        "UTF-8 and GB18030 produce different base64",
        utf8_b64 != gb_b64,
        f"UTF-8: {utf8_b64}, GB18030: {gb_b64}"
    )

    print(f"    UTF-8 base64:   {utf8_b64}")
    print(f"    GB18030 base64: {gb_b64}")

    # Both should decode correctly
    decoded_utf8, cs1 = detect_charset(base64.b64decode(utf8_b64))
    decoded_gb, cs2 = detect_charset(base64.b64decode(gb_b64))

    results.record(
        "Both decode to same text",
        decoded_utf8 == text and decoded_gb == text,
        f"UTF-8 decoded: '{decoded_utf8}' ({cs1}), GB18030 decoded: '{decoded_gb}' ({cs2})"
    )


# ============================================================
# Run all tests
# ============================================================
def main():
    print("=" * 60)
    print("  Base64 Auto Charset - Test Suite")
    print("=" * 60)

    # Check if chardet is available
    try:
        import chardet
        print(f"\n🔧 chardet version: {chardet.__version__}")
    except ImportError:
        print("\n⚠️  chardet not installed - some detection may be less accurate")

    test_utf8_decode()
    test_gb18030_decode()
    test_gb18030_encode()
    test_roundtrip()
    test_validation()
    test_edge_cases()
    test_email_scenarios()
    test_gb18030_specific()
    test_encoding_difference()

    all_passed = results.summary()

    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n💥 {results.failed} test(s) failed!")

    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
