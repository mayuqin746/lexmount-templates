# 打开网页并验证标题

这是 Lexmount Templates 的第一个可运行 POC 模板。它会创建一个临时云端浏览器，访问目标网页，验证最终 URL 和页面标题，保存截图证据，并在结束时关闭 Session。

默认任务：

- 目标 URL：`https://www.baidu.com/`
- URL 应包含：`baidu.com`
- 标题应包含：`百度一下`

## 授权体验

模板不要求开发者手动填写 API Key、Project ID 或 `.env`。

- 已授权：直接执行任务。
- 未授权：运行程序时自动调用 `browser-cli auth login --open`，浏览器会打开 Lexmount 授权页面；用户确认后，程序继续执行。
- 授权信息只保存在本地，不写入仓库、命令输出或任务产物。

## 前置环境

- Git
- [uv](https://docs.astral.sh/uv/)：仅在本机尚未安装 `browser-cli` 时用于自动安装
- TypeScript 入口：Node.js 18+
- Python 入口：Python 3.10+

两个启动器都会检查 `browser-cli`。如果本机尚未安装，会执行：

```bash
uv tool install --force git+https://github.com/lexmount/browser-cli.git
```

## TypeScript 方式

```bash
git clone --depth 1 https://github.com/mayuqin746/lexmount-template-open-page-and-verify.git
cd lexmount-template-open-page-and-verify/typescript
npm install
npm start
```

自定义输入：

```bash
npm start -- --url https://example.com --expected-url example.com --expected-title "Example Domain"
```

## Python 方式

```bash
git clone --depth 1 https://github.com/mayuqin746/lexmount-template-open-page-and-verify.git
cd lexmount-template-open-page-and-verify/python
python run.py
```

自定义输入：

```bash
python run.py --url https://example.com --expected-url example.com --expected-title "Example Domain"
```

## 输出与验收

运行成功时，启动器只输出经过过滤的安全 JSON 摘要，不输出 Session ID、内部连接地址或凭证；同时在当前语言目录的 `artifacts/` 下生成：

- `page.png`：页面截图证据。

验收条件：

1. 网页授权过程中不要求用户手动输入密钥；
2. 云端浏览器 Session 创建成功；
3. 目标网页加载成功；
4. URL 和标题验证通过；
5. 截图成功写入；
6. 成功或失败后，临时 Session 均被关闭。
7. 终端输出中不包含 Session ID、`connect_url`、`inspect_url` 或凭证。

## 文件结构

```text
open-page-and-verify/
├── README.md
├── prompt.md
├── typescript/
│   ├── package.json
│   ├── tsconfig.json
│   └── src/run.ts
└── python/
    └── run.py
```
