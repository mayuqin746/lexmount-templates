# Agent Prompt

请使用 `browser-cli` 完成以下任务：

- 目标 URL：`https://www.baidu.com/`
- 验证条件：最终 URL 包含 `baidu.com`，页面标题包含“百度一下”
- 输出：最终 URL、页面标题、页面状态，以及一张页面截图

执行要求：

1. 先运行 `browser-cli auth status` 检查本地授权。
2. 如果当前未授权，运行 `browser-cli auth login --open`，让用户在打开的 Lexmount 网页中确认授权；不要要求用户复制或输入 API Key、Project ID 或其他密钥。
3. 授权完成后运行 `browser-cli doctor --json`，确认 `ready_for_browser_actions=true`。
4. 创建一个临时云端浏览器 Session，打开目标 URL，等待页面加载完成。
5. 验证最终 URL 和页面标题，读取页面信息并保存截图证据。
6. 返回结构化结果，至少包含 `ok`、`url`、`title`、`screenshot` 和 `cleanup`；不要返回 Session ID、`connect_url`、`inspect_url`、凭证或其他内部连接信息。
7. 无论任务成功或失败，都必须关闭本次创建的临时 Session。
