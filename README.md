# Lexmount Templates

Lexmount Browser 的可运行模板集合。每个模板包含任务说明、Agent Prompt，以及可独立运行的 TypeScript/Python 入口。

## 模板列表

| 模板 | TypeScript | Python | 说明 |
| --- | --- | --- | --- |
| [`open-page-and-verify`](./templates/open-page-and-verify/) | ✅ | ✅ | 创建云端浏览器，打开网页，验证 URL 与标题并保存截图 |

## 目录结构

```text
lexmount-templates/
├── README.md
└── templates/
    └── open-page-and-verify/
        ├── README.md
        ├── prompt.md
        ├── typescript/
        └── python/
```

每个模板的运行命令、环境要求和验收条件都记录在对应目录的 `README.md` 中。

模板不要求开发者在仓库中保存 API Key 或 Project ID。未授权时，运行入口会打开 Lexmount 网页，让用户确认授权后继续执行。
