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

          <div class="form-grid">
            <el-form-item label="练习编号">
              <el-input v-model="exerciseId" placeholder="例如 ex_001" />
            </el-form-item>
            <el-form-item label="题型">
              <el-select v-model="exerciseType" placeholder="选择题型">
                <el-option label="单选题" value="single_choice" />
                <el-option label="判断题" value="true_false" />
                <el-option label="简答题" value="short_answer" />
              </el-select>
            </el-form-item>
          </div>

          <el-form-item label="提交答案">
            <el-radio-group
              v-if="exerciseType === 'single_choice'"
              v-model="answerChoice"
              class="answer-options"
            >
              <el-radio-button label="A">A</el-radio-button>
              <el-radio-button label="B">B</el-radio-button>
              <el-radio-button label="C">C</el-radio-button>
              <el-radio-button label="D">D</el-radio-button>
            </el-radio-group>

            <el-radio-group
              v-else-if="exerciseType === 'true_false'"
              v-model="answerBoolean"
              class="answer-options"
            >
              <el-radio-button :label="true">正确</el-radio-button>
              <el-radio-button :label="false">错误</el-radio-button>
            </el-radio-group>

            <el-input
              v-else
              v-model="answerText"
              type="textarea"
              :rows="5"
              placeholder="请输入简答内容"
            />
          </el-form-item>
        </el-form>

        <div class="form-actions">
          <el-button @click="resetForm">重置</el-button>
          <el-button type="primary" :loading="grading" @click="handleGrade">
            提交评测
          </el-button>
        </div>

        <div class="results-section">
          <div class="section-title">评测结果</div>
          <el-card v-if="gradingResult" class="result-card" shadow="never">
            <div class="result-header">
              <div class="result-title">
                {{ gradingResult.correct ? "判定：正确" : "判定：需改进" }}
              </div>
              <div class="result-score">得分：{{ gradingResult.score }}</div>
            </div>
            <div class="result-body">
              <div class="result-row">
                <span class="result-label">反馈</span>
                <span class="result-text">{{ gradingResult.feedback }}</span>
              </div>
              <div class="result-row">
                <span class="result-label">建议</span>
                <span class="result-text">
                  {{ gradingResult.suggestion || "暂无补充建议" }}
                </span>
              </div>
            </div>

            <div v-if="gradingResult.matched_points?.length" class="result-tags">
              <div class="tag-label">已覆盖要点</div>
              <div class="tag-list">
                <span
                  v-for="point in gradingResult.matched_points"
                  :key="point"
                  class="tag success"
                >
                  {{ point }}
                </span>
              </div>
            </div>

            <div v-if="gradingResult.missing_points?.length" class="result-tags">
              <div class="tag-label">待补充要点</div>
              <div class="tag-list">
                <span
                  v-for="point in gradingResult.missing_points"
                  :key="point"
                  class="tag warning"
                >
                  {{ point }}
                </span>
              </div>
            </div>
          </el-card>
          <div v-else class="empty-result">
            暂无评测结果，请先选择课程并提交练习答案。
          </div>
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
const exerciseId = ref("");
const exerciseType = ref("single_choice");
const answerChoice = ref("");
const answerBoolean = ref(null);
const answerText = ref("");
const grading = ref(false);
const gradingResult = ref(null);

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

const resetForm = () => {
  exerciseId.value = "";
  exerciseType.value = "single_choice";
  answerChoice.value = "";
  answerBoolean.value = null;
  answerText.value = "";
  gradingResult.value = null;
};

const handleGrade = async () => {
  if (!selectedCourse.value) {
    ElMessage.warning("请先选择课程");
    return;
  }
  if (!exerciseId.value.trim()) {
    ElMessage.warning("请填写练习编号");
    return;
  }

  let answer = "";
  if (exerciseType.value === "single_choice") {
    if (!answerChoice.value) {
      ElMessage.warning("请选择答案选项");
      return;
    }
    answer = answerChoice.value;
  } else if (exerciseType.value === "true_false") {
    if (answerBoolean.value === null) {
      ElMessage.warning("请选择判断结果");
      return;
    }
    answer = answerBoolean.value;
  } else {
    if (!answerText.value.trim()) {
      ElMessage.warning("请填写简答内容");
      return;
    }
    answer = answerText.value.trim();
  }

  grading.value = true;
  gradingResult.value = null;
  try {
    gradingResult.value = await apiRequest(
      `/courses/${selectedCourse.value}/exercises/grade`,
      {
        method: "POST",
        body: JSON.stringify({
          exercise_id: exerciseId.value.trim(),
          course_id: selectedCourse.value,
          type: exerciseType.value,
          answer,
        }),
      }
    );
  } catch (error) {
    ElMessage.error(error.message || "评测失败");
  } finally {
    grading.value = false;
  }
};

watch(exerciseType, () => {
  answerChoice.value = "";
  answerBoolean.value = null;
  answerText.value = "";
  gradingResult.value = null;
});

onMounted(() => {
  loadCourses();
});
</script>

<style scoped>
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
