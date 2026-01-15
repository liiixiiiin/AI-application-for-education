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
          </div>

          <el-form-item label="输入问题">
            <el-input
              v-model="question"
              type="textarea"
              :rows="4"
              placeholder="例如：主键和外键的作用是什么？"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </el-form>

        <div class="form-actions">
          <div class="form-hint">回答将附带引用片段（占位流程）。</div>
          <el-button type="primary" :loading="sending" @click="submitQuestion">
            发起问答
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
              <strong>占位流程</strong>
              <p>当前为占位实现，后续接入模型生成。</p>
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
import { apiRequest } from "../services/api";
import { ElMessage } from "element-plus";

const courses = ref([]);
const loadingCourses = ref(false);
const selectedCourse = ref("");
const question = ref("");
const topK = ref(5);
const sending = ref(false);
const history = ref([]);

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
  const payload = {
    course_id: selectedCourse.value,
    question: question.value.trim(),
    top_k: topK.value,
  };

  try {
    const response = await apiRequest(`/courses/${selectedCourse.value}/qa`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    history.value = [
      {
        id: `${Date.now()}`,
        question: payload.question,
        answer: response.answer || "暂无回答",
        citations: response.citations || [],
        time: new Date().toLocaleString(),
      },
      ...history.value,
    ];
    question.value = "";
  } catch (error) {
    ElMessage.error(error.message || "问答请求失败");
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
  grid-template-columns: 1fr 180px;
  gap: 16px;
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
