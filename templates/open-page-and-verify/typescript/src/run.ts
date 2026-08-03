import { spawnSync, type SpawnSyncOptions } from "node:child_process";
import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

type JsonObject = Record<string, unknown>;

const BROWSER_CLI_REPOSITORY = "git+https://github.com/lexmount/browser-cli.git";
const here = dirname(fileURLToPath(import.meta.url));
const languageRoot = resolve(here, "..");
const artifactsDir = resolve(languageRoot, "artifacts");
const screenshotPath = resolve(artifactsDir, "page.png");

const argumentValue = (name: string, fallback: string): string => {
  const index = process.argv.indexOf(name);
  return index >= 0 && process.argv[index + 1] ? process.argv[index + 1] : fallback;
};

const targetUrl = argumentValue("--url", "https://www.baidu.com/");
const expectedUrl = argumentValue("--expected-url", "baidu.com");
const expectedTitle = argumentValue("--expected-title", "百度一下");

const run = (command: string, args: string[], options: SpawnSyncOptions = {}) => {
  return spawnSync(command, args, {
    encoding: "utf8",
    windowsHide: true,
    env: {
      ...process.env,
      PYTHONUTF8: "1",
      PYTHONIOENCODING: "utf-8",
    },
    ...options,
  });
};

const commandExists = (command: string): boolean => {
  const result = run(command, ["--version"]);
  return !result.error && result.status === 0;
};

const ensureBrowserCli = (): void => {
  if (commandExists("browser-cli")) return;

  if (!commandExists("uv")) {
    throw new Error("未找到 browser-cli 或 uv。请先安装 uv：https://docs.astral.sh/uv/");
  }

  console.log("首次运行：正在安装 browser-cli…");
  const install = run("uv", ["tool", "install", "--force", BROWSER_CLI_REPOSITORY], {
    stdio: "inherit",
  });
  if (install.status !== 0 || !commandExists("browser-cli")) {
    throw new Error("browser-cli 安装失败。");
  }
};

const runCliJson = (args: string[]): JsonObject => {
  const result = run("browser-cli", args);
  if (result.error || result.status !== 0) {
    throw new Error(`browser-cli 命令执行失败：${args.slice(0, 2).join(" ")}`);
  }

  try {
    return JSON.parse(String(result.stdout)) as JsonObject;
  } catch {
    throw new Error(`browser-cli 命令未返回有效 JSON：${args.slice(0, 2).join(" ")}`);
  }
};

const actionResult = (response: JsonObject): JsonObject => {
  return (response.result as JsonObject | undefined) ?? response;
};

const runtimeAuthUsable = (status: JsonObject): boolean => {
  if (status.runtime_auth_usable === true) return true;
  const credentials = status.api_key_credentials as JsonObject | undefined;
  return credentials?.usable_for_runtime === true;
};

const ensureAuthorized = (): void => {
  let status = runCliJson(["auth", "status"]);
  if (!runtimeAuthUsable(status)) {
    console.log("首次运行：即将打开 Lexmount 网页，请在网页中确认授权。无需输入 API Key 或 Project ID。");
    const login = run("browser-cli", ["auth", "login", "--open"], { stdio: "inherit" });
    if (login.status !== 0) throw new Error("网页授权未完成。");
    status = runCliJson(["auth", "status"]);
  }

  if (!runtimeAuthUsable(status)) throw new Error("当前授权不能用于云端浏览器任务。");

  const doctor = runCliJson(["doctor", "--json"]);
  if (doctor.ready_for_browser_actions !== true) {
    throw new Error("browser-cli 尚未准备好执行浏览器任务，请根据 doctor 输出修复后重试。");
  }
};

const main = (): void => {
  ensureBrowserCli();
  ensureAuthorized();
  mkdirSync(artifactsDir, { recursive: true });

  console.log(`正在验证：${targetUrl}`);
  let sessionId: string | null = null;
  let page: JsonObject = {};
  let screenshot: JsonObject = {};
  let cleanup = "session_not_created";
  let taskError: unknown;

  try {
    const created = runCliJson(["session", "create"]);
    const session = (created.session as JsonObject | undefined) ?? {};
    sessionId = typeof session.session_id === "string" ? session.session_id : null;
    if (!sessionId) throw new Error("云端浏览器创建成功，但没有返回可用的 Session。");

    runCliJson(["action", "open-url", "--session-id", sessionId, "--url", targetUrl]);
    runCliJson(["action", "wait-load-state", "--session-id", sessionId, "--state", "complete"]);
    runCliJson([
      "action", "wait-url", "--session-id", sessionId,
      "--url", expectedUrl, "--match", "contains",
    ]);
    runCliJson([
      "action", "wait-title", "--session-id", sessionId,
      "--title", expectedTitle, "--match", "contains",
    ]);
    page = actionResult(runCliJson(["action", "page-info", "--session-id", sessionId]));
    screenshot = actionResult(runCliJson([
      "action", "screenshot", "--session-id", sessionId, "--output", screenshotPath,
    ]));
  } catch (error) {
    taskError = error;
  } finally {
    if (sessionId) {
      try {
        const closed = runCliJson(["session", "close", "--session-id", sessionId]);
        cleanup = closed.closed === true ? "session_closed" : "session_close_unconfirmed";
      } catch {
        cleanup = "session_close_failed";
      }
    }
  }

  if (taskError) {
    throw new Error(`模板任务执行失败；清理状态：${cleanup}。`);
  }

  console.log(JSON.stringify({
    ok: true,
    url: page.url ?? targetUrl,
    title: page.title ?? null,
    screenshot: screenshot.path ?? screenshotPath,
    cleanup,
  }, null, 2));
};

try {
  main();
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
}
