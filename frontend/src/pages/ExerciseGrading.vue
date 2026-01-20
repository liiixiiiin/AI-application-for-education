<template>
  <div class="grade-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/courses' }">工作区</el-breadcrumb-item>
        <el-breadcrumb-item>练习评测</el-breadcrumb-item>
      </el-breadcrumb>
      <h1 class="page-title mt-4">练习评测</h1>
      <p class="page-subtitle">提交练习答案并获得正确性判定、反馈与改进建议。</p>
    </div>

    <div class="grade-layout">
      <div class="grade-main card">
        <el-form label-position="top">
          <div class="form-grid-3">
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

            <el-form-item label="选择练习批次">
              <el-select
                v-model="selectedBatchId"
                placeholder="请选择批次"
                filterable
                :loading="loadingBatches"
                :disabled="!selectedCourse"
                style="width: 100%"
              >
                <el-option
                  v-for="batch in batches"
                  :key="batch.batch_id"
                  :label="batch.title"
                  :value="batch.batch_id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="操作">
              <el-button type="primary" :disabled="!selectedBatchId" @click="loadBatchDetails">
                开始练习
              </el-button>
            </el-form-item>
          </div>
        </el-form>

        <div v-if="currentExercises.length" class="exercise-solving-section mt-8">
          <div class="section-title">练习题目 (共 {{ currentExercises.length }} 题)</div>
          
          <div v-for="(exercise, index) in currentExercises" :key="exercise.exercise_id" class="solve-card mb-6">
            <div class="solve-header">
              <span class="solve-index">第 {{ index + 1 }} 题</span>
              <el-tag size="small" effect="plain">{{ typeLabel(exercise.type) }}</el-tag>
            </div>
            
            <div class="solve-question mt-4">{{ exercise.question }}</div>

            <div v-if="exercise.type === 'single_choice'" class="solve-options mt-4">
              <el-radio-group v-model="studentAnswers[exercise.exercise_id]" class="vertical-radio-group">
                <el-radio v-for="opt in exercise.options" :key="opt.key" :label="opt.key">
                  <span class="opt-key">{{ opt.key }}.</span> {{ opt.text }}
                </el-radio>
              </el-radio-group>
            </div>

            <div v-else-if="exercise.type === 'true_false'" class="solve-options mt-4">
              <el-radio-group v-model="studentAnswers[exercise.exercise_id]">
                <el-radio :label="true">正确</el-radio>
                <el-radio :label="false">错误</el-radio>
              </el-radio-group>
            </div>

            <div v-else class="solve-options mt-4">
              <el-input
                v-model="studentAnswers[exercise.exercise_id]"
                type="textarea"
                :rows="4"
                placeholder="请输入你的回答..."
              />
            </div>

            <!-- 评测结果展示 -->
            <div v-if="gradingResults[exercise.exercise_id]" class="grading-feedback mt-4">
              <el-alert
                :title="gradingResults[exercise.exercise_id].correct ? '回答正确' : '需改进'"
                :type="gradingResults[exercise.exercise_id].correct ? 'success' : 'warning'"
                :closable="false"
                show-icon
              >
                <template #default>
                  <div class="feedback-content">
                    <p><strong>得分:</strong> {{ gradingResults[exercise.exercise_id].score }}</p>
                    <p><strong>反馈:</strong> {{ gradingResults[exercise.exercise_id].feedback }}</p>
                    <p v-if="gradingResults[exercise.exercise_id].suggestion">
                      <strong>建议:</strong> {{ gradingResults[exercise.exercise_id].suggestion }}
                    </p>
                    
                    <div class="analysis-box mt-2">
                      <div class="analysis-label">题目解析与答案</div>
                      <div class="analysis-text">{{ formatAnswer(exercise.answer) }}</div>
                      <div v-if="exercise.analysis" class="analysis-sub mt-1">{{ exercise.analysis }}</div>
                    </div>
                  </div>
                </template>
              </el-alert>
            </div>

            <div class="solve-footer mt-4">
              <el-button
                type="primary"
                size="small"
                :loading="gradingIds.has(exercise.exercise_id)"
                :disabled="!canSubmitAnswer(exercise)"
                @click="submitSingleGrade(exercise)"
              >
                {{ gradingResults[exercise.exercise_id] ? '重新提交' : '提交评测' }}
              </el-button>
            </div>
          </div>
        </div>
        <div v-else class="empty-result">
          请选择练习批次并点击“开始练习”。
        </div>
      </div>

      <div class="grade-sidebar">
        <div class="info-card">
          <div class="info-icon">
            <ClipboardCheck :size="18" />
          </div>
          <h3 class="info-title">评测提示</h3>
          <ul class="info-list">
            <li>
              <strong>提交格式</strong>
              <p>请确保课程、题型与答案匹配，系统会返回正确性与建议。</p>
            </li>
            <li>
              <strong>判断题</strong>
              <p>支持正确 / 错误选项，后台会进行格式校验。</p>
            </li>
            <li>
              <strong>简答题</strong>
              <p>将按关键要点进行匹配，反馈缺失项与改进方向。</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import { ClipboardCheck } from "lucide-vue-next";
import { ElMessage } from "element-plus";
import { apiRequest } from "../services/api";

const courses = ref([]);
const loadingCourses = ref(false);
const selectedCourse = ref("");

const batches = ref([]);
const loadingBatches = ref(false);
const selectedBatchId = ref("");

const currentExercises = ref([]);
const studentAnswers = ref({});
const gradingResults = ref({});
const gradingIds = ref(new Set());

const loadCourses = async () => {
  loadingCourses.value = true;
  try {
    courses.value = await apiRequest("/courses");
  } catch (error) {
    ElMessage.error(error.message || "加载课程失败");
  } finally {
    loadingCourses.value = false;
  }
};

const loadBatches = async () => {
  if (!selectedCourse.value) {
    batches.value = [];
    return;
  }
  loadingBatches.value = true;
  try {
    const payload = await apiRequest(`/courses/${selectedCourse.value}/exercises/batches`);
    batches.value = payload;
  } catch (error) {
    ElMessage.error(error.message || "加载批次失败");
  } finally {
    loadingBatches.value = false;
  }
};

const loadBatchDetails = async () => {
  if (!selectedBatchId.value) return;
  try {
    const payload = await apiRequest(`/courses/${selectedCourse.value}/exercises/batches/${selectedBatchId.value}`);
    currentExercises.value = payload.exercises || [];
    studentAnswers.value = {};
    gradingResults.value = {};
    gradingIds.value.clear();
    ElMessage.success(`已加载 ${currentExercises.value.length} 道练习题`);
  } catch (error) {
    ElMessage.error(error.message || "加载题目详情失败");
  }
};

const submitSingleGrade = async (exercise) => {
  const answer = studentAnswers.value[exercise.exercise_id];
  if (!canSubmitAnswer(exercise)) {
    ElMessage.warning("请先填写答案");
    return;
  }

  gradingIds.value.add(exercise.exercise_id);
  try {
    const result = await apiRequest(
      `/courses/${selectedCourse.value}/exercises/grade`,
      {
        method: "POST",
        body: JSON.stringify({
          exercise_id: exercise.exercise_id,
          course_id: selectedCourse.value,
          type: exercise.type,
          answer,
        }),
      }
    );
    gradingResults.value = {
      ...gradingResults.value,
      [exercise.exercise_id]: result,
    };
    ElMessage.success("评测完成");
  } catch (error) {
    ElMessage.error(error.message || "评测失败");
  } finally {
    gradingIds.value.delete(exercise.exercise_id);
  }
};

const canSubmitAnswer = (exercise) => {
  const answer = studentAnswers.value[exercise.exercise_id];
  if (exercise.type === "true_false") {
    return answer === true || answer === false;
  }
  if (exercise.type === "short_answer") {
    return typeof answer === "string" && answer.trim().length > 0;
  }
  return !!answer;
};

watch(selectedCourse, () => {
  loadBatches();
  selectedBatchId.value = "";
  currentExercises.value = [];
});

const typeLabel = (type) => {
  const map = {
    single_choice: "单选题",
    true_false: "判断题",
    short_answer: "简答题",
  };
  return map[type] || type;
};

const formatAnswer = (answer) => {
  if (answer === true) return "正确";
  if (answer === false) return "错误";
  return answer || "-";
};

onMounted(() => {
  loadCourses();
});
</script>

<style scoped>
.form-grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 120px;
  gap: 16px;
  align-items: flex-end;
}

.solve-card {
  padding: 24px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-soft);
  background: white;
}

.solve-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.solve-index {
  font-weight: 700;
  color: var(--color-text-muted);
}

.solve-question {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.6;
}

.vertical-radio-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.opt-key {
  font-weight: 700;
  margin-right: 4px;
}

.analysis-box {
  padding: 12px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
  border: 1px dashed rgba(0, 0, 0, 0.1);
}

.analysis-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.analysis-text {
  font-weight: 600;
}

.analysis-sub {
  font-size: 13px;
  color: var(--color-text-secondary);
}

.mb-6 {
  margin-bottom: 24px;
}

.mt-8 {
  margin-top: 32px;
}

.grade-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.grade-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 24px;
}

.grade-main {
  padding: 28px;
}

.grade-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.answer-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

.results-section {
  margin-top: 32px;
}

.section-title {
  font-weight: 600;
  margin-bottom: 16px;
}

.result-card {
  border-radius: 16px;
  border: 1px solid #e5e7eb;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.result-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.result-score {
  font-size: 14px;
  color: #10b981;
  font-weight: 600;
}

.result-body {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
}

.result-row {
  display: flex;
  gap: 12px;
}

.result-label {
  width: 60px;
  font-weight: 600;
  color: #6b7280;
}

.result-text {
  color: #1f2937;
}

.result-tags {
  margin-top: 12px;
}

.tag-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 6px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  background: #f3f4f6;
  color: #374151;
}

.tag.success {
  background: #ecfdf3;
  color: #047857;
}

.tag.warning {
  background: #fff7ed;
  color: #c2410c;
}

.empty-result {
  padding: 24px;
  text-align: center;
  color: #9ca3af;
  border: 1px dashed #e5e7eb;
  border-radius: 16px;
}

@media (max-width: 1024px) {
  .grade-layout {
    grid-template-columns: 1fr;
  }

  .grade-sidebar {
    order: -1;
  }
}

@media (max-width: 720px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .result-row {
    flex-direction: column;
    gap: 4px;
  }
}
</style>
