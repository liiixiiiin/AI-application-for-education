<template>
  <div class="session-root">
    <!-- ==================== SUMMARY VIEW ==================== -->
    <div v-if="showSummary" class="summary-page">
      <div class="summary-container">
        <div class="summary-header">
          <h1 class="summary-title">练习完成</h1>
          <p class="summary-subtitle">以下是本次练习的统计数据</p>
        </div>

        <div class="summary-grid">
          <div class="summary-ring-card">
            <div class="ring-wrapper">
              <svg viewBox="0 0 120 120" class="ring-svg">
                <circle cx="60" cy="60" r="52" fill="none" stroke="#f1f5f9" stroke-width="10" />
                <circle
                  cx="60" cy="60" r="52"
                  fill="none"
                  :stroke="accuracyRate >= 0.6 ? '#22c55e' : '#f59e0b'"
                  stroke-width="10"
                  stroke-linecap="round"
                  :stroke-dasharray="`${accuracyRate * 326.73} 326.73`"
                  stroke-dashoffset="0"
                  transform="rotate(-90 60 60)"
                  class="ring-progress"
                />
              </svg>
              <div class="ring-text">
                <span class="ring-pct">{{ Math.round(accuracyRate * 100) }}%</span>
                <span class="ring-label">正确率</span>
              </div>
            </div>
          </div>

          <div class="summary-stats-card">
            <div class="stat-row">
              <span class="stat-label">总题数</span>
              <span class="stat-value">{{ exercises.length }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">正确</span>
              <span class="stat-value correct">{{ correctCount }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">错误</span>
              <span class="stat-value wrong">{{ wrongCount }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">未评测</span>
              <span class="stat-value">{{ exercises.length - Object.keys(gradingResults).length }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">用时</span>
              <span class="stat-value">{{ formattedTime }}</span>
            </div>
          </div>
        </div>

        <div v-if="typeStats.length" class="summary-section">
          <h3 class="section-heading">各题型正确率</h3>
          <div class="type-stats">
            <div v-for="ts in typeStats" :key="ts.type" class="type-stat-item">
              <span class="type-stat-label">{{ typeLabel(ts.type) }}</span>
              <div class="type-stat-bar-track">
                <div
                  class="type-stat-bar-fill"
                  :style="{ width: ts.rate * 100 + '%' }"
                  :class="{ good: ts.rate >= 0.6, poor: ts.rate < 0.6 }"
                />
              </div>
              <span class="type-stat-pct">{{ Math.round(ts.rate * 100) }}%</span>
            </div>
          </div>
        </div>

        <div v-if="weakPoints.length" class="summary-section">
          <h3 class="section-heading">薄弱知识点</h3>
          <div class="weak-points">
            <span v-for="wp in weakPoints" :key="wp" class="weak-tag">{{ wp }}</span>
          </div>
        </div>

        <div class="summary-actions">
          <el-button @click="showSummary = false">返回查看题目</el-button>
          <el-button type="primary" @click="goBack">返回练习列表</el-button>
        </div>
      </div>
    </div>

    <!-- ==================== EXERCISE VIEW ==================== -->
    <template v-else>
      <!-- Top Bar -->
      <header class="top-bar">
        <button class="back-btn" @click="goBack">
          <ArrowLeft :size="18" />
          <span>返回</span>
        </button>
        <div class="top-center">
          <span class="q-indicator">第 {{ currentIndex + 1 }} 题 / 共 {{ exercises.length }} 题</span>
        </div>
        <div class="top-right">
          <Clock :size="16" class="timer-icon" />
          <span class="timer-text">{{ formattedTime }}</span>
        </div>
      </header>

      <!-- Main Question Area -->
      <main class="question-area" ref="questionAreaRef">
        <div v-if="loading" class="loading-state">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
          <p>加载题目中...</p>
        </div>

        <div v-else-if="!exercises.length" class="empty-state">
          <p>未找到练习题目，请返回重新选择。</p>
          <el-button type="primary" @click="goBack">返回</el-button>
        </div>

        <div v-else class="question-card">
          <div class="question-top">
            <el-tag size="small" effect="plain" class="type-tag">{{ typeLabel(currentExercise.type) }}</el-tag>
          </div>

          <div class="question-text">{{ currentExercise.question }}</div>

          <!-- Single Choice -->
          <div v-if="currentExercise.type === 'single_choice'" class="options-area">
            <label
              v-for="opt in currentExercise.options"
              :key="opt.key"
              class="option-item"
              :class="{
                selected: studentAnswers[currentExercise.exercise_id] === opt.key,
                correct: currentResult && opt.key === currentExercise.answer,
                wrong: currentResult && !currentResult.correct && studentAnswers[currentExercise.exercise_id] === opt.key && opt.key !== currentExercise.answer,
                disabled: !!currentResult
              }"
              @click="!currentResult && selectChoice(opt.key)"
            >
              <span class="option-radio">
                <span v-if="studentAnswers[currentExercise.exercise_id] === opt.key" class="radio-dot" />
              </span>
              <span class="option-key">{{ opt.key }}.</span>
              <span class="option-text">{{ opt.text }}</span>
            </label>
          </div>

          <!-- True/False -->
          <div v-else-if="currentExercise.type === 'true_false'" class="options-area tf-options">
            <label
              v-for="opt in tfOptions"
              :key="opt.value"
              class="option-item tf-item"
              :class="{
                selected: studentAnswers[currentExercise.exercise_id] === opt.value,
                correct: currentResult && opt.value === currentExercise.answer,
                wrong: currentResult && !currentResult.correct && studentAnswers[currentExercise.exercise_id] === opt.value && opt.value !== currentExercise.answer,
                disabled: !!currentResult
              }"
              @click="!currentResult && selectTrueFalse(opt.value)"
            >
              <span class="option-radio">
                <span v-if="studentAnswers[currentExercise.exercise_id] === opt.value" class="radio-dot" />
              </span>
              <span class="option-text">{{ opt.label }}</span>
            </label>
          </div>

          <!-- Fill in Blank -->
          <div v-else-if="currentExercise.type === 'fill_in_blank'" class="options-area">
            <div
              v-for="blank in (currentExercise.blanks || [])"
              :key="blank.index"
              class="blank-row"
            >
              <span class="blank-label">第 {{ blank.index }} 空</span>
              <el-input
                :model-value="(studentAnswers[currentExercise.exercise_id] || [])[blank.index - 1] || ''"
                @update:model-value="val => updateBlank(blank.index - 1, val)"
                placeholder="请填写答案"
                :disabled="!!currentResult"
              />
            </div>
          </div>

          <!-- Short Answer -->
          <div v-else class="options-area">
            <el-input
              v-model="studentAnswers[currentExercise.exercise_id]"
              type="textarea"
              :rows="5"
              placeholder="请输入你的回答..."
              :disabled="!!currentResult"
            />
          </div>

          <!-- Submit Button -->
          <div v-if="!currentResult" class="submit-area">
            <el-button
              type="primary"
              :loading="submitting"
              :disabled="!canSubmit"
              @click="submitAnswer"
            >
              提交评测
            </el-button>
          </div>

          <!-- ==================== Analysis Card ==================== -->
          <transition name="slide-fade">
            <div v-if="currentResult" class="analysis-card" :class="currentResult.correct ? 'is-correct' : 'is-wrong'">
              <div class="analysis-header">
                <div class="result-badge" :class="currentResult.correct ? 'correct' : 'wrong'">
                  <CircleCheck v-if="currentResult.correct" :size="20" />
                  <CircleX v-else :size="20" />
                  <span>{{ currentResult.correct ? '回答正确' : '回答错误' }}</span>
                </div>
                <div class="result-score">得分: {{ currentResult.score }}</div>
              </div>

              <div v-if="currentResult.feedback" class="analysis-feedback">
                {{ currentResult.feedback }}
              </div>

              <div class="answer-compare">
                <div class="compare-row">
                  <span class="compare-label">你的答案</span>
                  <span class="compare-value" :class="currentResult.correct ? 'correct' : 'wrong'">
                    {{ formatUserAnswer(currentExercise) }}
                  </span>
                </div>
                <div class="compare-row">
                  <span class="compare-label">正确答案</span>
                  <span class="compare-value correct">
                    {{ formatCorrectAnswer(currentExercise) }}
                  </span>
                </div>
              </div>

              <div v-if="currentExercise.analysis" class="analysis-body">
                <div class="analysis-body-title">解析</div>
                <div class="analysis-body-content" v-html="renderMarkdown(currentExercise.analysis)" />
              </div>

              <div v-if="currentResult.suggestion" class="analysis-suggestion">
                <strong>建议：</strong>{{ currentResult.suggestion }}
              </div>

              <div v-if="currentExercise.knowledge_points?.length" class="analysis-kps">
                <span class="kp-tag" v-for="kp in currentExercise.knowledge_points" :key="kp">{{ kp }}</span>
              </div>
            </div>
          </transition>
        </div>
      </main>

      <!-- Bottom Bar -->
      <footer class="bottom-bar">
        <button class="nav-btn" :disabled="currentIndex === 0" @click="goToQuestion(currentIndex - 1)">
          <ArrowLeft :size="16" />
          上一题
        </button>

        <div class="progress-dots">
          <button
            v-for="(ex, idx) in exercises"
            :key="ex.exercise_id"
            class="dot"
            :class="dotClass(ex, idx)"
            @click="goToQuestion(idx)"
            :title="`第 ${idx + 1} 题`"
          />
        </div>

        <div class="nav-right-group">
          <el-button
            v-if="allGraded"
            type="primary"
            size="small"
            @click="showSummary = true"
          >
            查看总结
          </el-button>
          <button
            class="nav-btn"
            :disabled="currentIndex === exercises.length - 1"
            @click="goToQuestion(currentIndex + 1)"
          >
            下一题
            <ArrowRight :size="16" />
          </button>
        </div>
      </footer>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, ArrowRight, Clock, CircleCheck, CircleX } from "lucide-vue-next";
import { Loading } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { renderMarkdown } from "../utils/markdown";
import { apiRequest } from "../services/api";

const route = useRoute();
const router = useRouter();

const exercises = ref([]);
const loading = ref(true);
const currentIndex = ref(0);
const studentAnswers = ref({});
const gradingResults = ref({});
const submitting = ref(false);
const showSummary = ref(false);
const questionAreaRef = ref(null);

const courseId = computed(() => route.query.courseId);
const batchId = computed(() => route.query.batchId);
const currentExercise = computed(() => exercises.value[currentIndex.value] || {});
const currentResult = computed(() => gradingResults.value[currentExercise.value?.exercise_id]);

const tfOptions = [
  { value: true, label: "正确" },
  { value: false, label: "错误" },
];

// ---- Timer ----
const elapsedSeconds = ref(0);
let timerInterval = null;

const formattedTime = computed(() => {
  const m = Math.floor(elapsedSeconds.value / 60);
  const s = elapsedSeconds.value % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
});

const startTimer = () => {
  timerInterval = setInterval(() => {
    elapsedSeconds.value++;
  }, 1000);
};

// ---- Data Loading ----
const loadExercises = async () => {
  if (!courseId.value || !batchId.value) {
    loading.value = false;
    return;
  }
  try {
    const payload = await apiRequest(`/courses/${courseId.value}/exercises/batches/${batchId.value}`);
    exercises.value = payload.exercises || [];
  } catch (error) {
    ElMessage.error(error.message || "加载题目失败");
  } finally {
    loading.value = false;
  }
};

// ---- Answer Handling ----
const selectChoice = (key) => {
  studentAnswers.value = { ...studentAnswers.value, [currentExercise.value.exercise_id]: key };
};

const selectTrueFalse = (val) => {
  studentAnswers.value = { ...studentAnswers.value, [currentExercise.value.exercise_id]: val };
};

const updateBlank = (blankIdx, val) => {
  const eid = currentExercise.value.exercise_id;
  const totalBlanks = (currentExercise.value.blanks || []).length;
  const current = studentAnswers.value[eid] || Array(totalBlanks).fill("");
  const updated = [...current];
  updated[blankIdx] = val;
  studentAnswers.value = { ...studentAnswers.value, [eid]: updated };
};

const canSubmit = computed(() => {
  const ex = currentExercise.value;
  const answer = studentAnswers.value[ex.exercise_id];
  if (ex.type === "true_false") return answer === true || answer === false;
  if (ex.type === "short_answer") return typeof answer === "string" && answer.trim().length > 0;
  if (ex.type === "fill_in_blank") return Array.isArray(answer) && answer.some(a => typeof a === "string" && a.trim().length > 0);
  return !!answer;
});

const submitAnswer = async () => {
  const ex = currentExercise.value;
  const answer = studentAnswers.value[ex.exercise_id];
  submitting.value = true;
  try {
    const result = await apiRequest(`/courses/${courseId.value}/exercises/grade`, {
      method: "POST",
      body: JSON.stringify({
        exercise_id: ex.exercise_id,
        course_id: courseId.value,
        type: ex.type,
        answer,
      }),
    });
    gradingResults.value = { ...gradingResults.value, [ex.exercise_id]: result };
  } catch (error) {
    ElMessage.error(error.message || "评测失败");
  } finally {
    submitting.value = false;
  }
};

// ---- Navigation ----
const goToQuestion = (idx) => {
  if (idx < 0 || idx >= exercises.value.length) return;
  currentIndex.value = idx;
  nextTick(() => {
    questionAreaRef.value?.scrollTo({ top: 0, behavior: "smooth" });
  });
};

const goBack = () => {
  router.push("/exercises/grade");
};

const dotClass = (ex, idx) => {
  const result = gradingResults.value[ex.exercise_id];
  const answered = studentAnswers.value[ex.exercise_id] !== undefined;
  return {
    active: idx === currentIndex.value,
    answered: answered && !result,
    correct: result?.correct,
    wrong: result && !result.correct,
  };
};

// ---- Summary Computed ----
const correctCount = computed(() =>
  Object.values(gradingResults.value).filter(r => r.correct).length
);
const wrongCount = computed(() =>
  Object.values(gradingResults.value).filter(r => !r.correct).length
);
const accuracyRate = computed(() => {
  const total = Object.keys(gradingResults.value).length;
  return total > 0 ? correctCount.value / total : 0;
});
const allGraded = computed(() =>
  exercises.value.length > 0 && Object.keys(gradingResults.value).length === exercises.value.length
);

const typeStats = computed(() => {
  const map = {};
  exercises.value.forEach(ex => {
    if (!map[ex.type]) map[ex.type] = { type: ex.type, total: 0, correct: 0 };
    map[ex.type].total++;
    const r = gradingResults.value[ex.exercise_id];
    if (r?.correct) map[ex.type].correct++;
  });
  return Object.values(map).map(t => ({ ...t, rate: t.total > 0 ? t.correct / t.total : 0 }));
});

const weakPoints = computed(() => {
  const kps = {};
  exercises.value.forEach(ex => {
    const r = gradingResults.value[ex.exercise_id];
    if (r && !r.correct && ex.knowledge_points?.length) {
      ex.knowledge_points.forEach(kp => { kps[kp] = (kps[kp] || 0) + 1; });
    }
  });
  return Object.entries(kps).sort((a, b) => b[1] - a[1]).map(([kp]) => kp);
});

// ---- Formatting ----
const typeLabel = (type) => {
  const map = { single_choice: "单选题", true_false: "判断题", fill_in_blank: "填空题", short_answer: "简答题" };
  return map[type] || type;
};

const formatUserAnswer = (ex) => {
  const ans = studentAnswers.value[ex.exercise_id];
  if (ex.type === "true_false") return ans === true ? "正确" : "错误";
  if (ex.type === "fill_in_blank" && Array.isArray(ans)) return ans.map((a, i) => `第${i + 1}空：${a || "（空）"}`).join("；");
  if (ex.type === "single_choice" && ex.options) {
    const opt = ex.options.find(o => o.key === ans);
    return opt ? `${ans}. ${opt.text}` : ans;
  }
  return ans || "（未作答）";
};

const formatCorrectAnswer = (ex) => {
  if (ex.type === "true_false") return ex.answer === true ? "正确" : "错误";
  if (ex.type === "fill_in_blank" && ex.blanks?.length) {
    return ex.blanks.map(b => {
      let s = `第${b.index}空：${b.answer}`;
      if (b.alternatives?.length) s += `（也可填：${b.alternatives.join("、")}）`;
      return s;
    }).join("；");
  }
  if (ex.type === "single_choice" && ex.options) {
    const opt = ex.options.find(o => o.key === ex.answer);
    return opt ? `${ex.answer}. ${opt.text}` : ex.answer;
  }
  return ex.answer || "-";
};

// `renderMarkdown` is imported from utils/markdown.js (handles LaTeX via KaTeX).

// ---- Keyboard shortcuts ----
const handleKeydown = (e) => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
  if (e.key === "ArrowLeft") goToQuestion(currentIndex.value - 1);
  if (e.key === "ArrowRight") goToQuestion(currentIndex.value + 1);
};

// ---- Lifecycle ----
onMounted(async () => {
  await loadExercises();
  startTimer();
  window.addEventListener("keydown", handleKeydown);
});

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval);
  window.removeEventListener("keydown", handleKeydown);
});
</script>

<style scoped>
.session-root {
  min-height: 100vh;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
}

/* ==================== Top Bar ==================== */
.top-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 56px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 100;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.15s;
}
.back-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.top-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}
.q-indicator {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.top-right {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #64748b;
}
.timer-icon { opacity: 0.6; }
.timer-text {
  font-size: 15px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: #334155;
}

/* ==================== Question Area ==================== */
.question-area {
  flex: 1;
  margin-top: 56px;
  margin-bottom: 64px;
  padding: 40px 24px;
  overflow-y: auto;
  display: flex;
  justify-content: center;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding-top: 120px;
  color: #94a3b8;
}

.question-card {
  width: 100%;
  max-width: 720px;
}

.question-top {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.type-tag {
  font-size: 12px;
}

.question-text {
  font-size: 17px;
  font-weight: 600;
  line-height: 1.8;
  color: #0f172a;
  margin-bottom: 28px;
}

/* ==================== Options - Shared ==================== */
.options-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.option-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
  background: white;
  user-select: none;
}
.option-item:hover:not(.disabled) {
  border-color: #94a3b8;
  background: #f8fafc;
}
.option-item.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}
.option-item.correct {
  border-color: #22c55e;
  background: #f0fdf4;
}
.option-item.wrong {
  border-color: #ef4444;
  background: #fef2f2;
}
.option-item.disabled {
  cursor: default;
}

.option-radio {
  width: 18px;
  height: 18px;
  min-width: 18px;
  border: 2px solid #cbd5e1;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 2px;
  transition: border-color 0.15s;
}
.option-item.selected .option-radio { border-color: #3b82f6; }
.option-item.correct .option-radio { border-color: #22c55e; }
.option-item.wrong .option-radio { border-color: #ef4444; }

.radio-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3b82f6;
}
.option-item.correct .radio-dot { background: #22c55e; }
.option-item.wrong .radio-dot { background: #ef4444; }

.option-key {
  font-weight: 700;
  color: #475569;
  min-width: 20px;
}

.option-text {
  font-size: 15px;
  line-height: 1.6;
  color: #1e293b;
}

/* True/False horizontal */
.tf-options {
  flex-direction: row;
  gap: 16px;
}
.tf-item {
  flex: 1;
  justify-content: center;
  text-align: center;
}

/* Fill in blank */
.blank-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.blank-label {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
  min-width: 48px;
}

/* Submit area */
.submit-area {
  display: flex;
  justify-content: flex-start;
  margin-top: 8px;
}

/* ==================== Analysis Card ==================== */
.analysis-card {
  margin-top: 28px;
  border-radius: 12px;
  padding: 24px;
  border: 1.5px solid;
}
.analysis-card.is-correct {
  background: #f0fdf4;
  border-color: #bbf7d0;
}
.analysis-card.is-wrong {
  background: #fffbeb;
  border-color: #fde68a;
}

.analysis-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.result-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
}
.result-badge.correct { color: #16a34a; }
.result-badge.wrong { color: #d97706; }

.result-score {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
}

.analysis-feedback {
  font-size: 14px;
  color: #334155;
  margin-bottom: 16px;
  line-height: 1.6;
}

.answer-compare {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  margin-bottom: 16px;
}

.compare-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.compare-label {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  min-width: 60px;
  flex-shrink: 0;
}

.compare-value {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.5;
}
.compare-value.correct { color: #16a34a; }
.compare-value.wrong { color: #dc2626; }

.analysis-body {
  margin-bottom: 16px;
}
.analysis-body-title {
  font-size: 13px;
  font-weight: 700;
  color: #475569;
  margin-bottom: 8px;
}
.analysis-body-content {
  font-size: 14px;
  color: #334155;
  line-height: 1.75;
}
.analysis-body-content :deep(p) {
  margin: 0 0 8px 0;
}
.analysis-body-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 13px;
}

.analysis-suggestion {
  font-size: 13px;
  color: #92400e;
  background: rgba(245, 158, 11, 0.1);
  padding: 10px 14px;
  border-radius: 8px;
  line-height: 1.6;
  margin-bottom: 16px;
}

.analysis-kps {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.kp-tag {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

/* ==================== Bottom Bar ==================== */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: white;
  border-top: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 100;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  padding: 8px 14px;
  border-radius: 8px;
  transition: all 0.15s;
}
.nav-btn:hover:not(:disabled) {
  background: #f1f5f9;
  color: #0f172a;
}
.nav-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.progress-dots {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: center;
  max-width: 50%;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #cbd5e1;
  background: transparent;
  cursor: pointer;
  padding: 0;
  transition: all 0.15s;
}
.dot:hover { border-color: #94a3b8; }
.dot.active { border-color: #3b82f6; background: #3b82f6; }
.dot.answered { border-color: #3b82f6; background: #bfdbfe; }
.dot.correct { border-color: #22c55e; background: #22c55e; }
.dot.wrong { border-color: #ef4444; background: #ef4444; }

.nav-right-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ==================== Transition ==================== */
.slide-fade-enter-active {
  transition: all 0.35s ease;
}
.slide-fade-leave-active {
  transition: all 0.2s ease;
}
.slide-fade-enter-from {
  opacity: 0;
  transform: translateY(16px);
}
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ==================== Summary Page ==================== */
.summary-page {
  min-height: 100vh;
  background: #f8fafc;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
}

.summary-container {
  width: 100%;
  max-width: 640px;
}

.summary-header {
  text-align: center;
  margin-bottom: 36px;
}
.summary-title {
  font-size: 28px;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 8px 0;
  letter-spacing: -0.03em;
}
.summary-subtitle {
  font-size: 15px;
  color: #64748b;
  margin: 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 32px;
}

.summary-ring-card,
.summary-stats-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 28px;
}

.ring-wrapper {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto;
}
.ring-svg {
  width: 100%;
  height: 100%;
}
.ring-progress {
  transition: stroke-dasharray 0.8s ease;
}
.ring-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.ring-pct {
  display: block;
  font-size: 24px;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}
.ring-label {
  display: block;
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f1f5f9;
}
.stat-row:last-child { border-bottom: none; }
.stat-label {
  font-size: 14px;
  color: #64748b;
}
.stat-value {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}
.stat-value.correct { color: #16a34a; }
.stat-value.wrong { color: #dc2626; }

.summary-section {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
}
.section-heading {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 16px 0;
}

.type-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.type-stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
}
.type-stat-label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  min-width: 56px;
}
.type-stat-bar-track {
  flex: 1;
  height: 8px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}
.type-stat-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}
.type-stat-bar-fill.good { background: #22c55e; }
.type-stat-bar-fill.poor { background: #f59e0b; }
.type-stat-pct {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  min-width: 36px;
  text-align: right;
}

.weak-points {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.weak-tag {
  display: inline-flex;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  background: #fef2f2;
  color: #dc2626;
}

.summary-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 32px;
}

/* ==================== Responsive ==================== */
@media (max-width: 640px) {
  .question-area { padding: 24px 16px; }
  .top-bar, .bottom-bar { padding: 0 16px; }
  .summary-grid { grid-template-columns: 1fr; }
  .tf-options { flex-direction: column; }
  .progress-dots { max-width: 40%; }
}
</style>
