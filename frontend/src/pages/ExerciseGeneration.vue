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
                v-for="item in suggestedKnowledge"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>
        </el-form>

        <div class="form-actions">
          <el-button @click="resetForm">重置条件</el-button>
          <el-button type="primary" :loading="generating" @click="handleGenerate">
            生成练习
          </el-button>
        </div>

        <div class="results-section">
          <div class="section-title">生成结果</div>
          <div v-if="exercises.length" class="exercise-list">
            <el-card
              v-for="exercise in exercises"
              :key="exercise.exercise_id"
              class="exercise-card"
              shadow="never"
            >
              <div class="exercise-header">
                <div>
                  <div class="exercise-title">{{ exercise.question }}</div>
                  <div class="exercise-meta">
                    <span class="badge badge-primary">{{ typeLabel(exercise.type) }}</span>
                    <span class="badge badge-success">{{ difficultyLabel(exercise.difficulty) }}</span>
                  </div>
                </div>
                <div class="exercise-id">{{ exercise.exercise_id }}</div>
              </div>

              <div v-if="exercise.options?.length" class="exercise-options">
                <div v-for="option in exercise.options" :key="option.key" class="option-row">
                  <span class="option-key">{{ option.key }}</span>
                  <span class="option-text">{{ option.text }}</span>
                </div>
              </div>

              <div class="exercise-answer">
                <div class="answer-title">标准答案</div>
                <div class="answer-text">
                  {{ formatAnswer(exercise.answer) }}
                </div>
              </div>

              <div v-if="exercise.rubric?.length" class="exercise-rubric">
                <div class="answer-title">评分要点</div>
                <div class="rubric-list">
                  <div v-for="(item, idx) in exercise.rubric" :key="idx" class="rubric-item">
                    <span>{{ item.point }}</span>
                    <span class="rubric-score">+{{ item.score }}</span>
                  </div>
                </div>
              </div>

              <div class="exercise-footer">
                <div class="footer-block">
                  <div class="footer-label">知识点</div>
                  <div class="footer-tags">
                    <span v-for="point in exercise.knowledge_points" :key="point" class="tag">
                      {{ point }}
                    </span>
                  </div>
                </div>
                <div class="footer-block">
                  <div class="footer-label">来源片段</div>
                  <div class="footer-tags">
                    <span v-for="chunk in exercise.source_chunks" :key="chunk" class="tag muted">
                      {{ chunk }}
                    </span>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
          <div v-else class="empty-result">
            暂无练习生成结果，请先选择课程并设置题型与知识点范围。
          </div>
        </div>
      </div>

      <div class="exercise-sidebar">
        <div class="info-card">
          <div class="info-icon">
            <Sparkles :size="18" />
          </div>
          <h3 class="info-title">生成提示</h3>
          <ul class="info-list">
            <li>
              <strong>题型覆盖</strong>
              <p>支持单选 / 判断 / 简答，系统将自动补齐答案与解析。</p>
            </li>
            <li>
              <strong>知识点范围</strong>
              <p>可输入多个关键词作为知识点范围，生成时按顺序覆盖。</p>
            </li>
            <li>
              <strong>引用字段</strong>
              <p>每道题都会附带知识点来源片段 ID，便于追溯。</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { Sparkles } from "lucide-vue-next";
import { ElMessage } from "element-plus";
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

const resetForm = () => {
  selectedTypes.value = ["single_choice", "true_false", "short_answer"];
  difficulty.value = "easy";
  count.value = 10;
  knowledgeScope.value = [];
  exercises.value = [];
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
