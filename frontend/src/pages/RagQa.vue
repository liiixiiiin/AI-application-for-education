<template>
  <div class="rag-qa-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/courses' }">工作区</el-breadcrumb-item>
        <el-breadcrumb-item>RAG 问答</el-breadcrumb-item>
      </el-breadcrumb>
      <h1 class="page-title mt-4">RAG 问答</h1>
      <p class="page-subtitle">基于知识库的多轮对话问答，支持上下文记忆与引用追溯。</p>
    </div>

    <div class="chat-layout">
      <!-- Conversation sidebar -->
      <aside class="conv-sidebar">
        <div class="sidebar-header">
          <el-select
            v-model="selectedCourse"
            placeholder="选择课程"
            filterable
            :loading="loadingCourses"
            style="width: 100%"
            @change="onCourseChange"
          >
            <el-option v-for="c in courses" :key="c.id" :label="c.title" :value="c.id" />
          </el-select>
          <el-button class="new-conv-btn" @click="createNewConversation" :disabled="!selectedCourse">
            <Plus :size="16" /> 新对话
          </el-button>
        </div>
        <div class="conv-list">
          <div
            v-for="conv in conversations"
            :key="conv.id"
            class="conv-item"
            :class="{ active: conv.id === activeConvId }"
            @click="switchConversation(conv.id)"
          >
            <div class="conv-title">{{ conv.title }}</div>
            <div class="conv-time">{{ formatTime(conv.updated_at) }}</div>
            <button class="conv-delete" @click.stop="deleteConv(conv.id)" title="删除对话">
              <Trash2 :size="14" />
            </button>
          </div>
          <div v-if="!conversations.length && selectedCourse" class="conv-empty">
            暂无对话，发送消息将自动创建。
          </div>
        </div>
      </aside>

      <!-- Chat main area -->
      <div class="chat-main card">
        <!-- Settings bar -->
        <div class="chat-settings">
          <div class="settings-left">
            <span class="settings-label">Top-K</span>
            <el-input-number v-model="topK" :min="1" :max="10" controls-position="right" size="small" />
          </div>
          <div class="settings-right">
            <el-switch v-model="useWebSearch" active-text="联网" size="small" />
            <el-switch v-model="isEvaluationMode" active-text="RAGAS" size="small" />
          </div>
        </div>

        <!-- Messages -->
        <div class="messages-container" ref="messagesContainer">
          <div v-if="!messages.length" class="chat-empty">
            <MessageSquare :size="40" />
            <p>选择课程并输入问题，开始对话。</p>
          </div>
          <div v-for="msg in messages" :key="msg.id" class="message" :class="msg.role">
            <div class="message-avatar">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
            <div class="message-body">
              <div class="message-content" v-html="renderContent(msg.content)"></div>
              <!-- Citations for assistant messages -->
              <div v-if="msg.role === 'assistant' && msg.citations && msg.citations.length" class="msg-citations">
                <div class="citations-toggle" @click="msg._showCitations = !msg._showCitations">
                  <FileText :size="14" />
                  {{ msg.citations.length }} 条引用
                  <ChevronDown :size="14" :class="{ rotated: msg._showCitations }" />
                </div>
                <div v-if="msg._showCitations" class="citations-body">
                  <div v-for="(c, ci) in msg.citations" :key="ci" class="citation-card">
                    <div class="citation-title">{{ c.title_path || '未命名' }}</div>
                    <div class="citation-meta">{{ c.source_doc_name }} · {{ c.chunk_id }}</div>
                    <div class="citation-excerpt">{{ c.excerpt }}</div>
                  </div>
                </div>
              </div>
              <!-- Web search sources -->
              <div v-if="msg.role === 'assistant' && msg.webSources && msg.webSources.length" class="msg-web-sources">
                <div class="web-sources-toggle" @click="msg._showWebSources = !msg._showWebSources">
                  <Globe :size="14" />
                  {{ msg.webSources.length }} 条联网来源
                  <ChevronDown :size="14" :class="{ rotated: msg._showWebSources }" />
                </div>
                <div v-if="msg._showWebSources" class="web-sources-body">
                  <a
                    v-for="(ws, wi) in msg.webSources"
                    :key="wi"
                    class="web-source-card"
                    :href="ws.url"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <span class="web-source-index">[{{ ws.index || wi + 1 }}]</span>
                    <span class="web-source-title">{{ ws.title || ws.url }}</span>
                    <span v-if="ws.site_name" class="web-source-site">{{ ws.site_name }}</span>
                  </a>
                </div>
              </div>
              <!-- RAGAS scores -->
              <div v-if="msg._metrics && msg._metrics.length" class="msg-scores">
                <div
                  v-for="name in msg._metrics"
                  :key="name"
                  class="score-chip"
                  :class="msg._scores && msg._scores[name] != null ? getScoreClass(msg._scores[name]) : 'chip-na'"
                >
                  {{ formatMetricName(name) }}
                  {{ msg._scores && msg._scores[name] != null ? (msg._scores[name] * 100).toFixed(0) + '%' : 'N/A' }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- RAGAS ground truth input -->
        <div v-if="isEvaluationMode" class="ground-truth-bar">
          <el-input v-model="groundTruth" placeholder="标准答案（可选，用于 RAGAS 评测）" size="small" />
        </div>

        <!-- Input area -->
        <div class="chat-input-area">
          <el-input
            v-model="question"
            :placeholder="selectedCourse ? '输入问题…' : '请先选择课程'"
            :disabled="!selectedCourse"
            @keydown.enter.exact.prevent="sendMessage"
            size="large"
          />
          <el-button
            type="primary"
            :loading="sending"
            :disabled="!selectedCourse || !question.trim()"
            @click="sendMessage"
          >
            <Send :size="16" />
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref, watch } from "vue";
import { MessageSquare, Plus, Trash2, Send, FileText, ChevronDown, Globe } from "lucide-vue-next";
import { apiRequest, apiStream } from "../services/api";
import { renderMarkdown } from "../utils/markdown";
import { ElMessage } from "element-plus";

const courses = ref([]);
const loadingCourses = ref(false);
const selectedCourse = ref("");
const conversations = ref([]);
const activeConvId = ref("");
const messages = ref([]);
const question = ref("");
const topK = ref(5);
const useWebSearch = ref(false);
const isEvaluationMode = ref(false);
const groundTruth = ref("");
const sending = ref(false);
const messagesContainer = ref(null);

let _nextMsgId = 1;
const tempId = () => `tmp_${_nextMsgId++}`;

const formatTime = (iso) => {
  if (!iso) return "";
  const d = new Date(iso);
  return `${(d.getMonth() + 1).toString().padStart(2, "0")}/${d.getDate().toString().padStart(2, "0")} ${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
};

const formatMetricName = (name) => {
  const map = { faithfulness: "忠实度", answer_relevancy: "相关性", context_precision: "上下文精度", context_recall: "上下文召回" };
  return map[name] || name;
};

const getScoreClass = (score) => {
  if (score >= 0.8) return "chip-high";
  if (score >= 0.5) return "chip-medium";
  return "chip-low";
};

const renderContent = (text) => renderMarkdown(text);

const scrollToBottom = () => {
  nextTick(() => {
    const el = messagesContainer.value;
    if (el) el.scrollTop = el.scrollHeight;
  });
};

// ── Data loading ──

const loadCourses = async () => {
  loadingCourses.value = true;
  try {
    courses.value = await apiRequest("/courses");
    if (!selectedCourse.value && courses.value.length) {
      selectedCourse.value = courses.value[0].id;
    }
  } catch (e) {
    ElMessage.error(e.message || "加载课程失败");
  } finally {
    loadingCourses.value = false;
  }
};

const loadConversations = async () => {
  if (!selectedCourse.value) {
    conversations.value = [];
    return;
  }
  try {
    conversations.value = await apiRequest(`/conversations?course_id=${selectedCourse.value}`);
    if (conversations.value.length && !activeConvId.value) {
      await switchConversation(conversations.value[0].id);
    } else if (!conversations.value.length) {
      activeConvId.value = "";
      messages.value = [];
    }
  } catch (e) {
    ElMessage.error(e.message || "加载对话列表失败");
  }
};

const loadMessages = async (convId) => {
  try {
    const detail = await apiRequest(`/conversations/${convId}`);
    messages.value = (detail.messages || []).map((m) => ({ ...m, _showCitations: false, _scores: null, _metrics: null }));
    scrollToBottom();
  } catch (e) {
    ElMessage.error(e.message || "加载消息失败");
  }
};

// ── Conversation management ──

const onCourseChange = () => {
  activeConvId.value = "";
  messages.value = [];
  loadConversations();
};

const switchConversation = async (convId) => {
  activeConvId.value = convId;
  await loadMessages(convId);
};

const createNewConversation = async () => {
  if (!selectedCourse.value) return;
  try {
    const conv = await apiRequest("/conversations", {
      method: "POST",
      body: JSON.stringify({ course_id: selectedCourse.value }),
    });
    conversations.value = [conv, ...conversations.value];
    activeConvId.value = conv.id;
    messages.value = [];
  } catch (e) {
    ElMessage.error(e.message || "创建对话失败");
  }
};

const deleteConv = async (convId) => {
  try {
    await apiRequest(`/conversations/${convId}`, { method: "DELETE" });
    conversations.value = conversations.value.filter((c) => c.id !== convId);
    if (activeConvId.value === convId) {
      if (conversations.value.length) {
        await switchConversation(conversations.value[0].id);
      } else {
        activeConvId.value = "";
        messages.value = [];
      }
    }
  } catch (e) {
    ElMessage.error(e.message || "删除失败");
  }
};

// ── Send message ──

const sendMessage = async () => {
  if (!selectedCourse.value || !question.value.trim() || sending.value) return;

  sending.value = true;
  const userQuestion = question.value.trim();
  question.value = "";

  const userMsg = { id: tempId(), role: "user", content: userQuestion, citations: [], _showCitations: false, _scores: null, _metrics: null };
  messages.value.push(userMsg);
  scrollToBottom();

  const payload = {
    course_id: selectedCourse.value,
    question: userQuestion,
    top_k: topK.value,
    use_web_search: useWebSearch.value,
    conversation_id: activeConvId.value || undefined,
  };

  try {
    if (isEvaluationMode.value) {
      if (groundTruth.value.trim()) payload.ground_truth = groundTruth.value.trim();
      const endpoint = `/courses/${selectedCourse.value}/qa/evaluate`;
      const resp = await apiRequest(endpoint, { method: "POST", body: JSON.stringify(payload) });
      const assistantMsg = {
        id: tempId(),
        role: "assistant",
        content: resp.answer || "暂无回答",
        citations: resp.citations || [],
        _showCitations: false,
        _scores: resp.scores || null,
        _metrics: resp.metrics || null,
      };
      messages.value.push(assistantMsg);
      if (resp.conversation_id) handleConvId(resp.conversation_id);
      groundTruth.value = "";
    } else {
      const endpoint = `/courses/${selectedCourse.value}/qa/stream`;
      const assistantMsgId = tempId();
      const assistantMsg = { id: assistantMsgId, role: "assistant", content: "", citations: [], webSources: [], _showCitations: false, _showWebSources: false, _scores: null, _metrics: null };
      messages.value.push(assistantMsg);
      scrollToBottom();

      await apiStream(endpoint, { method: "POST", body: JSON.stringify(payload) }, (event, data) => {
        const idx = messages.value.findIndex((m) => m.id === assistantMsgId);
        if (idx === -1) return;
        if (event === "delta") {
          messages.value[idx].content += data?.text || "";
          scrollToBottom();
        } else if (event === "web_sources") {
          messages.value[idx].webSources = data?.sources || [];
          scrollToBottom();
        } else if (event === "done") {
          messages.value[idx].content = data?.answer || messages.value[idx].content || "暂无回答";
          messages.value[idx].citations = data?.citations || [];
          if (data?.web_sources?.length) {
            messages.value[idx].webSources = data.web_sources;
          }
          if (data?.conversation_id) handleConvId(data.conversation_id);
        } else if (event === "error") {
          ElMessage.error(data?.message || "请求失败");
        }
      });
    }
  } catch (e) {
    ElMessage.error(e.message || "请求失败");
  } finally {
    sending.value = false;
    scrollToBottom();
  }
};

const handleConvId = (convId) => {
  if (!activeConvId.value || activeConvId.value !== convId) {
    activeConvId.value = convId;
    loadConversations();
  }
};

// ── Init ──

watch(selectedCourse, () => {
  if (selectedCourse.value) loadConversations();
});

onMounted(async () => {
  await loadCourses();
  if (selectedCourse.value) await loadConversations();
});
</script>

<style scoped>
.rag-qa-page {
  max-width: 1300px;
  margin: 0 auto;
}

.mt-4 {
  margin-top: 16px;
}

/* ── Layout ── */

.chat-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 20px;
  height: calc(100vh - 240px);
  min-height: 500px;
}

/* ── Sidebar ── */

.conv-sidebar {
  display: flex;
  flex-direction: column;
  background: var(--color-card-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--color-border-soft);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.new-conv-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conv-item {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  position: relative;
  transition: background 0.15s;
}

.conv-item:hover {
  background: var(--color-bg-alt);
}

.conv-item.active {
  background: rgba(59, 130, 246, 0.08);
  border-left: 3px solid var(--color-primary);
}

.conv-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 24px;
}

.conv-time {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-top: 2px;
}

.conv-delete {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}

.conv-item:hover .conv-delete {
  opacity: 1;
}

.conv-delete:hover {
  color: var(--color-error);
  background: rgba(239, 68, 68, 0.08);
}

.conv-empty {
  text-align: center;
  color: var(--color-text-muted);
  font-size: 13px;
  padding: 24px 16px;
}

/* ── Chat main ── */

.chat-main {
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.chat-settings {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid var(--color-border-soft);
  background: var(--color-bg-alt);
}

.settings-left,
.settings-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.settings-label {
  font-size: 12px;
  color: var(--color-text-muted);
  font-weight: 600;
}

/* ── Messages ── */

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chat-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  gap: 12px;
}

.chat-empty p {
  font-size: 14px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: var(--color-primary);
  color: #fff;
}

.message.assistant .message-avatar {
  background: var(--color-border-soft);
  color: var(--color-text-secondary);
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.65;
  word-break: break-word;
}

.message.user .message-content {
  background: var(--color-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-content {
  background: var(--color-bg-alt);
  color: var(--color-text-main);
  border: 1px solid var(--color-border-soft);
  border-bottom-left-radius: 4px;
}

/* ── Markdown inside message bubbles ── */

.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3),
.message-content :deep(h4) {
  margin: 12px 0 6px;
  font-weight: 700;
  line-height: 1.4;
}

.message-content :deep(h1) { font-size: 18px; }
.message-content :deep(h2) { font-size: 16px; }
.message-content :deep(h3) { font-size: 15px; }
.message-content :deep(h4) { font-size: 14px; }

.message-content :deep(p) {
  margin: 6px 0;
}

.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 6px 0;
  padding-left: 20px;
}

.message-content :deep(li) {
  margin: 3px 0;
}

.message-content :deep(strong) {
  font-weight: 700;
}

.message-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 10px 0;
  font-size: 13px;
}

.message-content :deep(th),
.message-content :deep(td) {
  border: 1px solid var(--color-border);
  padding: 6px 10px;
  text-align: left;
}

.message-content :deep(th) {
  background: var(--color-border-soft);
  font-weight: 600;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', monospace;
}

.message-content :deep(pre) {
  background: #1e293b;
  color: #e2e8f0;
  padding: 12px 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 10px 0;
  font-size: 13px;
  line-height: 1.5;
}

.message-content :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.message-content :deep(blockquote) {
  border-left: 3px solid var(--color-primary);
  margin: 8px 0;
  padding: 4px 12px;
  color: var(--color-text-secondary);
}

.message-content :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border-soft);
  margin: 12px 0;
}

.message-content :deep(a) {
  color: var(--color-primary);
  text-decoration: none;
}

.message-content :deep(a:hover) {
  text-decoration: underline;
}

/* ── Math (KaTeX) ── */

.message-content :deep(.katex) {
  font-size: 1.02em;
}

.message-content :deep(.katex-display) {
  margin: 10px 0;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 4px 0;
}

.message-content :deep(.katex-display > .katex) {
  white-space: normal;
}

.message-content :deep(.katex-error) {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.08);
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 13px;
}

/* Inverted colors for the user bubble so KaTeX stays legible on the blue background. */
.message.user .message-content :deep(.katex),
.message.user .message-content :deep(.katex .mord),
.message.user .message-content :deep(.katex .mop),
.message.user .message-content :deep(.katex .mbin),
.message.user .message-content :deep(.katex .mrel) {
  color: #fff;
}

/* ── Citations ── */

.msg-citations {
  margin-left: 4px;
}

.citations-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-primary);
  cursor: pointer;
  font-weight: 600;
  padding: 4px 0;
}

.citations-toggle .rotated {
  transform: rotate(180deg);
}

.citations-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 6px;
}

.citation-card {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: #fff;
  border: 1px solid var(--color-border);
  font-size: 12px;
}

.citation-card .citation-title {
  font-weight: 600;
  margin-bottom: 2px;
}

.citation-card .citation-meta {
  color: var(--color-text-muted);
  margin-bottom: 4px;
}

.citation-card .citation-excerpt {
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* ── Web sources ── */

.msg-web-sources {
  margin-left: 4px;
  margin-top: 4px;
}

.web-sources-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-primary);
  cursor: pointer;
  user-select: none;
}

.web-sources-toggle .rotated {
  transform: rotate(180deg);
}

.web-sources-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 6px;
}

.web-source-card {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: #fff;
  border: 1px solid var(--color-border);
  font-size: 12px;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.15s;
}

.web-source-card:hover {
  border-color: var(--color-primary);
}

.web-source-index {
  color: var(--color-primary);
  font-weight: 600;
  flex-shrink: 0;
}

.web-source-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.web-source-site {
  color: var(--color-text-muted);
  flex-shrink: 0;
  font-size: 11px;
}

/* ── Scores ── */

.msg-scores {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-left: 4px;
}

.score-chip {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}

.chip-high {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.chip-medium {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.chip-low {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.chip-na {
  background: rgba(148, 163, 184, 0.1);
  color: #94a3b8;
}

/* ── Ground truth bar ── */

.ground-truth-bar {
  padding: 8px 20px;
  border-top: 1px solid var(--color-border-soft);
  background: rgba(245, 158, 11, 0.04);
}

/* ── Input area ── */

.chat-input-area {
  display: flex;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid var(--color-border-soft);
  background: var(--color-card-bg);
}

.chat-input-area .el-input {
  flex: 1;
}

/* ── Responsive ── */

@media (max-width: 900px) {
  .chat-layout {
    grid-template-columns: 1fr;
    height: auto;
  }

  .conv-sidebar {
    max-height: 200px;
  }
}
</style>
