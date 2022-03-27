<script setup>
// ToDo migrate to vue
/*function showSuccess(message) {
    $(".alert-success").html(message).fadeTo(3000, 500).slideUp(500, function () {
        $(".alert-success").slideUp(500);
    });
}

function showInfo(message) {
    $(".alert-info").html(message).fadeTo(10000, 500).slideUp(500, function () {
        $(".alert-info").slideUp(500);
    });
}

function showInfoLong(message) {
    $(".alert-info").html(message).show();
}

function showDanger(message) {
    $(".alert-danger").html(message).fadeTo(5000, 500).slideUp(500, function () {
        $(".alert-danger").slideUp(500);
    });
}*/
</script>

<template>
  <div class="alert alert-info container fixed-top" v-text="info" role="alert"
       style="display: none; z-index: 1080"></div>
  <div class="alert alert-success container fixed-top" v-text="success"
       style="display: none; z-index: 1090"></div>
  <div class="alert alert-danger container fixed-top" v-text="error"
       style="display: none; z-index: 1100"></div>
</template>
