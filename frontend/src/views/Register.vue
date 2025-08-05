<template>
  <div class="register-container">
    <form @submit.prevent="handleRegister" class="register-form">
      <h2>Register</h2>

      <div class="form-group">
        <label for="username">Username</label>
        <input
            type="text"
            id="username"
            v-model="username"
            required
            placeholder="Choose a username"
        />
      </div>

      <div class="form-group">
        <label for="email">Email</label>
        <input
            type="email"
            id="email"
            v-model="email"
            required
            placeholder="Enter your email"
        />
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <input
            type="password"
            id="password"
            v-model="password"
            required
            placeholder="Create a password"
        />
      </div>

      <div class="form-group">
        <label for="password2">Confirm Password</label>
        <input
            type="password"
            id="password2"
            v-model="password2"
            required
            placeholder="Confirm your password"
        />
      </div>

      <div v-if="message" class="alert" :class="successful ? 'alert-success' : 'alert-danger'">
        {{ message }}
      </div>

      <div class="form-group">
        <button class="btn btn-primary btn-block" :disabled="loading">
          <span v-if="loading">Loading...</span>
          <span v-else>Register</span>
        </button>
      </div>

      <div class="form-group text-center">
        <p>
          Already have an account?
          <router-link to="/login">Login here</router-link>
        </p>
      </div>
    </form>
  </div>
</template>

<script>
export default {
  name: 'Register',
  data() {
    return {
      username: '',
      email: '',
      password: '',
      password2: '',
      loading: false,
      message: '',
      successful: false
    };
  },
  methods: {
    handleRegister() {
      this.message = '';
      this.successful = false;
      this.loading = true;

      if (this.password !== this.password2) {
        this.message = "Passwords don't match";
        this.loading = false;
        return;
      }

      this.$store.dispatch('auth/register', {
        username: this.username,
        email: this.email,
        password: this.password,
        password2: this.password2
      }).then(
          data => {
            this.message = data.message || "Registration successful! You can now login.";
            this.successful = true;
            this.loading = false;

            // Redirect to login after a delay
            setTimeout(() => {
              this.$router.push('/login');
            }, 2000);
          },
          error => {
            this.message = (error.response && error.response.data)
                ? Object.values(error.response.data).flat().join(', ')
                : "Registration failed. Please try again.";
            this.successful = false;
            this.loading = false;
          }
      );
    }
  }
};
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80vh;
  padding: 2rem;
}

.register-form {
  width: 100%;
  max-width: 400px;
  padding: 2rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
}

h2 {
  text-align: center;
  margin-bottom: 2rem;
  color: #333;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.btn {
  cursor: pointer;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  font-size: 1rem;
}

.btn-primary {
  background-color: #4CAF50;
  color: white;
}

.btn-block {
  width: 100%;
}

.alert {
  padding: 0.75rem;
  margin-bottom: 1rem;
  border-radius: 4px;
}

.alert-danger {
  background-color: #f8d7da;
  color: #721c24;
}

.alert-success {
  background-color: #d4edda;
  color: #155724;
}

.text-center {
  text-align: center;
}
</style>