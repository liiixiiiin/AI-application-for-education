# 教育系统技术路线方案 - 单人毕设版本

> **项目定位**: 单人毕设项目，需要平衡功能完整性和开发效率

## 一、架构设计（简化版）

### 1.1 整体架构（单体架构）
```
前端 (Next.js)
    ↓
后端API (Spring Boot 单体应用)
    ├── 业务逻辑层
    ├── AI服务集成层 (调用外部AI API)
    └── 数据访问层
    ↓
数据库 (MySQL/PostgreSQL + Redis)
```

**为什么选择单体架构？**
- ✅ 开发简单，无需服务治理
- ✅ 部署方便，一个应用搞定
- ✅ 调试容易，问题定位快
- ✅ 适合毕设展示，功能集中

### 1.2 技术栈选型（精简版）

#### 前端技术栈
- **框架**: Next.js 14+ (App Router)
  - 理由：功能强大，开发效率高，适合毕设展示
- **UI框架**: 
  - **Ant Design** (推荐，组件丰富，文档完善)
  - Tailwind CSS (可选，快速样式)
- **状态管理**: 
  - **Zustand** (轻量，够用)
  - React Query (服务端状态)
- **数据可视化**: 
  - **ECharts** (功能强大，中文文档好)
- **富文本编辑器**: 
  - **TipTap** (或直接用Ant Design的Input.TextArea，先实现功能)
- **代码编辑器**: 
  - **Monaco Editor** (编程题必需)
- **实时通信**: 
  - **WebSocket** (Spring Boot原生支持)

#### 后端技术栈（推荐：Java Spring Boot）

**核心框架**:
- **Spring Boot 3.x** (单体应用，不用Spring Cloud)
- **Spring Security** (认证授权)
- **Spring Data JPA** (数据持久化，简单)
- **Spring WebSocket** (实时通信)

**为什么选Java？**
- ✅ 企业级应用，毕设加分
- ✅ 生态完善，问题好解决
- ✅ 文档丰富，学习资源多
- ✅ 性能稳定，适合展示

**数据库选择**:
- **MySQL** (主数据库，简单易用，或PostgreSQL)
- **Redis** (缓存、会话，可选，初期可不用)
- **本地文件存储** (课件、文档，初期用本地，后期可升级OSS)

**AI集成方案**:
- **直接调用OpenAI API** (最简单，推荐)
  - 或使用国内API：通义千问、文心一言等
- **向量数据库**: 初期可不用，直接用API的上下文
  - 后期需要时用 **Chroma** (轻量级，Python，可独立部署)

#### AI服务（简化方案）

**方案一：直接调用API（推荐）**
- OpenAI GPT-4 API / GPT-3.5-turbo (成本低)
- 或 国内：通义千问、文心一言、智谱AI
- 优点：简单，无需部署，直接调用
- 缺点：需要API Key，有调用成本

**方案二：本地部署（可选）**
- Ollama + Qwen/Llama (免费，本地运行)
- 优点：免费，数据安全
- 缺点：需要GPU，配置复杂

**代码执行**:
- **Docker容器** (安全执行学生代码)
- 或使用 **Judge0 API** (在线判题服务，免费版可用)

---

## 二、核心功能实现方案（简化版）

### 2.1 教师侧 - 备课与设计

**简化实现**:
1. **文档上传**: 
   - 支持PDF/Word/TXT上传
   - 使用Apache POI解析Word，PDFBox解析PDF
   - 存储到数据库（文本内容）或文件系统

2. **内容生成**:
   ```
   上传文档 → 解析文本 → 调用AI API生成内容 → 保存到数据库
   ```
   - 使用OpenAI API，Prompt设计好即可
   - 生成JSON格式，前端渲染

3. **前端实现**:
   - 文件上传组件 (Ant Design Upload)
   - 富文本编辑器 (TipTap或简单TextArea)
   - 生成按钮 + Loading状态

### 2.2 教师侧 - 考核内容生成

**简化实现**:
1. **题目生成**:
   - 调用AI API，传入课程内容
   - 生成JSON格式题目（选择题、填空题、简答题、编程题）
   - 存储到数据库

2. **编程题**:
   - 前端：Monaco Editor
   - 后端：Docker执行代码（或Judge0 API）

### 2.3 教师侧 - 学情数据分析

**简化实现**:
1. **答案检测**:
   - 文本题：使用Embedding计算相似度（调用OpenAI Embeddings API）
   - 编程题：自动化测试

2. **数据分析**:
   - SQL聚合查询统计
   - ECharts可视化展示
   - AI生成分析报告（调用API）

### 2.4 学生侧 - 在线学习助手

**简化实现**:
1. **问答系统**:
   ```
   学生问题 → 检索相关课程内容 → 调用AI API生成回答 → 流式返回
   ```
   - 使用数据库全文检索（MySQL FULLTEXT）或简单关键词匹配
   - 调用AI API，传入课程上下文

2. **前端**:
   - 聊天界面（类似ChatGPT）
   - 流式显示（Server-Sent Events或WebSocket）

### 2.5 学生侧 - 实时练习评测

**简化实现**:
1. **题目生成**:
   - 基于学生历史数据，调用AI生成个性化题目

2. **实时评测**:
   - 文本题：异步处理，WebSocket返回结果
   - 编程题：Docker执行，实时返回

### 2.6 管理侧 - 大屏概览

**简化实现**:
1. **数据统计**:
   - SQL查询 + 定时任务（Spring Scheduled）
   - Redis缓存（可选）

2. **可视化**:
   - ECharts图表
   - 响应式布局

---

## 三、项目结构（单体架构）

### 3.1 前端项目结构
```
front/
├── app/                    # Next.js App Router
│   ├── (auth)/
│   │   ├── login/          # 登录页
│   │   └── register/       # 注册页
│   ├── (teacher)/
│   │   ├── prepare/        # 备课页面
│   │   ├── exam/           # 考核管理
│   │   └── analytics/      # 学情分析
│   ├── (student)/
│   │   ├── learn/          # 学习助手
│   │   └── practice/       # 练习评测
│   └── (admin)/
│       ├── users/          # 用户管理
│       ├── resources/      # 资源管理
│       └── dashboard/      # 大屏概览
├── components/
│   ├── ui/                # 基础组件
│   ├── editor/            # 编辑器组件
│   ├── charts/            # 图表组件
│   └── chat/              # 聊天组件
├── lib/
│   ├── api/               # API调用
│   └── utils/             # 工具函数
├── hooks/                 # 自定义Hooks
├── stores/                # 状态管理
└── types/                 # TypeScript类型
```

### 3.2 后端项目结构（Spring Boot单体）
```
backend/
├── src/main/java/com/edu/
│   ├── EduApplication.java          # 启动类
│   ├── config/                      # 配置类
│   │   ├── SecurityConfig.java      # 安全配置
│   │   ├── WebSocketConfig.java     # WebSocket配置
│   │   └── RedisConfig.java         # Redis配置（可选）
│   ├── controller/                  # 控制器层
│   │   ├── AuthController.java      # 认证
│   │   ├── UserController.java      # 用户管理
│   │   ├── CourseController.java    # 课程管理
│   │   ├── ContentController.java   # 内容生成
│   │   ├── ExamController.java      # 考核管理
│   │   ├── PracticeController.java  # 练习评测
│   │   ├── ChatController.java      # 问答助手
│   │   └── AnalyticsController.java # 数据分析
│   ├── service/                     # 业务逻辑层
│   │   ├── impl/                    # 实现类
│   │   └── AiService.java           # AI服务封装
│   ├── repository/                  # 数据访问层
│   │   └── *.Repository.java        # JPA Repository
│   ├── entity/                      # 实体类
│   │   ├── User.java
│   │   ├── Course.java
│   │   ├── Exam.java
│   │   └── ...
│   ├── dto/                         # 数据传输对象
│   ├── vo/                          # 视图对象
│   └── common/                      # 公共类
│       ├── Result.java              # 统一响应
│       └── ExceptionHandler.java    # 异常处理
├── src/main/resources/
│   ├── application.yml              # 配置文件
│   └── static/                      # 静态资源
└── pom.xml                          # Maven依赖
```

---

## 四、数据库设计（简化版）

### 核心表结构

```sql
-- 用户表
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('ADMIN', 'TEACHER', 'STUDENT') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 课程表
CREATE TABLE courses (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    teacher_id BIGINT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,                    -- 课程内容（JSON格式）
    knowledge_base TEXT,             -- 知识库文档内容
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(id)
);

-- 题目表
CREATE TABLE questions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    course_id BIGINT NOT NULL,
    type ENUM('CHOICE', 'FILL', 'SHORT', 'CODE') NOT NULL,
    content TEXT NOT NULL,           -- 题目内容（JSON格式）
    answer TEXT,                     -- 参考答案
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

-- 学生答案表
CREATE TABLE student_answers (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    student_id BIGINT NOT NULL,
    question_id BIGINT NOT NULL,
    answer TEXT NOT NULL,
    score DECIMAL(5,2),
    feedback TEXT,                   -- AI生成的反馈
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- 练习记录表
CREATE TABLE practice_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    student_id BIGINT NOT NULL,
    course_id BIGINT NOT NULL,
    question_id BIGINT NOT NULL,
    is_correct BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id),
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (question_id) REFERENCES questions(id)
);
```

---

## 五、开发阶段规划（单人版）

### Phase 1: 基础搭建 (1-2周)
- [ ] 前端项目初始化 (Next.js)
- [ ] 后端项目初始化 (Spring Boot)
- [ ] 数据库设计与创建
- [ ] 用户认证系统（登录/注册）
- [ ] 基础UI框架搭建

### Phase 2: 核心功能开发 (3-4周)
- [ ] 文档上传与解析
- [ ] AI内容生成（备课功能）
- [ ] 考核题目生成
- [ ] 在线学习助手（问答）
- [ ] 练习评测系统

### Phase 3: 数据分析与可视化 (1-2周)
- [ ] 学情数据分析
- [ ] 大屏概览开发
- [ ] 数据报表

### Phase 4: 优化与完善 (1-2周)
- [ ] 功能测试
- [ ] 性能优化
- [ ] 文档编写
- [ ] 部署准备

**总计**: 6-10周（可根据实际情况调整）

---

## 六、技术难点与解决方案（简化版）

### 6.1 AI API调用
- **难点**: API调用、流式响应、错误处理
- **方案**: 
  - 使用Spring的RestTemplate或WebClient
  - 流式响应使用Server-Sent Events
  - 统一异常处理

### 6.2 代码执行安全
- **难点**: 防止恶意代码
- **方案**: 
  - 使用Docker容器隔离
  - 资源限制（CPU、内存、时间）
  - 或使用Judge0 API（更简单）

### 6.3 实时通信
- **难点**: WebSocket实现
- **方案**: 
  - Spring WebSocket，简单易用
  - 或使用Server-Sent Events（更简单）

---

## 七、推荐技术栈总结（最终版）

### 前端
- **框架**: Next.js 14+ (App Router)
- **UI**: Ant Design
- **状态**: Zustand + React Query
- **图表**: ECharts
- **编辑器**: Monaco Editor

### 后端
- **框架**: Spring Boot 3.x (单体应用)
- **安全**: Spring Security
- **数据**: Spring Data JPA
- **数据库**: MySQL + Redis（可选）
- **实时**: Spring WebSocket

### AI服务
- **LLM**: OpenAI API / 国内API（通义千问等）
- **向量化**: OpenAI Embeddings API（或不用，直接用上下文）
- **代码执行**: Docker / Judge0 API

### 部署
- **容器化**: Docker
- **数据库**: MySQL（本地或云数据库）
- **部署**: 单机部署即可

---

## 八、开发建议

### 8.1 优先级建议
1. **先实现核心功能**，再优化细节
2. **先完成一个完整流程**（如备课→生成题目→学生答题），再扩展其他功能
3. **AI功能先用简单方案**（直接调用API），后期再优化

### 8.2 技术选型建议
- **如果熟悉Java**: 选Spring Boot，稳定可靠
- **如果熟悉Node.js**: 选NestJS，前后端统一
- **如果熟悉Python**: 选FastAPI，AI集成方便

### 8.3 毕设展示建议
- **重点展示AI功能**（内容生成、智能问答）
- **数据可视化**（大屏概览，视觉效果好）
- **完整流程演示**（从备课到学生答题到数据分析）

---

## 九、快速开始

### 1. 创建前端项目
```bash
npx create-next-app@latest front --typescript --tailwind --app
cd front
npm install antd @ant-design/icons zustand @tanstack/react-query echarts monaco-editor
```

### 2. 创建后端项目
- 使用Spring Initializr创建Spring Boot项目
- 选择依赖：Web, Security, JPA, MySQL, WebSocket

### 3. 配置数据库
- 创建MySQL数据库
- 配置application.yml

### 4. 开始开发
- 先实现用户认证
- 再实现核心业务功能
- 最后完善和优化

---

*此方案专为单人毕设项目设计，平衡功能完整性和开发效率。*

