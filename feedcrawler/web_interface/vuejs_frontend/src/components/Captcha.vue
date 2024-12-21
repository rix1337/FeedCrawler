<script setup>
import {initializeCaptcha} from '@/obfuscated/captcha.js';
import {inject, onMounted, onUnmounted, ref} from 'vue';
import axios from 'axios';

const toast = inject('toast');

const props = defineProps({
  title: String,
  link: String,
  password: String,
});

const tokenReady = ref(false);

function handleToken(event) {
  const token = event.detail; // Capture token from custom event
  const {title, link, password} = props;

  document.getElementById('puzzle-captcha')?.remove();
  tokenReady.value = true;

  axios
      .post('api/captcha_token/', {
        token,
        title,
        link,
        password,
      })
      .then(function () {
        toast.success('CAPTCHA gelöst, Token: ' + token);
        tokenReady.value = false;
      })
      .catch(function () {
        toast.error('Konnte CAPTCHA nicht lösen, Token: ' + token);
        tokenReady.value = false;
      });
}

onMounted(() => {
  initializeCaptcha(); // Initialize Captcha
  document.addEventListener('captchatoken', handleToken);
});

onUnmounted(() => {
  document.removeEventListener('captchatoken', handleToken);
});
</script>

<template>
  <span v-if="tokenReady" class="spinner-border spinner-border-sm" role="status"></span>
  <div id="captcha" class="card">
    <input type="hidden" id="link-hidden" value=""/>
    <div id="puzzle-captcha" aria-style="mobile">
      <strong>CAPTCHA erscheint nur bei deaktiviertem AdBlocker!</strong>
    </div>
  </div>
</template>
