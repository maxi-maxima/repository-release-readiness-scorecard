# repository-release-readiness-scorecard

评估一个开源仓库是否已经具备可信公开发布的基础条件。

## 痛点

AI agents、MCP servers、成本控制、发布闸门和创作者工作流都在快速演进，但很多团队仍缺少小型、本地、可审计的工具：既能直接放进 CI，也能从终端运行，而且不需要把私有数据发送到第三方 SaaS。

## 为什么是现在

2026 年 6 月的趋势研究显示，MCP 作为 agent 集成标准、CLI-first coding agents、验证瓶颈、agent 安全控制、实用成本治理和内容自动化都在快速升温。本项目针对这些高信号运营缺口之一，提供一个小而可审计的工具。

## 安装

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows Git Bash
pip install -e .
```

除 Python 标准库外无需运行时依赖。

## 运行

```bash
python -m repository_release_readiness_scorecard examples/sample-repo
python -m repository_release_readiness_scorecard . --min-score 70
python -m repository_release_readiness_scorecard . --min-score 70 --require-check LICENSE --require-check tests
```

`--min-score` 可让 CI 自定义通过阈值。默认仍为 `80`，早期项目也可以调低阈值用于提示型报告。`--require-check` 还可以把指定发布卫生检查设为强制项，即使总分已达标也会单独把关。

## 示例输出

对 `examples/` 中的文件运行上面的命令，可以得到适合演示、Issue 报告和 CI 日志的确定性输出。

## 自检

```bash
python -m unittest discover -s tests
```

## 路线图

- 增加更丰富的机器可读输出，用于 CI annotations。
- 增加更多来自 agent 和 MCP 工作流的真实 fixture。
- 为没有 Python 环境的用户发布打包二进制。
- 增加用于 pull-request 自动化的 GitHub Action 示例。

## License

MIT
