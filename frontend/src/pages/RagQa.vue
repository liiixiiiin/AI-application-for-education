<template>
  <div class="rag-qa-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/courses' }">工作区</el-breadcrumb-item>
        <el-breadcrumb-item>RAG 问答</el-breadcrumb-item>
      </el-breadcrumb>
      <h1 class="page-title mt-4">RAG 问答</h1>
      <p class="page-subtitle">输入问题并查看引用片段，快速定位知识库来源。</p>
    </div>

    <div class="qa-layout">
      <div class="qa-main card">
        <el-form label-position="top" class="qa-form">
          <div class="form-row">
            <el-form-item label="选择课程">
              <el-select
                v-model="selectedCourse"
                placeholder="请选择课程"
                filterable
                :loading="loadingCourses"
                style="width: 100%"
              >
                <el-option
                  v-for="course in courses"
                  :key="course.id"
                  :label="course.title"
                  :value="course.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="检索深度">
              <el-input-number
                v-model="topK"
                :min="1"
                :max="10"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="启用 RAGAS 评测" class="eval-toggle">
              <el-switch v-model="isEvaluationMode" />
            </el-form-item>
          </div>

          <el-form-item label="输入问题">
            <el-input
              v-model="question"
              type="textarea"
              :rows="3"
              placeholder="例如：主键和外键的作用是什么？"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>

          <el-collapse-transition>
            <div v-if="isEvaluationMode">
              <el-form-item label="标准答案 (可选)" hint="提供标准答案可计算精度与召回率">
                <el-input
                  v-model="groundTruth"
                  type="textarea"
                  :rows="2"
                  placeholder="输入标准答案以进行更全面的评测..."
                />
              </el-form-item>
            </div>
          </el-collapse-transition>
        </el-form>

        <div class="form-actions">
          <div class="form-hint">
            {{
              isEvaluationMode
                ? "评测将计算忠实度、相关性等指标，耗时较长。"
                : "回答将附带引用片段，模型未配置时返回占位回复。"
            }}
          </div>
          <el-button
            :type="isEvaluationMode ? 'warning' : 'primary'"
            :loading="sending"
            @click="submitQuestion"
          >
            {{ isEvaluationMode ? "发起评测" : "发起问答" }}
          </el-button>
        </div>

        <div class="history-section">
          <div class="section-title">历史记录</div>
          <div v-if="history.length" class="history-list">
            <div v-for="item in history" :key="item.id" class="history-card">
              <div class="history-meta">
                <span class="history-label">问题</span>
                <span class="history-time">{{ item.time }}</span>
              </div>
              <div class="history-question">{{ item.question }}</div>

              <div class="history-block">
                <div class="history-label">回答</div>
                <p class="history-answer">{{ item.answer }}</p>
              </div>

              <div v-if="item.scores && Object.keys(item.scores).length" class="history-block">
                <div class="history-label">RAGAS 评测指标</div>
                <div class="score-grid">
                  <div v-for="(score, name) in item.scores" :key="name" class="score-item">
                    <div class="score-name">{{ formatMetricName(name) }}</div>
                    <div class="score-value" :class="getScoreClass(score)">
                      {{ (score * 100).toFixed(1) }}%
                    </div>
                  </div>
                </div>
              </div>

              <div class="history-block">
                <div class="history-label">引用</div>
                <div v-if="item.citations.length" class="citation-list">
                  <div
                    v-for="(citation, index) in item.citations"
                    :key="`${item.id}-${index}`"
                    class="citation-item"
                  >
                    <div class="citation-title">
                      {{ citation.title_path || "未命名章节" }}
                    </div>
                    <div class="citation-meta">
                      {{ citation.source_doc_name }} · {{ citation.chunk_id }}
                      <span v-if="citation.score !== undefined && citation.score !== null" class="citation-score">
                        (V: {{ ((1 - citation.score) * 100).toFixed(0) }}%
                        <span v-if="citation.bm25_score !== undefined && citation.bm25_score !== null">
                          / B: {{ (citation.bm25_score * 100).toFixed(0) }}%
                        </span>
                        <span v-if="citation.hybrid_score !== undefined && citation.hybrid_score !== null">
                          / H: {{ (citation.hybrid_score * 100).toFixed(0) }}%
                        </span>
                        <span v-if="citation.rerank_score !== undefined && citation.rerank_score !== null">
                          / R: {{ (citation.rerank_score * 100).toFixed(0) }}%
                        </span>)
                      </span>
                    </div>
                    <div class="citation-excerpt">
                      {{ citation.excerpt || "暂无片段内容" }}
                    </div>
                  </div>
                </div>
                <div v-else class="empty-hint">暂无引用片段。</div>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">还没有问答记录，试试提一个问题。</div>
        </div>
      </div>

      <div class="qa-sidebar">
        <div class="info-card">
          <div class="info-icon">
            <MessageSquare :size="18" />
          </div>
          <h3 class="info-title">使用提示</h3>
          <ul class="info-list">
            <li>
              <strong>引用展示</strong>
              <p>回答将展示引用片段与来源文档，便于核对。</p>
            </li>
            <li>
              <strong>检索深度</strong>
              <p>可调整 Top-K 值，控制引用数量。</p>
            </li>
            <li>
              <strong>模型配置</strong>
              <p>若后端已配置外部模型 API，将生成真实答案。</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { MessageSquare } from "lucide-vue-next";
import { apiRequest, apiStream } from "../services/api";
import { ElMessage } from "element-plus";

const courses = ref([]);
const loadingCourses = ref(false);
const selectedCourse = ref("");
const question = ref("");
const topK = ref(5);
const isEvaluationMode = ref(false);
const groundTruth = ref("");
const sending = ref(false);
const history = ref([]);

const formatMetricName = (name) => {
  const map = {
    faithfulness: "忠实度",
    answer_relevancy: "答案相关性",
    context_precision: "上下文精度",
    context_recall: "上下文召回率",
  };
  return map[name] || name;
};

const getScoreClass = (score) => {
  if (score >= 0.8) return "score-high";
  if (score >= 0.5) return "score-medium";
  return "score-low";
};

const prependHistoryItem = (item) => {
  history.value = [item, ...history.value];
};

const updateHistoryItem = (id, updates) => {
  const index = history.value.findIndex((item) => item.id === id);
  if (index === -1) return;
  history.value.splice(index, 1, { ...history.value[index], ...updates });
};

const loadCourses = async () => {
  loadingCourses.value = true;
  try {
    courses.value = await apiRequest("/courses");
    if (!selectedCourse.value && courses.value.length) {
      selectedCourse.value = courses.value[0].id;
    }
  } catch (error) {
    ElMessage.error(error.message || "加载课程失败");
  } finally {
    loadingCourses.value = false;
  }
};

const submitQuestion = async () => {
  if (!selectedCourse.value) {
    ElMessage.warning("请先选择课程");
    return;
  }
  if (!question.value.trim()) {
    ElMessage.warning("请输入问题");
    return;
  }
  if (sending.value) return;

  sending.value = true;
  const endpoint = isEvaluationMode.value
    ? `/courses/${selectedCourse.value}/qa/evaluate`
    : `/courses/${selectedCourse.value}/qa/stream`;

  const payload = {
    course_id: selectedCourse.value,
    question: question.value.trim(),
    top_k: topK.value,
  };

  if (isEvaluationMode.value && groundTruth.value.trim()) {
    payload.ground_truth = groundTruth.value.trim();
  }

  try {
    if (isEvaluationMode.value) {
      const response = await apiRequest(endpoint, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      prependHistoryItem({
        id: `${Date.now()}`,
        question: payload.question,
        answer: response.answer || "暂无回答",
        citations: response.citations || [],
        scores: response.scores || null,
        time: new Date().toLocaleString(),
      });
      question.value = "";
      groundTruth.value = "";
    } else {
      const entryId = `${Date.now()}`;
      let streamedAnswer = "";
      prependHistoryItem({
        id: entryId,
        question: payload.question,
        answer: "",
        citations: [],
        scores: null,
        time: new Date().toLocaleString(),
      });
      await apiStream(
        endpoint,
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
        (event, data) => {
          if (event === "delta") {
            const text = data?.text || "";
            if (text) {
              streamedAnswer += text;
              updateHistoryItem(entryId, { answer: streamedAnswer });
            }
            return;
          }
          if (event === "error") {
            ElMessage.error(data?.message || "请求失败");
            return;
          }
          if (event === "done") {
            updateHistoryItem(entryId, {
              answer: data?.answer || streamedAnswer || "暂无回答",
              citations: data?.citations || [],
            });
            question.value = "";
          }
        }
      );
    }
  } catch (error) {
    ElMessage.error(error.message || "请求失败");
  } finally {
    sending.value = false;
  }
};

onMounted(loadCourses);
</script>

<style scoped>
.rag-qa-page {
  max-width: 1200px;
  margin: 0 auto;
}

.mt-4 {
  margin-top: 16px;
}

.qa-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 24px;
}

.qa-form {
  margin-bottom: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 180px 140px;
  gap: 16px;
  align-items: flex-end;
}

.eval-toggle {
  margin-bottom: 18px;
  display: flex;
  justify-content: center;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.form-hint {
  color: var(--color-text-muted);
  font-size: 14px;
}

.score-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
  margin-top: 10px;
}

.score-item {
  background: #fff;
  border: 1px solid var(--color-border-soft);
  padding: 10px;
  border-radius: var(--radius-sm);
  text-align: center;
}

.score-name {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-bottom: 4px;
}

.score-value {
  font-size: 18px;
  font-weight: 700;
}

.score-high {
  color: #10b981;
}

.score-medium {
  color: #f59e0b;
}

.score-low {
  color: #ef4444;
}

.history-section {
  border-top: 1px solid var(--color-border-soft);
  padding-top: 24px;
}

.section-title {
  font-weight: 700;
  font-size: 16px;
  margin-bottom: 16px;
}

.history-list {
  display: grid;
  gap: 16px;
}

.history-card {
  padding: 20px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  background: var(--color-bg-alt);
}

.history-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--color-text-muted);
  font-size: 12px;
  margin-bottom: 6px;
}

.history-label {
  font-weight: 600;
  color: var(--color-text-secondary);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.history-question {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.history-block {
  margin-top: 12px;
}

.history-answer {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.citation-list {
  display: grid;
  gap: 12px;
  margin-top: 8px;
}

.citation-item {
  padding: 12px 14px;
  border-radius: var(--radius-sm);
  background: #fff;
  border: 1px solid var(--color-border);
}

.citation-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.citation-meta {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-bottom: 6px;
}

.citation-score {
  margin-left: 8px;
  color: var(--color-primary);
  font-weight: 500;
}

.citation-excerpt {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.empty-state,
.empty-hint {
  color: var(--color-text-muted);
  font-size: 14px;
  padding: 12px 0;
}

.qa-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-card {
  background: #fff;
  border-radius: var(--radius-md);
  padding: 24px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.info-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(59, 130, 246, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  margin-bottom: 12px;
}

.info-title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 700;
}

.info-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 12px;
  color: var(--color-text-secondary);
}

.info-list strong {
  display: block;
  margin-bottom: 4px;
  color: var(--color-text-main);
}

@media (max-width: 1024px) {
  .qa-layout {
    grid-template-columns: 1fr;
  }

  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
