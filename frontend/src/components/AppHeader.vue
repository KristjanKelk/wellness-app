<template>
  <header class="app-header">
    <div class="container">
      <nav class="navbar">
        <router-link to="/" class="navbar-brand">
          <div class="logo">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16 2C8.268 2 2 8.268 2 16C2 23.732 8.268 30 16 30C23.732 30 30 23.732 30 16C30 8.268 23.732 2 16 2Z" fill="#30C1B1"/>
              <path d="M16 6C13.791 6 12 7.791 12 10V16C12 18.209 13.791 20 16 20C18.209 20 20 18.209 20 16V10C20 7.791 18.209 6 16 6Z" fill="white"/>
              <path d="M12 22C12 23.105 12.895 24 14 24H18C19.105 24 20 23.105 20 22C20 20.895 19.105 20 18 20H14C12.895 20 12 20.895 12 22Z" fill="white"/>
            </svg>
          </div>
          <span class="brand-name">Wellness</span>
        </router-link>

        <div class="nav-menu">
          <template v-if="isLoggedIn">
            <router-link to="/dashboard" class="nav-link">Dashboard</router-link>
            <router-link to="/profile" class="nav-link">Profile</router-link>
            <router-link to="/settings" class="nav-link">Settings</router-link>
            <button @click="logout" class="btn-logout">Logout</button>
          </template>
          <template v-else>
            <router-link to="/login" class="nav-link">Login</router-link>
            <router-link to="/register" class="btn-primary">Sign Up</router-link>
          </template>
        </div>

        <!-- Mobile menu toggle -->
        <button class="mobile-menu-toggle" @click="toggleMobileMenu" aria-label="Toggle menu">
          <span></span>
          <span></span>
          <span></span>
        </button>

        <!-- Mobile menu -->
        <div class="mobile-menu" :class="{ 'is-active': mobileMenuOpen }">
          <div class="mobile-menu-container">
            <button class="mobile-menu-close" @click="closeMobileMenu">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>

            <div class="mobile-menu-items">
              <template v-if="isLoggedIn">
                <router-link to="/dashboard" class="mobile-menu-link" @click="closeMobileMenu">Dashboard</router-link>
                <router-link to="/profile" class="mobile-menu-link" @click="closeMobileMenu">Profile</router-link>
                <router-link to="/settings" class="mobile-menu-link" @click="closeMobileMenu">Settings</router-link>
                <button @click="logoutAndCloseMobile" class="mobile-menu-button">Logout</button>
              </template>
              <template v-else>
                <router-link to="/login" class="mobile-menu-link" @click="closeMobileMenu">Login</router-link>
                <router-link to="/register" class="mobile-menu-button" @click="closeMobileMenu">Sign Up</router-link>
              </template>
            </div>
          </div>
        </div>
      </nav>
    </div>
  </header>
</template>

<script>
import { ref, computed } from 'vue';
import { useStore } from 'vuex';
import { useRouter } from 'vue-router';

export default {
  name: 'AppHeader',
  setup() {
    const store = useStore();
    const router = useRouter();
    const mobileMenuOpen = ref(false);

    const isLoggedIn = computed(() => store.getters['auth/isLoggedIn']);

    const logout = () => {
      store.dispatch('auth/logout');
      router.push('/login');
    };

    const toggleMobileMenu = () => {
      mobileMenuOpen.value = !mobileMenuOpen.value;

      // Disable body scroll when menu is open
      if (mobileMenuOpen.value) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }
    };

    const closeMobileMenu = () => {
      mobileMenuOpen.value = false;
      document.body.style.overflow = '';
    };

    const logoutAndCloseMobile = () => {
      closeMobileMenu();
      logout();
    };

    return {
      isLoggedIn,
      mobileMenuOpen,
      logout,
      toggleMobileMenu,
      closeMobileMenu,
      logoutAndCloseMobile
    };
  }
}
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_utilities.scss';

.app-header {
  background-color: $white;
  box-shadow: $shadow;
  position: sticky;
  top: 0;
  z-index: $z-index-sticky;
}

.navbar {
  @include flex-between;
  height: 64px;
  padding: 0 $spacing-4;
}

.navbar-brand {
  @include flex(row, flex-start, center);
  gap: $spacing-2;
  color: $secondary;
  text-decoration: none;

  &:hover {
    color: $secondary;
  }
}

.logo {
  display: flex;
  align-items: center;
}

.brand-name {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  display: none;

  @include responsive('md') {
    display: block;
  }
}

.nav-menu {
  @include flex(row, flex-end, center);
  gap: $spacing-6;

  @include responsive('md') {
    gap: $spacing-8;
  }

  // Hide on mobile
  @media (max-width: 767px) {
    display: none;
  }
}

.nav-link {
  color: $secondary;
  text-decoration: none;
  font-weight: $font-weight-medium;
  transition: $transition-base;
  position: relative;

  &:hover {
    color: $primary;
  }

  &.router-link-active {
    color: $primary;

    &:after {
      content: '';
      position: absolute;
      bottom: -4px;
      left: 0;
      right: 0;
      height: 2px;
      background-color: $primary;
    }
  }
}

.btn-logout {
  background: none;
  border: none;
  color: $error;
  font-weight: $font-weight-medium;
  cursor: pointer;
  transition: $transition-base;

  &:hover {
    color: darken($error, 10%);
  }
}

// Mobile menu
.mobile-menu-toggle {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 24px;
  height: 18px;
  background: transparent;
  border: none;
  cursor: pointer;

  @include responsive('md') {
    display: none;
  }

  span {
    display: block;
    width: 100%;
    height: 2px;
    background-color: $secondary;
    transition: $transition-base;
  }
}

.mobile-menu {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background-color: rgba($secondary, 0.5);
  z-index: $z-index-modal;
  visibility: hidden;
  opacity: 0;
  .mobile-menu {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  background-color: rgba($secondary, 0.5);
  z-index: $z-index-modal;
  visibility: hidden;
  opacity: 0;
  transition: visibility 0.3s ease, opacity 0.3s ease;

  &.is-active {
    visibility: visible;
    opacity: 1;
  }
}

.mobile-menu-container {
  position: absolute;
  top: 0;
  right: 0;
  width: 80%;
  max-width: 320px;
  height: 100%;
  background-color: $white;
  padding: $spacing-6;
  transform: translateX(100%);
  transition: transform 0.3s ease;

  .is-active & {
    transform: translateX(0);
  }
}

.mobile-menu-close {
  position: absolute;
  top: $spacing-4;
  right: $spacing-4;
  background: none;
  border: none;
  color: $gray;
  cursor: pointer;
  padding: $spacing-2;

  &:hover {
    color: $secondary;
  }
}

.mobile-menu-items {
  display: flex;
  flex-direction: column;
  margin-top: $spacing-8;
}

.mobile-menu-link {
  padding: $spacing-4 0;
  color: $secondary;
  text-decoration: none;
  font-weight: $font-weight-medium;
  border-bottom: 1px solid $gray-lighter;

  &:hover {
    color: $primary;
  }

  &.router-link-active {
    color: $primary;
  }
}

.mobile-menu-button {
  margin-top: $spacing-4;
  @include button-primary;
  display: block;
  width: 100%;
}
}

</style>