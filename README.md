# Base64 Auto Charset - Sublime Text Plugin

一个 Sublime Text 插件，支持 Base64 解码时自动检测字符集（UTF-8、GB18030/GBK/GB2312 等），以及使用指定字符集进行 Base64 编码。

## 功能

### 🔓 Base64 解码（自动字符集检测）
- 自动检测 Base64 解码后的字节流编码格式
- 支持 UTF-8、UTF-8 BOM、GB18030/GBK/GB2312、Big5、EUC-JP、Shift_JIS、EUC-KR 等
- 使用 `chardet` 库增强检测准确性（可选依赖）
- 支持无 padding 的 base64 字符串
- 可在原位替换或在新标签页中打开

### 🔒 Base64 编码
- **GB18030 编码**：将选中文本以 GB18030 字符集编码后转为 Base64
- **UTF-8 编码**：将选中文本以 UTF-8 字符集编码后转为 Base64

## 安装

### 方法一：手动安装
1. 打开 Sublime Text，菜单选择 `Preferences` → `Browse Packages...`
2. 将整个 `base64-decode-autocharset` 文件夹复制到 `Packages` 目录下
3. 重启 Sublime Text

### 方法二：软链接（开发模式）
```bash
ln -s /path/to/base64-decode-autocharset ~/Library/Application\ Support/Sublime\ Text/Packages/Base64AutoCharset
```

### 可选：安装 chardet
Sublime Text 4 使用 Python 3.8，可以安装 `chardet` 提高字符集检测准确性：
```bash
# 进入 Sublime Text 的 Python lib 目录安装
pip install chardet -t ~/Library/Application\ Support/Sublime\ Text/Lib/python38
```

> 注意：不安装 chardet 也可以正常使用，插件内置了常见字符集的检测逻辑。

## 使用方法

### 命令面板（主要方式）
按 `Cmd+Shift+P`（macOS）或 `Ctrl+Shift+P`（Windows/Linux），输入 `Base64`：

| 命令 | 功能 |
|------|------|
| `Base64: Decode (Auto Charset)` | 解码并自动检测字符集，原位替换 |
| `Base64: Decode to New Tab (Auto Charset)` | 解码到新标签页，不修改原文 |
| `Base64: Encode (GB18030)` | 以 GB18030 编码后转 Base64 |
| `Base64: Encode (UTF-8)` | 以 UTF-8 编码后转 Base64 |

### 右键菜单
选中文本后右键，可以看到 `Base64 Auto Charset` 子菜单。

### 主菜单
`Edit` → `Base64 Auto Charset` 子菜单。

## 使用场景

### 企业邮箱开发
在处理邮件协议（SMTP/IMAP）时，邮件头部的 Subject、From、To 等字段经常使用 Base64 编码，且可能是 GB18030 或 UTF-8 字符集：

```
# 邮件头中的 Base64 编码
Subject: =?gb18030?B?xOO6w8rAvec=?=
# 选中 "xOO6w8rAvec=" 后按 Ctrl+Shift+D
# 自动解码为：你好世界（检测到 GB18030 字符集）
```

### 调试接口数据
API 返回的 Base64 编码数据，可直接选中后解码查看原文。

## 字符集检测策略

检测顺序：
1. **UTF-8 BOM** - 检查 `\xef\xbb\xbf` 头部
2. **UTF-8** - 尝试 UTF-8 解码，如含非 ASCII 字节则用 chardet 辅助判断
3. **GB18030** - 尝试 GB18030 解码（兼容 GBK、GB2312）
4. **其他 CJK** - 依次尝试 Big5、EUC-JP、Shift_JIS、EUC-KR
5. **chardet 检测** - 使用 chardet 库进行统计分析
6. **Latin-1 兜底** - 最后使用 Latin-1（永远不会失败）

## 测试

```bash
python3 test_base64_auto_charset.py
```

测试覆盖 9 组共 48 个测试用例：
- UTF-8 Base64 解码
- GB18030 Base64 解码
- GB18030 Base64 编码
- UTF-8/GB18030 双向 Round-trip
- Base64 格式验证
- 边界情况
- 邮件场景模拟
- GB18030 特殊字符
- 编码差异验证

## 文件结构

```
base64-decode-autocharset/
├── Base64AutoCharset.py              # 插件主代码
├── Base64AutoCharset.sublime-commands # 命令面板配置
├── Default.sublime-keymap            # 快捷键配置
├── Context.sublime-menu              # 右键菜单
├── Main.sublime-menu                 # 主菜单
├── test_base64_auto_charset.py       # 测试脚本
└── README.md                         # 本文件
```

## License

MIT
