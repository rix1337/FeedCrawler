<script setup>
import "@/assets/scss/app.scss";
import { useStore } from "vuex";

const store = useStore();
</script>

<template>
	<router-view />
</template>