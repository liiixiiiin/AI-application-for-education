<template>
  <div class="personalized-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/courses' }">工作区</el-breadcrumb-item>
        <el-breadcrumb-item>个性化练习</el-breadcrumb-item>
      </el-breadcrumb>
      <h1 class="page-title mt-4">个性化练习</h1>
      <p class="page-subtitle">基于知识追踪的个性化练习推荐，精准定位薄弱知识点。</p>
    </div>

    <div class="personalized-layout">
      <div class="personalized-main card">
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
        </el-form>

        <!-- Mastery Section -->
        <div v-if="selectedCourse" class="mastery-section">
          <div class="section-header">
            <div class="section-title">知识点掌握度</div>
            <div v-if="masteryItems.length" class="section-summary">
              共 {{ masteryItems.length }} 个知识点 · 薄弱项 {{ weakPoints.length }} 个
            </div>
          </div>

          <div v-if="loadingState" class="loading-hint">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>加载掌握度数据...</span>
          </div>

          <div v-else-if="masteryItems.length" class="mastery-list">
            <div
              v-for="item in masteryItems"
              :key="item.knowledge_point"
              class="mastery-item"
            >
              <div class="mastery-label">
                <span class="kp-name">{{ item.knowledge_point }}</span>
                <el-tag
                  v-if="item.mastery < 0.6"
                  size="small"
                  type="danger"
                  effect="dark"
                  class="weak-tag"
                >
                  薄弱
                </el-tag>
              </div>
              <div class="mastery-bar-area">
                <el-progress
                  :percentage="Math.round(item.mastery * 100)"
                  :stroke-width="10"
                  :color="masteryColor(item.mastery)"
                  :show-text="false"
                />
              </div>
              <div class="mastery-pct" :style="{ color: masteryColor(item.mastery) }">
                {{ Math.round(item.mastery * 100) }}%
              </div>
              <div class="mastery-count">
                {{ item.attempt_count }} 次
              </div>
            </div>
          </div>

          <div v-else class="empty-mastery">
            <div class="empty-icon">
              <BarChart3 :size="32" />
            </div>
            <p>暂无掌握度数据</p>
            <p class="empty-hint">完成练习评测后，系统将自动追踪你的知识点掌握情况。</p>
          </div>
        </div>

        <!-- Recommendation Section -->
        <div v-if="selectedCourse" class="recommend-section">
          <div class="section-title">生成推荐练习</div>
          <div class="recommend-controls">
            <el-form-item label="生成数量" class="inline-item">
              <el-input-number v-model="recCount" :min="1" :max="20" controls-position="right" />
            </el-form-item>
            <el-form-item label="难度" class="inline-item">
              <el-radio-group v-model="recDifficulty">
                <el-radio-button label="easy">基础</el-radio-button>
                <el-radio-button label="medium">进阶</el-radio-button>
                <el-radio-button label="hard">挑战</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </div>
          <div class="recommend-actions">
            <el-button
              type="primary"
              :loading="generating"
              @click="handleGenerate"
              :disabled="!selectedCourse"
            >
              生成推荐练习
            </el-button>
            <span v-if="weakPoints.length" class="weak-hint">
              将针对 {{ weakPoints.length }} 个薄弱知识点出题
            </span>
            <span v-else-if="masteryItems.length" class="weak-hint good">
              暂无薄弱项，将针对掌握度较低的知识点进行巩固
            </span>
          </div>
        </div>

        <!-- Generated Exercises -->
        <div v-if="exercises.length" class="results-section">
          <div class="section-header">
            <div class="section-title">推荐练习</div>
            <div class="header-actions">
              <el-button size="small" type="success" @click="openSaveDialog">
                保存此批次
              </el-button>
              <el-button
                size="small"
                type="primary"
                @click="startSession"
                :disabled="!savedBatchId"
              >
                开始练习
              </el-button>
            </div>
          </div>
          <div class="exercise-list">
            <el-card
              v-for="(exercise, index) in exercises"
              :key="exercise.exercise_id"
              class="exercise-card"
              shadow="never"
            >
              <div class="exercise-header">
                <div class="flex-grow">
                  <div class="exercise-question">{{ exercise.question }}</div>
                  <div class="exercise-meta mt-2">
                    <el-tag size="small">{{ typeLabel(exercise.type) }}</el-tag>
                    <el-tag size="small" type="success" class="ml-2">
                      {{ difficultyLabel(exercise.difficulty) }}
                    </el-tag>
                    <el-tag
                      v-for="kp in exercise.knowledge_points"
                      :key="kp"
                      size="small"
                      type="info"
                      class="ml-2"
                    >
                      {{ kp }}
                    </el-tag>
                  </div>
                </div>
              </div>

              <div v-if="exercise.options?.length" class="exercise-options">
                <div v-for="opt in exercise.options" :key="opt.key" class="option-row">
                  <span class="option-key">{{ opt.key }}.</span>
                  <span class="option-text">{{ opt.text }}</span>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="personalized-sidebar">
        <div class="info-card">
          <div class="info-icon">
            <Target :size="18" />
          </div>
          <h3 class="info-title">个性化学习</h3>
          <ul class="info-list">
            <li>
              <strong>知识追踪</strong>
              <p>系统自动记录每次作答表现，使用 EMA 算法实时更新掌握度。</p>
            </li>
            <li>
              <strong>薄弱识别</strong>
              <p>掌握度低于 60% 的知识点自动标记为薄弱项。</p>
            </li>
            <li>
              <strong>精准推荐</strong>
              <p>基于薄弱知识点自动生成针对性练习，加速补齐短板。</p>
            </li>
            <li>
              <strong>持续进步</strong>
              <p>反复练习后掌握度实时更新，直观看到学习进步。</p>
            </li>
          </ul>
        </div>

        <div v-if="recentAttempts.length" class="info-card mt-4">
          <h3 class="info-title">最近作答</h3>
          <div class="recent-list">
            <div v-for="att in recentAttempts.slice(0, 5)" :key="att.id" class="recent-item">
              <div class="recent-score" :class="att.score >= 0.8 ? 'good' : att.score >= 0.5 ? 'mid' : 'poor'">
                {{ Math.round(att.score * 100) }}
              </div>
              <div class="recent-detail">
                <div class="recent-kps">{{ att.knowledge_points.join('、') || '-' }}</div>
                <div class="recent-time">{{ formatDate(att.created_at) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Save Dialog -->
    <el-dialog v-model="saveDialogVisible" title="保存推荐练习批次" width="400px">
      <el-form label-position="top">
        <el-form-item label="批次名称">
          <el-input v-model="batchTitle" placeholder="例如：薄弱知识点专项训练" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveBatch">确定保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { Target, BarChart3 } from "lucide-vue-next";
import { Loading } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { apiRequest } from "../services/api";

const router = useRouter();

const courses = ref([]);
const loadingCourses = ref(false);
const selectedCourse = ref("");

const masteryItems = ref([]);
const weakPoints = ref([]);
const loadingState = ref(false);

const recentAttempts = ref([]);

const recCount = ref(5);
const recDifficulty = ref("easy");
const exercises = ref([]);
const generating = ref(false);

const saveDialogVisible = ref(false);
const batchTitle = ref("");
const saving = ref(false);
const savedBatchId = ref(null);

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

const loadKnowledgeState = async () => {
  if (!selectedCourse.value) {
    masteryItems.value = [];
    weakPoints.value = [];
    return;
  }
  loadingState.value = true;
  try {
    const payload = await apiRequest(`/knowledge-state?course_id=${selectedCourse.value}`);
    masteryItems.value = payload.items || [];
    weakPoints.value = payload.weak_points || [];
  } catch (error) {
    ElMessage.error(error.message || "加载掌握度失败");
  } finally {
    loadingState.value = false;
  }
};

const loadRecentAttempts = async () => {
  if (!selectedCourse.value) {
    recentAttempts.value = [];
    return;
  }
  try {
    recentAttempts.value = await apiRequest(`/exercise-attempts?course_id=${selectedCourse.value}&limit=10`);
  } catch {
    recentAttempts.value = [];
  }
};

watch(selectedCourse, () => {
  exercises.value = [];
  savedBatchId.value = null;
  loadKnowledgeState();
  loadRecentAttempts();
});

const handleGenerate = async () => {
  if (!selectedCourse.value) return;
  generating.value = true;
  savedBatchId.value = null;
  try {
    const payload = await apiRequest("/recommended-exercises", {
      method: "POST",
      body: JSON.stringify({
        course_id: selectedCourse.value,
        count: recCount.value,
        difficulty: recDifficulty.value,
      }),
    });
    exercises.value = payload.generated || [];
    ElMessage.success(`已生成 ${exercises.value.length} 道推荐练习`);
  } catch (error) {
    ElMessage.error(error.message || "生成推荐练习失败");
  } finally {
    generating.value = false;
  }
};

const openSaveDialog = () => {
  const weakNames = weakPoints.value.slice(0, 3).join("、");
  batchTitle.value = weakNames ? `薄弱项训练：${weakNames}` : `个性化练习 ${new Date().toLocaleString()}`;
  saveDialogVisible.value = true;
};

const handleSaveBatch = async () => {
  if (!batchTitle.value.trim()) {
    ElMessage.warning("请输入批次名称");
    return;
  }
  saving.value = true;
  try {
    const payload = await apiRequest(`/courses/${selectedCourse.value}/exercises/batches`, {
      method: "POST",
      body: JSON.stringify({
        title: batchTitle.value,
        exercises: exercises.value,
      }),
    });
    savedBatchId.value = payload.batch_id;
    saveDialogVisible.value = false;
    ElMessage.success("保存成功，可以开始练习");
  } catch (error) {
    ElMessage.error(error.message || "保存失败");
  } finally {
    saving.value = false;
  }
};

const startSession = () => {
  if (!savedBatchId.value) return;
  router.push({
    path: "/exercises/session",
    query: { courseId: selectedCourse.value, batchId: savedBatchId.value },
  });
};

const masteryColor = (mastery) => {
  if (mastery >= 0.8) return "#22c55e";
  if (mastery >= 0.6) return "#f59e0b";
  return "#ef4444";
};

const typeLabel = (type) => {
  const map = { single_choice: "单选题", true_false: "判断题", fill_in_blank: "填空题", short_answer: "简答题" };
  return map[type] || type;
};

const difficultyLabel = (val) => {
  const map = { easy: "基础", medium: "进阶", hard: "挑战" };
  return map[val] || val;
};

const formatDate = (value) => {
  if (!value) return "-";
  const d = new Date(value);
  return d.toLocaleString();
};

onMounted(loadCourses);
</script>

<style scoped>
.personalized-page {
  max-width: 1100px;
  margin: 0 auto;
}

.mt-4 { margin-top: 16px; }
.ml-2 { margin-left: 8px; }
.mt-2 { margin-top: 8px; }

.personalized-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 24px;
  align-items: start;
}

.personalized-main {
  padding: 32px;
}

.personalized-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Section */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-main);
}

.section-summary {
  font-size: 13px;
  color: var(--color-text-muted);
}

/* Mastery */
.mastery-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border-soft);
}

.loading-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: var(--color-text-muted);
  font-size: 14px;
}

.mastery-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mastery-item {
  display: grid;
  grid-template-columns: 160px 1fr 48px 48px;
  gap: 12px;
  align-items: center;
}

.mastery-label {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.kp-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-main);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.weak-tag {
  flex-shrink: 0;
}

.mastery-bar-area {
  min-width: 0;
}

.mastery-pct {
  font-size: 13px;
  font-weight: 700;
  text-align: right;
}

.mastery-count {
  font-size: 12px;
  color: var(--color-text-muted);
  text-align: right;
}

.empty-mastery {
  text-align: center;
  padding: 40px 20px;
  color: var(--color-text-muted);
}

.empty-icon {
  margin-bottom: 12px;
  opacity: 0.4;
}

.empty-mastery p {
  margin: 4px 0;
  font-size: 14px;
}

.empty-hint {
  font-size: 13px !important;
  color: var(--color-text-muted);
}

/* Recommend */
.recommend-section {
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border-soft);
}

.recommend-controls {
  display: flex;
  gap: 24px;
  margin-top: 12px;
}

.inline-item {
  margin-bottom: 0;
}

.recommend-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.weak-hint {
  font-size: 13px;
  color: var(--color-text-muted);
}

.weak-hint.good {
  color: var(--color-success);
}

/* Results */
.results-section {
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border-soft);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.exercise-list {
  display: grid;
  gap: 12px;
}

.exercise-card {
  border-radius: var(--radius-md);
  border-color: var(--color-border-soft);
}

.exercise-header {
  display: flex;
  gap: 16px;
}

.flex-grow {
  flex-grow: 1;
}

.exercise-question {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-main);
  line-height: 1.6;
}

.exercise-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.exercise-options {
  margin-top: 12px;
  display: grid;
  gap: 6px;
}

.option-row {
  display: flex;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 8px;
  background: var(--color-bg-alt);
  font-size: 13px;
}

.option-key {
  font-weight: 700;
  color: var(--color-text-main);
}

.option-text {
  color: var(--color-text-secondary);
}

/* Info Card */
.info-card {
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 24px;
}

.info-icon {
  width: 32px;
  height: 32px;
  background-color: var(--color-border-soft);
  color: var(--color-text-main);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  margin-bottom: 16px;
}

.info-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-main);
  margin: 0 0 16px 0;
}

.info-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.info-list li {
  margin-bottom: 16px;
}

.info-list li:last-child {
  margin-bottom: 0;
}

.info-list strong {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-main);
  margin-bottom: 4px;
}

.info-list p {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.5;
}

/* Recent Attempts */
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.recent-score {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.recent-score.good {
  background: #f0fdf4;
  color: #16a34a;
}

.recent-score.mid {
  background: #fffbeb;
  color: #d97706;
}

.recent-score.poor {
  background: #fef2f2;
  color: #dc2626;
}

.recent-detail {
  min-width: 0;
}

.recent-kps {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-main);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-time {
  font-size: 11px;
  color: var(--color-text-muted);
}

/* Responsive */
@media (max-width: 1000px) {
  .personalized-layout {
    grid-template-columns: 1fr;
  }
  .mastery-item {
    grid-template-columns: 120px 1fr 44px 44px;
  }
}
</style>
