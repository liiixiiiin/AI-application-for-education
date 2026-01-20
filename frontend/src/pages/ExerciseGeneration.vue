<template>
  <div class="exercise-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/courses' }">工作区</el-breadcrumb-item>
        <el-breadcrumb-item>练习生成</el-breadcrumb-item>
      </el-breadcrumb>
      <h1 class="page-title mt-4">练习生成</h1>
      <p class="page-subtitle">基于课程知识库快速生成多题型练习，输出答案与知识点来源。</p>
    </div>

    <div class="exercise-layout">
      <div class="exercise-main card">
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
            <el-form-item label="题型">
              <el-checkbox-group v-model="selectedTypes">
                <el-checkbox label="single_choice">单选题</el-checkbox>
                <el-checkbox label="true_false">判断题</el-checkbox>
                <el-checkbox label="short_answer">简答题</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
            <el-form-item label="难度">
              <el-radio-group v-model="difficulty">
                <el-radio-button label="easy">基础</el-radio-button>
                <el-radio-button label="medium">进阶</el-radio-button>
                <el-radio-button label="hard">挑战</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="数量">
              <el-input-number v-model="count" :min="1" :max="20" controls-position="right" />
            </el-form-item>
          </div>

          <el-form-item label="知识点范围">
            <el-select
              v-model="knowledgeScope"
              multiple
              filterable
              allow-create
              placeholder="输入或选择知识点"
              style="width: 100%"
            >
              <el-option
                v-for="kp in savedKnowledgePoints"
                :key="kp.id"
                :label="kp.point"
                :value="kp.point"
              />
              <el-option
                v-for="item in suggestedKnowledge"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
            <div class="helper-text">
              <span v-if="!savedKnowledgePoints.length">
                提示：该课程暂无保存的知识点。你可以手动输入，或点击“生成练习”由系统自动提取。
              </span>
              <span v-else>
                已加载该课程保存的 {{ savedKnowledgePoints.length }} 个知识点。留空则自动覆盖。
              </span>
            </div>
          </el-form-item>
        </el-form>

        <div class="form-actions">
          <el-button @click="resetForm">重置条件</el-button>
          <el-button type="primary" :loading="generating" @click="handleGenerate">
            生成练习
          </el-button>
        </div>

        <div class="results-section">
          <div class="section-header">
            <div class="section-title">生成结果</div>
            <div v-if="exercises.length" class="header-actions">
              <el-button type="success" size="small" @click="openSaveDialog">
                保存此批次
              </el-button>
            </div>
          </div>
          <div v-if="exercises.length" class="exercise-list">
            <el-card
              v-for="(exercise, index) in exercises"
              :key="exercise.exercise_id"
              class="exercise-card"
              shadow="never"
            >
              <div class="exercise-header">
                <div class="flex-grow">
                  <div class="exercise-title">
                    <el-input
                      v-model="exercises[index].question"
                      type="textarea"
                      autosize
                      placeholder="题目内容"
                    />
                  </div>
                  <div class="exercise-meta mt-2">
                    <el-tag size="small">{{ typeLabel(exercise.type) }}</el-tag>
                    <el-tag size="small" type="success" class="ml-2">
                      {{ difficultyLabel(exercise.difficulty) }}
                    </el-tag>
                  </div>
                </div>
                <div class="exercise-actions">
                  <el-button
                    type="danger"
                    icon="Delete"
                    circle
                    size="small"
                    @click="removeExercise(index)"
                  />
                </div>
              </div>

              <div v-if="exercise.options?.length" class="exercise-options">
                <div v-for="(option, optIdx) in exercise.options" :key="option.key" class="option-edit-row">
                  <span class="option-key">{{ option.key }}</span>
                  <el-input v-model="exercises[index].options[optIdx].text" size="small" />
                </div>
              </div>

              <div class="exercise-answer mt-4">
                <div class="answer-title">标准答案</div>
                <el-input
                  v-if="exercise.type === 'short_answer'"
                  v-model="exercises[index].answer"
                  type="textarea"
                  autosize
                />
                <el-radio-group
                  v-else-if="exercise.type === 'true_false'"
                  v-model="exercises[index].answer"
                >
                  <el-radio :label="true">正确</el-radio>
                  <el-radio :label="false">错误</el-radio>
                </el-radio-group>
                <el-select
                  v-else-if="exercise.type === 'single_choice'"
                  v-model="exercises[index].answer"
                  placeholder="选择正确选项"
                >
                  <el-option label="A" value="A" />
                  <el-option label="B" value="B" />
                  <el-option label="C" value="C" />
                  <el-option label="D" value="D" />
                </el-select>
              </div>

              <div v-if="exercise.rubric?.length" class="exercise-rubric mt-4">
                <div class="answer-title">评分要点</div>
                <div v-for="(item, rIdx) in exercise.rubric" :key="rIdx" class="rubric-edit-item">
                  <el-input v-model="exercises[index].rubric[rIdx].point" size="small" />
                  <el-input-number
                    v-model="exercises[index].rubric[rIdx].score"
                    :precision="1"
                    :step="0.1"
                    :min="0"
                    :max="1"
                    size="small"
                    style="width: 100px"
                  />
                </div>
              </div>

              <div class="exercise-footer">
                <div class="footer-block">
                  <div class="footer-label">知识点 (逗号分隔)</div>
                  <el-input
                    :model-value="exercise.knowledge_points.join(', ')"
                    @update:model-value="val => exercises[index].knowledge_points = val.split(',').map(s => s.trim())"
                    size="small"
                  />
                </div>
              </div>
            </el-card>
          </div>
          <div v-else class="empty-result">
            暂无练习生成结果，请先选择课程并设置题型与知识点范围。
          </div>
        </div>

        <div class="history-section mt-12">
          <div class="section-header">
            <div class="section-title">历史练习批次</div>
            <el-button size="small" plain @click="loadHistory">刷新列表</el-button>
          </div>
          <el-table :data="history" class="custom-table" style="width: 100%" v-loading="loadingHistory">
            <el-table-column prop="title" label="批次名称" min-width="200" />
            <el-table-column prop="count" label="题目数" width="100" />
            <el-table-column label="生成时间" width="180">
              <template #default="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="scope">
                <el-button size="small" @click="viewBatch(scope.row)">查看/编辑</el-button>
                <el-button size="small" type="danger" plain @click="deleteBatch(scope.row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="exercise-sidebar">
        <div class="info-card">
          <div class="info-icon">
            <Sparkles :size="18" />
          </div>
          <h3 class="info-title">教师功能说明</h3>
          <ul class="info-list">
            <li>
              <strong>编辑题目</strong>
              <p>生成的题目可以直接在卡片中修改内容、选项和答案。</p>
            </li>
            <li>
              <strong>持久化存储</strong>
              <p>点击“保存此批次”将题目以文件形式永久存储，供学生练习。</p>
            </li>
            <li>
              <strong>历史管理</strong>
              <p>在下方列表可以查看和管理以往生成的题目文件。</p>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 保存批次弹窗 -->
    <el-dialog v-model="saveDialogVisible" title="保存练习批次" width="400px">
      <el-form label-position="top">
        <el-form-item label="批次名称">
          <el-input v-model="batchTitle" placeholder="例如：第一章随堂练习" />
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
import { Sparkles, Delete } from "lucide-vue-next";
import { ElMessage, ElMessageBox } from "element-plus";
import { apiRequest } from "../services/api";

const courses = ref([]);
const loadingCourses = ref(false);
const selectedCourse = ref("");
const selectedTypes = ref(["single_choice", "true_false", "short_answer"]);
const difficulty = ref("easy");
const count = ref(10);
const knowledgeScope = ref([]);
const exercises = ref([]);
const generating = ref(false);
const savedKnowledgePoints = ref([]);

const history = ref([]);
const loadingHistory = ref(false);
const saveDialogVisible = ref(false);
const batchTitle = ref("");
const saving = ref(false);
const currentBatchId = ref(null);

const suggestedKnowledge = [
  "主键",
  "外键",
  "关系模型",
  "SQL",
  "索引",
  "事务",
  "范式",
];

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

const loadKnowledgePoints = async () => {
  if (!selectedCourse.value) {
    savedKnowledgePoints.value = [];
    return;
  }
  try {
    const payload = await apiRequest(`/courses/${selectedCourse.value}/knowledge-points`);
    savedKnowledgePoints.value = payload;
  } catch (error) {
    ElMessage.error(error.message || "加载知识点失败");
  }
};

const loadHistory = async () => {
  if (!selectedCourse.value) {
    history.value = [];
    return;
  }
  loadingHistory.value = true;
  try {
    const payload = await apiRequest(`/courses/${selectedCourse.value}/exercises/batches`);
    history.value = payload;
  } catch (error) {
    ElMessage.error(error.message || "加载历史失败");
  } finally {
    loadingHistory.value = false;
  }
};

watch(selectedCourse, () => {
  loadKnowledgePoints();
  loadHistory();
  exercises.value = [];
  currentBatchId.value = null;
});

const handleGenerate = async () => {
  if (!selectedCourse.value) {
    ElMessage.warning("请先选择课程");
    return;
  }
  if (!selectedTypes.value.length) {
    ElMessage.warning("请至少选择一种题型");
    return;
  }
  generating.value = true;
  currentBatchId.value = null;
  try {
    const payload = await apiRequest(
      `/courses/${selectedCourse.value}/exercises/generate`,
      {
        method: "POST",
        body: JSON.stringify({
          course_id: selectedCourse.value,
          count: count.value,
          types: selectedTypes.value,
          difficulty: difficulty.value,
          knowledge_scope: knowledgeScope.value.length ? knowledgeScope.value : null,
        }),
      }
    );
    exercises.value = payload.generated || [];
    ElMessage.success("练习生成完成");
  } catch (error) {
    ElMessage.error(error.message || "练习生成失败");
  } finally {
    generating.value = false;
  }
};

const removeExercise = (index) => {
  exercises.value.splice(index, 1);
};

const openSaveDialog = () => {
  batchTitle.value = `练习批次 ${new Date().toLocaleString()}`;
  saveDialogVisible.value = true;
};

const handleSaveBatch = async () => {
  if (!batchTitle.value.trim()) {
    ElMessage.warning("请输入批次名称");
    return;
  }
  saving.value = true;
  try {
    if (currentBatchId.value) {
      // Update existing
      await apiRequest(`/courses/${selectedCourse.value}/exercises/batches/${currentBatchId.value}`, {
        method: "PUT",
        body: JSON.stringify({
          title: batchTitle.value,
          exercises: exercises.value,
        }),
      });
      ElMessage.success("更新成功");
    } else {
      // Create new
      await apiRequest(`/courses/${selectedCourse.value}/exercises/batches`, {
        method: "POST",
        body: JSON.stringify({
          title: batchTitle.value,
          exercises: exercises.value,
        }),
      });
      ElMessage.success("保存成功");
    }
    saveDialogVisible.value = false;
    await loadHistory();
  } catch (error) {
    ElMessage.error(error.message || "保存失败");
  } finally {
    saving.value = false;
  }
};

const viewBatch = async (batch) => {
  try {
    const payload = await apiRequest(`/courses/${selectedCourse.value}/exercises/batches/${batch.batch_id}`);
    exercises.value = payload.exercises || [];
    currentBatchId.value = batch.batch_id;
    batchTitle.value = batch.title;
    ElMessage.info(`已加载批次：${batch.title}`);
    window.scrollTo({ top: 400, behavior: 'smooth' });
  } catch (error) {
    ElMessage.error(error.message || "加载批次失败");
  }
};

const deleteBatch = async (batch) => {
  try {
    await ElMessageBox.confirm(`确定删除批次「${batch.title}」吗？`, "确认删除", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
    await apiRequest(`/courses/${selectedCourse.value}/exercises/batches/${batch.batch_id}`, {
      method: "DELETE",
    });
    ElMessage.success("删除成功");
    await loadHistory();
    if (currentBatchId.value === batch.batch_id) {
      exercises.value = [];
      currentBatchId.value = null;
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || "删除失败");
    }
  }
};

const formatDate = (value) => {
  if (!value) return "-";
  const d = new Date(value);
  return d.toLocaleString();
};

const resetForm = () => {
  selectedTypes.value = ["single_choice", "true_false", "short_answer"];
  difficulty.value = "easy";
  count.value = 10;
  knowledgeScope.value = [];
  exercises.value = [];
  currentBatchId.value = null;
};

const typeLabel = (type) => {
  const map = {
    single_choice: "单选题",
    true_false: "判断题",
    short_answer: "简答题",
  };
  return map[type] || type;
};

const difficultyLabel = (value) => {
  const map = { easy: "基础", medium: "进阶", hard: "挑战" };
  return map[value] || value;
};

const formatAnswer = (answer) => {
  if (answer === true) return "正确";
  if (answer === false) return "错误";
  return answer || "-";
};

onMounted(loadCourses);
</script>

<style scoped>
.exercise-page {
  max-width: 1100px;
  margin: 0 auto;
}

.mt-4 {
  margin-top: 16px;
}

.exercise-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 24px;
  align-items: start;
}

.exercise-main {
  padding: 32px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border-soft);
}

.results-section {
  margin-top: 32px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 16px;
}

.exercise-list {
  display: grid;
  gap: 16px;
}

.exercise-card {
  border-radius: var(--radius-md);
  border-color: var(--color-border-soft);
}

.exercise-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.exercise-actions {
  flex-shrink: 0;
}

.option-edit-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.rubric-edit-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.ml-2 {
  margin-left: 8px;
}

.mt-2 {
  margin-top: 8px;
}

.mt-12 {
  margin-top: 48px;
}

.flex-grow {
  flex-grow: 1;
}

.history-section {
  padding-top: 32px;
  border-top: 2px dashed var(--color-border-soft);
}

.exercise-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 8px;
}

.exercise-meta {
  display: flex;
  gap: 8px;
}

.exercise-id {
  font-size: 12px;
  color: var(--color-text-muted);
}

.exercise-options {
  margin: 16px 0;
  display: grid;
  gap: 8px;
}

.option-row {
  display: flex;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 10px;
  background: var(--color-bg-alt);
}

.option-key {
  font-weight: 700;
  color: var(--color-text-main);
}

.option-text {
  color: var(--color-text-secondary);
}

.exercise-answer {
  padding: 12px;
  border-radius: 10px;
  background: #f8fafc;
  margin-bottom: 12px;
}

.exercise-rubric {
  padding: 12px;
  border-radius: 10px;
  background: #fff7ed;
}

.answer-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.answer-text {
  font-size: 13px;
  color: var(--color-text-main);
}

.rubric-list {
  display: grid;
  gap: 6px;
}

.rubric-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.rubric-score {
  font-weight: 600;
  color: #f97316;
}

.exercise-footer {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border-soft);
}

.footer-label {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
  margin-bottom: 6px;
}

.footer-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.1);
  color: var(--color-primary);
  font-size: 11px;
  font-weight: 600;
}

.tag.muted {
  background: rgba(15, 23, 42, 0.06);
  color: var(--color-text-secondary);
}

.empty-result {
  padding: 20px;
  border-radius: var(--radius-sm);
  background: var(--color-bg-alt);
  color: var(--color-text-muted);
  font-size: 14px;
}

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
  margin-bottom: 20px;
}

.info-list strong {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-main);
  margin-bottom: 4px;
}

@media (max-width: 1000px) {
  .exercise-layout {
    grid-template-columns: 1fr;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .exercise-footer {
    grid-template-columns: 1fr;
  }
}
</style>
