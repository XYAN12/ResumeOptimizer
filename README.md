# Resume Optimizer Agent

一个从零实现的“简历优化 Agent”全栈应用。用户可以上传或粘贴简历，输入目标岗位 JD，先获得匹配分析，再在确认后生成忠于原始事实的优化版简历，并导出为 Markdown、DOCX、PDF。

## 项目特点

- Agent 风格的多阶段流程，而不是单次 prompt 拼接
- 显式拆分 `resume parser`、`jd analyzer`、`gap analysis`、`resume rewrite`、`export service`
- 强化事实约束：原始简历 facts 是最高优先级上下文
- 必须先分析、再由用户确认、最后才生成优化版简历
- 支持上传 `pdf`、`docx`、`md`、`txt` 或直接粘贴文本
- 支持导出为 `md`、`docx`、`pdf`
- 提供 Docker 构建与启动方式

## Docker 构建与启动

### 启动前准备

确保本机已安装：

- Docker
- Docker Compose

其中：

- macOS 和 Windows 通常使用 Docker Desktop
- Linux 通常使用 Docker Engine + Docker Compose Plugin

先在项目根目录创建 `.env`：

#### macOS / Linux

```bash
cp .env.example .env
```

#### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

#### Windows CMD

```cmd
copy .env.example .env
```

然后编辑 `.env`，至少填入：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

如果你不想启用 DeepSeek，也可以暂时留空，但 README 建议在正式体验 Agent 能力时配置该值。

### 使用 Docker Compose 启动

#### macOS

```bash
docker compose up --build
```

#### Linux

```bash
docker compose up --build
```

如果当前 Linux 用户没有 Docker 权限，可能需要：

```bash
sudo docker compose up --build
```

#### Windows PowerShell

```powershell
docker compose up --build
```

#### Windows CMD

```cmd
docker compose up --build
```

启动完成后访问：

- 前端: `http://localhost:8081`
- 后端: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

### 端口冲突时的启动方法

如果本机 `8081` 或 `8000` 已被占用，可以覆盖端口。

#### macOS / Linux

```bash
FRONTEND_PORT=8080 BACKEND_PORT=8001 docker compose up --build
```

#### Windows PowerShell

```powershell
$env:FRONTEND_PORT=8081
$env:BACKEND_PORT=8001
docker compose up --build
```

#### Windows CMD

```cmd
set FRONTEND_PORT=8081
set BACKEND_PORT=8001
docker compose up --build
```

对应访问地址会变为：

- 前端: `http://localhost:8081`
- 后端: `http://localhost:8001`
- Swagger: `http://localhost:8001/docs`

### 后台启动

如果希望容器在后台运行：

#### macOS / Linux

```bash
docker compose up -d --build
```

#### Windows PowerShell / CMD

```powershell
docker compose up -d --build
```

### 停止服务

#### macOS / Linux

```bash
docker compose down
```

#### Windows PowerShell / CMD

```powershell
docker compose down
```

### 单独构建

```bash
docker build -f backend/Dockerfile -t resume-optimizer-backend .
docker build -f frontend/Dockerfile -t resume-optimizer-frontend .
```

## 项目结构

```text
.
├── backend
│   ├── app
│   │   ├── api
│   │   ├── core
│   │   ├── models
│   │   ├── services
│   │   └── utils
│   ├── tests
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
├── frontend
│   ├── src
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── .env.example
└── README.md
```

## 架构设计

### 1. Agent Pipeline

应用采用显式多阶段 Agent 编排：

1. `resume parser`
   从原始简历文本或上传文件中抽取文本，并整理成结构化 `ResumeFacts`。

2. `jd analyzer`
   对 JD 做职责、技能、关键词和资历要求抽取，生成 `JDProfile`。

3. `gap analysis`
   基于 `ResumeFacts + JDProfile` 输出：
   - 匹配亮点
   - 主要缺口
   - 具体优化建议
   - 事实约束说明

4. `resume rewrite`
   仅在用户确认后执行。
   改写阶段只允许复用 `ResumeFacts` 里的结构化事实，不允许自由添加信息。

5. `export service`
   将最终 markdown 导出为 `md`、`docx`、`pdf`。

### 2. Context Engineering / Memory

内存状态由 `AgentMemoryStore` 管理，每次分析都会创建一个 `session_id`，关联以下上下文：

- `resume_text`: 原始简历文本
- `resume_facts`: 结构化事实，高优先级上下文
- `jd_text`: 原始 JD
- `jd_profile`: 解析后的目标岗位上下文
- `analysis`: 分析结论与 trace
- `rewrite`: 改写结果与 trace
- `approval_required`: 是否仍需用户确认

### 3. 事实约束策略

`rewrite` 阶段必须遵守以下约束：

- 不允许新增未经原始简历支持的公司、学校、项目、技术栈、奖项、指标、时间线
- 如果 JD 中出现而简历 facts 中不存在，只能作为 gap 提示，不能伪造补齐
- 前端会显式展示“需先确认后生成”的流程

## 环境变量

从环境变量读取配置，API Key 不会硬编码在代码或文档示例里。

核心变量：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- `RESUME_OPTIMIZER_APP_ENV`
- `RESUME_OPTIMIZER_DEBUG`
- `RESUME_OPTIMIZER_EXPORT_DIR`

复制样例配置：

```bash
cp .env.example .env
```

然后在 `.env` 中至少补充：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

说明：

- `DEEPSEEK_API_KEY` 必须写在 `.env` 中或通过系统环境变量注入，不能直接写进代码。
- 如果暂时不填写 `DEEPSEEK_API_KEY`，当前项目仍可启动，但会使用本地 deterministic 流程，而不是远程模型增强版流程。
- Docker Compose 会自动读取项目根目录下的 `.env`。

## 本地开发

### 后端

```bash
python3 -m pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：

- API 文档: `http://localhost:8000/docs`
- 健康检查: `http://localhost:8000/api/health`

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问：

- 前端页面: `http://localhost:5173`

如果前端不在默认地址访问，可以设置：

```bash
VITE_API_BASE_URL=http://localhost:8000/api
```

## 示例使用流程

1. 打开前端页面。
2. 上传简历文件，或粘贴原始简历文本。
3. 粘贴目标岗位 JD。
4. 点击“开始分析”，查看：
   - 匹配亮点
   - 主要缺口
   - 具体优化建议
   - 事实约束
5. 用户确认后，点击“生成优化版简历”。
6. 在线查看优化结果。
7. 导出为 Markdown、DOCX、PDF。

## API 概览

### `POST /api/resume/analyze-text`

请求体：

```json
{
  "resume_text": "原始简历文本",
  "jd_text": "目标岗位 JD"
}
```

### `POST /api/resume/analyze-file`

表单字段：

- `file`
- `jd_text`

### `POST /api/resume/rewrite`

请求体：

```json
{
  "session_id": "会话 ID",
  "confirmed": true
}
```

### `POST /api/resume/export`

请求体：

```json
{
  "session_id": "会话 ID",
  "format": "pdf"
}
```

## 错误处理

当前实现覆盖了这些基础错误处理：

- 空输入校验
- 文件格式校验
- 文件大小限制
- 会话不存在
- 未确认前禁止生成优化版简历
- 未生成优化结果前禁止导出
- 文件解析失败
- DeepSeek API 调用失败时抛出明确错误

## 测试与验证

已提供后端测试：

```bash
python3 -m pytest backend/tests -c backend/pytest.ini
```

## 当前实现说明

- 当前默认分析与改写流程采用本地 deterministic service，以保证无外部依赖时也能运行与测试。
- `DeepSeekClient` 已预留，API Key 通过环境变量读取，可在后续将分析和改写阶段替换为更严格的结构化 LLM 输出。
- 内存存储当前使用进程内 `AgentMemoryStore`，适合 demo 和单机部署；生产化可替换为 Redis 或数据库。

## 合理假设

- 这是一个可公开发布到 GitHub 的 demo / MVP 项目，因此优先保证结构清晰、可运行、可 Docker 化、可扩展。
- PDF 导出采用基础文本排版而非复杂模板化简历布局。
- 若未配置 `DEEPSEEK_API_KEY`，应用仍可工作，但使用本地规则型 Agent 服务，而不是远程模型增强版分析。
