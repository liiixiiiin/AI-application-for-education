<template>
  <div class="split-login-container">
    <!-- Left Side: Brand Visual -->
    <div class="visual-side">
      <div class="visual-content">
        <div class="logo-box-large">
          <BookOpen :size="32" />
        </div>
        <div class="visual-text">
          <h1 class="brand-heading">Empowering Education with AI.</h1>
          <p class="brand-subheading">
            构建您的专属知识库，利用大模型驱动的智能教学体，让每一堂实训课都变得精准而高效。
          </p>
        </div>
        
        <div class="feature-badges">
          <div class="f-badge"><CheckCircle :size="16" /> RAG 增强问答</div>
          <div class="f-badge"><CheckCircle :size="16" /> 自动练习生成</div>
          <div class="f-badge"><CheckCircle :size="16" /> 实时学情分析</div>
        </div>
      </div>
      <!-- Background Abstract Shape -->
      <div class="abstract-shape"></div>
    </div>

    <!-- Right Side: Login Form -->
    <div class="form-side">
      <div class="login-box-wrapper">
        <div class="mobile-logo">
          <BookOpen :size="24" />
          <span>教育智能体</span>
        </div>

        <div class="form-header">
          <h2 class="form-title">{{ activeTab === 'login' ? '欢迎回来' : '创建新账号' }}</h2>
          <p class="form-subtitle">
            {{ activeTab === 'login' ? '请输入您的凭据以访问控制中心' : '只需几步，开启您的智能化教学之旅' }}
          </p>
        </div>

        <div class="tabs-container">
          <div class="custom-segmented-control">
            <button 
              class="segment-item" 
              :class="{ active: activeTab === 'login' }"
              @click="activeTab = 'login'"
            >
              账户登录
            </button>
            <button 
              class="segment-item" 
              :class="{ active: activeTab === 'register' }"
              @click="activeTab = 'register'"
            >
              新用户注册
            </button>
          </div>
        </div>

        <transition name="fade" mode="out-in">
          <div :key="activeTab" class="form-content-area">
            <!-- Login Form -->
            <el-form
              v-if="activeTab === 'login'"
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              label-position="top"
              @submit.prevent="handleLogin"
            >
              <el-form-item label="电子邮箱" prop="email">
                <el-input
                  v-model="loginForm.email"
                  placeholder="name@university.edu"
                />
              </el-form-item>
              <el-form-item label="安全密码" prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="••••••••"
                  show-password
                />
              </el-form-item>
              <div class="form-footer-actions">
                <el-button
                  type="primary"
                  class="full-width-btn"
                  :loading="loading"
                  native-type="submit"
                >
                  立即登录
                </el-button>
              </div>
            </el-form>

            <!-- Register Form -->
            <el-form
              v-else
              ref="registerFormRef"
              :model="registerForm"
              :rules="registerRules"
              label-position="top"
              @submit.prevent="handleRegister"
            >
              <el-form-item label="您的姓名" prop="name">
                <el-input v-model="registerForm.name" placeholder="张三" />
              </el-form-item>
              <el-form-item label="电子邮箱" prop="email">
                <el-input v-model="registerForm.email" placeholder="name@university.edu" />
              </el-form-item>
              <el-form-item label="账户角色" prop="role">
                <el-select v-model="registerForm.role" placeholder="请选择您的权限身份" style="width: 100%">
                  <el-option label="👨‍🏫 教师 (备课与管理)" value="teacher" />
                  <el-option label="🎓 学生 (练习与答疑)" value="student" />
                  <el-option label="⚙️ 管理员 (系统维护)" value="admin" />
                </el-select>
              </el-form-item>
              <el-form-item label="设置密码" prop="password">
                <el-input v-model="registerForm.password" type="password" placeholder="至少 6 位字符" show-password />
              </el-form-item>
              <div class="form-footer-actions">
                <el-button
                  type="primary"
                  class="full-width-btn"
                  :loading="loading"
                  native-type="submit"
                >
                  创建我的账号
                </el-button>
              </div>
            </el-form>
          </div>
        </transition>

        <div class="copyright-notice">
          © 2026 智能实训平台. 专业的 AI 教学解决方案.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { apiRequest } from "../services/api";
import { setSession } from "../stores/session";
import { BookOpen, CheckCircle } from "lucide-vue-next";
import { ElMessage } from "element-plus";

const router = useRouter();
const activeTab = ref("login");
const loading = ref(false);

const loginForm = reactive({
  email: "",
  password: "",
});

const registerForm = reactive({
  name: "",
  email: "",
  role: "teacher",
  password: "",
});

const loginRules = {
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "请输入正确的邮箱格式", trigger: "blur" },
  ],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const registerRules = {
  name: [{ required: true, message: "请输入姓名", trigger: "blur" }],
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "请输入正确的邮箱格式", trigger: "blur" },
  ],
  role: [{ required: true, message: "请选择角色", trigger: "change" }],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码长度不能少于 6 位", trigger: "blur" },
  ],
};

const handleLogin = async () => {
  loading.value = true;
  try {
    const data = await apiRequest("/auth/login", {
      method: "POST",
      body: JSON.stringify(loginForm),
    });
    setSession(data.token, data.user);
    ElMessage.success("登录成功，欢迎进入");
    router.push("/courses");
  } catch (error) {
    ElMessage.error(error.message || "登录失败");
  } finally {
    loading.value = false;
  }
};

const handleRegister = async () => {
  loading.value = true;
  try {
    const data = await apiRequest("/auth/register", {
      method: "POST",
      body: JSON.stringify(registerForm),
    });
    setSession(data.token, data.user);
    ElMessage.success("注册成功，开启旅程");
    router.push("/courses");
  } catch (error) {
    ElMessage.error(error.message || "注册失败");
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.split-login-container {
  display: flex;
  min-height: 100vh;
  width: 100%;
  background-color: white;
}

/* Left Side Styles */
.visual-side {
  flex: 1.2;
  background-color: #0f172a;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px;
}

.visual-content {
  position: relative;
  z-index: 10;
  max-width: 600px;
}

.logo-box-large {
  width: 64px;
  height: 64px;
  background: white;
  color: #0f172a;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  margin-bottom: 48px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.brand-heading {
  font-size: 56px;
  font-weight: 800;
  color: white;
  line-height: 1.1;
  margin-bottom: 24px;
  letter-spacing: -0.05em;
}

.brand-subheading {
  font-size: 20px;
  color: #94a3b8;
  line-height: 1.6;
  margin-bottom: 40px;
}

.feature-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.f-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 99px;
  color: #f1f5f9;
  font-size: 14px;
  font-weight: 500;
}

.abstract-shape {
  position: absolute;
  top: -10%;
  right: -10%;
  width: 800px;
  height: 800px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%);
  filter: blur(60px);
}

/* Right Side Styles */
.form-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background-color: #f8fafc;
}

.login-box-wrapper {
  width: 100%;
  max-width: 420px;
}

.mobile-logo {
  display: none;
  align-items: center;
  gap: 12px;
  font-weight: 700;
  margin-bottom: 40px;
}

.form-header {
  margin-bottom: 40px;
}

.form-title {
  font-size: 32px;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 8px 0;
  letter-spacing: -0.03em;
}

.form-subtitle {
  color: #64748b;
  font-size: 16px;
}

.custom-segmented-control {
  display: flex;
  background: #f1f5f9;
  padding: 4px;
  border-radius: 10px;
  margin-bottom: 32px;
}

.segment-item {
  flex: 1;
  border: none;
  background: transparent;
  padding: 10px;
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  border-radius: 7px;
  transition: all 0.2s;
}

.segment-item.active {
  background: white;
  color: #0f172a;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.full-width-btn {
  width: 100%;
  padding: 14px !important;
  font-size: 16px !important;
}

.copyright-notice {
  margin-top: 48px;
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
}

@media (max-width: 1024px) {
  .visual-side {
    display: none;
  }
  .mobile-logo {
    display: flex;
  }
  .form-side {
    background-color: white;
  }
}
</style>
