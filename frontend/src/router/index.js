import { createRouter, createWebHistory } from "vue-router";
import LoginPage from "../pages/Login.vue";
import CoursesPage from "../pages/Courses.vue";
import CreateCoursePage from "../pages/CreateCourse.vue";
import AdminDashboard from "../pages/AdminDashboard.vue";
import { getSession } from "../stores/session";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/login" },
    { path: "/login", component: LoginPage },
    { path: "/courses", component: CoursesPage },
    { path: "/courses/new", component: CreateCoursePage },
    { path: "/admin", component: AdminDashboard },
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
  return true;
});

export default router;
