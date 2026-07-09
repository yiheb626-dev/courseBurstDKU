const state = {
  courses: [],
  activeJobId: null,
  pollTimer: null,
  overrideVerified: false,
  language: "zh",
  lastJobs: [],
  lastActiveJob: null,
  timeSyncPayload: null,
  timeSyncCaptureSettleSeconds: null,
  timeSyncUseJobSuffix: false,
};

const LANGUAGE_STORAGE_KEY = "courseRush.language";

const I18N = {
  zh: {
    "common.none": "无",
    "common.unnamed": "(未命名)",
    "common.delete": "删除",
    "common.currentTab": "当前标签页",
    "common.unknownError": "未知错误",
    "common.yes": "YES",
    "common.no": "NO",
    "cart.empty": "还没有读取到购物车课程。请先启动专用浏览器并打开 Shopping Cart 页面。",
    "cart.requireNameOrNbr": "请至少填写课程名称或 Class Nbr",
    "cart.reading": "正在读取购物车课程...",
    "cart.connecting": "正在连接当前 Edge CDP 标签页并解析 Shopping Cart。",
    "cart.readFailed": "读取购物车失败",
    "cart.readFailedPeriod": "读取购物车失败。",
    "cart.readDone": "购物车课程已读取",
    "cart.noCourses": "未识别到课程",
    "cart.readCount": "已从 {url} 读取 {count} 门课程。",
    "cart.noRows": "未识别到课程行。候选文本 {count} 条；请确认浏览器停留在 Shopping Cart 列表区域。",
    "launch.createRunning": "正在创建任务...",
    "launch.createFailed": "创建失败",
    "launch.scheduled": "任务已定时",
    "launch.cliStarted": "CLI 已启动",
    "launch.longScheduleWarning": "提示：定时超过 10 分钟，可能发生会话超时；已按设置启用 10 分钟保活刷新。",
    "status.noJobs": "暂无任务。",
    "status.stopping": "正在停止任务...",
    "status.stopped": "任务已停止",
    "status.stopFailed": "停止失败",
    "jobStatus.created": "已创建",
    "jobStatus.scheduled": "已定时",
    "jobStatus.starting": "启动中",
    "jobStatus.capturing": "捕获中",
    "jobStatus.running": "运行中",
    "jobStatus.success": "成功",
    "jobStatus.completed": "已完成",
    "jobStatus.failed": "失败",
    "jobStatus.stopped": "已停止",
    "jobStatus.rejected": "已拒绝",
    "log.empty": "暂无日志。",
    "strategy.hybridLocked": "混合策略需要先验证 Override Code 后才能打开。",
    "strategy.hybridLockedStatus": "混合策略未解锁",
    "strategy.burstDefaultOpen": "Burst 已开放默认参数；如需修改 Burst 参数，请先验证 Override Code。",
    "strategy.hybridBackendReject": "混合策略需要先验证 Override Code；未验证时后端会拒绝创建任务。",
    "override.defaultStatus": "安全上限：默认每秒最多 5 个请求；Burst 默认参数可直接使用；Override Code 验证通过后最高开放至每秒 50 个请求并允许修改 Burst/混合参数。",
    "override.emptyPrompt": "请输入 Override Code 后再验证。默认上限仍为每秒 5 个请求。",
    "override.emptyStatus": "Override Code 为空",
    "override.verifying": "正在验证 Override Code...",
    "override.verifyingStatus": "正在验证速率上限 Override Code...",
    "override.verified": "验证通过：本次任务最高开放至每秒 {max} 个请求。",
    "override.verifiedStatus": "Override Code 验证通过",
    "override.failed": "验证失败：默认上限仍为每秒 5 个请求。",
    "override.invalidStatus": "Override Code 无效",
    "cleanup.cacheConfirm": "请先关闭专用 Edge。确认清理缓存和扩展数据，并保留登录态？",
    "cleanup.cacheCleaning": "正在清理浏览器缓存...",
    "cleanup.cacheDone": "缓存清理完成，释放约 {mb} MB",
    "cleanup.cacheLocked": "清理完成但有文件被占用，已释放约 {mb} MB",
    "cleanup.historyConfirm": "这会停止当前任务，并删除浏览器历史、任务状态和 CLI 日志；DKUHub cookies、登录数据和本地存储会保留。确认继续？",
    "cleanup.historyClearing": "正在清空历史记录...",
    "cleanup.historyDone": "历史记录已清空，释放约 {mb} MB",
    "cleanup.historyLocked": "历史清理完成但有文件被占用，已释放约 {mb} MB",
    "browser.launching": "正在启动专用浏览器...",
    "browser.launchFailed": "浏览器启动失败",
    "browser.launched": "浏览器已启动，PID {pid}",
    "timeSync.connecting": "正在连接腾讯 NTP 时间服务器...",
    "timeSync.fetching": "正在获取官方时间偏移...",
    "timeSync.fetched": "时间偏移已获取",
    "timeSync.failedStatus": "时间校准失败",
    "timeSync.failed": "时间校准失败：{error}。创建任务时会重试；失败则使用本机时间。",
    "timeSync.connectFailed": "无法连接时间服务器",
    "timeSync.disabled": "时间校准未启用。",
    "timeSync.jobFailed": "任务创建时校准失败：{error}。本次任务使用本机时间。",
    "timeSync.jobFormulaSuffix": " 本次任务会按该公式修正 CLI 启动时间。",
    "timeSync.ahead": "提前",
    "timeSync.behind": "延后",
    "timeSync.noAdjust": "不调整",
    "timeSync.resultWithSettle": "官方时间偏移 {offset} ms，RTT {rtt} ms；CLI 启动 = 自动启动时间 - 捕获沉淀 {settle}s - NTP offset，约{direction} {lead} ms。",
    "timeSync.resultOffsetOnly": "官方时间偏移 {offset} ms，RTT {rtt} ms；仅按 NTP offset 计算会{direction} {lead} ms。",
    "backend.hybridRequiresOverride": "混合策略需要先验证 override code。",
    "backend.burstDefaultOnly": "burst 未验证时只能使用默认参数。",
    "jobMessage.enrollmentDetected": "检测到选课成功，任务已停止。",
    "jobMessage.allRequestsFinished": "已完成全部配置的请求。",
    "jobMessage.allBurstFinished": "已完成全部配置的 Burst 轮次。",
    "jobMessage.allHybridFinished": "已完成全部配置的混合请求。",
    "jobMessage.replayingRequests": "正在重放请求。",
    "jobMessage.replayingBurst": "正在重放 Burst 请求。",
    "jobMessage.replayingSmooth": "正在重放平滑请求。",
    "jobMessage.playwrightMissing": "Playwright 未安装或无法加载。",
    "jobMessage.connectingCdp": "正在连接 Edge CDP。",
    "jobMessage.failedConnectCdp": "无法通过 CDP 连接 Edge。",
    "jobMessage.noTabs": "未找到已打开的 Edge 标签页。",
    "jobMessage.waitingManual": "正在等待手动点击 enroll。",
    "jobMessage.captureTimedOut": "超时且未匹配到请求。",
    "jobMessage.capturedReplaying": "已捕获请求模板，正在重放。",
    "jobMessage.launchingCli": "正在启动 CLI 窗口。",
    "jobMessage.cliLaunched": "CLI 窗口已启动。",
    "jobMessage.stoppedFromWeb": "已从网页控制台停止。",
    "jobMessage.scheduledRefreshed": "已定时，浏览器会话已刷新。",
    "jobMessage.jobCreated": "任务已创建。",
    "jobMessage.scheduledToStart": "已定时在 {time} 启动。",
    "jobMessage.timeSyncFailedLocal": "时间同步失败，将使用本机时间。{error}",
    "jobMessage.captureCandidate": "已捕获候选请求：{endpoint}",
    "jobMessage.failedLaunchCli": "启动 CLI 失败：{error}",
    "jobMessage.sessionRefreshFailed": "已定时，会话刷新失败：{error}",
    "service.noMatchingTab": "未找到匹配的浏览器标签页。请先打开购物车页面。",
    "service.cartReadFailed": "读取购物车失败：{error}",
    "service.edgeWindowsOnly": "当前仅支持在 Windows 上自动启动 Edge。",
    "service.edgeNotFound": "未找到 Microsoft Edge 可执行文件。请手动填写 Edge 路径。",
    "service.edgePathMissing": "Edge 可执行文件不存在：{path}",
    "service.edgeLaunchFailed": "启动 Edge 失败：{error}"
  },
  en: {
    "app.title": "Course Rush Control Console",
    "app.subtitle": "Bind a dedicated Edge enrollment page, read shopping cart courses, and launch course-rush jobs on schedule.",
    "tabs.aria": "Page tabs",
    "tabs.browser": "Dedicated Browser",
    "tabs.cart": "Shopping Cart Courses",
    "tabs.launch": "Launch Course Rush",
    "tabs.settings": "Settings",
    "app.webReady": "Web Ready",
    "common.restoreDefaults": "Restore Defaults",
    "common.refresh": "Refresh",
    "common.none": "None",
    "common.unnamed": "(Untitled)",
    "common.delete": "Delete",
    "common.currentTab": "current tab",
    "common.unknownError": "Unknown error",
    "common.yes": "YES",
    "common.no": "NO",
    "language.zh": "中文",
    "language.en": "English",
    "browser.title": "Dedicated Browser",
    "browser.intro": "Use this tab to bind the enrollment system. Start a dedicated Edge window, sign in to DKUHub there, and stay on the Shopping Cart page.",
    "browser.edgeExecutable": "Edge executable",
    "browser.edgeExecutablePlaceholder": "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "browser.debugPort": "CDP debug port",
    "browser.startUrl": "Start page",
    "browser.startUrlPlaceholder": "https://dkuhub.dku.edu.cn",
    "browser.userDataDir": "Dedicated browser user directory",
    "browser.userDataDirPlaceholder": "D:\\edge-cdp-profile",
    "browser.launchHint": "Starting will open an independent Edge window with remote debugging enabled.",
    "browser.launchButton": "Start Dedicated Browser",
    "cart.title": "Shopping Cart Courses",
    "cart.readButton": "Read Shopping Cart Courses",
    "cart.addButton": "Add Manually",
    "cart.readSummaryInitial": "The course table will be read from the current Shopping Cart page when possible. Execution still uses the captured enroll request.",
    "cart.courseName": "Course name",
    "cart.courseNamePlaceholder": "e.g. CS 201",
    "cart.component": "Type",
    "cart.componentPlaceholder": "LEC / REC / LAB",
    "cart.classNbr": "Class Nbr",
    "cart.classNbrPlaceholder": "1041",
    "cart.section": "Section",
    "cart.sectionPlaceholder": "01",
    "cart.instructor": "Instructor",
    "cart.instructorPlaceholder": "Instructor",
    "cart.note": "Note",
    "cart.notePlaceholder": "Priority, alternatives, etc.",
    "cart.table.course": "Course",
    "cart.table.component": "Type",
    "cart.table.classNbr": "Class Nbr",
    "cart.table.section": "Section",
    "cart.table.instructor": "Instructor",
    "cart.table.status": "Status",
    "cart.empty": "No shopping cart courses have been read yet. Start the dedicated browser and open the Shopping Cart page first.",
    "cart.requireNameOrNbr": "Enter at least a course name or Class Nbr.",
    "cart.reading": "Reading shopping cart courses...",
    "cart.connecting": "Connecting to the current Edge CDP tab and parsing Shopping Cart.",
    "cart.readFailed": "Failed to read shopping cart",
    "cart.readFailedPeriod": "Failed to read shopping cart.",
    "cart.readDone": "Shopping cart courses loaded",
    "cart.noCourses": "No courses recognized",
    "cart.readCount": "Read {count} course(s) from {url}.",
    "cart.noRows": "No course rows were recognized. Candidate text count: {count}. Confirm the browser is showing the Shopping Cart list area.",
    "launch.title": "Launch Course Rush",
    "launch.clearSchedule": "Clear Schedule",
    "launch.scheduledStart": "Auto start time",
    "launch.scheduleHint": "Schedule within 10 minutes when possible; a later time may let the login session expire.",
    "launch.keepSessionAlive": "Refresh the browser page every 10 minutes while waiting to keep the session active when possible",
    "launch.timeSyncEnabled": "Use Tencent NTP official time to calibrate the auto start time",
    "launch.timeServer": "Time server",
    "launch.getTimeOffset": "Get Time Offset",
    "launch.timeSyncStatusInitial": "The official time offset is fetched once when the job is created; actual CLI start time = auto start time - capture settle seconds - NTP offset.",
    "launch.createRun": "Create and Run Job",
    "launch.createRunning": "Creating job...",
    "launch.createFailed": "Failed to create job",
    "launch.scheduled": "Job scheduled",
    "launch.cliStarted": "CLI started",
    "launch.longScheduleWarning": "Tip: the schedule is more than 10 minutes away, so the session may time out; 10-minute keep-alive refresh is enabled by your settings.",
    "status.title": "Job Status",
    "status.currentJob": "Current job",
    "status.status": "Status",
    "status.round": "Round",
    "status.enrolled": "Succeeded",
    "status.message": "Message",
    "status.stop": "Stop Job",
    "status.noJobs": "No jobs.",
    "status.stopping": "Stopping job...",
    "status.stopped": "Job stopped",
    "status.stopFailed": "Failed to stop",
    "jobStatus.created": "Created",
    "jobStatus.scheduled": "Scheduled",
    "jobStatus.starting": "Starting",
    "jobStatus.capturing": "Capturing",
    "jobStatus.running": "Running",
    "jobStatus.success": "Success",
    "jobStatus.completed": "Completed",
    "jobStatus.failed": "Failed",
    "jobStatus.stopped": "Stopped",
    "jobStatus.rejected": "Rejected",
    "log.title": "CLI Sync Log",
    "log.empty": "No logs yet.",
    "settings.title": "Settings",
    "settings.intro": "Course-rush parameters live here. Defaults are conservative and include a safety limit of 5 requests per second.",
    "settings.language": "Language",
    "settings.cdpUrl": "Edge CDP URL",
    "settings.pageKeyword": "Page keyword",
    "settings.captureKeywords": "Capture keywords",
    "settings.captureTimeout": "Capture timeout seconds",
    "settings.captureSettleSeconds": "Capture settle seconds",
    "settings.autoClickEnroll": "Click Enroll once automatically to capture the request",
    "strategy.aria": "Course-rush strategy group",
    "strategy.title": "Course-rush Strategy Group",
    "strategy.hint": "Smooth is the default strategy. Burst can use its default parameters directly; editing Burst or using Hybrid requires an Override Code.",
    "strategy.smooth": "Smooth",
    "strategy.burst": "Burst",
    "strategy.hybrid": "Hybrid",
    "strategy.requestsPerSecond": "Requests per second",
    "strategy.totalRequests": "Total requests",
    "strategy.smoothHint": "Smooth mode sends one request at fixed intervals. Total requests of 0 means continue until success or manual stop.",
    "strategy.requestsPerBurstRound": "Requests per round",
    "strategy.burstRoundsPerSecond": "Burst rounds per second",
    "strategy.totalRounds": "Total rounds",
    "strategy.burstHint": "Burst mode sends multiple concurrent requests per round. Without verified Override Code, only default parameters can be used. Total rounds of 0 means continue until success or manual stop.",
    "strategy.initialBurstRounds": "Initial Burst rounds",
    "strategy.burstCount": "Burst requests per round",
    "strategy.hybridBurstRoundsPerSecond": "Burst rounds per second",
    "strategy.hybridSmoothRps": "Smooth-stage requests per second",
    "strategy.hybridHint": "Hybrid mode covers the opening moment with a short Burst phase, then switches to smooth single requests. Total requests of 0 means continue until success or manual stop. Requires Override Code to unlock.",
    "strategy.hybridLocked": "Verify Override Code before opening Hybrid strategy.",
    "strategy.hybridLockedStatus": "Hybrid strategy is locked",
    "strategy.burstDefaultOpen": "Burst default parameters are available. Verify Override Code before changing Burst parameters.",
    "strategy.hybridBackendReject": "Hybrid strategy requires verified Override Code; the backend will reject jobs when it is not verified.",
    "override.label": "Override Code",
    "override.placeholder": "Default max 5 requests/sec",
    "override.verify": "Verify",
    "override.defaultStatus": "Safety limit: default max 5 requests per second. Burst defaults are available directly. After Override Code verification, the max opens to 50 requests per second and Burst/Hybrid parameters can be changed.",
    "override.emptyPrompt": "Enter Override Code before verifying. The default limit remains 5 requests per second.",
    "override.emptyStatus": "Override Code is empty",
    "override.verifying": "Verifying Override Code...",
    "override.verifyingStatus": "Verifying rate-limit Override Code...",
    "override.verified": "Verified: this job can use up to {max} requests per second.",
    "override.verifiedStatus": "Override Code verified",
    "override.failed": "Verification failed: the default limit remains 5 requests per second.",
    "override.invalidStatus": "Invalid Override Code",
    "cleanup.cacheTitle": "Browser Cache Cleanup",
    "cleanup.cacheHint": "Clean cache, extension data, metrics, component packages, and model files for the dedicated Edge profile. DKUHub cookies/session, login data, and local storage are kept. Close the dedicated Edge window before cleaning.",
    "cleanup.cacheButton": "Clean Cache (Keep Login)",
    "cleanup.cacheConfirm": "Close the dedicated Edge window first. Clean cache and extension data while keeping the login session?",
    "cleanup.cacheCleaning": "Cleaning browser cache...",
    "cleanup.cacheDone": "Cache cleanup finished, freed about {mb} MB",
    "cleanup.cacheLocked": "Cleanup finished with some locked files, freed about {mb} MB",
    "cleanup.historyTitle": "Clear History",
    "cleanup.historyHint": "Delete browsing history, prediction records, and download history from the dedicated Edge profile, and clear job status, settings, and CLI logs. DKUHub cookies, login data, and local storage are not deleted.",
    "cleanup.historyButton": "Clear History",
    "cleanup.historyConfirm": "This will stop the current job and delete browser history, job status, and CLI logs. DKUHub cookies, login data, and local storage will be kept. Continue?",
    "cleanup.historyClearing": "Clearing history...",
    "cleanup.historyDone": "History cleared, freed about {mb} MB",
    "cleanup.historyLocked": "History cleanup finished with some locked files, freed about {mb} MB",
    "browser.launching": "Starting dedicated browser...",
    "browser.launchFailed": "Failed to start browser",
    "browser.launched": "Browser started, PID {pid}",
    "timeSync.connecting": "Connecting to Tencent NTP time server...",
    "timeSync.fetching": "Fetching official time offset...",
    "timeSync.fetched": "Time offset fetched",
    "timeSync.failedStatus": "Time calibration failed",
    "timeSync.failed": "Time calibration failed: {error}. Job creation will retry; if it still fails, local time will be used.",
    "timeSync.connectFailed": "Cannot connect to time server",
    "timeSync.disabled": "Time calibration is disabled.",
    "timeSync.jobFailed": "Calibration failed during job creation: {error}. This job uses local time.",
    "timeSync.jobFormulaSuffix": " This job will adjust the CLI start time with that formula.",
    "timeSync.ahead": "ahead",
    "timeSync.behind": "behind",
    "timeSync.noAdjust": "no adjustment",
    "timeSync.resultWithSettle": "Official time offset {offset} ms, RTT {rtt} ms; CLI start = auto start time - capture settle {settle}s - NTP offset, about {lead} ms {direction}.",
    "timeSync.resultOffsetOnly": "Official time offset {offset} ms, RTT {rtt} ms; using only NTP offset would be about {lead} ms {direction}.",
    "backend.hybridRequiresOverride": "Hybrid strategy requires a verified override code.",
    "backend.burstDefaultOnly": "Without verification, Burst can only use default parameters.",
    "jobMessage.enrollmentDetected": "Enrollment detected. Task stopped.",
    "jobMessage.allRequestsFinished": "All configured requests finished.",
    "jobMessage.allBurstFinished": "All configured burst rounds finished.",
    "jobMessage.allHybridFinished": "All configured hybrid requests finished.",
    "jobMessage.replayingRequests": "Replaying requests.",
    "jobMessage.replayingBurst": "Replaying burst requests.",
    "jobMessage.replayingSmooth": "Replaying smooth requests.",
    "jobMessage.playwrightMissing": "Playwright is not installed or cannot load.",
    "jobMessage.connectingCdp": "Connecting to Edge CDP.",
    "jobMessage.failedConnectCdp": "Failed to connect Edge by CDP.",
    "jobMessage.noTabs": "No open Edge tabs found.",
    "jobMessage.waitingManual": "Waiting for manual enroll click.",
    "jobMessage.captureTimedOut": "Timed out without matching request.",
    "jobMessage.capturedReplaying": "Captured request template. Replaying now.",
    "jobMessage.launchingCli": "Launching CLI window.",
    "jobMessage.cliLaunched": "CLI window launched.",
    "jobMessage.stoppedFromWeb": "Stopped from web dashboard.",
    "jobMessage.scheduledRefreshed": "Scheduled. Browser session refreshed.",
    "jobMessage.jobCreated": "Job created.",
    "jobMessage.scheduledToStart": "Scheduled to start at {time}.",
    "jobMessage.timeSyncFailedLocal": "Time sync failed; using local clock. {error}",
    "jobMessage.captureCandidate": "Captured candidate request: {endpoint}",
    "jobMessage.failedLaunchCli": "Failed to launch CLI: {error}",
    "jobMessage.sessionRefreshFailed": "Scheduled. Session refresh failed: {error}",
    "service.noMatchingTab": "No matching browser tab found. Open the shopping cart page first.",
    "service.cartReadFailed": "Failed to read shopping cart: {error}",
    "service.edgeWindowsOnly": "Automatic Edge launch is currently implemented for Windows only.",
    "service.edgeNotFound": "Microsoft Edge executable was not found. Fill the Edge path manually.",
    "service.edgePathMissing": "Edge executable does not exist: {path}",
    "service.edgeLaunchFailed": "Failed to launch Edge: {error}"
  }
};

const MESSAGE_TRANSLATIONS = [
  {pattern: /^混合策略需要先验证 override code。$/, key: "backend.hybridRequiresOverride"},
  {pattern: /^burst 未验证时只能使用默认参数。$/, key: "backend.burstDefaultOnly"},
  {pattern: /^Enrollment detected\. Task stopped\.$/, key: "jobMessage.enrollmentDetected"},
  {pattern: /^All configured requests finished\.$/, key: "jobMessage.allRequestsFinished"},
  {pattern: /^All configured burst rounds finished\.$/, key: "jobMessage.allBurstFinished"},
  {pattern: /^All configured hybrid requests finished\.$/, key: "jobMessage.allHybridFinished"},
  {pattern: /^Replaying requests\.$/, key: "jobMessage.replayingRequests"},
  {pattern: /^Replaying burst requests\.$/, key: "jobMessage.replayingBurst"},
  {pattern: /^Replaying smooth requests\.$/, key: "jobMessage.replayingSmooth"},
  {pattern: /^Playwright is not installed or cannot load\.$/, key: "jobMessage.playwrightMissing"},
  {pattern: /^Connecting to Edge CDP\.$/, key: "jobMessage.connectingCdp"},
  {pattern: /^Failed to connect Edge by CDP\.$/, key: "jobMessage.failedConnectCdp"},
  {pattern: /^No open Edge tabs found\.$/, key: "jobMessage.noTabs"},
  {pattern: /^Waiting for manual enroll click\.$/, key: "jobMessage.waitingManual"},
  {pattern: /^Timed out without matching request\.$/, key: "jobMessage.captureTimedOut"},
  {pattern: /^Captured request template\. Replaying now\.$/, key: "jobMessage.capturedReplaying"},
  {pattern: /^Launching CLI window\.$/, key: "jobMessage.launchingCli"},
  {pattern: /^CLI window launched\.$/, key: "jobMessage.cliLaunched"},
  {pattern: /^Stopped from web dashboard\.$/, key: "jobMessage.stoppedFromWeb"},
  {pattern: /^Scheduled\. Browser session refreshed\.$/, key: "jobMessage.scheduledRefreshed"},
  {pattern: /^Job created\./, key: "jobMessage.jobCreated"},
  {pattern: /^Scheduled to start at (.+?)\./, key: "jobMessage.scheduledToStart", params: (match) => ({time: match[1]})},
  {pattern: /^Time sync failed; using local clock\. (.+)$/, key: "jobMessage.timeSyncFailedLocal", params: (match) => ({error: match[1]})},
  {pattern: /^Captured candidate request: (.+)$/, key: "jobMessage.captureCandidate", params: (match) => ({endpoint: match[1]})},
  {pattern: /^Failed to launch CLI: (.+)$/, key: "jobMessage.failedLaunchCli", params: (match) => ({error: match[1]})},
  {pattern: /^Scheduled\. Session refresh failed: (.+)$/, key: "jobMessage.sessionRefreshFailed", params: (match) => ({error: match[1]})},
  {pattern: /^No matching browser tab found\. Open the shopping cart page first\.$/, key: "service.noMatchingTab"},
  {pattern: /^Failed to read shopping cart: (.+)$/, key: "service.cartReadFailed", params: (match) => ({error: match[1]})},
  {pattern: /^Automatic Edge launch is currently implemented for Windows only\.$/, key: "service.edgeWindowsOnly"},
  {pattern: /^Microsoft Edge executable was not found\. Fill the Edge path manually\.$/, key: "service.edgeNotFound"},
  {pattern: /^Edge executable does not exist: (.+)$/, key: "service.edgePathMissing", params: (match) => ({path: match[1]})},
  {pattern: /^Failed to launch Edge: (.+)$/, key: "service.edgeLaunchFailed", params: (match) => ({error: match[1]})}
];

const $ = (selector) => document.querySelector(selector);

function loadSavedLanguage() {
  try {
    const saved = localStorage.getItem(LANGUAGE_STORAGE_KEY);
    return saved === "en" ? "en" : "zh";
  } catch (error) {
    return "zh";
  }
}

function saveLanguage(language) {
  try {
    localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
  } catch (error) {
    // localStorage can be unavailable in private or restricted contexts.
  }
}

function t(key, params = {}, fallback = "") {
  const template = I18N[state.language]?.[key] ?? I18N.zh[key] ?? fallback ?? key;
  return String(template).replace(/\{(\w+)\}/g, (match, name) => (
    Object.prototype.hasOwnProperty.call(params, name) ? String(params[name]) : match
  ));
}

function rememberDefaultText(element, property) {
  const safeProperty = property.replace(/[^a-z0-9]/gi, "_");
  const dataKey = property === "textContent" ? "i18nDefault" : `i18nDefault${capitalize(safeProperty)}`;
  if (!element.dataset[dataKey]) {
    element.dataset[dataKey] = property === "textContent" ? getElementOwnText(element) : element.getAttribute(property) || "";
  }
  return element.dataset[dataKey];
}

function getElementOwnText(element) {
  const textNode = Array.from(element.childNodes).find((node) => (
    node.nodeType === Node.TEXT_NODE && node.textContent.trim()
  ));
  return textNode ? textNode.textContent.trim() : element.textContent.trim();
}

function setElementOwnText(element, value) {
  const textNode = Array.from(element.childNodes).find((node) => (
    node.nodeType === Node.TEXT_NODE && node.textContent.trim()
  ));
  if (!textNode) {
    element.textContent = value;
    return;
  }
  const leading = textNode.textContent.match(/^\s*/)[0];
  const trailing = textNode.textContent.match(/\s*$/)[0];
  textNode.textContent = `${leading}${value}${trailing}`;
}

function translatedTextForElement(element, key, property) {
  const fallback = rememberDefaultText(element, property);
  return I18N[state.language]?.[key] ?? fallback;
}

function applyLanguage() {
  document.documentElement.lang = state.language === "en" ? "en" : "zh-CN";
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.dataset.runtimeI18n || element.dataset.i18n;
    const params = parseRuntimeParams(element);
    setElementOwnText(element, t(key, params, translatedTextForElement(element, key, "textContent")));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    const key = element.dataset.i18nPlaceholder;
    element.setAttribute("placeholder", t(key, {}, translatedTextForElement(element, key, "placeholder")));
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((element) => {
    const key = element.dataset.i18nAriaLabel;
    element.setAttribute("aria-label", t(key, {}, translatedTextForElement(element, key, "aria-label")));
  });
  const languageSelect = $("#languageSelect");
  if (languageSelect) {
    languageSelect.value = state.language;
  }
  renderCourses();
  renderJobList(state.lastJobs);
  if (state.lastActiveJob) {
    renderActiveJob(state.lastActiveJob);
  }
  renderStoredTimeSyncResult();
}

function parseRuntimeParams(element) {
  if (!element.dataset.runtimeI18nParams) return {};
  try {
    return JSON.parse(element.dataset.runtimeI18nParams);
  } catch (error) {
    return {};
  }
}

function setTranslatedText(selector, key, params = {}) {
  const element = typeof selector === "string" ? $(selector) : selector;
  if (!element) return;
  element.dataset.runtimeI18n = key;
  element.dataset.runtimeI18nParams = JSON.stringify(params);
  setElementOwnText(element, t(key, params, translatedTextForElement(element, key, "textContent")));
}

function setRawText(selector, value) {
  const element = typeof selector === "string" ? $(selector) : selector;
  if (!element) return;
  delete element.dataset.runtimeI18n;
  delete element.dataset.runtimeI18nParams;
  element.textContent = value;
}

function setLanguage(language) {
  state.language = language === "en" ? "en" : "zh";
  saveLanguage(state.language);
  applyLanguage();
}

function rememberTimeSyncResult(payload, captureSettleSeconds = null, useJobSuffix = false) {
  state.timeSyncPayload = payload;
  state.timeSyncCaptureSettleSeconds = captureSettleSeconds;
  state.timeSyncUseJobSuffix = useJobSuffix;
  renderStoredTimeSyncResult();
}

function clearRememberedTimeSyncResult() {
  state.timeSyncPayload = null;
  state.timeSyncCaptureSettleSeconds = null;
  state.timeSyncUseJobSuffix = false;
}

function renderStoredTimeSyncResult() {
  if (!state.timeSyncPayload) return;
  const suffix = state.timeSyncUseJobSuffix ? t("timeSync.jobFormulaSuffix") : "";
  setRawText("#timeSyncStatus", formatTimeSyncResult(state.timeSyncPayload, state.timeSyncCaptureSettleSeconds) + suffix);
}

function translateMessage(message) {
  if (!message) return "";
  for (const entry of MESSAGE_TRANSLATIONS) {
    const match = String(message).match(entry.pattern);
    if (match) {
      const params = entry.params ? entry.params(match) : {};
      return t(entry.key, params, message);
    }
  }
  return message;
}

function formatJobStatus(status) {
  if (!status) return "-";
  return t(`jobStatus.${status}`, {}, status);
}

function activateTab(tabId) {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === tabId);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === tabId);
  });
}

function formDataToObject(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function formDataToSettings() {
  const data = formDataToObject($("#jobForm"));
  return {
    cdp_url: data.cdp_url,
    page_url_keyword: data.page_url_keyword,
    capture_keywords: data.capture_keywords,
    capture_timeout: Number(data.capture_timeout || 120),
    capture_settle_seconds: Number(data.capture_settle_seconds || 1.5),
    auto_click_enroll: $("#jobForm").elements.auto_click_enroll.checked,
    strategy_mode: data.strategy_mode || "smooth",
    smooth_requests_per_second: Number(data.smooth_requests_per_second || 2.5),
    smooth_total_requests: Number(data.smooth_total_requests || 50),
    burst_count: Number(data.burst_count || 5),
    burst_rounds_per_second: Number(data.burst_rounds_per_second || 0.9),
    burst_rounds: Number(data.burst_rounds || 10),
    hybrid_burst_count: Number(data.hybrid_burst_count || 5),
    hybrid_burst_rounds: Number(data.hybrid_burst_rounds || 2),
    hybrid_burst_rounds_per_second: Number(data.hybrid_burst_rounds_per_second || 0.9),
    hybrid_smooth_requests_per_second: Number(data.hybrid_smooth_requests_per_second || 2.5),
    hybrid_total_requests: Number(data.hybrid_total_requests || 50),
    rate_limit_override_code: data.rate_limit_override_code || "",
    keep_session_alive: $("#jobForm").elements.keep_session_alive.checked,
    time_sync_enabled: $("#jobForm").elements.time_sync_enabled.checked,
    time_sync_server: data.time_sync_server || "ntp.tencent.com",
    scheduled_start: normalizeLocalDateTime(data.scheduled_start),
    selected_courses: state.courses,
  };
}

function normalizeLocalDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toISOString();
}

function addCourse() {
  const course = {
    name: $("#courseName").value.trim(),
    class_nbr: $("#courseNbr").value ? Number($("#courseNbr").value) : null,
    component: $("#courseComponent").value.trim().toUpperCase(),
    section: $("#courseSection").value.trim(),
    instructor: $("#courseInstructor").value.trim(),
    note: $("#courseNote").value.trim(),
  };
  if (!course.name && !course.class_nbr) {
    setTranslatedText("#serverStatus", "cart.requireNameOrNbr");
    return;
  }
  state.courses.push(course);
  $("#courseName").value = "";
  $("#courseComponent").value = "";
  $("#courseNbr").value = "";
  $("#courseSection").value = "";
  $("#courseInstructor").value = "";
  $("#courseNote").value = "";
  renderCourses();
}

function removeCourse(index) {
  state.courses.splice(index, 1);
  renderCourses();
}

function renderCourses() {
  const table = $("#courseTable");
  if (!state.courses.length) {
    table.innerHTML = `<tr class="empty-row"><td colspan="7">${escapeHtml(t("cart.empty"))}</td></tr>`;
    return;
  }
  table.innerHTML = state.courses.map((course, index) => `
    <tr>
      <td>
        <strong>${escapeHtml(course.name || t("common.unnamed"))}</strong>
        ${course.source_text ? `<div class="job-meta">${escapeHtml(course.source_text).slice(0, 160)}</div>` : ""}
      </td>
      <td><span class="type-badge">${escapeHtml(course.component || componentFromSection(course.section) || "-")}</span></td>
      <td>${course.class_nbr || "-"}</td>
      <td>${escapeHtml(course.section || "-")}</td>
      <td>${escapeHtml(course.instructor || "-")}</td>
      <td>${escapeHtml(course.note || "-")}</td>
      <td><button type="button" class="link-btn" onclick="removeCourse(${index})">${escapeHtml(t("common.delete"))}</button></td>
    </tr>
  `).join("");
}

function componentFromSection(section) {
  const match = String(section || "").match(/-(LEC|LAB|REC|SEM|DIS|IND|RSC)\b/i);
  return match ? match[1].toUpperCase() : "";
}

async function readCartCourses() {
  const settings = formDataToSettings();
  setTranslatedText("#serverStatus", "cart.reading");
  setTranslatedText("#cartReadSummary", "cart.connecting");
  const response = await fetch("/api/cart/read", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({settings}),
  });
  const payload = await response.json();
  if (!response.ok || !payload.ok) {
    setRawText("#serverStatus", translateMessage(payload.message) || t("cart.readFailed"));
    setRawText("#cartReadSummary", translateMessage(payload.message) || t("cart.readFailedPeriod"));
    return;
  }

  state.courses = payload.courses || [];
  renderCourses();
  setTranslatedText("#serverStatus", state.courses.length ? "cart.readDone" : "cart.noCourses");
  if (state.courses.length) {
    setTranslatedText("#cartReadSummary", "cart.readCount", {
      url: payload.attached_url || t("common.currentTab"),
      count: state.courses.length,
    });
  } else {
    setTranslatedText("#cartReadSummary", "cart.noRows", {count: payload.candidate_count || 0});
  }
}

async function launchBrowser(event) {
  event.preventDefault();
  const browser = formDataToObject($("#browserForm"));
  setTranslatedText("#serverStatus", "browser.launching");
  const response = await fetch("/api/browser/launch", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({browser}),
  });
  const payload = await response.json();
  if (!response.ok || !payload.ok) {
    setRawText("#serverStatus", translateMessage(payload.message) || t("browser.launchFailed"));
    return;
  }
  setTranslatedText("#serverStatus", "browser.launched", {pid: payload.pid});
  $("#jobForm").elements.cdp_url.value = payload.cdp_url;
  if (payload.start_url) {
    const host = new URL(payload.start_url).host;
    if (host) $("#jobForm").elements.page_url_keyword.value = host;
  }
}

async function createJob(event) {
  event.preventDefault();
  const settings = formDataToSettings();
  const warningKey = scheduledStartWarningKey(settings.scheduled_start);
  if (warningKey) {
    setTranslatedText("#serverStatus", warningKey);
  } else {
    setTranslatedText("#serverStatus", "launch.createRunning");
  }
  const response = await fetch("/api/jobs", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({settings}),
  });
  const payload = await response.json();
  if (!response.ok) {
    setRawText("#serverStatus", translateMessage(payload.message || payload.error) || t("launch.createFailed"));
    return;
  }
  state.activeJobId = payload.job_id;
  renderTimeSyncFromJob(payload);
  setTranslatedText("#serverStatus", payload.status === "scheduled" ? "launch.scheduled" : "launch.cliStarted");
  renderActiveJob(payload);
  await refreshJobs();
  activateTab("launchTab");
  startPolling();
}

function scheduledStartWarningKey(scheduledStart) {
  if (!scheduledStart) return "";
  const start = new Date(scheduledStart);
  if (Number.isNaN(start.getTime())) return "";
  const minutes = (start.getTime() - Date.now()) / 60000;
  if (minutes > 10) {
    return "launch.longScheduleWarning";
  }
  return "";
}

async function refreshJobs() {
  const response = await fetch("/api/jobs");
  const payload = await response.json();
  renderJobList(payload.jobs || []);
}

function renderJobList(jobs) {
  state.lastJobs = jobs;
  const list = $("#jobList");
  if (!jobs.length) {
    list.innerHTML = `<div class="job-meta">${escapeHtml(t("status.noJobs"))}</div>`;
    return;
  }
  list.innerHTML = jobs.map((job) => `
    <div class="job-item ${job.job_id === state.activeJobId ? "active" : ""}" data-job-id="${escapeAttr(job.job_id)}">
      <div>
        <div class="job-id">${escapeHtml(job.job_id)}</div>
        <div class="job-meta">${escapeHtml(translateMessage(job.message || ""))}</div>
      </div>
      <span class="badge ${escapeAttr(job.status)}">${escapeHtml(formatJobStatus(job.status))}</span>
    </div>
  `).join("");
  list.querySelectorAll(".job-item").forEach((item) => {
    item.addEventListener("click", () => {
      state.activeJobId = item.dataset.jobId;
      loadActiveJob();
      startPolling();
    });
  });
}

async function loadActiveJob() {
  if (!state.activeJobId) return;
  const response = await fetch(`/api/jobs/${encodeURIComponent(state.activeJobId)}`);
  const payload = await response.json();
  if (response.ok) {
    renderActiveJob(payload);
  }
}

function renderActiveJob(job) {
  state.lastActiveJob = job;
  $("#activeJobId").textContent = job.job_id || t("common.none");
  $("#activeJobStatus").textContent = formatJobStatus(job.status) || "-";
  $("#activeRound").textContent = job.round_no || "0";
  $("#activeEnrolled").textContent = job.enrolled ? t("common.yes") : t("common.no");
  $("#activeMessage").textContent = translateMessage(job.message) || "-";
  if (job.log) {
    setRawText("#logBox", job.log);
  } else {
    setTranslatedText("#logBox", "log.empty");
  }
  $("#stopBtn").disabled = !job.job_id || ["success", "completed", "failed", "stopped"].includes(job.status);
}

async function stopActiveJob() {
  if (!state.activeJobId) return;
  setTranslatedText("#serverStatus", "status.stopping");
  const response = await fetch(`/api/jobs/${encodeURIComponent(state.activeJobId)}/stop`, {method: "POST"});
  const payload = await response.json();
  if (response.ok) {
    setTranslatedText("#serverStatus", "status.stopped");
    renderActiveJob(payload);
    await refreshJobs();
  } else {
    setRawText("#serverStatus", translateMessage(payload.error) || t("status.stopFailed"));
  }
}

async function cleanBrowserCache() {
  if (!confirm(t("cleanup.cacheConfirm"))) {
    return;
  }
  setTranslatedText("#serverStatus", "cleanup.cacheCleaning");
  const response = await fetch("/api/browser/clean-cache", {method: "POST"});
  const payload = await response.json();
  const mb = ((payload.removed_bytes || 0) / 1024 / 1024).toFixed(1);
  if (response.ok && payload.ok) {
    setTranslatedText("#serverStatus", "cleanup.cacheDone", {mb});
  } else {
    setTranslatedText("#serverStatus", "cleanup.cacheLocked", {mb});
  }
}

async function testTimeSync() {
  const form = $("#jobForm");
  const server = form.elements.time_sync_server.value.trim() || "ntp.tencent.com";
  setTranslatedText("#timeSyncStatus", "timeSync.connecting");
  setTranslatedText("#serverStatus", "timeSync.fetching");
  const response = await fetch("/api/time/sync", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({server}),
  });
  const payload = await response.json();
  if (response.ok && payload.ok) {
    rememberTimeSyncResult(payload);
    setTranslatedText("#serverStatus", "timeSync.fetched");
  } else {
    clearRememberedTimeSyncResult();
    setTranslatedText("#timeSyncStatus", "timeSync.failed", {error: payload.error || t("timeSync.connectFailed")});
    setTranslatedText("#serverStatus", "timeSync.failedStatus");
  }
}

async function verifyRateLimitOverride() {
  const codeInput = $("#jobForm").elements.rate_limit_override_code;
  const code = codeInput.value.trim();
  if (!code) {
    setTranslatedText("#overrideStatus", "override.emptyPrompt");
    setTranslatedText("#serverStatus", "override.emptyStatus");
    return;
  }

  setTranslatedText("#overrideStatus", "override.verifying");
  setTranslatedText("#serverStatus", "override.verifyingStatus");
  const response = await fetch("/api/rate-limit/verify", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({code}),
  });
  const payload = await response.json();
  if (response.ok && payload.ok) {
    state.overrideVerified = true;
    setTranslatedText("#overrideStatus", "override.verified", {max: Number(payload.max_requests_per_second || 50).toFixed(0)});
    setTranslatedText("#serverStatus", "override.verifiedStatus");
    updateStrategyLockState();
  } else {
    state.overrideVerified = false;
    setTranslatedText("#overrideStatus", "override.failed");
    setTranslatedText("#serverStatus", "override.invalidStatus");
    updateStrategyLockState();
  }
}

function renderTimeSyncFromJob(job) {
  const settings = job.config && job.config.settings;
  if (!settings || !settings.time_sync_enabled) {
    clearRememberedTimeSyncResult();
    setTranslatedText("#timeSyncStatus", "timeSync.disabled");
    return;
  }
  if (settings.time_offset_ms === null || settings.time_offset_ms === undefined || settings.time_offset_ms === "") {
    clearRememberedTimeSyncResult();
    setTranslatedText("#timeSyncStatus", "timeSync.jobFailed", {error: settings.time_sync_error || t("common.unknownError")});
    return;
  }
  rememberTimeSyncResult({
    server_name: settings.time_sync_server,
    offset_ms: settings.time_offset_ms,
    rtt_ms: settings.time_sync_rtt_ms,
    checked_at: settings.time_sync_checked_at,
  }, settings.capture_settle_seconds, true);
}

function formatTimeSyncResult(payload, captureSettleSeconds = null) {
  const offset = Number(payload.offset_ms || 0);
  const rtt = Number(payload.rtt_ms || 0);
  if (captureSettleSeconds !== null && captureSettleSeconds !== undefined && captureSettleSeconds !== "") {
    const settleMs = Number(captureSettleSeconds || 0) * 1000;
    const totalLeadMs = settleMs + offset;
    const direction = totalLeadMs > 0 ? t("timeSync.ahead") : totalLeadMs < 0 ? t("timeSync.behind") : t("timeSync.noAdjust");
    return t("timeSync.resultWithSettle", {
      offset: `${offset >= 0 ? "+" : ""}${offset.toFixed(1)}`,
      rtt: rtt.toFixed(1),
      settle: Number(captureSettleSeconds || 0).toFixed(1),
      direction,
      lead: Math.abs(totalLeadMs).toFixed(1),
    });
  }
  const direction = offset > 0 ? t("timeSync.ahead") : offset < 0 ? t("timeSync.behind") : t("timeSync.noAdjust");
  return t("timeSync.resultOffsetOnly", {
    offset: `${offset >= 0 ? "+" : ""}${offset.toFixed(1)}`,
    rtt: rtt.toFixed(1),
    direction,
    lead: Math.abs(offset).toFixed(1),
  });
}

async function clearHistory() {
  if (!confirm(t("cleanup.historyConfirm"))) {
    return;
  }
  setTranslatedText("#serverStatus", "cleanup.historyClearing");
  const response = await fetch("/api/history/clear", {method: "POST"});
  const payload = await response.json();
  const mb = ((payload.removed_bytes || 0) / 1024 / 1024).toFixed(1);
  state.activeJobId = null;
  state.lastActiveJob = null;
  $("#activeJobId").textContent = t("common.none");
  $("#activeJobStatus").textContent = "-";
  $("#activeRound").textContent = "-";
  $("#activeEnrolled").textContent = "-";
  $("#activeMessage").textContent = "-";
  setTranslatedText("#logBox", "log.empty");
  $("#stopBtn").disabled = true;
  await refreshJobs();
  if (response.ok && payload.ok) {
    setTranslatedText("#serverStatus", "cleanup.historyDone", {mb});
  } else {
    setTranslatedText("#serverStatus", "cleanup.historyLocked", {mb});
  }
}

function startPolling() {
  if (state.pollTimer) clearInterval(state.pollTimer);
  state.pollTimer = setInterval(async () => {
    await refreshJobs();
    await loadActiveJob();
  }, 1500);
}

async function loadDefaults() {
  const response = await fetch("/api/defaults");
  const payload = await response.json();
  applySettings(payload.settings || {});
  applyBrowserSettings(payload.browser || {});
}

async function loadBrowserDefaults() {
  const response = await fetch("/api/browser/defaults");
  const payload = await response.json();
  applyBrowserSettings(payload.browser || {});
}

function applySettings(settings) {
  const form = $("#jobForm");
  state.overrideVerified = false;
  for (const [key, value] of Object.entries(settings)) {
    const input = form.elements[key];
    if (!input) continue;
    if (input.type === "checkbox") {
      input.checked = Boolean(value);
      continue;
    }
    input.value = value ?? "";
  }
  activateStrategy(settings.strategy_mode || "smooth");
  updateStrategyLockState();
}

function applyBrowserSettings(browser) {
  const form = $("#browserForm");
  for (const [key, value] of Object.entries(browser)) {
    const input = form.elements[key];
    if (!input) continue;
    input.value = value ?? "";
  }
  if (browser.remote_debugging_port) {
    $("#jobForm").elements.cdp_url.value = `http://127.0.0.1:${browser.remote_debugging_port}`;
  }
}

function clearSchedule() {
  $("#jobForm").elements.scheduled_start.value = "";
}

function activateStrategy(strategy) {
  if (isStrategyLocked(strategy)) {
    setTranslatedText("#overrideStatus", "strategy.hybridLocked");
    setTranslatedText("#serverStatus", "strategy.hybridLockedStatus");
    updateStrategyLockState();
    return;
  }

  $("#jobForm").elements.strategy_mode.value = strategy;
  document.querySelectorAll(".strategy-tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.strategy === strategy);
  });
  document.querySelectorAll(".strategy-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `strategy${capitalize(strategy)}`);
  });
  if (strategy === "burst" && !state.overrideVerified) {
    setTranslatedText("#overrideStatus", "strategy.burstDefaultOpen");
  } else if (strategy === "hybrid" && !state.overrideVerified) {
    setTranslatedText("#overrideStatus", "strategy.hybridBackendReject");
  }
}

function updateStrategyLockState() {
  if (isStrategyLocked($("#jobForm").elements.strategy_mode.value)) {
    activateStrategy("smooth");
  }

  document.querySelectorAll(".strategy-tab").forEach((tab) => {
    const locked = isStrategyLocked(tab.dataset.strategy);
    tab.classList.toggle("locked", locked);
    tab.disabled = locked;
    tab.setAttribute("aria-disabled", locked ? "true" : "false");
  });
  document.querySelectorAll("#strategyBurst input").forEach((input) => {
    input.disabled = !state.overrideVerified;
  });
  document.querySelectorAll("#strategyHybrid input").forEach((input) => {
    input.disabled = !state.overrideVerified;
  });
}

function isStrategyLocked(strategy) {
  return strategy === "hybrid" && !state.overrideVerified;
}

function capitalize(value) {
  return String(value || "").charAt(0).toUpperCase() + String(value || "").slice(1);
}

function preventInputEnterSubmit(event) {
  if (event.key !== "Enter") return;
  const target = event.target;
  if (!target || target.tagName !== "INPUT") return;
  event.preventDefault();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

window.removeCourse = removeCourse;

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => activateTab(tab.dataset.tab));
});
$("#browserForm").addEventListener("submit", launchBrowser);
$("#browserDefaultsBtn").addEventListener("click", loadBrowserDefaults);
$("#readCartBtn").addEventListener("click", readCartCourses);
$("#addCourseBtn").addEventListener("click", addCourse);
$("#jobForm").addEventListener("submit", createJob);
$("#refreshBtn").addEventListener("click", async () => {
  await refreshJobs();
  await loadActiveJob();
});
$("#resetBtn").addEventListener("click", loadDefaults);
$("#clearScheduleBtn").addEventListener("click", clearSchedule);
$("#stopBtn").addEventListener("click", stopActiveJob);
$("#cleanCacheBtn").addEventListener("click", cleanBrowserCache);
$("#clearHistoryBtn").addEventListener("click", clearHistory);
$("#timeSyncBtn").addEventListener("click", testTimeSync);
$("#verifyOverrideBtn").addEventListener("click", verifyRateLimitOverride);
$("#jobForm").elements.rate_limit_override_code.addEventListener("input", () => {
  state.overrideVerified = false;
  setTranslatedText("#overrideStatus", "override.defaultStatus");
  updateStrategyLockState();
});
$("#languageSelect").addEventListener("change", (event) => {
  setLanguage(event.target.value);
});
document.querySelectorAll(".strategy-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    if (tab.disabled) return;
    activateStrategy(tab.dataset.strategy);
  });
});
document.addEventListener("keydown", preventInputEnterSubmit);

state.language = loadSavedLanguage();
applyLanguage();
loadDefaults();
refreshJobs();
updateStrategyLockState();
startPolling();
