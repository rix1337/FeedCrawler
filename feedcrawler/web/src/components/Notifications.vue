<template>
  <div class="alert alert-info container fixed-top" v-model="info" role="alert"
       style="display: none; z-index: 1080;"></div>
  <div class="alert alert-success container fixed-top" v-model="success"
       style="display: none; z-index: 1090;"></div>
  <div class="alert alert-danger container fixed-top" v-model="error"
       style="display: none; z-index: 1100;"></div>
</template>
