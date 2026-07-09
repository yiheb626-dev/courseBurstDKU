# Course Rush Web

这是给抢课脚本做的独立网页端项目。原始脚本没有被改动，副本保存在 `legacy/` 目录中。

## 功能

- 一键启动专用 Edge 窗口：自动带上 `--remote-debugging-port` 和独立 `--user-data-dir`。
- 在专用浏览器里打开选课系统页面，登录后供抢课任务捕获请求。
- 从 Shopping Cart 页面自动读取课程信息；读取失败时仍可手动补充。
- 任务启动后默认自动点击一次 `Enroll In Selected Classes` 来捕获真实请求，不再需要手动点击；如果页面按钮未识别，会回退为手动点击提示。
- 设置捕获关键词、捕获超时、抢课策略组参数和自动启动时间。
- 默认策略为平滑模式：每秒 2.5 个请求、总请求数 50；`总请求数 = 0` 才表示持续运行。
- 策略组提供平滑、burst、混合三种模式；burst 可直接使用默认参数，修改 burst 参数或使用混合模式需要 override code 验证通过。
- 默认强制安全上限：最多 5 个请求/秒；override code 验证通过后最高开放至 50 个请求/秒。
- 定时抢课建议设置在 10 分钟内；超过 10 分钟可能发生登录会话过期。开启保活后，等待期间会每 10 分钟刷新一次浏览器页面。
- 启动抢课任务后弹出独立 PowerShell CLI 窗口，窗口内返回捕获和抢课状态。
- Web 页面同步展示任务状态、轮次、是否成功和 CLI 日志尾部。

## 目录结构

```text
courseBurstDKU/
  legacy/                         # 原始脚本和说明副本
  run_web.py                      # 网页端启动入口
  src/course_rush_web/
    cli.py                        # 独立 CLI 任务入口
    core/
      burst_engine.py             # 捕获 + burst 重放核心逻辑
      models.py                   # 配置和状态模型
    services/
      browser_launcher.py         # 启动专用 Edge/CDP 浏览器
      cart_reader.py              # 从 Shopping Cart 页面读取课程
      job_store.py                # 配置、状态、日志文件读写
      task_manager.py             # 任务创建、定时、弹出 CLI、停止
    web/
      server.py                   # 标准库 HTTP JSON 服务
      templates/index.html        # 图形界面
      static/app.js               # 前端交互
      static/styles.css           # 页面样式
```

## 安装

```powershell
cd "D:\PycharmProjects\problemSolving\courseBurstDKU"
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## 启动网页端

```powershell
cd "D:\PycharmProjects\problemSolving\courseBurstDKU"
python .\run_web.py
```

启动后会自动打开默认浏览器进入控制台页面。默认访问地址：

```text
http://127.0.0.1:8765/
```

如果端口占用：

```powershell
python .\run_web.py --port 8777
```

如果只想启动服务、不自动打开浏览器：

```powershell
python .\run_web.py --no-open
```

## 使用流程

1. 打开网页端。
2. 在“专用浏览器”区域确认 Edge 路径、CDP 端口、起始页面和用户目录。
3. 点击“启动专用浏览器”，系统会弹出一个独立 Edge 窗口。
4. 在这个 Edge 窗口里登录选课系统，并停留在可以点击选课按钮的页面。
5. 点击“读取购物车课程”，确认页面里的课程表和 Shopping Cart 一致；LEC、REC、LAB、SEM 会分开显示。必要时可以手动补充。
6. 点击“创建并运行任务”，系统会弹出 PowerShell CLI 任务窗口。
7. 默认情况下，CLI 会自动点击一次 `Enroll In Selected Classes` 捕获请求；如果自动点击失败，CLI 会提示你手动点击一次。
8. 程序捕获真实请求后开始按配置 burst 重放，并在 CLI 和网页里同步状态。

课程表用于让你确认当前 Shopping Cart 内容和目标 Class Nbr；真正重放的 URL、headers、body 仍来自 Edge 中手动点击捕获到的 enroll 请求。运行日志里的 `TARGET CLASSES FROM REQUEST` 是最终实际抢课目标。

## 数据文件

运行时生成的数据保存在：

```text
courseBurstDKU/data/jobs/*.config.json
courseBurstDKU/data/jobs/*.status.json
courseBurstDKU/data/logs/*.log
```

专用浏览器用户数据默认保存在：

```text
courseBurstDKU/browser_profile/
```

`data/` 和 `browser_profile/` 都是运行时目录，不需要提交。
