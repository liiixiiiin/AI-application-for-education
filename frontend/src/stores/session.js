import { ref } from "vue";

const TOKEN_KEY = "edu_token";
const USER_KEY = "edu_user";

const loadSession = () => {
  const token = localStorage.getItem(TOKEN_KEY);
  const rawUser = localStorage.getItem(USER_KEY);
  return {
    token,
    user: rawUser ? JSON.parse(rawUser) : null,
  };
};

export const sessionState = ref(loadSession());

export const getSession = () => sessionState.value;

export const setSession = (token, user) => {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
  sessionState.value = { token, user };
};

export const clearSession = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  sessionState.value = { token: null, user: null };
};
