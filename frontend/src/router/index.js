import { createRouter, createWebHistory } from "vue-router";
import LoginPage from "../pages/Login.vue";
import CoursesPage from "../pages/Courses.vue";
import CreateCoursePage from "../pages/CreateCourse.vue";
import KnowledgeBaseUploadPage from "../pages/KnowledgeBaseUpload.vue";
import AdminDashboard from "../pages/AdminDashboard.vue";
import RagQaPage from "../pages/RagQa.vue";
import ExerciseGenerationPage from "../pages/ExerciseGeneration.vue";
import ExerciseGradingPage from "../pages/ExerciseGrading.vue";
import { getSession } from "../stores/session";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/login" },
    { path: "/login", component: LoginPage },
    { path: "/courses", component: CoursesPage },
    { path: "/courses/new", component: CreateCoursePage },
    { path: "/knowledge-base", component: KnowledgeBaseUploadPage },
    { path: "/admin", component: AdminDashboard },
    { path: "/qa", component: RagQaPage },
    { path: "/exercises", component: ExerciseGenerationPage },
    { path: "/exercises/grade", component: ExerciseGradingPage },
  ],
});

router.beforeEach((to) => {
  const session = getSession();
  if (to.path !== "/login" && !session.token) {
    return "/login";
  }
  if (to.path === "/courses/new" && session.user?.role !== "teacher") {
    return "/courses";
  }
  if (
    to.path === "/knowledge-base" &&
    session.user?.role !== "teacher" &&
    session.user?.role !== "admin"
  ) {
    return "/courses";
  }
  if (
    to.path === "/exercises" &&
    session.user?.role !== "teacher" &&
    session.user?.role !== "admin"
  ) {
    return "/courses";
  }
  return true;
});

export default router;
