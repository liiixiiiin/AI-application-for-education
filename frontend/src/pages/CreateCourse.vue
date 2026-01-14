<template>
  <div class="create-course-page">
    <div class="page-header">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/courses' }">工作区</el-breadcrumb-item>
        <el-breadcrumb-item>新建课程</el-breadcrumb-item>
      </el-breadcrumb>
      <h1 class="page-title mt-4">创建新课程</h1>
      <p class="page-subtitle">填入基本信息以开始构建您的实训知识库，AI 将根据这些信息进行初始化</p>
    </div>

    <div class="form-layout">
      <div class="form-main card">
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="handleSubmit"
        >
          <el-form-item label="课程标题" prop="title">
            <el-input
              v-model="form.title"
              placeholder="例如：高级数据库系统实训"
              maxlength="50"
            />
          </el-form-item>

          <el-form-item label="课程描述" prop="description">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="5"
              placeholder="简要描述课程目标、主要内容和受众，这有助于 AI 更好地理解您的需求..."
              maxlength="500"
            />
          </el-form-item>

          <div class="form-footer">
            <el-button @click="$router.push('/courses')">返回</el-button>
            <el-button
              type="primary"
              native-type="submit"
              :loading="loading"
            >
              创建并继续
            </el-button>
          </div>
        </el-form>
      </div>

      <div class="form-sidebar">
        <div class="info-card">
          <div class="info-icon">
            <Info :size="18" />
          </div>
          <h3 class="info-title">下一步工作</h3>
          <ul class="info-list">
            <li>
              <strong>上传知识库</strong>
              <p>创建后，您可以上传 PDF/Markdown 文档作为教学素材。</p>
            </li>
            <li>
              <strong>AI 自动分析</strong>
              <p>系统将自动提取文档中的关键知识点。</p>
            </li>
            <li>
              <strong>生成练习</strong>
              <p>您可以一键生成基于文档内容的随练题。</p>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { apiRequest } from "../services/api";
import { Info } from "lucide-vue-next";
import { ElMessage } from "element-plus";

const router = useRouter();
const loading = ref(false);
const formRef = ref(null);

const form = reactive({
  title: "",
  description: "",
});

const rules = {
  title: [
    { required: true, message: "请输入课程标题", trigger: "blur" },
    { min: 2, max: 50, message: "标题长度应在 2 到 50 个字符之间", trigger: "blur" },
  ],
  description: [
    { required: true, message: "请输入课程描述", trigger: "blur" },
  ],
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        await apiRequest("/courses", {
          method: "POST",
          body: JSON.stringify(form),
        });
        ElMessage.success("课程创建成功");
        router.push("/courses");
      } catch (err) {
        ElMessage.error(err.message || "创建课程失败");
      } finally {
        loading.value = false;
      }
    }
  });
};
</script>

<style scoped>
.create-course-page {
  max-width: 900px;
  margin: 0 auto;
}

.mt-4 {
  margin-top: 16px;
}

.form-layout {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 24px;
  align-items: start;
}

.form-main {
  padding: 32px;
}

.form-footer {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border-soft);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
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

.info-list p {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin: 0;
}

@media (max-width: 768px) {
  .form-layout {
    grid-template-columns: 1fr;
  }
}
</style>
